from django.urls import path, include

from . import views

urlpatterns = [
    # path('scrape_sec', views.scrape_bloomberg_company_data, name='search'),
    path('scrape_sec_document', views.scrape_sec_document, name='search1'),
    path('sec_link_scrape', views.sec_link_scrape, name='search4'),
    path('sec_document_scrape', views.sec_document_scrape, name='search5'),
    path('scrape_bloomberg_person', views.scrape_bloomberg_person, name='search6'),
    path('scrape_bloomberg_company', views.scrape_bloomberg_company, name='search7'),
    path('scrape_bloomberg_person', views.scrape_bloomberg_person, name='search8'),
    path('scrape_yahoo_links', views.scrape_yahoo_links, name='search9'),
    path('scrape_csv_contacts', views.scrape_csv_contacts, name='search10'),
    path('scrape_contacts_from_bloomberg', views.scrape_contacts_from_bloomberg, name='search11'),

]