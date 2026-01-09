from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.dialogflow_webhook, name='dialogflow_webhook'),
    path('test-upload/', views.test_upload_page, name='test_upload'),
    path('crop-disease/', views.crop_disease_prediction, name='crop_disease'),
]
