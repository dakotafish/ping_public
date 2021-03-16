from django.db import models
from django.db import connections
from signxml import XMLVerifier

import re
import xmlsec

class Entity(models.Model):
    '''Top Level Entity Class. The top of the heirarchy, its children include Destination, Certificate, and PrivateKey.'''
    VALIDATE_RESPONSE = 'RESPONSE'
    VALIDATE_ASSERTION = 'ASSERTION'
    SIGNATURE_VALIDATION_CHOICES = [
        (VALIDATE_RESPONSE, 'Validate Signature in SAML Response'),
        (VALIDATE_ASSERTION, 'Validate Signature in SAML Assertion'),
    ]

    entity_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    virtual_server_id = models.CharField(max_length=100, blank=True, null=True)
    is_encrypted = models.BooleanField(default=False)
    signature_validation = models.CharField(
        max_length=100,
        choices=SIGNATURE_VALIDATION_CHOICES,
        default=VALIDATE_RESPONSE,
    )
    # TODO - This should instead be default_destination and it should be a dropdown that allows you to choose from
    #  the existing destinations on this config.
    #  However, this could be tricky when initially creating the configuration.
    #  Maybe when adding a destination the UI should ask the user "make default?" each time.
    #  And if it's the only destination then you don't have a choice but to make it the default.
    default_relay_state = models.ForeignKey('RelayState', on_delete=models.RESTRICT, blank=True, null=True)
    # TODO - Entity and PrivateKey should have a Many2Many relationship
    private_keys = models.ManyToManyField("PrivateKey", blank=True)

    def build_entity(self, relay_state):
        # If the relaystate doesn't match anything that we have configured or if the client didnt send
        # a relaystate then we'll just use the default.
        self.relay_state = self.default_relay_state
        self.destination = self.default_relay_state.destination
        if relay_state:
            all_destinations = Destination.objects.filter(entity__id=self.id)
            for destination in all_destinations:
                # this will return the first relay_state that matches, regardless of if there are multiple matches
                matching_relay_state = destination.find_matching_relay_state(relay_state)
                if matching_relay_state:
                    self.relay_state = matching_relay_state
                    self.destination = destination
                    return self
        return self

    def check_signature(self, raw_saml_response):
        certificates = Certificate.objects.filter(entity__id=self.id)
        for cert in certificates:
            verified_saml = cert.validate_signature(raw_saml_response)
            if verified_saml:
                return verified_saml
        # if we made it this far then we failed to validate the signature
        # TODO - Need to raise a proper exception here.
        message = 'Failed to validate Signature with the following certificates:\n\t'
        print(message)
        for i in certificates: print(i)
        raise Exception(message)

    def decrypt_saml(self, verified_saml):
        # TODO - PrivateKey and Entity should be Many2Many so this lookup will need to be fixed.
        keys = PrivateKey.objects.filter(entity__id=self.id)
        for key in keys:
            decrypted_saml = key.decrypt_saml(verified_saml)
            if decrypted_saml:
                return decrypted_saml
        # if we made it this far then we failed to decrypt the saml
        # TODO - Need to raise a proper exception here.
        message = 'Failed to decrypt saml with the following keys:\n\t'
        print(message)
        for i in keys: print(i)
        raise Exception(message)


class Certificate(models.Model):
    '''Second Level Certificate Class. Responsible for verifying signatures.'''
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    certificate = models.TextField()
    #certificate_info = models.TextField(blank=True, null=True)
    #expiration_date = models.DateTimeField(blank=True, null=True)
    # TODO - Should probably store CN, Issue Date, Expiration, ect.
    subject = models.CharField(max_length=100, blank=True, null=True)
    issuer = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    subject_name_hash = models.CharField(max_length=100, blank=True, null=True)
    #not_before = models.CharField(max_length=100, blank=True, null=True)
    #not_after = models.CharField(max_length=100, blank=True, null=True)
    issue_date = models.DateTimeField(blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    common_name = models.CharField(max_length=100, blank=True, null=True)

    def validate_signature(self, raw_saml_response):
        cert = self.certificate
        try:
            verified = XMLVerifier().verify(raw_saml_response, x509_cert=cert, ignore_ambiguous_key_info=True)
        except Exception as e:
            # TODO - Need to handle this would-be exception properly but Im not sure what exception type this will throw
            print('\nFailed to Verify Signature. Exception:\n')
            print(e)
            # if the signature validation failed then we'll just return None so that the entity can try the next cert
            return None
        else:
            # if the signature validation worked then we'll return the verified saml
            return verified.signed_xml

class PrivateKey(models.Model):
    '''Second Level PrivateKey Class. Responsible for decrypting assertions and signing authN requests.'''
    #entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    # TODO - The key will need to be encrypted eventually
    key = models.TextField()
    key_info = models.TextField(blank=True, null=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    # TODO - allowed_decryption_methods needs to be a field and configurable on this model
    allowed_decryption_methods = ['aes128-cbc', 'aes256-cbc', 'tripledes-cbc']

    def decrypt_saml(self, verified_saml):
        '''
        1) First we determine the encryption method and set the key_data_constant appropriately
        '''
        encryption_method_node = verified_saml.find('{*}EncryptedAssertion').find('{*}EncryptedData').find('{*}EncryptionMethod')
        if encryption_method_node is not None:
            """
            Supported Encryption Algorithms are:
                Algorithm="http://www.w3.org/2001/04/xmlenc#aes128-cbc"
                Algorithm="http://www.w3.org/2001/04/xmlenc#aes256-cbc"
                Algorithm="http://www.w3.org/2001/04/xmlenc#tripledes-cbc"
            """
            encryption_method = encryption_method_node.attrib['Algorithm']
            encryption_method = encryption_method.split('#')[-1]
            if 'DES' in encryption_method.upper():
                key_data_constant = xmlsec.constants.KeyDataDes
            else:
                key_data_constant = xmlsec.constants.KeyDataAes
        # TODO - This assert should be an exception
        assert encryption_method in self.allowed_decryption_methods
        '''
        2) Next we Locate the EncryptedKey element 
            The EncryptedKey element will either be embedded inside the KeyInfo element
            OR the RetrievalMethod will Reference the EncryptedKey element ID
            Search 'RetrievalMethod' here for more info:
                http://docs.oasis-open.org/security/saml/v2.0/sstc-saml-errata-2.0-cd-04.html
        '''
        key_info = verified_saml.find('{*}EncryptedAssertion').find('{*}EncryptedData').find('{*}KeyInfo')
        if key_info.find('{*}EncryptedKey') is not None:
            # If the EncryptedKey is embedded inside KeyInfo then just grab it and move on.
            encrypted_key = key_info.find('{*}EncryptedKey')
        elif key_info.find('{*}RetrievalMethod') is not None:
            # If there is a RetrievalMethod then we need to search for the EncryptedKey
            enc_assertion = verified_saml.find('{*}EncryptedAssertion')
            reference_uri = key_info.find('{*}RetrievalMethod').attrib['URI'].strip('#')
            namespaces = {'enc': 'http://www.w3.org/2001/04/xmlenc#'}
            # TODO - Need to make sure this nonsense with the id casing is necessary.. it might not be.
            id_alternatives = ['Id', 'id', 'ID']
            for id_case in id_alternatives:
                xpath_expression = "//enc:EncryptedKey[@{0} = '{1}']".format(id_case, reference_uri)
                enc_key = enc_assertion.xpath(xpath_expression, namespaces=namespaces)
                if enc_key is not None:
                    encrypted_key = enc_key
                    break
        assert encrypted_key is not None
        '''
        3) Now we add our private key to the encryption context so that we can decrypt the encrypted_key
        '''
        try:
            key_manager = xmlsec.KeysManager()
            '''
            This can be changed to load the key from a file like so if necessary:
                key_manager.add_key(xmlsec.Key.from_file(key, xmlsec.KeyFormat.PEM))
            '''
            key_manager.add_key(xmlsec.Key.from_data(self.key, xmlsec.KeyFormat.PEM))
            encryption_context = xmlsec.EncryptionContext(key_manager)
            key_data = encryption_context.decrypt(encrypted_key)
            assert key_data is not None
        except Exception as e:
            # TODO - This exception needs to be more specific but I don't know what kind of exception it will throw yet
            print('Failed decryption with key: ')
            print(e)
            # We failed to decrypt key_data so we should return None so that Entity knows to try the next key.
            return None
        '''
        4) Now that we decrypted encrypted_key we clear the encryption context and use that key to decrypt the assertion
        '''
        encryption_context.reset()
        encryption_context.key = xmlsec.Key.from_binary_data(self.key_data_constant, key_data)
        encrypted_data = verified_saml.find('{*}EncryptedAssertion').find('{*}EncryptedData')
        decrypted_assertion = encryption_context.decrypt(encrypted_data)
        encryption_context.reset()
        encrypted_assertion = verified_saml.find('{*}EncryptedAssertion')
        verified_saml.remove(encrypted_assertion)
        verified_saml.append(decrypted_assertion)
        return verified_saml

class TokenConfiguration(models.Model):
    COOKIE = 'COOKIE'
    QUERY_STRING = 'QUERY_STRING'
    TOKEN_LOCATION_CHOICES = [
        (COOKIE, 'Send the token as a Cookie'),
        (QUERY_STRING, 'Send the token as a Query String'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    token_name = models.CharField(max_length=20)
    token_location = models.CharField(
        max_length=50,
        choices=TOKEN_LOCATION_CHOICES,
        default=QUERY_STRING,
    )
    # TODO - The token_password will need to be encrypted eventually
    token_password = models.CharField(max_length=100)

class Destination(models.Model):
    '''Second Level Destination Class. Its children include RelayState and Attribute.'''
    # COOKIE = 'COOKIE'
    # QUERY_STRING = 'QUERY_STRING'
    # TOKEN_LOCATION_CHOICES = [
    #     (COOKIE, 'Send the token as a Cookie'),
    #     (QUERY_STRING, 'Send the token as a Query String'),
    # ]

    token_configuration = models.ForeignKey(TokenConfiguration, on_delete=models.RESTRICT, blank=True, null=True)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    # token_name = models.CharField(max_length=20)
    # token_location = models.CharField(
    #     max_length=50,
    #     choices=TOKEN_LOCATION_CHOICES,
    #     default=QUERY_STRING,
    # )
    # # TODO - The token_password will need to be encrypted eventually
    # token_password = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    def find_matching_relay_state(self, received_relay_state):
        all_relay_states = RelayState.objects.filter(destination__id=self.id)
        for relay_state in all_relay_states:
            if relay_state.matches(received_relay_state):
                return relay_state
        # if we made it this far then none of the relay_states for this destination matched so we return None.
        return None

    def process_attributes(self, saml_attributes, data_store):
        all_attributes = Attribute.objects.filter(destination__id=self.id)
        token = dict()
        for attribute in all_attributes:
            if attribute.include_in_token:
                token_attribute = attribute.process_attribute(saml_attributes, data_store)
                token[token_attribute['name']] = token_attribute['value']


class DataStore(models.Model):
    name = models.CharField(max_length=100, default='default')
    key = models.CharField(max_length=100, default='default')
    description = models.TextField()

    def __str__(self):
        return self.name


class RelayState(models.Model):
    '''Third Level RelayState Class.'''
    SIMPLE = 'SIMPLE'
    REGEX = 'REGEX'
    URL_PATTERN_CHOICES = [
        (SIMPLE, 'Simple URL Match with wildcard(*).'),
        (REGEX, 'Python Regular Expression Match.'),
    ]

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    destination_endpoint = models.CharField(max_length=200)
    # TODO - Need a seperate DataStore model so that this isn't just some random string here.
    #data_store = models.CharField(max_length=100, default='default')
    data_store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    url_pattern = models.CharField(max_length=200)
    pattern_type = models.CharField(
        max_length=50,
        choices=URL_PATTERN_CHOICES,
        default=SIMPLE,
    )

    def matches(self, relay_state):
        # return True if the URL Pattern matches what we received, otherwise return false.
        pattern = self.url_pattern
        if self.url_pattern == self.SIMPLE:
            pattern = self.format_pf_expression()
        match = re.match(pattern, relay_state, re.IGNORECASE)
        if match:
            return True
        else:
            return False

    def format_pf_expression(self):
        ''''
        We can pretty easily support the PingFed style URL matching syntax here.
        As far as I can tell they just use * as a wildcard. ie https://*.url.com* matches https://anything.url.com/uri
        The (non-greedy) Python Regex equivalent would be something like this: https://.*?\.url\.com.*
        So if we escape the . and ? characters and then replace * with .*? we should be good to go.
        '''
        pattern = self.url_pattern
        pattern = pattern.replace('?', r'\?')
        pattern = pattern.replace('.', r'\.')
        pattern = pattern.replace('*', r'.*?')
        return pattern

# class DataStore(models.Model):
#     name = models.CharField(max_length=100)
#     description = models.TextField()
#     configuration = models.TextField()

class Attribute(models.Model):
    '''
    Third Level Attribute Class.
    There are three types of attributes at the moment.
    1) Assertion Type - We take a value received in a SAML Attribute and add it to the Token.
    2) String Type - We just add a static value directly to the Token.
    3) Query Type - We use the values in the SAML Attributes to Query a value from a database.
    '''
    saml_attribute_name_help_text = "The name of the attribute received in the SAML"
    include_in_token_help_text = "Should this be included in the token that is passed to the application?"
    token_attribute_name_help_text = "The name to give the attribute value when adding it to the token that is passed "\
                                     "to the application."
    token_attribute_value_help_text = "The value to add to the token that is passed to the application."
    query_help_text = """Use the SAML Attribute Values in a SQL query. Given an Attribute named SSO_ID, the correct
                          syntax would be: \n\t\t SELECT username FROM users WHERE username  = %(SSO_ID)s 
                          \nThis syntax protects against SQL injection and is the only parameter substitution that should
                          be used."""
    ASSERTION = 'ASSERTION'
    STRING = 'STRING'
    QUERY = 'QUERY'
    ATTRIBUTE_TYPE_CHOICES = [
        (ASSERTION, 'ASSERTION - Take a value from a SAML Attribute and add it to the token.'),
        (STRING, 'STRING - Add a static string value to the token.'),
        (QUERY, 'QUERY - Use the SAML Attributes to run a query. Add the query result to the token.'),
    ]

    destination = models.ForeignKey(Destination, on_delete=models.CASCADE)
    attribute_type = models.CharField(
        max_length=50,
        choices=ATTRIBUTE_TYPE_CHOICES,
        default=ASSERTION,
    )
    saml_attribute_name = models.CharField(max_length=100, help_text=saml_attribute_name_help_text,
                                           blank=True, null=True)
    include_in_token = models.BooleanField(default=False, help_text=include_in_token_help_text)
    token_attribute_name = models.CharField(max_length=100, blank=True, null=True,
                                            help_text=token_attribute_name_help_text)
    token_attribute_value = models.CharField(max_length=100, blank=True, null=True,
                                             help_text=token_attribute_value_help_text)
    query = models.TextField(blank=True, null=True, help_text=query_help_text)
    query_parameters = models.ManyToManyField("Attribute", blank=True)
    # TODO - I'm not sure if this is the best strategy. I can use ManyToMany like this and the user will choose from \
    #  the existing attributes set up on this destination. OR This could be a delimted field and the user just gives \
    #  a list of the attribute names.

    def process_attribute(self, saml_attributes, data_store):
        if self.attribute_type == self.STRING:
            return self.process_string_attribute()
        elif self.attribute_type == self.ASSERTION:
            return self.process_assertion_attribute(saml_attributes)
        elif self.attribute_type == self.QUERY:
            return self.process_query_attribute(saml_attributes, data_store)
        else:
            return None

    def process_string_attribute(self):
        return {
            'name': self.token_attribute_name,
            'value': self.token_attribute_value
        }

    def process_assertion_attribute(self, saml_attributes):
        if self.saml_attribute_name in saml_attributes:
            return {
                'name': self.token_attribute_name,
                'value': saml_attributes[self.saml_attribute_name]
            }
        else:
            return {
                'name': self.token_attribute_name,
                'value': '0'
            }

    def process_query_attribute(self, saml_attributes, data_store):
        query = self.query
        query_parameters = dict()
        for param in self.query_parameters.all():
            name = param.saml_attribute_name
            value = saml_attributes[name]
            query_parameters[name] = value
        with connections[data_store].cursor() as cursor:
            result_set = cursor.execute(query, query_parameters)
            result = cursor.fetchone()
            if result is not None:
                result = result[0]
            else:
                result = "None"
            return {
                'name': self.token_attribute_name,
                'value': result,
            }