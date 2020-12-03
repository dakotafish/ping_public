from lxml import etree
from base64 import b64decode
import datetime

from sp.models import Entity


class SamlProcessor:

    def __init__(self, saml_response, relay_state):
        self.raw_saml_response = b64decode(saml_response)
        self.received_relay_state = relay_state
        self.entity = None
        self.verified_saml = None
        self.saml = None
        self.processed_attributes = None

        self.build_entity()
        self.process_signature_and_encryption()
        self.saml = Saml(self.verified_saml)
        self.validate_saml()
        self.process_saml_attributes()

    def build_entity(self):
        issuer_id = etree.fromstring(self.raw_saml_response).find('{*}Issuer').text.strip()
        entity = Entity.objects.get(entity_id__iexact=issuer_id)
        self.entity = entity.build_entity(self.received_relay_state)

    def process_signature_and_encryption(self):
        verified_saml = self.entity.check_signature(self.raw_saml_response)
        if verified_saml:
            self.verified_saml = verified_saml

        if self.entity.is_encrypted:
            decrypted_saml = self.entity.decrypt_saml(self.verified_saml)
            if decrypted_saml:
                self.verified_saml = decrypted_saml

    def validate_saml(self):
        # check audience restriction
        audience = 'benefitfocus.com:sp'
        if self.entity.virtual_server_id:
            audience = self.entity.virtual_server_id
        if audience != self.saml.audience_restriction:
            message = "AudienceRestriction in the SAML does not match the configuration. \t"
            message += str(self.saml.audience_restriction) + ' != ' + str(audience)
            raise Exception(message)
        # check notBefore & notAfter
        now = datetime.datetime.utcnow()
        not_before = datetime.datetime.strptime(self.saml.not_before, "%Y-%m-%dT%H:%M:%S.%fZ")
        not_on_or_after = datetime.datetime.strptime(self.saml.not_on_or_after, "%Y-%m-%dT%H:%M:%S.%fZ")
        if now < (not_before - datetime.timedelta(minutes=5)):
            message = 'SAML is violating notBefore condition.\n\t'
            message += 'Now = ' + str(now) + '\n\tNotBefore = ' + str(not_before - datetime.timedelta(minutes=5))
            # TODO - Need better exceptions
            raise Exception(message)
        if now > not_on_or_after:
            message = 'SAML is violating notOnOrAfter condition.\n\t'
            message += 'Now = ' + str(now) + '\n\tnotOnOrAfter = ' + str(not_on_or_after)
            raise Exception(message)
        # check saml status (might not be necessary)
        if 'success' not in str(self.saml.status).lower():
            message = 'SAML status is NOT success. \n\t Status: ' + str(self.saml.status)
            raise Exception(message)

    def process_saml_attributes(self):
        saml_attributes = self.saml.attributes
        self.processed_attributes = self.entity.destination.process_attributes(saml_attributes,
                                                                               self.entity.relay_state.data_store)


class Saml:

    def __init__(self, verified_saml):
        if isinstance(verified_saml, str):
            self.verified_saml = etree.fromstring(verified_saml)
        else:
            self.verified_saml = verified_saml
        saml = self.verified_saml
        if saml.attrib:
            attrs = saml.attrib
            self.destination = attrs['Destination']
            self.response_id = attrs['ID']
            self.issue_instant = attrs['IssueInstant']
        self.issuer = saml.find('{*}Issuer').text
        self.status = saml.find('{*}Status').find('{*}StatusCode').attrib['Value']
        assertion = saml.find('{*}Assertion')
        self.assertion_id = assertion.attrib['ID']
        subject = assertion.find('{*}Subject')
        self.saml_subject = subject.find('{*}NameID').text
        subject_confirmation = subject.find('{*}SubjectConfirmation').find('{*}SubjectConfirmationData')
        self.destination = subject_confirmation.attrib['Recipient']
        conditions = assertion.find('{*}Conditions')
        self.not_before = conditions.attrib['NotBefore']
        self.not_on_or_after = conditions.attrib['NotOnOrAfter']
        self.audienct_restriction = conditions.find('{*}AudienceRestriction').find('{*}Audience').text
        # Attribute Information
        attr_statement = assertion.find('{*}AttributeStatement')
        attributes = dict()
        attrs = attr_statement.findall('{*}Attribute')
        for attr in attrs:
            attribute_name = attr.attrib['Name']
            attribute_value = attr.find('{*}AttributeValue').text
            attributes[attribute_name] = attribute_value
        # This if statement just avoids a key error if someone sends an attribute named saml_subject
        if 'saml_subject' not in attributes:
            attributes['saml_subject'] = self.saml_subject
        self.attributes = attributes

    def __str__(self):
        return etree.tostring(self.verified_saml).decode()