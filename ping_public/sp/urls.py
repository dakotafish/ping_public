from django.urls import path

from . import views

urlpatterns = [
    path('sp/ACS.saml2', views.ServiceProvider.as_view(), name='ServiceProvider'),
]
