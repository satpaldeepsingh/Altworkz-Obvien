from django.urls import path, include

from . import views

urlpatterns = [
    
    path('', views.index, name='userboard'),
    path('multi-delete', views.multidelete_contacts, name='multidelete_contacts'),    
    path('edit/<int:id>', views.edit, name='edit'),
    path('update/<int:id>', views.update, name='update'),
    path('update_profile/<int:id>', views.update_profile, name='update_profile'),    
    path('delete/<int:id>', views.destroy, name='delete'),
    path('view/<int:id>', views.view_profile, name='view_profile'),
    path('update-user-tags', views.update_user_contact_tags, name='update_user_tags'),
    
    #path('view/<int:id>', views.profile, name='profile'),

]
