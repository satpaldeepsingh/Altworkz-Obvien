from django import forms
from django.core.validators import FileExtensionValidator
import csv
from io import TextIOWrapper

class ImportCSVForm(forms.Form):
    csv = forms.FileField(required=True, error_messages={
        'required': "Please Select CSV File"
    }, validators=[FileExtensionValidator(allowed_extensions=['csv'])])

    CHOICES1 = (('social_csv', 'social_csv'), ('custom_csv', 'custom_csv'),)
    csv_type = forms.ChoiceField(widget=forms.Select, choices=CHOICES1, required=True, error_messages={
        'required': "Please Select CSV Type"
    })

    CHOICES = (('1st_degrees', '1st_degrees'), ('poi', 'poi'),)
    contact_type = forms.ChoiceField(widget=forms.Select, choices=CHOICES, required=True, error_messages={
        'required': "Please Select Contact Type"
    })

    tags = forms.CharField(widget=forms.TextInput(attrs={'size': '20', 'placeholder': 'add tags'}), required=False
                           , error_messages={
            'required': "Please Enter Tag(s)"
        })

    csv_tags = forms.CharField(widget=forms.TextInput(attrs={'size': '20', 'placeholder': 'add tags'}), required=True
                           , error_messages={
            'required': "Please Enter Tag(s)"
        })

    # def clean_csv(self):
    #     CSV_HEADERS_CONSTANTS=[
    #         "first_name","middle_name","last_name","email","phone","mobile","country","city","school1","school1_start_year","school1_end_year","school1_abbreviation",
    #         "school2","school2_start_year","school2_end_year","school2_abbreviation","school3","school3_start_year","school3_end_year","school3_abbreviation",
    #         "organization1_name","organization1_start_date","organization1_end_date","organization1_job_title","organization2_name","organization2_start_date",
    #         "organization2_end_date","organization2_job_title","organization3_name","organization3_start_date","organization3_end_date","organization3_job_title",
    #         "total_work_experience_in_years","fb_profile_url","twitter_profile_url","linkedin_profile_url","bloomberg_profile_url","description","tags"
    #     ]
    #     cleaned_data = super(ImportCSVForm, self).clean()
    #     f = TextIOWrapper(self.cleaned_data.get('csv').file, encoding='UTF-8')
    #     csv_file_dict = csv.DictReader(f)
    #     headers =csv_file_dict.fieldnames
    #     csv_header_el = set(headers)
    #     csv_headers_cons = set(CSV_HEADERS_CONSTANTS)
    #     if len(headers) > 0:
    #         if not csv_header_el.issubset(csv_headers_cons):
    #             raise forms.ValidationError("Headers in CSV are not Identical!")
    #     else:
    #         raise forms.ValidationError("Headers in CSV are incorrect")
    #     return cleaned_data