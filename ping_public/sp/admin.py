from django.contrib import admin

from . import models

admin.site.register(models.Entity)
admin.site.register(models.Certificate)
admin.site.register(models.Destination)
admin.site.register(models.RelayState)
admin.site.register(models.Attribute)
