from sp.models import PrivateKey
from lxml import etree

# to import this to the django shell use:
# from sp.utils.saml_tools import decrypt_saml

def decrypt_saml(key_id=1, saml_string=''):
    pk = PrivateKey.objects.get(pk=key_id)
    saml = etree.fromstring(saml_string)
    decrypted = pk.decrypt_saml(saml)
    return etree.tostring(decrypted).decode()

