from django.http import HttpResponse
from django.shortcuts import render
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json

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
            relay_state = post_data['RelayState'].strip()
        else:
            relay_state = None

        saml_processor = SamlProcessor(saml_response, relay_state)
        token = saml_processor.processed_attributes

        display = '<ol>'
        display += ('<li>' + 'Issuer: ' + str(saml_processor.saml.issuer) + '</li>')
        display += ('<li>' + 'Audience: ' + str(saml_processor.saml.audience_restriction) + '</li>')
        display += ('<li>' + 'SAML Attributes Received: </li><ul>')
        for k, v in saml_processor.saml.attributes.items():
            display += ('<li>' + 'Attribute Name: ' + str(k) + '</li><li style="text-index: 40px">Attribute Value: ' + str(v) + '</li><br>')
        display += ('</ul><li>' + 'Generated Token: </li><br>')
        pretty_token = json.dumps(token, indent=None, separators=(',<br>', ': '))
        display += pretty_token
        return HttpResponse(display)