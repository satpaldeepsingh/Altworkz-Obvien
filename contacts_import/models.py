from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    middle_name = models.CharField(max_length=50, null=True)
    last_name = models.CharField(max_length=50, null=True)
    photo = models.CharField(max_length=500, null=True)
    country = models.CharField(max_length=50, null=True)
    city = models.CharField(max_length=50, null=True)
    zip_code = models.CharField(max_length=50, null=True)
    street_address = models.CharField(max_length=500, null=True)
    area = models.CharField(max_length=500, null=True)
    description = models.TextField(null=True)
    bloomberg_url = models.CharField(max_length=100, null=True)
    is_bloomberg_scraped = models.BooleanField(default=False)
    last_scraped_bloomberg = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    users = models.ManyToManyField(
        User, related_name='contacts')
    tags = models.ManyToManyField(
        'Tag',  related_name='c_tags')

    class Meta:
        db_table = "contacts"


class ContactNumber(models.Model):
    contact = models.ForeignKey(
        'Contact', related_name="contact_number", on_delete=models.CASCADE, )
    contact_number_primary = models.CharField(max_length=50,  null=True)
    contact_number_secondary = models.CharField(max_length=50, null=True)
    contact_number_tertiary = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contact_numbers"


class ContactEmail(models.Model):
    contact = models.ForeignKey(
        'Contact', related_name="contact_email", on_delete=models.CASCADE, )
    contact_email_primary = models.CharField(
        max_length=50,  blank=False, unique=True)
    contact_email_secondary = models.CharField(max_length=50, null=True)
    contact_email_tertiary = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contact_emails"

class ContactDescription(models.Model):
    contact = models.ForeignKey(
        'Contact', related_name="contact_description", on_delete=models.CASCADE, )
    description= models.TextField(null=True)
    source = models.ForeignKey(
        'ContactScrapeSource', related_name="contact_description", on_delete=models.CASCADE, )
    platform = models.ForeignKey(
        'SocialProfile', related_name="contact_description", on_delete=models.CASCADE, )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contact_description"

class ContactScrapeSource(models.Model):
    source_name= models.CharField(max_length=150, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contact_scrape_source"

class Tag(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tags"


class ContactTag(models.Model):
    contact = models.ForeignKey('Contact', related_name="contact_tags", on_delete=models.CASCADE,)
    tag = models.ForeignKey('Tag', related_name="cont_tags", on_delete=models.CASCADE,)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contact_tags"
        
class CSVTag(models.Model):
    id = models.AutoField(primary_key=True)
    contact = models.ForeignKey('Contact', related_name="csv_tags", on_delete=models.CASCADE,)
    user_id = models.IntegerField()
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "csv_tags"
        


class School(models.Model):
    school_name = models.CharField(max_length=250)
    source = models.ForeignKey(
        'ContactScrapeSource', related_name="schools", on_delete=models.CASCADE, )
    platform = models.ForeignKey(
        'SocialProfile', related_name="schools", on_delete=models.CASCADE, )
    school_abbreviation = models.CharField(max_length=10, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schools"


class Education(models.Model):
    contact = models.ForeignKey(
        'Contact', related_name='educations', on_delete=models.CASCADE,)
    source = models.ForeignKey(
        'ContactScrapeSource', related_name="educations", on_delete=models.CASCADE, )
    platform = models.ForeignKey(
        'SocialProfile', related_name="educations", on_delete=models.CASCADE, )
    school = models.ManyToManyField(
        'School', verbose_name="school", related_name='school')
    degree = models.CharField(max_length=200)
    school_start_year = models.CharField(max_length=20, null=True)
    school_end_year = models.CharField(max_length=20, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "educations"


class Organization(models.Model):
    organization_name = models.CharField(max_length=150)
    organization_symbol = models.CharField(max_length=50, null=True)
    sector = models.CharField(max_length=50, null=True)
    industry = models.CharField(max_length=50, null=True)
    sub_industry = models.CharField(max_length=50, null=True)
    address = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=50, null=True)
    state = models.CharField(max_length=50, null=True)
    zipcode = models.CharField(max_length=10, null=True)
    country = models.CharField(max_length=50, null=True)
    phone = models.CharField(max_length=20, null=True)
    website = models.CharField(max_length=50, null=True)
    founded = models.CharField(max_length=50, null=True)
    number_of_employees = models.CharField(max_length=20, null=True)
    bloomberg_url = models.CharField(max_length=150, null=True)
    is_bloomberg_scraped = models.BooleanField(default=False)
    is_yahoo_scraped = models.BooleanField(default=False)
    last_scraped_bloomberg = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "organizations"


class Job(models.Model):
    contact = models.ForeignKey(
        'Contact', related_name="jobs", on_delete=models.CASCADE, )
    source = models.ForeignKey(
        'ContactScrapeSource', related_name="jobs", on_delete=models.CASCADE, )
    platform = models.ForeignKey(
        'SocialProfile', related_name="jobs", on_delete=models.CASCADE, )
    organization = models.ManyToManyField(
        'Organization', verbose_name="organization", related_name='organization')
    job_title = models.CharField(max_length=250, null=True)
    job_start_date = models.CharField(max_length=20, null=True)
    job_end_date = models.CharField(max_length=20, null=True)
    country = models.CharField(max_length=50, null=True)
    city = models.CharField(max_length=50, null=True)
    area = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "jobs"


class SocialProfile(models.Model):
    contact = models.ForeignKey(
        'Contact', related_name="social_profiles", on_delete=models.CASCADE, )
    platform = models.CharField(max_length=50,  null=True)
    platform_link = models.CharField(max_length=500, null=True)
    is_scraped = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "social_profiles"


class ContactDegree(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contact_degree = models.ForeignKey(
        'Contact', related_name='contacts_degrees', on_delete=models.CASCADE, )
    user_contact_id = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contacts_degrees"

class ContactSocialPlatform(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    contacts_social_platform = models.ForeignKey(
        'Contact', related_name='contacts_social_platform', on_delete=models.CASCADE, )
    csv_platform = models.CharField(max_length=50, null=True)
    user_contact_id = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contacts_social_platform"


class ContactMembership(models.Model):

    contact = models.ForeignKey(
        'Contact', related_name='contact_memberships', on_delete=models.CASCADE, )
    title = models.CharField(max_length=50, null=True)
    company = models.CharField(max_length=50, null=True)
    tenure = models.CharField(max_length=50, null=True)
    membership_type = models.CharField(max_length=50, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contacts_memberships"


class PersonofInterest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poi = models.ForeignKey(
        'Contact', related_name='contacts_degrees_poi', on_delete=models.CASCADE, )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "persons_of_interests"
 
class FeedbackSearchTerm(models.Model):
    search_term = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feedback_search_term"

class UserFeedback(models.Model): 
    feedback = models.SmallIntegerField(null=False)
    contact = models.ForeignKey(
        'Contact', related_name="user_feedback", on_delete=models.CASCADE, )
    feedback_search_term = models.ForeignKey(
        'FeedbackSearchTerm', related_name="user_feedback", on_delete=models.CASCADE, )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "user_feedback"