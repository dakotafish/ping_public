from lxml import etree
from signxml import XMLVerifier
from base64 import b64decode
import datetime
#import xmlsec
#import Crypto.Cipher.AES as AES
# Need to remove Crypto.Cipher.AES dependency

from sp.models import Entity, Certificate
from .saml_decrypter import SamlDecrypter



#test_cert_location = '/Users/dfischer/Documents/bf_certs/test.partner.benefitfocus.com.crt'
#test_cert = open(test_cert_location, 'rb').read()
#test_cert = test_cert.decode()


class SamlProcessor:
    #test_cert = open('/Users/dfischer/Documents/bf_certs/test.partner.benefitfocus.com.crt', 'rb').read().decode()

    def __init__(self, saml_response):
        self.saml_response = b64decode(saml_response)
        self.xml_verifier_object = None
        self.signed_data = None
        self.signed_xml = None
        self.signature_xml = None

        self.entity = None
        self.issuer_id = None
        self.certificates = None
        self.active_cert = None

        self.find_config()
        self.validate_signature()
        self.saml = Saml(self.signed_xml)
        self.validate_saml()

    def find_config(self):
        root = etree.fromstring(self.saml_response)
        issuer_id = root.find('{*}Issuer').text
        self.entity = Entity.objects.get(entity_id__iexact=issuer_id)
        self.issuer_id = self.entity.entity_id
        self.certificates = Certificate.objects.filter(entity__id=self.entity.id)



    def validate_signature(self):
        '''
        verified = XMLVerifier().verify(self.saml_response, x509_cert=test_cert,
                                         ignore_ambiguous_key_info=True)
        '''
        for certificate in self.certificates:
            cert = certificate.certificate
            try:
                verified = XMLVerifier().verify(self.saml_response, x509_cert=cert,
                                            ignore_ambiguous_key_info=True)
            #except signxml.exceptions.InvalidSignature as e:
            except Exception as e:
                print(e)
            else:
                self.active_cert = cert
                self.xml_verifier_object = verified
                self.signed_data = verified.signed_data
                self.signed_xml = verified.signed_xml
                self.signature_xml = verified.signature_xml
        if self.active_cert is None:
            message = 'Failed to validate Signature with the following certificates:\n\t'
            # need to include list of attempted certs in the exception
            # but first need to parse cert info and store it in the database
            raise Exception(message)

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
            raise Exception(message)
        if now > not_on_or_after:
            message = 'SAML is violating notOnOrAfter condition.\n\t'
            message += 'Now = ' + str(now) + '\n\tnotOnOrAfter = ' + str(not_on_or_after)
            raise Exception(message)
        # check saml status (this might not be necessary)
        if 'success' not in str(self.saml.status).lower():
            message = 'SAML status is NOT success. \n\t Status: ' + str(self.saml.status)
            raise Exception(message)



class Saml:

    def __init__(self, verified_saml):
        # There's lots of room for this to be trimmed down.
        self.verified_saml = verified_saml
        self.testing_saml_data = dict()

        saml = self.verified_saml
        self.destination = saml.attrib['Destination']
        self.issue_instant = saml.attrib['IssueInstant']
        self.id = saml.attrib['ID']
        self.issuer = saml.find('{*}Issuer').text
        self.status = saml.find('{*}Status').find('{*}StatusCode').attrib['Value']
        self.assertion = saml.find('{*}Assertion')
        self.assertion_id = self.assertion.attrib['ID']
        self.assertion_issue_instant = self.assertion.attrib['IssueInstant']
        self.assertion_issuer = self.assertion.find('{*}Issuer').text
        self.subject = self.assertion.find('{*}Subject')
        self.name_id = self.subject.find('{*}NameID')
        self.saml_subject = self.subject.find('{*}NameID').text
        self.name_id_format = self.name_id.attrib['Format']
        self.subject_confirmation_data = self.subject.find('{*}SubjectConfirmation').find('{*}SubjectConfirmationData')
        self.recipient = self.subject_confirmation_data.attrib['Recipient']
        #not_on_or_after = subject_confirmation_data['NotOnOrAfter']
        self.conditions = self.assertion.find('{*}Conditions')
        self.not_before = self.conditions.attrib['NotBefore']
        self.not_on_or_after = self.conditions.attrib['NotOnOrAfter']
        self.audience_restriction = self.conditions.find('{*}AudienceRestriction').find('{*}Audience').text

        # Attribute information
        attributes = dict()
        attr_statement = self.assertion.find('{*}AttributeStatement')
        attrs = attr_statement.findall('{*}Attribute')
        for attr in attrs:
            attribute_name = attr.attrib['Name']
            attribute_value = attr.find('{*}AttributeValue').text
            attributes[attribute_name] = attribute_value
        attributes['saml_subject'] = self.saml_subject
        self.attributes = attributes
