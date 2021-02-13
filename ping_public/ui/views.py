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
        if model_instance == 'NEW':
            # if a model instance doesn't exist yet then the reverse() function will fail
            # so we short circuit __init__() for NEW model instances
            self.model_instance = model_instance
            self.model_instance_id = model_instance
        else:
            self.model_instance = model_instance
            self.model_instance_id = model_instance.id
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
        self.parent_model = parent_model
        self.parent_instance = parent_instance
        self.parent_instance_id = parent_instance.id
        self.create_new_url = reverse('CreateNew', kwargs={
            'role': 'sp',
            'model': self.model,
            'parent_instance': self.parent_instance_id
        })
        self.template = self.templates[self.model]
        self.unique_element_id = self.model + "_" + str(self.model_instance_id)
        self.form = None
        self.set_form()

    def set_form(self):
        unique_auto_id = self.unique_element_id + '_%s'
        if self.model_instance == 'NEW':
            forms = {
                'ENTITY': EntityForm(auto_id=unique_auto_id),
                'CERTIFICATE': CertificateForm(),
                'DESTINATION': DestinationForm(auto_id=unique_auto_id),
                'RELAYSTATE': RelayStateForm(auto_id=unique_auto_id),
                'ATTRIBUTE': AttributeForm(auto_id=unique_auto_id),
            }
        else:
            forms = {
                'ENTITY': EntityForm(instance=self.model_instance, auto_id=unique_auto_id),
                'CERTIFICATE': CertificateForm(),
                'DESTINATION': DestinationForm(instance=self.model_instance, auto_id=unique_auto_id),
                'RELAYSTATE': RelayStateForm(instance=self.model_instance, auto_id=unique_auto_id),
                'ATTRIBUTE': AttributeForm(instance=self.model_instance, auto_id=unique_auto_id),
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
        self.new_certificate = Meta(model='CERTIFICATE', model_instance='NEW', parent_model='ENTITY',
                                    parent_instance=self.model_instance)
        certificates = Certificate.objects.filter(entity__id=self.model_instance_id)
        for certificate in certificates:
            cert_meta = Meta(model='CERTIFICATE', model_instance=certificate, parent_model='ENTITY',
                             parent_instance=self.model_instance)
            self.certificates.append(cert_meta)

    def set_destinations(self):
        self.new_destination = Meta(model='DESTINATION', model_instance='NEW', parent_model='ENTITY',
                                    parent_instance=self.model_instance)
        destinations = Destination.objects.filter(entity__id=self.model_instance_id)
        for destination in destinations:
            destination_meta = DestinationTemplate(model='DESTINATION', model_instance=destination,
                                                   parent_model='ENTITY', parent_instance=self.model_instance)
            self.destinations.append(destination_meta)


class DestinationTemplate(Meta):

    def __init__(self, model, model_instance, parent_model, parent_instance):
        super().__init__(model, model_instance, parent_model, parent_instance)
        self.relay_states = []
        self.set_relay_states()
        self.attributes = []
        self.set_attributes()

    def set_relay_states(self):
        print(self.model_instance)
        print(self.model_instance_id)
        self.new_relay_state = Meta(model='RELAYSTATE', model_instance='NEW', parent_model='DESTINATION',
                                    parent_instance=self.model_instance)
        relay_states = RelayState.objects.filter(destination__id=self.model_instance_id)
        for relay_state in relay_states:
            relay_state_meta = Meta(model='RELAYSTATE', model_instance=relay_state, parent_model='DESTINATION',
                                    parent_instance=self.model_instance)
            self.relay_states.append(relay_state_meta)

    def set_attributes(self):
        self.new_attribute = Meta(model='ATTRIBUTE', model_instance='NEW', parent_model='DESTINATION',
                                  parent_instance=self.model_instance)
        attributes = Attribute.objects.filter(destination__id=self.model_instance_id)
        for attribute in attributes:
            attribute_meta = Meta(model='ATTRIBUTE', model_instance=attribute, parent_model='DESTINATION',
                                  parent_instance=self.model_instance)
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
        return JsonResponse(status)
        #return HttpResponse(status['message'], status=status['status'])

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
            new_instance = form.save()
            return self.SUCCESS
        else:
            # TODO - Need a better method of passing status messages
            # To produce one of the validation errors just remove "required=False" from parent_instance on the entity form
            errors = form.errors.as_text()
            status = self.FAIL
            status['message'] = status['message'].format(errors)
            return status


class Delete(generic.DetailView):
    SUCCESS = {'status': 200, 'message': 'Deleted Successfully.'}
    FAIL = {'status': 500, 'message': 'Something went wrong, please try again. Errors: {0}'}

    def delete(self, request, *args, **kwargs):
        # to access the body of a delete request you just use request.body
        print('Received the Delete Request --------')
        model = kwargs['model']
        model_instance_id = kwargs['model_id']
        status = self.process_delete(model=model, model_instance_id=model_instance_id)
        #return HttpResponse(status['message'], status=status['status'])
        return JsonResponse(status) #, safe=False)

    def process_delete(self, model, model_instance_id):
        model = model.upper()
        if model == 'CERTIFICATE':
            model_instance = Certificate.objects.get(pk=model_instance_id)
            model_instance.delete()
            return self.SUCCESS
        elif model == 'DESTINATION':
            model_instance = Destination.objects.get(pk=model_instance_id)
            model_instance.delete()
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
            'TEMPLATE': 'destination_form.html'
        },
        'RELAYSTATE': {
            'FORM': RelayStateForm(),
            'MODEL_INSTANCE': RelayState(),
            'TEMPLATE': 'relaystate_form.html'
        },
        'ATTRIBUTE': {
            'FORM': AttributeForm(),
            'TEMPLATE': 'attribute_form.html'
        },
    }

    def get(self, request, *args, **kwargs):
        model = kwargs['model'].upper()
        parent_instance_id = kwargs['parent_instance']
        form = self.fetch_new_form(model, parent_instance_id)
        template = self.model_map[model]['TEMPLATE']
        context_name = model.lower()
        response = {
            'new_form': render_to_string(template, {context_name: form}, request=request),
        }
        return JsonResponse(response)


    def fetch_new_form(self, model, parent_instance_id):
        parent_instance = None
        if model == 'DESTINATION':
            parent_instance = Entity.objects.get(pk=parent_instance_id)
            form = Meta(model=model, model_instance='NEW', parent_model='ENTITY',parent_instance=parent_instance)
            #form = DestinationTemplate(model=model, model_instance='NEW', parent_model='ENTITY', parent_instance=parent_instance)
            return form
        elif model == 'RELAYSTATE' or model == 'ATTRIBUTE':
            parent_instance = Destination.objects.get(pk=parent_instance_id)
            form = Meta(model=model, model_instance='NEW', parent_model='DESTINATION', parent_instance=parent_instance)
            return form


    def post(self, request, *args, **kwargs):
        model = kwargs['model']
        parent_instance = kwargs['parent_instance']
        post_data = request.POST.copy()
        files = request.FILES
        status = self.process_new_model(model=model, parent_instance=parent_instance, post_data=post_data, files=files)
        #return HttpResponse(status)
        return JsonResponse(status) #, safe=False)
        # TODO - Update, Delete, and CreateNew should all return a JsonResponse for all POST requests
        #  GET requests to CreateNew could still return a template and return that..

    def process_new_model(self, model, parent_instance, post_data, files):
        model_to_update = model.upper()
        if model_to_update == 'ENTITY':
            form = EntityForm(post_data)
        elif model_to_update == 'DESTINATION':
            entity = Entity.objects.get(pk=parent_instance)
            form = DestinationForm(post_data)
            form.instance.entity = entity
            new_instance = form.save()
            update_url = reverse('Update', kwargs={'role':'sp', 'model': model_to_update,
                                                   'model_id': str(new_instance.id)})
            delete_url = reverse('Delete', kwargs={'role':'sp', 'model': model_to_update,
                                                   'model_id': str(new_instance.id)})
            return {
                'message': 'SUCCESS',
                'unique_element_id': model_to_update + "_" + str(new_instance.id),
                'update_url': str(update_url),
                'delete_url': str(delete_url)
            }
        elif model_to_update == 'ATTRIBUTE':
            destination = Destination.objects.get(pk=parent_instance)
            form = AttributeForm(post_data)
            form.instance.destination = destination
            new_instance = form.save()
            update_url = reverse('Update', kwargs={'role':'sp', 'model': model_to_update,
                                                   'model_id': str(new_instance.id)})
            delete_url = reverse('Delete', kwargs={'role':'sp', 'model': model_to_update,
                                                   'model_id': str(new_instance.id)})
            return {
                'message': 'SUCCESS',
                'unique_element_id': model_to_update + "_" + str(new_instance.id),
                'update_url': str(update_url),
                'delete_url': str(delete_url)
            }
        elif model_to_update == 'RELAYSTATE':
            destination = Destination.objects.get(pk=parent_instance)
            form = RelayStateForm(post_data)
            form.instance.destination = destination
            new_instance = form.save()
            update_url = reverse('Update', kwargs={'role':'sp', 'model': model_to_update,
                                                   'model_id': str(new_instance.id)})
            delete_url = reverse('Delete', kwargs={'role':'sp', 'model': model_to_update,
                                                   'model_id': str(new_instance.id)})
            return {
                'message': 'SUCCESS',
                'unique_element_id': model_to_update + "_" + str(new_instance.id),
                'update_url': str(update_url),
                'delete_url': str(delete_url)
            }
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
                delete_url = reverse('Delete', kwargs={
                    'role': 'sp',
                    'model': model_to_update,
                    'model_id': new_model_instance.id,
                })
                common_name = new_model_instance.common_name
                serial_number = str(new_model_instance.serial_number)
                issue_date = str(new_model_instance.issue_date).split(' ')[0]
                expiration_date = str(new_model_instance.issue_date).split(' ')[0]
                status = {
                    'message': 'SUCCESS',
                    'delete_url': delete_url,
                    'common_name': common_name,
                    'serial_number': serial_number,
                    'issue_date': issue_date,
                    'expiration_date': expiration_date,
                }
                print(status)
                return status
        else:
            # TODO - Need a better method of passing status messages
            # To produce one of the validation errors when testing just remove "required=False" from parent_instance on the entity form
            errors = form.errors.as_data()
            return errors


