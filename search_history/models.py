from django.db import models
from django.contrib.auth.models import User
from contacts_import.models import Contact

class SearchTerm(models.Model):

    search_term = models.CharField(max_length=150)
    search_term_name = models.CharField(max_length=200)
    filters = models.CharField(max_length=1000, null=True)
    filter_weights = models.CharField(max_length=1000, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(User, related_name='search_terms')

    class Meta:
        db_table = "search_terms"


class SearchHistory(models.Model):
    id = models.AutoField(primary_key=True)
    search_term = models.CharField(max_length=150, default='')
    filters = models.CharField(max_length=1000, null=True)
    filter_weights = models.CharField(max_length=1000, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = "search_history"


class ContactViewHistory(models.Model):

    # contact_id = models.IntegerField()
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, default = "")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_contact_view_history"