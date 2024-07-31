from django.db import models

# Create your models here.
from django.db import models

# Create your models here.
class Type(models.Model):
    type_name = models.CharField(max_length=255, blank=True)


class Industry(models.Model):
    industry_name = models.TextField( null=True)


class Information(models.Model):
    name = models.CharField(max_length=255, blank=True)
    type_key = models.ForeignKey(Type , on_delete=models.CASCADE , null=True)
    industry_key = models.ForeignKey(Industry ,  on_delete=models.CASCADE ,null=True)
    image = models.TextField()
    


class Content_type(models.Model):
    keyID = models.CharField(max_length=255)
    keyValue = models.TextField()
    Info_Key = models.ForeignKey(Information , on_delete=models.CASCADE , null=True)
    
class SubContent_type(models.Model):
    Sub_keyID = models.CharField(max_length=255)
    Sub_keyValue = models.TextField()
    SubKey_Description = models.TextField()
    level_Info = models.IntegerField()
    Content_Key = models.ForeignKey(Content_type , on_delete=models.CASCADE ,null=True)
