from django.urls import path, include

from . import views

urlpatterns = [
    path('clearbit', views.clearbit, name='clearbit'),
    path('data-enrichment/email', views.clearbit, name='clearbit'),

    path('test_email', views.send_test_email, name='test_email'),
    path('test-hit', views.test_hit, name='test_hit'),
    path('gsearch', views.Gsearch, name='gsearch'),
    path('search', views.search, name='search'),
    path('scrape', views.scrape, name='scrape'),
]
