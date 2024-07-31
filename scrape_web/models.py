from django.db import models
from django.contrib.auth.models import User
from contacts_import.models import Organization
# Create your models here.


class Sec(models.Model):
    company = models.ForeignKey(Organization, on_delete=models.CASCADE)
    sec_link = models.CharField(max_length=500)
    cik = models.CharField(max_length=200, null=True)
    filed_date = models.DateTimeField()
    is_scraped = models.BooleanField(default=False)
    last_scraped = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sec"

class SecLinkScrape(models.Model):
    from_scrape = models.DateTimeField()
    to_scrape = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sec_link_scrape"

class SecDocumentScrape(models.Model):
    from_scrape = models.IntegerField()
    to_scrape = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sec_document_scrape"

class BloomCompanyScrape(models.Model):
    from_scrape = models.IntegerField()
    to_scrape = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bloom_comany_scrape"