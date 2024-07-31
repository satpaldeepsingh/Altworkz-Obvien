"""altworkz URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.http import Http404
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path('orm/', include('ORM.urls')),
    path('', include('search.urls')),
    # path('api/', include('api.urls')),
    path('search/', include('search.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/change-password/', auth_views.PasswordChangeView.as_view(template_name='registration/change-password.html',),),
    path('accounts/', include('django.contrib.auth.urls')),
    path('userboard/', include('userboard.urls'), name='userboard'),
    path('contacts/', include('contacts_import.urls')),
    path('search-history/', include('search_history.urls')),
    path('scrape_web/', include('scrape_web.urls')),
    path('twitter/', include('twitter.urls')),
    path('wikipedia/', include('wikipedia_scrape.urls')),
    # path(r'api/v1/invite/', include('drf_simple_invite.urls', namespace='drf_simple_invite')),

    
]
