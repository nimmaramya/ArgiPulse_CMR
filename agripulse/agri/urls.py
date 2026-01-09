from django.urls import path
from . import views

urlpatterns = [
    path("",views.index, name='index'),
    path("crop-protection/", views.crop_protection, name='crop_protection'),
    path("seed/", views.seed, name='seed'),
    path("fertilizer/", views.fertilizer, name='fertilizer'),
    path("tools/", views.tools, name='tools'),
    path("yield-prediction/", views.yield_prediction, name='yield_prediction'),
    # path("api/agri-news/", views.govt_agri_updates, name="agri-news"),
    # path("api/agri-updates/", views.agri_rss_news, name="agri-updates"),
    path("test_disease_detection/", views.test_disease_detection, name='test_disease_detection'),
]