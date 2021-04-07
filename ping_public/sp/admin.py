from django.contrib import admin

from . import models

#admin.site.register(models.Entity)
admin.site.register(models.Certificate)
admin.site.register(models.Destination)
admin.site.register(models.RelayState)
admin.site.register(models.Attribute)
admin.site.register(models.DataStore)
admin.site.register(models.PrivateKey)


# @admin.register(models.Entity)
# class EntityAdmin(admin.ModelAdmin):
#     list_display = ("name", "entity_id", "description")
#     search_fields = ("entity_id", )
#     #list_select_related = ("attribute",)

class CertificateInline(admin.StackedInline):
    model = models.Certificate

    def get_extra(self, request, obj=None, **kwargs):
        # if this is brand new then return an empty certificate form, otherwise just return the existing form(s)
        extra = 1
        if obj:
            return 0
        return extra

@admin.register(models.Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("entity_id", "name", "description")
    search_fields = ("entity_id", "name",)
    list_select_related = True
    inlines = [
        CertificateInline,
    ]


# class RelayStateInline(admin.StackedInline):
#     model = models.RelayState
#
#     def get_extra(self, request, obj=None, **kwargs):
#         # if this is brand new then return an empty RelayState form, otherwise just return the existing form(s)
#         extra = 1
#         if obj:
#             return 0
#         return extra


# class AttributeInline(admin.StackedInline):
#     model = models.Attribute
#     filter_horizontal = ["query_parameters"]
#
#     def get_extra(self, request, obj=None, **kwargs):
#         # if this is brand new then return an empty RelayState form, otherwise just return the existing form(s)
#         extra = 1
#         if obj:
#             return 0
#         return extra
#
#
# @admin.register(models.Destination)
# class DestinationAdmin(admin.ModelAdmin):
#     list_display = ("entity", "name", "description")
#     search_fields = ("entity", "name",)
#     list_select_related = True
#     inlines = [
#         RelayStateInline,
#         AttributeInline,
#     ]


# AssertionAttribute, TokenString, TokenQuery

# # TODO - If I want the django admin console to make sense I'll need to fix these again
# class AssertionAttributeInline(admin.StackedInline):
#     model = models.AssertionAttribute
#
#     def get_extra(self, request, obj=None, **kwargs):
#         # if this is brand new then return an empty form, otherwise just return the existing form(s)
#         extra = 1
#         if obj:
#             return 0
#         return extra


# class TokenStringInline(admin.StackedInline):
#     model = models.TokenString
#
#     def get_extra(self, request, obj=None, **kwargs):
#         # if this is brand new then return an empty form, otherwise just return the existing form(s)
#         extra = 1
#         if obj:
#             return 0
#         return extra


# class TokenQueryInline(admin.StackedInline):
#     model = models.TokenQuery
#     filter_horizontal = ["query_parameters"]
#
#     def get_extra(self, request, obj=None, **kwargs):
#         # if this is brand new then return an empty form, otherwise just return the existing form(s)
#         extra = 1
#         if obj:
#             return 0
#         return extra

# @admin.register(models.Destination)
# class DestinationAdmin(admin.ModelAdmin):
#     list_display = ("entity", "name", "description")
#     search_fields = ("entity", "name",)
#     list_select_related = True
#     inlines = [
#         RelayStateInline,
#         TokenStringInline,
#         AssertionAttributeInline,
#         TokenQueryInline,
#     ]

'''
@admin.register(models.Destination)
class DestinationAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Certificate)
class CertificateAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Attribute)
class AttributeAdmin(admin.ModelAdmin):
    filter_horizontal = ["query_parameters"]
    list_display = ("attribute_name", "destination")
    list_select_related = ("destination",)

class DestinationInline(admin.StackedInline):
    model = models.Destination
    show_change_link = True

    def get_extra(self, request, obj=None, **kwargs):
        # if this is brand new then return an empty destination form, otherwise just return the existing form(s)
        extra = 1
        if obj:
            return 0
        return extra

class CertificateInline(admin.StackedInline):
    model = models.Certificate

    def get_extra(self, request, obj=None, **kwargs):
        # if this is brand new then return an empty certificate form, otherwise just return the existing form(s)
        extra = 1
        if obj:
            #return obj.certificate_set.count()
            return 0
        return extra

#from django.contrib.contenttypes.admin import GenericStackedInline
#class RelayStateInline(GenericStackedInline):
#    model = models.RelayState

class AttributeInline(admin.StackedInline):
    model = models.Attribute

@admin.register(models.Entity)
class EntityAdmin(admin.ModelAdmin):
    inlines = [
        CertificateInline,
        DestinationInline,
        #RelayStateInline,
    ]
'''