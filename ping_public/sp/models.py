from django.db import models
from django.db import connections

class Entity(models.Model):
    VALIDATE_RESPONSE = 'RESPONSE'
    VALIDATE_ASSERTION = 'ASSERTION'
    SIGNATURE_VALIDATION_CHOICES = [
        (VALIDATE_RESPONSE, 'Validate Signature in SAML Response'),
        (VALIDATE_ASSERTION, 'Validate Signature in SAML Assertion'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    entity_id = models.CharField(max_length=100)
    virtual_server_id = models.CharField(max_length=100, blank=True)
    is_encrypted = models.BooleanField(default=False)
    signature_validation = models.CharField(
        max_length=100,
        choices=SIGNATURE_VALIDATION_CHOICES,
        default=VALIDATE_RESPONSE,
    )
    default_relay_state = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.entity_id

    def get_destination(self, relay_state):
        # method to find the destination based on the relay_state
        '''
        I think this needs to be changed so that the relaystate doesn't have to match exactly.
        Old:
        destination = Destination.objects.filter(entity__id=self.id, relaystate__url_pattern=relay_state)
        New:
        destination = Destination.objects.filter(entity__id=self.id, relaystate__url_pattern__istartswith=relay_state)
        Note: Could also do iregex or regex to match the URL. That'd probably work better but be more complicated
        '''
        used_default_relay_state_flag = False
        if relay_state == None:
            relay_state = self.default_relay_state
            used_default_relay_state_flag = True
        #destination = Destination.objects.filter(entity__id=self.id, relaystate__url_pattern=relay_state)
        destination = Destination.objects.filter(entity__id=self.id, relaystate__url_pattern__istartswith=relay_state)
        if len(destination) != 1:
            if used_default_relay_state_flag:
                message = 'No RelayState was received.\n Attempted to use default RelayState value of: ' + str(relay_state)
            else:
                message = 'The RelayState that was received did not match any of the configured RelayStates \
                            for this Connection.\n\t Received RelayState: ' + str(relay_state)
            raise Exception(message)
        return destination[0]


class Certificate(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    certificate = models.TextField()
    certificate_info = models.TextField()
    expiration_date = models.DateTimeField()

    def __str__(self):
        return 'Still need to parse the certs and get their info.'

    def get_public_key(self):
        return self.certificate

class Destination(models.Model):
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    destination_endpoint = models.CharField(max_length=200)
    data_store = models.CharField(max_length=100, default='default')

    def __str__(self):
        return self.name

    def get_all_attributes(self):
        return Attribute.objects.filter(destination__id=self.id)

class RelayState(models.Model):
    '''
    This model still needs some work.
        1) I'm not sure if PF currently sends the OpenToken to a certain URL per application
            or if it just goes to the RelayState with that OpenToken as a cookie/querystring?
        2) It might be helpful to return a RegEx for the url_pattern
            or at least do relaystate.starts_with(url_pattern) like pingfed does
    '''
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    url_pattern = models.CharField(max_length=200)

    def __str__(self):
        return self.url_pattern


class Attribute(models.Model):
    ASSERTION_VALUE = 'ASSERTION'
    ALTER_ASSERTION_VALUE = 'ALTER'
    QUERY = 'QUERY'
    STRING = 'STRING'
    ATTRIBUTE_TYPES = [
        (ASSERTION_VALUE, 'Take value as is from the assertion.'),
        (ALTER_ASSERTION_VALUE, 'Take value from the assertion and alter it.'),
        (QUERY, 'Use values from the assertion to run a query.'),
        (STRING, 'Add a static string to the token.'),
    ]

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    attribute_type = models.CharField(
        max_length=100,
        choices=ATTRIBUTE_TYPES,
        default=ASSERTION_VALUE,
    )
    attribute_name = models.CharField(max_length=100)
    attribute_value = models.CharField(max_length=100, blank=True)
    query = models.TextField(blank=True, null=True)
    query_parameters = models.ManyToManyField("self", blank=True)
    token_attribute_name = models.CharField(max_length=100, default='test')
    include_in_token = models.BooleanField(default=False)

    def __str__(self):
        return self.attribute_name

    def get_token_value(self, received_attributes, data_store='default'):
        '''
        :param data_store: indicates the data_store to run a query on when necessary.
        :param received_attributes: a dict that contains the attriutes received in the SAML.
        :return: a tuple that contains a key/value to be added to the token.
        '''
        if self.attribute_type == 'ASSERTION':
            if self.attribute_name in received_attributes:
                #attr_name = str(self.attribute_name)
                # in order to add the attribute to the token with a different name
                token_attribute_name = self.token_attribute_name
                attr_value = received_attributes[self.attribute_name]
                # return token_attribute_name, attr_value
                return {
                    'name': token_attribute_name,
                    'value': attr_value,
                    'include_in_token': self.include_in_token
                }
        elif self.attribute_type == 'STRING':
            # return self.token_attribute_name, self.attribute_value
            return {
                'name': self.token_attribute_name,
                'value': self.attribute_value,
                'include_in_token': self.include_in_token
            }
        elif self.attribute_type == 'QUERY':
            query = self.query
            query_parameters = dict()
            for param in self.query_parameters.all():
                name = param.attribute_name
                value = received_attributes[param.attribute_name]
                query_parameters[name] = value

            with connections[data_store].cursor() as cursor:
                result_set = cursor.execute(query, query_parameters)
                result = cursor.fetchone()[0]
                return {
                    'name': self.token_attribute_name,
                    'value': result,
                    'include_in_token': self.include_in_token
                }


def format_query(query, db_type):
    '''
    SQLite requires you to write your queries like this:
        SELECT username FROM users WHERE username  = :username
    Whereas Oracle lets you write them like this:
        SELECT username FROM users WHERE username  = %(username)s

    I want this function to reformat the queries for SQLite while I'm testing.

    Note: Would never be able to use this in prod since it wouldn't protect against sql injection

    :param query:
    :param db_type:
    :return:
    '''
    if db_type == 'sqlite':
        more_params = True
        working = query
        while more_params:
            substitution_index = working.index("%(")
            working[substitution_index:].replace(")", "", 1)
            working = working[:substitution_index] + working[substitution_index:].replace(")", "", 1)
            working.replace("%(", ":", 1)
            print(working)
            if "%(" not in working:
                more_params = False
        return working


        working = query.replace("%(", ":")
