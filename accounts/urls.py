from django.urls import path, re_path

from accounts.views import *


urlpatterns = [
    path('login/', login_view, name='login'),
    path('send-test-email/', send_test_email, name='login'),  
    path('send-email2/',Invite_sendemail, name='sendemail2'),  
    #path('account-activation/', activate_account, name='activate_account'),
    
    re_path(r'^account-activation/(?P<activation_code>[a-zA-Z0-9]{25})$', activate_account),

    path('signup/', signup_view, name='signup'),
]
