from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

import json
from lxml import etree

from .utils.saml_processor import SamlProcessor

@method_decorator(csrf_exempt, name='dispatch')
class ServiceProvider(generic.ListView):
    attr = None

    def get(self, request, *args, **kwargs):
        return HttpResponse("Test")

    def post(self, request, *args, **kwargs):
        post_data = request.POST.copy()
        saml_response = post_data['SAMLResponse']
        if 'RelayState' in post_data:
            relay_state = post_data['RelayState']
        else:
            relay_state = None

        validated_saml = SamlProcessor(saml_response)

        token = self.build_token(validated_saml, relay_state)

        #validated_saml = validate_signature(saml_response)
        #if validated_saml is not None:
        #print(validated_saml.signed_xml)
        #return HttpResponse(str(validated_saml.issuer_id))
        #return HttpResponse(etree.tostring(validated_saml.signed_xml))
        #return HttpResponse(validated_saml.issuer_id)
        #return HttpResponse(str(validated_saml.issuer_id) + '--' + str(validated_saml.active_cert) + '--' + str(etree.tostring(validated_saml.signed_xml)))

        #test = 't--\n'
        #for k, v in validated_saml.saml.testing_saml_data.items():
        #    data = str(k) + ' --- ' + str(v) + '\n'
        #    test += data
        #return HttpResponse(test)

        #display = '<ul><li>Coffee</li><li>Tea</li><li>Milk</li></ul>'
        """
        display = '<ul>'
        display += ('<li>' + 'destination: ' + str(validated_saml.saml.destination) + '</li>')
        display += ('<li>' + 'issuer: ' + str(validated_saml.saml.issuer) + '</li>')
        display += ('<li>' + 'saml_subject: ' + str(validated_saml.saml.saml_subject) + '</li>')
        display += ('<li>' + 'recipient: ' + str(validated_saml.saml.recipient) + '</li>')
        display += ('<li>' + 'audience_restriction: ' + str(validated_saml.saml.audience_restriction) + '</li>')
        display += ('<li>' + 'status: ' + str(validated_saml.saml.status) + '</li>')
        for k, v in validated_saml.saml.attributes.items():
            display += ('<li>' + 'attr_name: ' + str(k) + '\tattr_value: ' + str(v) + '</li>')
        for k,v in token.items():
            display += ('<li>' + 'token_attr_name: ' + str(k) + '\ttoken_attr_value: ' + str(v) + '</li>')
        display += ('</ul')
        return HttpResponse(display)
        """
        display = '<ol>'
        display += ('<li>' + 'Issuer: ' + str(validated_saml.saml.issuer) + '</li>')
        display += ('<li>' + 'Audience: ' + str(validated_saml.saml.audience_restriction) + '</li>')
        # style="text-indent: 40px"
        display += ('<li>' + 'SAML Attributes Received: </li><ul>')
        for k, v in validated_saml.saml.attributes.items():
            display += ('<li>' + 'Attribute Name: ' + str(k) + '</li><li style="text-index: 40px">Attribute Value: ' + str(v) + '</li><br>')
        display += ('</ul><li>' + 'Generated Token: </li><br>')
        pretty_token = json.dumps(token, indent=None, separators=(',<br>', ': '))
        #display += '<p style="text-indent: 40px">' + pretty_token + '</p>'
        display += pretty_token
        return HttpResponse(display)

    def build_token(self, validated_saml, relay_state):
        entity = validated_saml.entity
        received_attributes = validated_saml.saml.attributes
        destination = entity.get_destination(relay_state)
        '''
        Probably need to add a method to dynamically find the datastore.
         Something like datastore = 'Dynamic' and then give a hash table {'attribute1/destination1/relaystate1': 'datastore1', 'attribute2/destination2/relaystate2': 'datastore2'}
         Then select the attribute/destination/relaystate to use to return the correct datastore from the hash table.
        '''
        data_store = destination.data_store
        attributes = destination.get_all_attributes()

        token_attributes = []
        for attribute in attributes:
            result = attribute.get_token_value(received_attributes, data_store)
            token_attributes.append(result)

        token = dict()
        for token_attribute in token_attributes:
            if token_attribute['include_in_token']:
                token[token_attribute['name']] = token_attribute['value']
        # pretty print the token with  print(json.dumps(token, indent=None, separators=(',\n', ': ')))
        return token
