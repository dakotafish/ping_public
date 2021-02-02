from django import forms
from django.forms import ModelForm
from sp.models import Entity, Certificate, Destination, RelayState, Attribute

import OpenSSL.crypto
from datetime import datetime

class EntityForm(ModelForm):
    model = forms.CharField(widget=forms.HiddenInput(), required=False)
    model_instance = forms.CharField(widget=forms.HiddenInput(), required=False)
    parent_instance = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Entity
        fields = '__all__'

    class Media:
        js = ('updateModel.js', 'general.js')


class CertificateForm(forms.Form):
    model = forms.CharField(widget=forms.HiddenInput(), required=False)
    model_instance = forms.CharField(widget=forms.HiddenInput(), required=False)
    parent_instance = forms.CharField(widget=forms.HiddenInput(), required=False)

    UPLOAD_METHOD_CHOICES = [
        ('FILE', 'Upload a File'),
        ('RAW', 'Copy & Paste the raw cert text')
    ]
    upload_method = forms.ChoiceField(choices=UPLOAD_METHOD_CHOICES)
    certificate_text = forms.CharField(widget=forms.Textarea, required=False)
    #certificate_file =
    certificate_file = forms.FileField(required=False, allow_empty_file=True)

    def save_certificate(self, certificate, parent_instance):
        cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)
        #parent_entity = Entity.objects.get(pk=self.cleaned_data['parent_instance'])
        parent_entity = Entity.objects.get(pk=parent_instance)
        common_name = self.get_common_name(cert)

        cert_instance = Certificate(
            entity=parent_entity,
            certificate=certificate,
            subject=cert.get_subject(),
            issuer=cert.get_issuer(),
            serial_number=cert.get_serial_number(),
            subject_name_hash=cert.subject_name_hash(),
            issue_date=datetime.strptime(cert.get_notBefore().decode('ascii'), '%Y%m%d%H%M%SZ'),
            #issue_date=cert.get_notBefore(),
            expiration_date=datetime.strptime(cert.get_notAfter().decode('ascii'), '%Y%m%d%H%M%SZ'),
            common_name=common_name,
        )
        print(cert.get_subject())
        cert_instance.save()
        return cert_instance

    def get_common_name(self, cert):
        cn_pieces = str(cert.get_subject()).split('/')
        # TODO - Replace this whole this with a regex
        for piece in cn_pieces:
            if "CN=" in piece:
                cn = piece.split('CN=')[1]
                for character in ['<', '>', '"', "'"]:
                    cn = cn.replace(character, "")
                return cn
            else:
                None


    # def __init__(self, certificate_file=None, *args, **kwargs):
    #     super(CertificateForm, self).__init__(*args, **kwargs)
    #     #if 'certificate_file' in kwargs:
    #         #self.fields['certificate_file'] = kwargs['certificate_file']
    #     if certificate_file:
    #         self.fields['certificate_text']['certificate_text'] = certificate_file
    #     print('self.fields --------------------------')
    #     print(self.fields)
    #
    # def save(self):
    #     if self.is_valid():
    #         parent_entity = self.cleaned_data.get('parent_instance')
    #         if self.cleaned_data.get('upload_method') == 'FILE':
    #             uploaded_certificate = self.cleaned_data.get('certificate_file')
    #         else:
    #             uploaded_certificate = self.cleaned_data.get('certificate_text')
    #         print('------uploaded_certificate--------')
    #         print(uploaded_certificate)

    # def __init__(self, parent_entity=None, *args, **kwargs):
    #     super(CertificateForm, self).__init__(*args, **kwargs)
    #     if parent_entity:
    #         self.fields['entity'] = parent_entity.id

class DestinationForm(ModelForm):
    model = forms.CharField(widget=forms.HiddenInput(), required=False)
    model_instance = forms.CharField(widget=forms.HiddenInput(), required=False)
    parent_instance = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Destination
        fields = '__all__'
        exclude = ['entity', ]

    class Media:
        js = ('updateModel.js', 'general.js')


class RelayStateForm(ModelForm):
    model = forms.CharField(widget=forms.HiddenInput(), required=False)
    model_instance = forms.CharField(widget=forms.HiddenInput(), required=False)
    parent_instance = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = RelayState
        fields = '__all__'
        exclude = ['destination', ]

    class Media:
        js = ('updateModel.js', 'general.js')


class AttributeForm(ModelForm):
    model = forms.CharField(widget=forms.HiddenInput(), required=False)
    model_instance = forms.CharField(widget=forms.HiddenInput(), required=False)
    parent_instance = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Attribute
        fields = '__all__'
        exclude = ['destination', ]

    class Media:
        js = ('entity-detail.js', 'general.js')