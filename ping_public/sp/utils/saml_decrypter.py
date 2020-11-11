import xmlsec
from lxml import etree

'''
Reference: https://github.com/mehcode/python-xmlsec/blob/master/tests/test_enc.py
    test_decrypt_key()
'''


class SamlDecrypter:

    def __init__(self, saml, decryption_keys, allowed_decryption_methods=['aes128-cbc', 'aes256-cbc', 'tripledes-cbc']):
        """
        saml -> An lxml object, in this case it should be a SAML Response with an Encrypted Assertion
        decryption_keys -> a list of raw private key data to attempt to decrypt the assertion with
        allowed_decryption_methods -> a list of acceptable encryption methods (Allows us to restrict encryption methods)
        """
        #self.saml = etree.fromstring(saml)
        # the saml argument will already be an xml object
        self.saml = saml
        self.allowed_decryption_methods = allowed_decryption_methods
        self.decryption_keys = decryption_keys
        self.encryption_method = None
        self.key_data_constant = None
        self.decrypted_assertion = None

        self.set_encryption_information()
        self.decrypt()

    def set_encryption_information(self):
        """ Determine the Encryption Method used and sets encryption_method & key_data_constant on the class """
        encryption_method_node = self.saml.find('{*}EncryptedAssertion').find('{*}EncryptedData').find('{*}EncryptionMethod')
        if encryption_method_node is not None:
            """
            Supported Encryption Algorithms are:
                Algorithm="http://www.w3.org/2001/04/xmlenc#aes128-cbc"
                Algorithm="http://www.w3.org/2001/04/xmlenc#aes256-cbc"
                Algorithm="http://www.w3.org/2001/04/xmlenc#tripledes-cbc"
            """
            encryption_method = encryption_method_node.attrib['Algorithm']
            encryption_method = encryption_method.split('#')
            self.encryption_method = encryption_method[-1]
            if 'DES' in self.encryption_method.upper():
                self.key_data_constant = xmlsec.constants.KeyDataDes
            else:
                self.key_data_constant = xmlsec.constants.KeyDataAes
        assert self.encryption_method in self.allowed_decryption_methods

    def decrypt(self):
        key_info = self.saml.find('{*}EncryptedAssertion').find('{*}EncryptedData').find('{*}KeyInfo')
        # The EncryptedKey element will either be embedded inside the KeyInfo element
        #  OR the RetrievalMethod will Reference the EncryptedKey element ID
        #  Search 'RetrievalMethod' here for more info:
        #   http://docs.oasis-open.org/security/saml/v2.0/sstc-saml-errata-2.0-cd-04.html
        if key_info.find('{*}EncryptedKey') is not None:
            # If the EncryptedKey is embedded inside KeyInfo then just grab it and move on.
            encrypted_key = key_info.find('{*}EncryptedKey')
        elif key_info.find('{*}RetrievalMethod') is not None:
            # If there is a RetrievalMethod then we need to search for the EncryptedKey
            enc_assertion = self.saml.find('{*}EncryptedAssertion')
            reference_uri = key_info.find('{*}RetrievalMethod').attrib['URI']
            reference_uri = reference_uri.strip('#')
            namespaces = {'enc': 'http://www.w3.org/2001/04/xmlenc#'}
            id_alternatives = ['Id', 'id', 'ID']
            for id_case in id_alternatives:
                xpath_expression = "//enc:EncryptedKey[@{0} = '{1}']".format(id_case, reference_uri)
                enc_key = enc_assertion.xpath(xpath_expression, namespaces=namespaces)
                if enc_key is not None:
                    encrypted_key = enc_key
                    break
        assert encrypted_key is not None
        # first we add our private key to the encryption context so that we can decrypt encrypted_key
        for key in self.decryption_keys:
            try:
                key_manager = xmlsec.KeysManager()
                #key_manager.add_key(xmlsec.Key.from_file(self.test_private_key, xmlsec.KeyFormat.PEM))
                # this will need to be changed to .from_data() once the keys are in the database
                key_manager.add_key(xmlsec.Key.from_file(key, xmlsec.KeyFormat.PEM))
                encryption_context = xmlsec.EncryptionContext(key_manager)
                key_data = encryption_context.decrypt(encrypted_key)
                if key_data is not None:
                    break
            except Exception as e:
                print('Failed decryption with key: ' + str(key))
                print(e)
        # Once we have decrypted encrypted_key we clear the encryption context and use that key to decrypt the assertion
        encryption_context.reset()
        encryption_context.key = xmlsec.Key.from_binary_data(self.key_data_constant, key_data)
        encrypted_data = self.saml.find('{*}EncryptedAssertion').find('{*}EncryptedData')
        decrypted_assertion = encryption_context.decrypt(encrypted_data)
        self.decrypted_assertion = decrypted_assertion
        encryption_context.reset()
        encrypted_assertion = self.saml.find('{*}EncryptedAssertion')
        self.saml.remove(encrypted_assertion)
        self.saml.append(decrypted_assertion)