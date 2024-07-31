from django.urls import path, include

from . import views

urlpatterns = [

    path('save_search_result', views.save_search_result, name='save_search1'),
    path('save_search', views.save_search, name='save_search'),
    path('delete_search_result', views.delete_search_result, name='delete_search'),
    path('search_like', views.search_like, name='serach like'),
    path('search_feedback', views.get_search_feedback, name='search_feedback'),
    path('save-viewed-contact', views.save_viewed_contact, name='save_viewed_contact'),

]
