from django.urls import path

from . import views

urlpatterns = [
    #path('test', views.Test.as_view(), name='Test'),
    path('<str:role>/entity/<str:pk>', views.EntityDetail.as_view(), name='EntityDetail'),
    #path('<str:role>/entity/<str:pk>', views.EntityDetail.as_view(), name='EntityDetail'),
    path('<str:role>/update/<str:model>/<str:model_id>', views.Update.as_view(), name='Update'),
    path('<str:role>/delete/<str:model>/<str:model_id>', views.Delete.as_view(), name='Delete'),
    path('<str:role>/create-new/<str:model>/<str:parent_instance>', views.CreateNew.as_view(), name='CreateNew'),
]