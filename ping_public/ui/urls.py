from django.urls import path

from . import views

urlpatterns = [
    path('', views.Home.as_view(), name='Home'),
    path('<str:role>', views.EntityList.as_view(), name='EntityList'),
    path('test/', views.get_name, name='get_name'),
    path('<str:role>/<int:pk>', views.EntityDetail.as_view(), name='EntityDetail'),
]