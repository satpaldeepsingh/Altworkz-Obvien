from django.urls import path, include, re_path

from . import views

urlpatterns = [
    path('', views.index, name='indexsearch'),
    path('elastic-search', views.es_search, name='elastic-search'),
    path('contact-details', views.get_contact_details, name='contact-details'),
    path('get-filter-suggestions', views.get_filters_suggestions, name='get-filter-suggestions'),
    path('elastic-search-json', views.es_search_json, name='elastic-search-json'),
    path('es-compare', views.es_compare, name='elastic-search-compare'),
    path('elastic-search-compare', views.es_search_json_compare,
         name='elastic-search-compare'),
    path('test', views.test, name='test'),
    path('10K', views.F10K),
    path('get-countries', views.get_countries_list, name='get-countries'),
    path('get-cities', views.get_cities_list, name='get-cities'),
    
    re_path(r'^index(?:msg=(?P<msg>\d+)/)?$', views.index),  # good

    # path('welcome/', views.welcome, name='welcome'),
    # path('signup', views.signup, name='signup'),
]

# urlpatterns += [
#     path('accounts/', include('django.contrib.auth.urls')),
# ]
