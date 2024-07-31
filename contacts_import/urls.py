from django.urls import path, include

from . import views 

urlpatterns = [
    path('', views.index, name='indexeE'),
    path('download-csv-template', views.download_csv_template, name='download-csv-template'),
    path('import_csv', views.import_csv, name='import_csv'),
    path('import_csv_sheet', views.import_csv_sheet, name='import_csv_sheet'),
    path('import-csv-ajax', views.import_csv_ajax, name='import_csv-ajax'),
    path('people-api', views.people_api, name='people_api'),
    path('people-contact-post', views.people_api_post, name='people_contact_post'),
    #path('facebook-api', views.facebook_api, name='facebook_api'),
    
    path('twitter-contacts-import', views.twitter_contacts_import, name='twitter_contacts_import'),
    
    path('twitter-contacts-test', views.twitter_test_auth, name='twitter_test_auth'),
    
    path('import-twitter-selected-contacts', views.import_twitter_selected_contacts, name='import_twitter_selected_contacts'),
    path('twitter-login', views.twitter_login, name='twitter_login'),
    path('twitter-token', views.twitter_token, name='twitter_token'),
    path('twitter-friends', views.twitter_friends, name='twitter_friends'), 
    path('twitter-callback', views.twitter_callback, name='twitter_callback'),
    path('twitter-callback', views.twitter_test_auth, name='twitter_test_auth'),
    path('twitter-logout', views.twitter_logout, name='twitter_logout'),

    path('twitter-test', views.twitter_test, name='twitter_test'), 

    path('facebook-contacts-import', views.facebook_contacts_import, name='facebook_contacts_import'),
    
    path('linkedin-contacts-import', views.linkedin_contacts_import, name='linkedin_contacts_import'),    
    path('linkedin-login', views.linkedin_login, name='linkedin_login'),
    path('linkedin-callback', views.linkedin_callback, name='linkedin_callback'),
    
    path('update-graph', views.update_graph, name='update_graph'),
  
]
