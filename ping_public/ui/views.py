from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from sp.models import Entity, Certificate, Destination, RelayState, Attribute
from .forms import EntityForm, CertificateForm, DestinationForm, RelayStateForm, AttributeForm


from django.template.loader import render_to_string
from django.template import RequestContext



class Meta:
    templates = {
        'ENTITY': 'entity-detail.html',
        'CERTIFICATE': 'certificate_form.html',
        'DESTINATION': 'destination_form.html',
        'RELAYSTATE': 'relaystate_form.html',
        'ATTRIBUTE': 'attribute_form.html',
    }

    def __init__(self, model, model_instance, parent_model, parent_instance):
        self.model = model.upper()
        self.model_instance = model_instance
        self.model_instance_id = model_instance.id
        self.parent_model = parent_model
        self.parent_instance = parent_instance
        self.parent_instance_id = parent_instance.id
        self.update_url = reverse('Update', kwargs={
            'role': 'sp',
            'model': self.model,
            'model_id': self.model_instance_id
        })
        self.delete_url = reverse('Delete', kwargs={
            'role': 'sp',
            'model': self.model,
            'model_id': self.model_instance_id
        })
        self.create_new_url = reverse('CreateNew', kwargs={
            'role': 'sp',
            'model': self.model,
            'parent_instance': self.parent_instance_id
        })
        self.template = self.templates[self.model]
        self.form = None
        self.set_form()
        self.unique_element_id = self.model + "_" + str(self.model_instance_id)

    def set_form(self):
        forms = {
            'ENTITY': EntityForm(instance=self.model_instance),
            'CERTIFICATE': CertificateForm(),
            'DESTINATION': DestinationForm(instance=self.model_instance),
            'RELAYSTATE': RelayStateForm(instance=self.model_instance),
            'ATTRIBUTE': AttributeForm(instance=self.model_instance),
        }
        self.form = forms[self.model]


class EntityTemplate(Meta):

    def __init__(self, model, model_instance, parent_model, parent_instance):
        super().__init__(model, model_instance, parent_model, parent_instance)
        self.new_certificate = None
        self.certificates = []
        self.set_certificates()
        self.destinations = []
        self.set_destinations()


    def set_certificates(self):
        # self.new_certificate is used in the template to create a new blank certificate form
        self.new_certificate = Meta('CERTIFICATE', self.model_instance, 'ENTITY', self.model_instance)
        certificates = Certificate.objects.filter(entity__id=self.model_instance_id)
        for certificate in certificates:
            cert_meta = Meta('CERTIFICATE', certificate, 'ENTITY', self.model_instance)
            self.certificates.append(cert_meta)

    def set_destinations(self):
        destinations = Destination.objects.filter(entity__id=self.model_instance_id)
        for destination in destinations:
            destination_meta = DestinationTemplate('DESTINATION', destination, 'ENTITY', self.model_instance)
            self.destinations.append(destination_meta)


class DestinationTemplate(Meta):

    def __init__(self, model, model_instance, parent_model, parent_instance):
        super().__init__(model, model_instance, parent_model, parent_instance)
        self.relay_states = []
        self.set_relay_states()
        self.attributes = []
        self.set_attributes()

    def set_relay_states(self):
        relay_states = RelayState.objects.filter(destination__id=self.model_instance_id)
        for relay_state in relay_states:
            relay_state_meta = Meta('RELAYSTATE', relay_state, 'DESTINATION', self.model_instance)
            self.relay_states.append(relay_state_meta)

    def set_attributes(self):
        attributes = Attribute.objects.filter(destination__id=self.model_instance_id)
        for attribute in attributes:
            attribute_meta = Meta('ATTRIBUTE', attribute, 'DESTINATION', self.model_instance)
            self.attributes.append(attribute_meta)


class NewEntityDetail(generic.DetailView):

    def get(self, request, *args, **kwargs):
        entity_key = kwargs['pk']
        entity_instance = Entity.objects.get(pk=entity_key)
        entity_template = EntityTemplate(model='ENTITY',
                                model_instance=entity_instance,
                                parent_model='ENTITY',
                                parent_instance=entity_instance)
        return render(request=request,
                      template_name=entity_template.template,
                      context={'entity_template': entity_template})




class Update(generic.DetailView):
    SUCCESS = {'status': 200, 'message': 'Saved Successfully.'}
    FAIL = {'status': 500, 'message': 'Something went wrong, please try again. Errors: {0}'}

    def post(self, request, *args, **kwargs):
        model = kwargs['model']
        model_instance_id = kwargs['model_id']
        post_data = request.POST.copy()
        status = self.process_update(model=model, model_instance_id=model_instance_id, post_data=post_data)
        return HttpResponse(status['message'], status=status['status'])

    def process_update(self, model, model_instance_id, post_data):
        model_to_update = model.upper()
        if model_to_update == 'ENTITY':
            model_instance = Entity.objects.get(pk=model_instance_id)
            form = EntityForm(post_data, instance=model_instance)
        elif model_to_update == 'DESTINATION':
            model_instance = Destination.objects.get(pk=model_instance_id)
            form = DestinationForm(post_data, instance=model_instance)
        elif model_to_update == 'ATTRIBUTE':
            model_instance = Attribute.objects.get(pk=model_instance_id)
            form = AttributeForm(post_data, instance=model_instance)
        elif model_to_update == 'RELAYSTATE':
            model_instance = RelayState.objects.get(pk=model_instance_id)
            form = RelayStateForm(post_data, instance=model_instance)
        if form.is_valid():
            form.save()
            return self.SUCCESS
        else:
            # TODO - Need a better method of passing status messages
            # To produce one of the validation errors just remove "required=False" from parent_instance on the entity form
            errors = form.errors.as_text()
            status = self.FAIL
            status['message'] = status['message'].format(errors)
            return status


class Delete(generic.DetailView):
    SUCCESS = {'STATUS': 200, 'MESSAGE': 'Deleted Successfully.'}
    FAIL = {'STATUS': 500, 'MESSAGE': 'Something went wrong, please try again. Errors: {0}'}

    def delete(self, request, *args, **kwargs):
        # to access the body of a delete request you just use request.body
        model = kwargs['model']
        model_instance_id = kwargs['model_id']
        status = self.process_delete(model=model, model_instance_id=model_instance_id)
        #return HttpResponse(status['message'], status=status['status'])
        return JsonResponse(status) #, safe=False)

    def process_delete(self, model, model_instance_id):
        model = model.upper()
        if model == 'CERTIFICATE':
            model_instance = Certificate.objects.get(pk=model_instance_id).delete()
            return self.SUCCESS
        else:
            error = "Failed to delete object with pk=" + str(model_instance_id)
            status = self.FAIL
            status['message'] = status['message'].format(error)
            return status



class CreateNew(generic.DetailView):
    model_map = {
        'DESTINATION': {
            'FORM': DestinationForm(),
            #'MODEL_INSTANCE': Destination(name='Creating New'),
            'TEMPLATE': 'destination-form.html'
        },
        'RELAYSTATE': {
            'FORM': RelayStateForm(),
            'MODEL_INSTANCE': RelayState(),
            'TEMPLATE': 'relaystate-form.html'
        },
        'ATTRIBUTE': {
            'FORM': AttributeForm(),
            'TEMPLATE': 'attribute-form.html'
        },
    }

    def get(self, request, *args, **kwargs):
        model = kwargs['model'].upper()
        parent_instance = kwargs['parent_instance']
        form = set_form_initial(form=self.model_map[model]['FORM'],
                                model=model,
                                model_instance=self.model_map[model]['MODEL_INSTANCE'],
                                parent_instance=parent_instance)
        return render(request=request,
                      template_name=self.model_map[model]['TEMPLATE'],
                      context={'form': form})

    def post(self, request, *args, **kwargs):
        model = kwargs['model']
        parent_instance = kwargs['parent_instance']
        post_data = request.POST.copy()
        files = request.FILES
        status = self.process_new_model(model=model, parent_instance=parent_instance, post_data=post_data, files=files)
        #return HttpResponse(status)
        return JsonResponse(status, safe=False)

    def process_new_model(self, model, parent_instance, post_data, files):
        model_to_update = model.upper()
        if model_to_update == 'ENTITY':
            form = EntityForm(post_data)
        elif model_to_update == 'DESTINATION':
            entity = Entity.objects.get(pk=parent_instance)
            form = DestinationForm(post_data)
            form.instance.entity = entity
        elif model_to_update == 'ATTRIBUTE':
            destination = Destination.objects.get(pk=parent_instance)
            form = AttributeForm(post_data)
            form.instance.destination = destination
        elif model_to_update == 'RELAYSTATE':
            destination = Destination.objects.get(pk=parent_instance)
            form = RelayStateForm(post_data)
            form.instance.destination = destination
        elif model_to_update == 'CERTIFICATE':
            form = CertificateForm(post_data)
            if form['certificate_text'].value():
                certificate = form['certificate_text'].value()
            else:
                certificate = ""
                for chunk in files['certificate_file'].chunks():
                    certificate += chunk.decode()

            if form.is_valid() and len(certificate) > 0:
                new_model_instance = form.save_certificate(certificate=certificate, parent_instance=parent_instance)
                new_update_url = reverse('Update', kwargs={
                    'role': 'sp',
                    'model': model_to_update,
                    'model_id': new_model_instance.id,
                })
                status = {
                    'MESSAGE': 'SUCCESS',
                    'UPDATE_URL': new_update_url,
                }
                print(status)
                return status


        # if form.is_valid():
        #     new_model_instance = form.save()
        #     new_update_url = reverse('Update', kwargs={
        #         'role': 'sp',
        #         'model': model_to_update,
        #         'model_id': new_model_instance.id
        #     })
        #     status = {
        #         'MESSAGE': 'SUCCESS',
        #         'UPDATE_URL': new_update_url,
        #     }
        #     print(status)
        #     return status
        else:
            # TODO - Need a better method of passing status messages
            # To produce one of the validation errors when testing just remove "required=False" from parent_instance on the entity form
            errors = form.errors.as_data()
            return errors



# def set_form_initial(form, model, model_instance, parent_instance):
#     form.initial['model'] = model
#     form.MODEL = model
#     form.initial['model_instance'] = model_instance
#     form.MODEL_INSTANCE = model_instance
#     form.initial['parent_instance'] = parent_instance
#     form.PARENT_INSTANCE = parent_instance
#     return form











# class zNewEntityDetail(generic.DetailView):
#
#     def get(self, request, *args, **kwargs):
#         primary_key = kwargs['pk']
#         entity_certs = Certificate.objects.filter(entity__id=primary_key)
#         destinations = Destination.objects.filter(entity__id=primary_key)
#         #destination = DestinationForm(instance=destinations[0])
#
#         destination = destinations[0]
#
#         # relaystates = RelayState.objects.filter(destination__id=destination.id)
#         # relaystate_forms = []
#         # for relaystate in relaystates:
#         #     form = RelayStateForm(instance=relaystate)
#         #     relaystate_forms.append(form)
#         print('RelayState Form:')
#         relaystates = RelayState.objects.filter(destination__id=destination.id)
#         relaystate_forms = [RelayStateForm(instance=relaystates[0])]
#         relaystate_form_as_string = render_to_string('relaystate_form.html', {'relaystate_forms': relaystate_forms}, request=request)
#         print(relaystate_form_as_string)
#
#         return render(request=request, template_name='relaystate_form.html', context={'relaystate_forms': relaystate_forms})
#
#
#     def get_cert(self):
#         primary_key = kwargs['pk']
#         entity_certs = Certificate.objects.filter(entity__id=primary_key)
#         certificate_rows = render_to_string('certificate_form.html', {'entity_certs': entity_certs }, request=request)
#         print('Cert Rows:')
#         print(certificate_rows)
#         return render(request=request,
#                     template_name='certificate_form.html',
#                     context={'entity_certs': entity_certs})
#
#     def get_destination(self):
#         primary_key = kwargs['pk']
#         entity_certs = Certificate.objects.filter(entity__id=primary_key)
#
#         destinations = Destination.objects.filter(entity__id=primary_key)
#         destination = DestinationForm(instance=destinations[0])
#         destination_form = render_to_string('destination_form.html', {'destination': destination}, request=request)
#
#         print('Destination Form:')
#         print(destination_form)
#         return render(request=request, template_name='destination_form.html', context={'destination': destination})


# class EntityDetail(generic.DetailView):
#
#     def get(self, request, *args, **kwargs):
#         primary_key = kwargs['pk']
#         entity_instance, entity_form = self.get_entity(entity_key=primary_key)
#         entity_certs = Certificate.objects.filter(entity__id=entity_instance.id)
#         destination_map = self.get_destination_map(entity_instance=entity_instance)
#         certificate_form = set_form_initial(form=CertificateForm(),
#                                             model='CERTIFICATE',
#                                             model_instance=Certificate(),
#                                             parent_instance=entity_instance.id)
#         return render(request=request,
#                       template_name='entity-detail.html',
#                       context={
#                           'entity_form': entity_form,
#                           'entity_certs': entity_certs,
#                           'certificate_form': certificate_form,
#                           'destination_map': destination_map
#                       })
#
#     def get_entity(self, entity_key):
#         if entity_key.upper() == 'NEW':
#             entity_instance = Entity()
#         else:
#             entity_instance = Entity.objects.get(pk=entity_key)
#         form = set_form_initial(form=EntityForm(instance=entity_instance),
#                                 model='ENTITY',
#                                 model_instance=entity_instance.id,
#                                 parent_instance=None)
#         return entity_instance, form
#
#     def get_destination_map(self, entity_instance):
#         destination_map = []
#         destinations = Destination.objects.filter(entity__id=entity_instance.id)
#         for destination in destinations:
#             destination_form = set_form_initial(form=DestinationForm(instance=destination),
#                                                 model='DESTINATION',
#                                                 model_instance=destination.id,
#                                                 parent_instance=entity_instance.id)
#             relay_state_forms = []
#             for relay_state in RelayState.objects.filter(destination__id=destination.id):
#                 form = set_form_initial(form=RelayStateForm(instance=relay_state),
#                                         model='RELAYSTATE',
#                                         model_instance=relay_state.id,
#                                         parent_instance=destination.id)
#                 relay_state_forms.append(form)
#             attribute_forms = []
#             for attribute in Attribute.objects.filter(destination__id=destination.id):
#                 form = set_form_initial(form=AttributeForm(instance=attribute),
#                                         model='ATTRIBUTE',
#                                         model_instance=attribute.id,
#                                         parent_instance=destination.id)
#                 attribute_forms.append(form)
#             destination_map.append(DestinationMap(entity_instance=entity_instance,
#                                                   destination_instance=destination,
#                                                   destination_form=destination_form,
#                                                   relay_state_forms=relay_state_forms,
#                                                   attribute_forms=attribute_forms)
#                                    )
#         return destination_map
#
#     # def set_form_initial(self, form, model, model_instance, parent_instance):
#     #     form.initial['model'] = model
#     #     form.model_for_url = str(model)
#     #     form.initial['model_instance'] = model_instance
#     #     form.model_instance_for_url = str(model_instance)
#     #     form.initial['parent_instance'] = parent_instance
#     #     form.parent_instance_for_url = str(parent_instance)
#     #     return form


# class DestinationMap:
#
#     def __init__(self, entity_instance, destination_instance, destination_form, relay_state_forms, attribute_forms):
#         self.entity_instance = entity_instance
#         self.destination_instance = destination_instance
#         self.destination_form = destination_form
#         self.relay_state_forms = relay_state_forms
#         self.attribute_forms = attribute_forms


