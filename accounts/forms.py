from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from contacts_import.models import Contact

class AuthenticationFormWithInactiveUsersOkay(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            print(user.is_active)
            raise ValidationError(
                _("This account is inactive."),
                code='inactive',
            )
            return False
        return True
        

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=30, required=True, help_text='Required.')
    first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    last_name = forms.CharField(max_length=30, required=True, help_text='Required.')
    job_title = forms.CharField(max_length=30, required=True, help_text='Required.')
    organization = forms.CharField(max_length=30, required=True, help_text='Required.')


    class Meta:
        model = User
        fields = ('username' , 'email','first_name', 'last_name', 'job_title', 'organization', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'email': 'Email Address',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'job_title': 'Job Title',
            'organization': 'Organization Name',
        }
        for key, value in placeholders.items():
            self.fields[key].widget.attrs['placeholder'] = value

