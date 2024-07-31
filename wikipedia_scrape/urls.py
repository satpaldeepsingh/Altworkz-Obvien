from django.urls import path
from . import views
urlpatterns = [
    path("search" , views.function_Search , name = "search"),
    path(r"search-results", views.scrape_results_type , name = "search-results"),
]
