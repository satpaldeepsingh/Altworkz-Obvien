from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.forms.models import model_to_dict
from django.dispatch import receiver
from contacts_import.models import Contact
from django.conf import settings
# Create your models here.


class AccountActivation(models.Model):
      activation_string = models.CharField(max_length=50,default='')
      user_id = models.IntegerField()
      useremail = models.EmailField(max_length=30 , unique=True)


class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE,primary_key = True)
    first_name = models.CharField(max_length=30, blank=False )
    last_name = models.CharField(max_length=30, blank=False )
    job_title = models.CharField(max_length=30, blank=False )
    organization = models.CharField(max_length=30, blank=False )
    #contact = models.OneToOneField(Contact, on_delete=models.CASCADE, default=0)

    contact_id = models.IntegerField(blank=True, default=0)
    is_first_login = models.IntegerField(default=1)

    
  

    activation_string = models.CharField(max_length=50, default='' ,blank=False)
    
    
    class Meta:
        db_table = "unactivated_account_codes"



@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        print("*********************************")
        p = Profile.objects.create(user=instance)

        current_user_id = instance.id
        instance.profile.save()
        new_profile = Profile.objects.filter(user_id=current_user_id).values()[0]
        contact_id = createContactProfile(new_profile['first_name'], new_profile['last_name'], new_profile['job_title'], new_profile['organization'], current_user_id)
        Profile.objects.filter(user_id=current_user_id).update(contact_id=contact_id)

def createContactProfile(first_name, last_name, job_title, organization, user_id):
    contact, created = Contact.objects.update_or_create(
        defaults={'user_id': user_id, 'first_name': first_name, 'middle_name': '',
                  'last_name': last_name},
        first_name=first_name,
        last_name=last_name,
    )

    return contact.id


