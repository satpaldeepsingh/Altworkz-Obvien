import codecs
from http.client import HTTPResponse
import json
from smtplib import OLDSTYLE_AUTH
#from tkinter import EXCEPTION
from django.urls import reverse

from pprint import pprint

from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render, redirect
import csv
import io
import re
from csv import DictReader
from django.contrib import messages
from contacts_import.forms import ImportCSVForm
from accounts.models import Profile
from contacts_import.models import Contact, Job, School, ContactScrapeSource, ContactDescription, Organization, \
    Education, Tag, ContactTag, SocialProfile, ContactDegree, PersonofInterest, ContactEmail, ContactNumber, \
    ContactSocialPlatform
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import quote
from io import TextIOWrapper
from .csv import *
from querystring_parser import parser
from scrape_web.views import scrape_csv_contacts
import threading
from django.core.mail import send_mail
from django.conf import settings

# def beta_login(request):
#     try:
#         context = {}
#         if request.session.get('csv_stats', None):
#                 context['csv_stats'] = request.session['csv_stats']
#                 del request.session['csv_stats']

#         if request.session.get('first_time_login', None) and request.session['first_time_login'] == True:
#                 context['first_time_login'] = True 
#                 request.session['first_time_login'] = False
#                 messages.success(request , "Welcome to Obvien! Let’s get you started shows walk-through <a href='#'>Ok</a>")
#         print(request.session.get)
#         return render(request, 'csv/csv_form.html')
#     except Exception as e:
#         print(request.session.get)

def index(request):
    try:
    # return HttpResponse("here",request)
        context = {}

        context['csv_headers'] = get_csv_headers()
        context['csv_initial_headers'] = context['csv_headers'][:7]
        context['csv_additional_headers'] = context['csv_headers'][7:]
        context['csv_headers_description'] = get_csv_headers_description()

        if request.session.get('csv_stats', None):
            context['csv_stats'] = request.session['csv_stats']
            del request.session['csv_stats']

        if request.session.get('first_time_login', None) and request.session['first_time_login'] == True:
            context['first_time_login'] = True 
            # messages.info(request , "Welcome to Obvien! Let’s get you started shows walk-through <a href='#'>Ok</a>")
            request.session['first_time_login'] = False
        print(request.session.get)
        # return HttpResponse(request , '<h1>Hello</h1>')
        return render(request, "csv/csv_form.html", context)
    except Exception as e:
        print('error: %s' % e)


def import_csv(request):
    if request.method == "POST":

        csv_form = ImportCSVForm(request.POST, request.FILES or None)

        header_index = 0         
        if csv_form.is_valid():
            csv_file = csv_form.cleaned_data['csv']
            csv_type = csv_form.cleaned_data['csv_type']
            contact_type = csv_form.cleaned_data['contact_type']
            tags = csv_form.cleaned_data['tags']
            csv_tags = csv_form.cleaned_data['csv_tags']
        else:
            errors = csv_form.errors.as_json()
            errors = json.loads(errors)
            try:
                if 'csv' in errors:
                    messages.add_message(request, messages.ERROR, errors['csv'][0]['message'])
                return redirect('indexeE')
            except Exception as e:
                return HttpResponse("Here" , e)
        data_set = csv_file.read().decode('ISO-8859-1')

        # setup a stream which is when we loop through each line we are able to handle a data in a stream
        io_string = io.StringIO(data_set)
        if csv_type == "custom_csv":
            header_uplod_csv = io_string.readlines()[0]
            header_uplods_csv = header_uplod_csv.split(",")
            header = [x.replace('\n', '') for x in header_uplods_csv]
            print("HEADER: %s" % header)
            headers = [i for i in header if i]
            io_string = io.StringIO(data_set)
            if not validate_csv_headers(headers):
                messages.add_message(request, messages.ERROR, 'Headers in CSV are not Identical!')
                return redirect('indexeE')
                # Social_CSV 
        elif csv_type == "social_csv":     
            header_uplod_csv = io_string.readline().strip()
            print('header_uplod_csv: %s' % header_uplod_csv)

            
            # while header_uplod_csv and ('first_name,' not in header_uplod_csv.lower() and 'last_name,' not in header_uplod_csv.lower()):
            #     header_index += 1
            #     #print("Updating header index to ")
            #     header_uplod_csv = io_string.readline().strip()  
            #     # print("header_uplod_csv:" , header_uplod_csv)

            # header_uplod_csv = io_string.readline().strip()  
            # print('jfkm',header_uplod_csv)
            # # messages.add_message(request, messages.ERROR, 'Work in progress!')
            # #return redirect('index')

            # # header_uplod_csv = io_string.readlines()[0]           
            header_uplods_csv = header_uplod_csv.split(",")            
            header = [x.replace('\r\n', '') for x in header_uplods_csv]
            print("headerrs:::-->" , header)
            headers = [i for i in header if i]
            print("Printing CSV headers :", headers)
            
            io_string = io.StringIO(data_set)
            if not validate_social_csv_header(headers):
                messages.add_message(request, messages.ERROR, 'Headers in CSV are not Identical!')
                return redirect('indexeE')
        else:
            header_uplod_csv = io_string.readlines()[0]
            header_uplods_csv = header_uplod_csv.split(",")
            header = [x.replace('\r\n', '') for x in header_uplods_csv]
            headers = [i for i in header if i]  
            io_string = io.StringIO(data_set)
            if not validate_csv_headers(headers):
                messages.add_message(request, messages.ERROR, 'Headers in CSV are not Identical!')
                return redirect('indexeE')
                # return HttpResponse("here")

        # start: validation insert
        
        if header_index > 0:

            val_data_set = csv.DictReader(codecs.iterdecode(request.FILES['csv'], 'ISO-8859-1'), fieldnames=get_social_csv_headers())
        
        else:
        
            val_data_set = csv.DictReader(codecs.iterdecode(request.FILES['csv'], 'ISO-8859-1'))

        csv_stats = {}
        total_rows = 0
        rejected_rows = [];

        if csv_type == "social_csv":
        
            header_index += 1

        for index, csv_row in enumerate(val_data_set):

            total_rows += 1
            rejection_reasons = []
                        
            if heaedr_index > 0:
                
                header_index -= 1
                continue 

            # if index < 5:
            
                # print("CSV Row ", csv_row)
                
            if csv_type == "custom_csv":
                print('===============DONE++++++++++++++++++1')
                

                if 'first_name' not in csv_row:

                    rejection_reasons.append({"field": "first_name", "msg": "First name column should be present"})

                elif not csv_row['first_name']:

                    rejection_reasons.append({"field": "first_name", "msg": "First name should not be empty"})

                if 'last_name' not in csv_row:

                    rejection_reasons.append({'field': 'last_name', 'msg': 'Last name column should be present'})

                elif not csv_row['last_name']:

                    rejection_reasons.append({'field': 'last_name', 'msg': 'Last name should not be empty'})

                if not csv_row['organization_name'] and not csv_row['organization_job_title']:
                    rejection_reasons.append({'field': 'organization_job_title/organization_name',
                                              'msg': 'organization job title or organization name should not be empty'})

                if csv_row.get('email', None) and (
                re.search('^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', csv_row['email'])) is None:
                    rejection_reasons.append(
                        {"field": 'email', 'value': csv_row['email'], "msg": "Email not in proper format"})

                if csv_row.get('mobile', None) and (
                re.search('^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$', csv_row['mobile'])) is None:
                    rejection_reasons.append({"field": "mobile", 'value': csv_row['mobile'],
                                              "msg": "Number field should not contain alphabets"})

                if csv_row.get('phone', None) and (
                re.search('^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$', csv_row['phone'])) is None:
                    rejection_reasons.append({"field": "phone", "value": csv_row['phone'],
                                              "msg": "Number field should be a valid phone number"})

                for url_field in ['photo', 'fb_profile_url', 'twitter_profile_url', 'linkedin_profile_url',
                                  'bloomberg_profile_url']:

                    if csv_row.get(url_field, None) and (re.search(
                            "(([\w]+:)?//)?(([\d\w]|%[a-fA-f\d]{2,2})+(:([\d\w]|%[a-fA-f\d]{2,2})+)?@)?([\d\w][-\d\w]{0,253}[\d\w]\.)+[\w]{2,63}(:[\d]+)?(/([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)*(\?(&?([-+_~.\d\w]|%[a-fA-f\d]{2,2})=?)*)?(#([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)?",
                            csv_row[url_field])) is None:
                        rejection_reasons.append({"field": url_field, "value": csv_row[url_field],
                                                  "msg": url_field + " field must be valid URL"})

                if len(rejection_reasons) > 0:
                    rejected_rows.append({"row_no": index + 2, "row": csv_row, "reasons": rejection_reasons})

                else:
                    school = csv_row['school'] if csv_row.get('school', None) else ''
                    school_start_year = ''
                    school_end_year = ''
                    school_abbreviation = ''
                    organization_name = csv_row['organization_name'] if csv_row.get('organization_name', None) else ''
                    organization_start_date = ''
                    organization_end_date = ''
                    organization_job_title = csv_row['organization_job_title'] if csv_row.get('organization_job_title',
                                                                                              None) else ''
                    contact_tags = csv_row['tags'] if csv_row.get('tags', None) else ''
                    contact_first_name = csv_row['first_name']
                    conatact_last_name = csv_row['last_name']
                    school = (''.join(e for e in school if e.isalnum()))
                    organization_name = (''.join(e for e in organization_name if e.isalnum() or e == ' '))
                    organization_job_title = (''.join(e for e in organization_job_title if e.isalnum() or e == ' '))
                    contact_first_name = (''.join(e for e in csv_row['first_name'] if e.isalnum() or e == ' '))
                    contact_last_name = (''.join(e for e in csv_row['last_name'] if e.isalnum() or e == ' '))
                    contact_middle_name = (''.join(e for e in csv_row['middle_name'] if e.isalnum() or e == ' '))
                    print('===============DONE++++++++++++++++++3')
                    
                    if Contact.objects.filter(first_name__iexact=contact_first_name,
                                              middle_name__iexact=contact_middle_name,
                                              last_name__iexact=contact_last_name).exists():
                        contact = Contact.objects.get(first_name=contact_first_name, middle_name=contact_middle_name,
                                                      last_name=contact_last_name)
                        
                        contact.users.add(request.user.id)
                        
                        if contact_tags != '' and contact_tags is not None:
                            tag_method(contact_tags, contact.id)

                        if tags:
                            tag_method(tags, contact.id)

                        if csv_tags:
                            csv_tag_method(csv_tags, request.user.id, contact.id)
                            
                        #csv_tag_method(request.FILES['csv'].name, request.user.id, contact.id)
                        continue

                    else:
                        contact, created = Contact.objects.update_or_create(
                            defaults={'user_id': request.user.id, 'first_name': contact_first_name,
                                      'middle_name': contact_middle_name,
                                      'last_name': contact_last_name,
                                      'photo': csv_row['photo'] if csv_row.get('photo', None) else '',
                                      'country': csv_row['country'] if csv_row.get('country', None) else '',
                                      'city': csv_row['city'] if csv_row.get('city', None) else '',
                                      'description': csv_row['description'] if csv_row.get('description',
                                                                                           None) else ''},
                            # first_name=(''.join(e for e in csv_row['first_name'] if e.isalnum())),
                            # last_name=(''.join(e for e in csv_row['last_name'] if e.isalnum())),
                            first_name=contact_first_name,
                            middle_name=contact_middle_name,
                            last_name=contact_last_name,
                        )

                        contact.users.add(request.user.id)

                        if csv_row['email'] != '' and csv_row['email'] is not None:

                            if ContactEmail.objects.filter(contact_email_primary__iexact=csv_row['email']).exists():

                                continue

                            else:

                                ContactEmail.objects.update_or_create(

                                    contact_email_primary=csv_row['email'],

                                    contact_id=contact.id

                                )

                        if csv_row['phone'] != '' and csv_row['phone'] is not None:
                            ContactNumber.objects.update_or_create(

                                contact_number_primary=csv_row['mobile'] if csv_row.get('mobile', None) else '',

                                contact_number_secondary=csv_row['phone'] if csv_row.get('phone', None) else '',

                                contact_id=contact.id

                            )

                        contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                            source_name='CSV',
                        )
                        source_id = contact_scrape_source.id
                                                                        

                        social_profiles, created = SocialProfile.objects.update_or_create(
                            platform_link='',
                            platform='CSV',
                            is_scraped='1',
                            contact_id=contact.id,
                        )
                        social_profiles_id = social_profiles.id

                        if csv_row['description'] != '' and csv_row['description'] is not None:
                            contact_description, created = ContactDescription.objects.update_or_create(
                                source_id=contact_scrape_source.id,
                                description=csv_row['description'] if csv_row.get('description', None) else '',
                                contact_id=contact.id,
                                platform_id=social_profiles_id
                            )

                        if school != '' and school is not None:
                            school1 = school_method(
                                school, school_start_year, school_end_year, school_abbreviation, contact.id, source_id,
                                social_profiles_id)

                        if organization_name != '' and organization_name is not None:
                            organization1 = organization_method(
                                organization_name, contact.id, source_id, social_profiles_id, organization_start_date,
                                organization_end_date,
                                organization_job_title)

                        if csv_row['fb_profile_url']:
                            SocialProfile.objects.update_or_create(
                                contact_id=contact.id,
                                platform='facebook',
                                platform_link=csv_row['fb_profile_url'],
                                is_scraped=0
                            )
                        if csv_row['twitter_profile_url']:
                            SocialProfile.objects.update_or_create(
                                contact_id=contact.id,
                                platform='twitter',
                                platform_link=csv_row['twitter_profile_url'],
                                is_scraped=0
                            )

                        if csv_row['linkedin_profile_url']:
                            SocialProfile.objects.update_or_create(
                                contact_id=contact.id,
                                platform='linkedin',
                                platform_link=csv_row['linkedin_profile_url'],
                                is_scraped=0
                            )
                        if csv_row['bloomberg_profile_url']:
                            SocialProfile.objects.update_or_create(
                                contact_id=contact.id,
                                platform='bloomberg',
                                platform_link=csv_row['bloomberg_profile_url'],
                                is_scraped=0
                            )

                        if contact_tags != '' and contact_tags is not None:
                            tag_method(contact_tags, contact.id)

                        if tags:
                            tag_method(tags, contact.id)

                        if csv_tags:
                            csv_tag_method(csv_tags, request.user.id, contact.id)
                           
                        #csv_tag_method(request.FILES['csv'].name, request.user.id, contact.id)

                        if contact_type == "1st_degrees":
                            new_profile = Profile.objects.filter(user_id=request.user.id).values()[0]
                            ContactDegree.objects.update_or_create(
                                user_id=request.user.id,
                                user_contact_id=new_profile['contact_id'],
                                contact_degree_id=contact.id
                            )
                        elif contact_type == "poi":
                            PersonofInterest.objects.update_or_create(
                                user_id=request.user.id,
                                poi_id=contact.id
                            )
                        else:
                            text = """<h1>Contact Type Error</h1>"""
                            return HttpResponse(text)

            else:
            

                if 'First Name' not in csv_row:

                    rejection_reasons.append({"field": "First Name", "msg": "First name column should be present"})

                elif not csv_row['First Name']:

                    rejection_reasons.append({"field": "First Name", "msg": "First name should not be empty"})

                if 'Last Name' not in csv_row:

                    rejection_reasons.append({'field': 'Last Name', 'msg': 'Last name column should be present'})

                elif not csv_row['Last Name']:

                    rejection_reasons.append({'field': 'Last Name', 'msg': 'Last name should not be empty'})




                if not csv_row['Company'] and not csv_row['Position']:
                    rejection_reasons.append({'field': 'Company/Position',
                                              'msg': 'organization job title or organization name should not be empty'})

                if csv_row.get('Email Address', None) and (
                        re.search('^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$',
                                  csv_row['Email Address'])) is None:
                    rejection_reasons.append(
                        {"field": 'Email Address', 'value': csv_row['Email Address'],
                         "msg": "Email not in proper format"})

                if len(rejection_reasons) > 0:
                    rejected_rows.append({"row_no": index + 2, "row": csv_row, "reasons": rejection_reasons})

                school = ''
                school_start_year = ''
                school_end_year = ''
                school_abbreviation = ''
                organization_name = csv_row['Company'] if csv_row.get('Company',
                                                                      None) else ''
                organization_start_date = ''
                organization_end_date = ''
                organization_job_title = csv_row['Position'] if csv_row.get('Position',
                                                                            None) else ''
                contact_tags = csv_row['tags'] if csv_row.get('tags', None) else ''

                contact_first_name = (''.join(e for e in csv_row['First Name'] if e.isalnum() or e == ' '))
                conatact_last_name = (''.join(e for e in csv_row['Last Name'] if e.isalnum() or e == ' '))
                organization_name = (''.join(e for e in organization_name if e.isalnum() or e == ' '))
                organization_job_title = (''.join(e for e in organization_job_title if e.isalnum() or e == ' '))

                if Contact.objects.filter(first_name__iexact=contact_first_name,
                                          last_name__iexact=conatact_last_name).exists():                    
                    
                    try:
                    
                        contact = Contact.objects.get(first_name=contact_first_name, last_name=conatact_last_name)
                        contact.users.add(request.user.id)
                    
                    except:
                    
                        print("Linkedin: contact count exception > 1")
                    
                    continue

                else:

                    contact, created = Contact.objects.update_or_create(
                        defaults={'user_id': request.user.id, 'first_name': contact_first_name,
                                  'middle_name': '',
                                  'last_name': conatact_last_name},
                        first_name=contact_first_name,
                        last_name=conatact_last_name,

                    )

                    contact.users.add(request.user.id)

                    if csv_row['Email Address'] != '' and csv_row['Email Address'] is not None:

                        if ContactEmail.objects.filter(contact_email_primary__iexact=csv_row['Email Address']).exists():

                            continue

                        else:
                            ContactEmail.objects.update_or_create(
                                contact_email_primary=csv_row['Email Address'],
                                contact_id=contact.id
                            )

                    contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                        source_name='CSV',
                    )
                    source_id = contact_scrape_source.id

                    social_profiles, created = SocialProfile.objects.update_or_create(
                        platform_link='',
                        platform='CSV',
                        is_scraped='1',
                        contact_id=contact.id,
                    )
                    social_profiles_id = social_profiles.id

                    if school != '' and school is not None:
                        school1 = school_method(
                            school, school_start_year, school_end_year, school_abbreviation, contact.id, source_id,
                            social_profiles_id)

                    if organization_name != '' and organization_name is not None:
                        organization1 = organization_method(
                            organization_name, contact.id, source_id, social_profiles_id, organization_start_date,
                            organization_end_date,
                            organization_job_title)

                    if contact_tags != '' and contact_tags is not None:
                        tag_method(contact_tags, contact.id)

                    if tags:
                        tag_method(tags, contact.id)

                    if contact_type == "1st_degrees":
                        new_profile = Profile.objects.filter(user_id=request.user.id).values()[0]
                        ContactDegree.objects.update_or_create(
                            user_id=request.user.id,
                            user_contact_id=new_profile['contact_id'],
                            contact_degree_id=contact.id
                        )

                        ContactSocialPlatform.objects.update_or_create(
                            user_id=request.user.id,
                            user_contact_id=new_profile['contact_id'],
                            contacts_social_platform_id=contact.id,
                            csv_platform='linkedin'
                        )

                    elif contact_type == "poi":
                        PersonofInterest.objects.update_or_create(
                            user_id=request.user.id,
                            poi_id=contact.id
                        )
                        new_profile = Profile.objects.filter(user_id=request.user.id).values()[0]
                        ContactSocialPlatform.objects.update_or_create(
                            user_id=request.user.id,
                            user_contact_id=new_profile['contact_id'],
                            contacts_social_platform_id=contact.id,
                            csv_platform='linkedin'
                        )
                    else:
                        text = """<h1>CSV Type Error</h1>"""
                        return HttpResponse(text)

        csv_stats['total_rows'] = total_rows
        csv_stats['total_rejected_rows'] = len(rejected_rows)
        csv_stats['total_processed_rows'] = total_rows - csv_stats['total_rejected_rows']

        # if len(rejected_rows) > 0:
        csv_stats["rejected_rows"] = rejected_rows
        request.session['csv_stats'] = csv_stats
        # Start Scrape contacts from social and web plateforms
        # download_thread = threading.Thread(target=scrape_csv_contacts, name="scrape_csv_contacts", args=(request.user.id,))
        # download_thread.start()
        print('===============DONE++++++++++++++++++3')

        return redirect('indexeE')
        # messages.add_message(request, messages.INFO, rejected_rows)

        #
        #     pass

        # end: validation insert
    # user_id = request.user.id
    # scrape_csv_contacts(user_id)


def import_csv_sheet(request):
    context = {}

    context['csv_headers'] = get_csv_headers()
    context['csv_initial_headers'] = context['csv_headers'][:7]
    context['csv_additional_headers'] = context['csv_headers'][7:]
    context['csv_headers_description'] = get_csv_headers_description()
    context['csv_table_headings'] = get_csv_table_headings()

    if request.session.get('csv_stats', None):
        context['csv_stats'] = request.session['csv_stats']
        del request.session['csv_stats']

    return render(request, "csv/csv_sheet.html", context)


@csrf_exempt
def import_csv_ajax(request):
    print(request.method)
    print(request.POST)

    if request.method == "POST":
        csv_rows = parser.parse(request.POST.urlencode())
        success_count = 0
        rejected_rows = []
        total_rows = 0

        # print(csv_rows['csv_rows'])

        for index, csv_row in enumerate(csv_rows['csv_rows']):

            # print(csv_rows['csv_rows'][index])
            add_row_validation = add_csv_row(csv_rows['csv_rows'][index], request.POST.get('contact_type'), "t1",
                                             request, index)

            if add_row_validation == True:
                success_count += 1
            else:
                rejected_rows.append(add_row_validation)

            total_rows += 1

        response = {}
        response['success_count'] = success_count
        response['rejected_rows'] = rejected_rows
        response['rejected_count'] = len(rejected_rows)
        response['total_rows'] = total_rows

        print(csv_rows)

        return HttpResponse(json.dumps(response))

    return HttpResponse("Nothing here")


def people_api(request):
    return render(request, "people/index.html")


@csrf_exempt
def people_api_post(request):
    if request.is_ajax() and request.method == 'POST':
        contacts = request.POST.get('contacts', None)
        file_tag = request.POST.get('file_tag')
        contacts_dict = json.loads(contacts)
        error_msg = []
        counter = 0
        for idx, val in enumerate(contacts_dict):
            counter = idx + 1
            try:
                contacts_dict[idx]["names"][0]["displayName"]
                display_name = contacts_dict[idx]["names"][0]["displayName"]
                first_name = ''
                middle_name = ''
                last_name = ''
                names = display_name.split(' ')

                if len(names) == 1:
                    first_name = names[0]
                    middle_name = ''
                    last_name = ''

                if len(names) == 2:
                    first_name = names[0]
                    middle_name = ''
                    last_name = names[1]
                if len(names) == 3:
                    first_name = names[0]
                    middle_name = names[1]
                    last_name = names[2]

            except:
                first_name = None
                continue
            try:
                contacts_dict[idx]["photos"][0]["url"]
                photo = contacts_dict[idx]["photos"][0]["url"]
            except:
                photo = None
            try:
                contacts_dict[idx]["emailAddresses"]
                email = contacts_dict[idx]["emailAddresses"][0]["value"]
            except:
                email = None
            try:
                contacts_dict[idx]["phoneNumbers"][0]["value"]
                phone = contacts_dict[idx]["phoneNumbers"][0]["value"]
            except:
                phone = None
            try:
                contacts_dict[idx]["biographies"][0]["value"]
                biographies = contacts_dict[idx]["biographies"][0]["value"]
            except:
                biographies = None
            try:
                contacts_dict[idx]["organizations"][0]["name"]
                organization = contacts_dict[idx]["organizations"][0]["name"]
            except:
                organization = None

            contact, created = Contact.objects.update_or_create(
                defaults={'user_id': request.user.id, 'first_name': first_name, 'middle_name': middle_name,
                          'last_name': last_name,
                          'description': biographies, 'photo': photo},
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
            )
            
            if file_tag != '':
                csv_tag_method(file_tag, request.user.id, contact.id)                        
                        
            if email is not None:
                if ContactEmail.objects.filter(contact_email_primary__iexact=email).exists():
                    # error_msg.append(email,first_name)
                    continue
                else:
                    ContactEmail.objects.update_or_create(
                        contact_email_primary=email,
                        contact_id=contact.id
                    )
            if phone is not None:
                ContactNumber.objects.update_or_create(
                    contact_number_primary=phone,
                    contact_id=contact.id
                )
            contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                source_name='Google Contact',
            )
            source_id = contact_scrape_source.id

            social_profiles, created = SocialProfile.objects.update_or_create(
                platform_link='',
                platform='Google Contact',
                is_scraped='1',
                contact_id=contact.id,
            )
            social_profiles_id = social_profiles.id

            contact_description, created = ContactDescription.objects.update_or_create(
                source_id=contact_scrape_source.id,
                description=biographies,
                contact_id=contact.id,
                platform_id=social_profiles_id
            )
            ContactDegree.objects.update_or_create(
                user_id=request.user.id,
                contact_degree_id=contact.id
            )
            contact.users.add(request.user.id)
            if organization is not None:
                organization_method(organization, contact.id, contact_scrape_source.id, social_profiles_id)

        return JsonResponse({"totalCount": counter})
        # message = "Contacts has been imported"
    else:
        message = "Not Ajax"
    return JsonResponse(message, safe=False)


def download_csv_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template.csv"'

    writer = csv.writer(response)
    writer.writerow(get_csv_headers())

    return response

    # response = FileResponse(open(os.path.join(settings.STATIC_ROOT, 'downloads/template.csv'), 'r'))
    # return response
    
def get_twitter_auth(request):
    import tweepy

    #return twitter_callback(request)
    auth = tweepy.OAuth1UserHandler('2bqgyafUPQSSRDB9IFLN1I7Ah', 'Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24')
    print("prev request verifier ", request.session.get('oauth_verifier'))
    # auth = tweepy.OAuth1UserHandler('lND3s1fMigwVipwKKHX1fzEgP', 'YZDrmRLJ14jqN82top6vnSl034PGF5JfwTeNgnjs3TPuOAOyah')
    token = request.session.get('request_token')
    auth.request_token = {'oauth_token': token}
    print("prev request verifier ", request.GET.get('oauth_verifier'))
    
    auth_url = auth.get_authorization_url(signin_with_twitter=True)
    verifier = request.session.get('oauth_verifier') 
    request.session['oauth_token'] = token
    request.session['oauth_verifier'] = verifier
    

    print('oauth_token ', token)

                # request.session.delete('request_token')
    auth.request_token = {'oauth_token': token, 'oauth_token_secret': verifier}


    print("Auth url ", auth_url)   
    #print("Session auth token ", request.session['oauth_token'])
    #print("Request get ", request.GET.get['oauth_token'])
    #for key, value in auth_url:
    #    print("key ", key, " value ", value)
    print("Request Session ", request.session.get('oauth_verifier'))
    
    access_token, access_token_secret = auth.get_access_token(
        request.GET.get('oauth_verifier')
    )  

    
    #print("Access Token ", access_token, "Access Token Secret ", access_token_secret)
    
    '''
    if 'access_token' in request.session:

        token = request.session.get('request_token')
        
        auth.request_token = {'oauth_token': request.session.get('request_token'),
                              'oauth_token_secret': request.session.get('oauth_verifier')}

        auth.set_access_token(request.session['access_token'][0], request.session['access_token'][1])
    '''
    return auth

def twitter_contacts_import(request):

    import tweepy
    from django.contrib.auth.models import User
    
    context = {}

    user = User.objects.get(id=request.user.id)
    contacts = user.contacts.all().order_by('-id')  
    
    user_contact_id = Profile.objects.filter(user_id=request.user.id).values()[0]

    twitter_profiles = SocialProfile.objects.filter(contact_id=user_contact_id['contact_id'], platform='twitter')
    
    print("twitter_profiles ", twitter_profiles)
    
    friends_cursor = -1 if request.GET.get('cursor', None) is None else request.GET.get('cursor')
    
    #print("cursor value ", cursor_value)
    
    #print(len(api.followers(cursor=cursor_value)))
    
    #print(type(api.followers(cursor=cursor_value)[0]))
    #print(type(api.followers(cursor=cursor_value)[1]))    
    
    #for cont in contacts:
    
    #    print("first name ", cont.first_name)
    #    print("last name ", cont.last_name)
        # print("twitter URL ", twitter_url)
            
    #print("contact ")
    #print(contacts)
    
    # del request.session['access_token']
    # del request.session['oauth_token']
    # del request.session['oauth_token_secret']
    # del request.session['oauth_verifier']    

    if 'access_token' in request.session:
    
        auth = get_twitter_auth(request)
    
        twitter_friends, prev_next_friends_cursor = get_friends_list(auth, friends_cursor)
        twitter_followers = get_followers_list(auth)
    
        for twitter_friend in twitter_friends:
        
            twitter_friend['connection_strength'] = '<span style="color:#fd6e6e">Out of Network</span> (Followed by you)' 
        
            for twitter_follower in twitter_followers:
            
                if twitter_follower['id'] == twitter_friend['id']:
                
                    twitter_friend['connection_strength'] = '<span style="color:#56b36a">1st</span> (Followed and following)' 
                    break
                    
        context['twitter_friends'] = twitter_friends
        context['twitter_followers'] = twitter_followers
        context['friends_cursor'] = prev_next_friends_cursor
        context['current_cursor'] = friends_cursor
        
    return render(request, "twitter/index.html", context)

def twitter_login(request):
    
    return render(request, "twitter/login.html")


def twitter_test_auth(request):
        import tweepy
        # auth = tweepy.OAuth1UserHandler('lND3s1fMigwVipwKKHX1fzEgP', 'YZDrmRLJ14jqN82top6vnSl034PGF5JfwTeNgnjs3TPuOAOyah')
        auth = tweepy.OAuth1UserHandler('i5vjFiOTq0gNkUA3peRtFNnOb', 'mLrS10j3PxLgcYKVqm3HhVpfQWbpxgPJircimh8adCsNqHEUxR')
        print('auth' ,auth)
        url = auth.get_authorization_url(signin_with_twitter=True)
        print("URL ", url)
        print("request oauth_token ", request.GET.get('oauth_token'))
        print("request oauth_token_secret ", request.GET.get('oauth_verifier'))    
        
        auth.request_token = {
            'oauth_token': request.GET.get('oauth_token'), 
            'oauth_token_secret':  request.GET.get('oauth_verifier')
        }  
        # print('a' , auth.request_token ,'b', request.GET.get('oauth_token' ),'c' , request.GET.get('oauth_verifier'))
        print("auth ", auth)
        
        auth = tweepy.OAuth1UserHandler(
        'lND3s1fMigwVipwKKHX1fzEgP', 'YZDrmRLJ14jqN82top6vnSl034PGF5JfwTeNgnjs3TPuOAOyah',
        request.GET.get('oauth_token'), request.GET.get('oauth_verifier')
        )
        api = tweepy.API(auth)    

        
        # print("Printing request.GET ")
        # for key, value in request.GET:
        #     print("key ", key, " value ", value)
        
        # print("Printing request.session ")      
        # for key, value in request.session:
        #     print("key ", key, " value ", value)
        
        
    
        try:
            access_token, access_token_secret = (
                auth.get_access_token(
                    request.GET.get('oauth_verifier')
                )
            )
            print('xnnfdnefdaml',access_token, access_token_secret)
            # access_token, access_token_secret = auth.get_access_token(request.GET.get('oauth_verifier'))
        except Exception as e:
            print('error : %s' , e)
        return JsonResponse({});

def twitter_token(request):
    import tweepy

    if 'request_token' in request.session and 'url' in request.session:

        return JsonResponse({'oauth_token': request.session['oauth_token'], 'url': request.session['redirect_url']})
    else:

        auth = tweepy.OAuth1UserHandler('2bqgyafUPQSSRDB9IFLN1I7Ah', 'Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24')
        #auth = tweepy.OAuth1UserHandler('lND3s1fMigwVipwKKHX1fzEgP', 'YZDrmRLJ14jqN82top6vnSl034PGF5JfwTeNgnjs3TPuOAOyah')
        # auth = tweepy.OAuth1UserHandler('i5vjFiOTq0gNkUA3peRtFNnOb', 'mLrS10j3PxLgcYKVqm3HhVpfQWbpxgPJircimh8adCsNqHEUxR')

        print("Auth ", auth)

        try:
            redirect_url = auth.get_authorization_url(signin_with_twitter=True)
            #print("redirect url ", redirect_url)
            request.session['request_token'] = auth.request_token['oauth_token']
            request.session['redirect_url'] = redirect_url

            return JsonResponse({'oauth_token': request.session['request_token'], 'url': request.session['redirect_url']})


        except tweepy.errors.TweepyException:
            print('Error! Failed to get request token.') 

    return JsonResponse({'oauth_token': '', 'url': ''})
print("DONE")

def twitter_callback(request):
    print("------------------------------Here starting----------------------------------")
    import tweepy
    from contextlib import redirect_stdout


    auth = tweepy.OAuthHandler('2bqgyafUPQSSRDB9IFLN1I7Ah', 'Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24')
    #auth = tweepy.OAuth1UserHandler('lND3s1fMigwVipwKKHX1fzEgP', 'YZDrmRLJ14jqN82top6vnSl034PGF5JfwTeNgnjs3TPuOAOyah')
    # auth = tweepy.OAuth1UserHandler('i5vjFiOTq0gNkUA3peRtFNnOb', 'mLrS10j3PxLgcYKVqm3HhVpfQWbpxgPJircimh8adCsNqHEUxR')
   
    prev_oauth_verifier = ''
    prev_oauth_token = ''
    
    if request.GET.get('oauth_token'):
        prev_oauth_token = request.GET.get('oauth_token')
    
    if request.GET.get('oauth_verifier'):
        prev_oauth_verifier = request.GET.get('oauth_verifier')
   
    #auth = get_twitter_auth(request)
    print("Request GET ", request.GET)
    print("\n-----------------------------------------\n")
    print("TWITTER Auth ")
    auth_url = auth.get_authorization_url(signin_with_twitter=True)
    print("request oauth_token ", request.GET.get("oauth_token"))
    print("Auth url ", auth_url)
    # print("request oauth_token ", request.GET.get("oauth_token"))
    # #for key, value in auth:
    # #    print("key ", key, " value ", value)
    # #print("Oauth url ", auth_url['request_token'])
    # pprint(vars(auth))  
    # print("Request GET ", request.GET)
    
    # request_token = auth.request_token["oauth_token"]
    # request_secret = auth.request_token["oauth_token_secret"]    
    # print("request_token ", request_token)
    # print("request_secret ", request_secret)
    # if 'oauth_verifier' in request.GET:
        # print("oauth_verifier ", request.GET.get('oauth_verifier'))
        # access_token, access_token_secret = auth.get_access_token(
            # auth.request_token
        # ) 
        # for item in request.GET:
            # print("item ", item)
        # print("Access Token ", access_token, "Access Token Secret ", access_token_secret)
    # else:
        # print("No oauth_token yet ")
        
    
    for key, value in request.session.items():
        print('{} => {}'.format(key, value))    
    print("Request Session ", (request.session))
    pprint(request.session)
    print("\n-----------------------------------------\n")
        
    if 'access_token' in request.session:
    
        print("if ", request.session)

        run_test_api(auth)

    else:

        with io.StringIO() as output_buffer, redirect_stdout(output_buffer):

            try:
                print('OOAUTH VERIFIER <br>')
                verifier = request.GET.get('oauth_verifier')
                
                print("try ")
                
                #print("twitter token ", twitter_tokentwitter_token(request))
                
                #print("Access Token ", tweepy.get_access_token())

                request.session['oauth_verifier'] = verifier

                print("verifier ", verifier)

                token = request.session.get('request_token')

                print('oauth_token ', token)

                # request.session.delete('request_token')
                auth.request_token = {'oauth_token': token, 'oauth_token_secret': verifier}


                access_token = auth.get_access_token(verifier)

                print('Getting access token ', access_token)

                request.session['access_token'] = access_token

                # run_test_api(auth)
                # return JsonResponse({'access_token': access_token})
                
                # return JsonResponse({'token_set': True}, safe=False)
                
                return redirect('/contacts/twitter-contacts-import');
      

            except tweepy.errors.TweepyException:
                print('Error! Failed to get access token.')

            f = open("token.txt", "w")
            f.write(output_buffer.getvalue())
            f.close()

            return HttpResponse(output_buffer.getvalue())

    return HttpResponse("Look into console<br>")

def get_followers_list (auth):
    import tweepy
    
    followers_list = []
    
    api = tweepy.API(auth)
        
    for user_follower in api.followers():
    
        user_follower = user_follower._json
    
        # friends_list.append({'name': friend_info['name']})
        # friends_list.append(friend_info)
            
        followers_list.append({'id': user_follower['id'], 'name': user_follower['name'], 'photo': user_follower['profile_image_url_https'], 'org': '', 'job_title': '', 'screen_name': user_follower['screen_name'], 'location': user_follower['location']})
                
    return followers_list


def get_friends_list (auth, cursor):
    import tweepy
    
    friends_list = []
    
    api = tweepy.API(auth)
    
    print("cursor ", cursor)
    user_friends = api.get_friends(cursor=cursor)
    
    if len(user_friends) > 1:
        
        for user_friend in user_friends[0]:
        
            friend_info = user_friend._json
        
            #friends_list.append(friend_info)

            friends_list.append({'id': friend_info['id'], 'name': friend_info['name'], 'description': friend_info['description'], 'photo': friend_info['profile_image_url_https'], 'org': '', 'job_title': '', 'screen_name': friend_info['screen_name'], 'location': friend_info['location']})
        
        prev_next_cursors = user_friends[1]
        
    
    
    return friends_list, prev_next_cursors
    
def import_twitter_selected_contacts(request):

    if request.is_ajax():
        
        contact_ids = request.POST.getlist('contact_ids[]')
        
        cursor = request.POST.get('cursor')
                
        file_tag = request.POST.get('file_tag')
        #next_cursor = request.POST.get('next_cursor')
        
        print(request.POST)
        
        contacts_to_be_imported = []
        
        if len(contact_ids) > 0:
        
            import_count = 0
        
            auth = get_twitter_auth(request) 
                        
            friends_list, next_prev_cursor = get_friends_list(auth, cursor=cursor)
            followers_list = get_followers_list(auth)
            
            # for twitter_friend in twitter_friends:
    
                # twitter_friend['connection_strength'] = '<span style="color:#fd6e6e">3rd+</span> (Followed by you)' 
    
                # for twitter_follower in twitter_followers:
        
                    # if twitter_follower['id'] == twitter_friend['id']:
            
                        # twitter_friend['connection_strength'] = '<span style="color:#56b36a">1st</span> (Followed and following)' 

            connection_strength = ''            
            
            for twitter_friend in friends_list:
            
                for contact_id in contact_ids:
                
                    if int(contact_id) == twitter_friend['id']:
                                                             
                        name = twitter_friend['name']
                        splitted_name = name.split(' ')
                        
                        first_name = ''
                        middle_name = ''
                        last_name = ''
                        city = ''
                        country = ''
                        
                        if 'photo' in twitter_friend:
                        
                            photo = twitter_friend['photo']
                            
                        else:
                        
                            photo = ''
                        
                        if len(splitted_name) == 2:
                        
                            first_name = splitted_name[0]
                            last_name = splitted_name[1]
                        
                        elif len(splitted_name) == 3:

                            first_name = splitted_name[0]
                            middle_name = splitted_name[1]
                            last_name = splitted_name[2]
                            
                        else:
                        
                            first_name = twitter_friend['name']
                            
                        location = twitter_friend['location'].split(', ')
                        
                        if len(location) > 0:
                        
                            if len(location) == 1:
                            
                                city = location[0]
                                
                            elif len(location) == 2:
                            
                                city = location[0]
                                country = location[1]
                                                    
                        contact, created = Contact.objects.update_or_create(
                            defaults={
                                'user_id': request.user.id, 
                                'first_name': first_name, 
                                'middle_name': middle_name, 
                                'last_name': last_name, 
                                'photo': photo,
                                'city': city,
                                'country': country
                            },
                            first_name=first_name,
                            middle_name=middle_name,
                            last_name=last_name,
                        )
                        
                        contact.users.add(request.user.id)
                        
                        if file_tag != '':
                            csv_tag_method(file_tag, request.user.id, contact.id)                        
                        
                        import_count += 1

                        for twitter_follower in followers_list:
                
                            if int(contact_id) == twitter_follower['id']:
                            
                                ContactDegree.objects.update_or_create(
                                    user_id=request.user.id,
                                    contact_degree_id=contact.id
                                )                        

                                break


                        social_profiles, created = SocialProfile.objects.update_or_create(
                            platform_link='https://www.twitter.com/'+twitter_friend['screen_name'],
                            platform='twitter',
                            is_scraped='0',
                            contact_id=contact.id,
                        ) 

                        social_profiles_id = social_profiles.id

                        contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                            source_name='Twitter',
                        )
                        source_id = contact_scrape_source.id

                        contact_description, created = ContactDescription.objects.update_or_create(
                            source_id=source_id,
                            description=twitter_friend['description'],
                            contact_id=contact.id,
                            platform_id=social_profiles_id
                        )


        return JsonResponse({'imported_contacts': import_count})
 
    return HttpResponse('Response ... ')
    
def twitter_logout(request):

    if 'access_token' in request.session:

        del request.session['access_token']
        
    return JsonResponse({'token_deleted': True}, safe=False)
        

def run_test_api(auth):
    import tweepy

    api = tweepy.API(auth)
    
    from contextlib import redirect_stdout    
    with io.StringIO() as buf, redirect_stdout(buf):

        print("Running Test API")

        user_followers = api.friends()

        # print(type(user_followers))
        # print(user_followers)

        for user_follower in user_followers:
            
            uf = user_follower._json
            
            print(json.dumps(uf, indent=4, sort_keys=False))

        print('redirected ... ')
               
        output = buf.getvalue()  

    return output

def twitter_friends(request):
    import tweepy
    from contextlib import redirect_stdout

    auth = tweepy.OAuthHandler('2bqgyafUPQSSRDB9IFLN1I7Ah', 'Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24')

    if 'access_token' in request.session:

        print('Using Valid access token')

        token = request.session.get('request_token')

        print('oauth_token ', token)

        # request.session.delete('request_token')
        auth.request_token = {'oauth_token': request.session.get('request_token'), 'oauth_token_secret': request.session.get('oauth_verifier')}
        auth.set_access_token(request.session['access_token'][0], request.session['access_token'][1])

        # auth.request_token = {'oauth_token': request.session[''], 'oauth_token_secret': verifier}
        # access_token = auth.get_access_token(verifier)
        # output = run_test_api(auth)
        
        return JsonResponse(get_friends_list(auth), safe=False)

    else:

        print('session ', request.session)

    return HttpResponse('Nothing to do')
    

def twitter_test (request):
    import tweepy

    auth = get_twitter_auth(request)

    api = tweepy.API(auth)

    # print(api.friends(cursor=-1))
    # for tw_friend in api.friends(cursor=-1):
    
    cursor_value = -1 if request.GET.get('cursor', None) is None else request.GET.get('cursor')
    
    print("cursor value ", cursor_value)
    
    print(len(api.friends(cursor=cursor_value)))
    
    print(type(api.friends(cursor=cursor_value)[0]))
    print(type(api.friends(cursor=cursor_value)[1]))
    
    
    for resp_type in api.friends(cursor=cursor_value):
    
    # for resp_type in api.followers(cursor=cursor_value):  
    
        print("\n")
        print("type ", type(resp_type))
        
        # print("*******************************", isinstance(resp_type, tuple))
        
        if isinstance(resp_type, tweepy.models.ResultSet):
        
            for twitter_friend in resp_type:
            
                print(twitter_friend)
                print("\n")
        
        elif isinstance(resp_type, tuple):
        
            print(resp_type)
            print("\n")
            # print(resp_type[1])
            
            
            #print(tw_friend_set.)
        
        #print(" is type? ", type(tw_friend) == "<class 'tuple'>")
        
        # if isinstance(tw_friend, tuple):
        
            # print(tw_friend)
            # print("\n")
            
        # else:
        
            # print(tw_friend._json)
            # print("\n")
        
        
        #print(tw_friend)
        #print("\n")
        
        
        
        #print(tw_friend._json)
        
        #if '_json' in tw_friend:
        
        #    print(tw_friend._json)
        
        #print(tw_friend._json)

    # print(api.friends(cursor=1488472945521268610))
    
    # print(json.dumps(api.friends(), indent=4, sort_keys=True))
    # print(api.followers())

    # twitter_friends = get_friends_list(auth)
    # twitter_followers = get_followers_list(auth)
    
    # print('twitter_friends ', twitter_friends)
    # print('twitter_followers ', twitter_followers)

    return HttpResponse('Nothing to do')
   
    
def facebook_contacts_import (request):

    context = {}
    
    #return HttpResponse("Testing Gunicorn auto restart")

    return render(request, "facebook/index.html", context)
    
def linkedin_contacts_import (request):

        context = {}
        #return HttpResponse("ghj")
        if 'linkedin_access_token' in request.session and request.session['linkedin_access_token'] is not None:
            
            import requests
    
            lite_profile = requests.get('https://api.linkedin.com/v2/me', headers = {
                'Authorization': 'Bearer ' + request.session['linkedin_access_token'],
            })  
            
            context['linkedin_lite_profile'] = (lite_profile.text)
            #return HttpResponse(context['linkedin_lite_profile'])
            #print(context['linkedin_lite_profile'])

        
            
            # context['linkedin_lite_profile'] = json.loads(lite_profile.text) 

            # print('access_token_request ', access_token_request.text)
            
            # print('LinkedIn Access Token ', request.session['linkedin_access_token'])
        
        return render(request, "linkedin/index.html", context)
        
def linkedin_login (request):

    context = {}
    
    return HttpResponse("Linkedin login")
    
def linkedin_callback (request):
    
    context = {}
    
    auth_code = request.GET.get('code', None)
    #return HttpResponse("auth code 123" + auth_code)
    if auth_code:

        import requests
        
        access_token_request = requests.post('https://www.linkedin.com/oauth/v2/accessToken', data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            #'client_id': '77awx9dduw0nez',
            #'client_secret': 'V0jax7jybmW1K9ni',
            'client_id': '774mkvff40jh88',
            'client_secret': 'nktafZ4ILChLqcYA',            
            'redirect_uri': 'http://127.0.0.1:8002/contacts/linkedin-callback',
        })
        
        response = access_token_request.text
        
        print(response)
        
        if 'access_token' in response:
        
            response = json.loads(response)
            
            request.session['linkedin_access_token'] = response['access_token']
            
            return redirect('/contacts/linkedin-contacts-import')
        
            # print("access_token_request : ", response['access_token'])

        return HttpResponse("auth code " + auth_code)
        
    # return HttpResponse("auth code " + auth_code)
    # return render(request , "linkedin/index.html")
    return HttpResponse("Linkedin callback")
    
def update_graph (request):

    import networkx as nx    
    import os.path
    
    #contact_degrees = ContactDegree.objects.filter(user_id=38)
    #contact_id = Profile.objects.filter(user_id=38)[0].contact_id

    contact_degrees = ContactDegree.objects.filter(user_id=request.user.id)   
    contact_id = Profile.objects.filter(user_id=request.user.id)[0].contact_id
        
    graph_nodes = []
    graph_edges = []
    already_present_nodes = []
    already_present_edges = []
    connection_graph_path = "/home/ec2-user/aw/altworkz/static/json/graphs/connections-graph.xml"
        
    if os.path.isfile(connection_graph_path):

        print("Reading graph file ..... \n")
        
        try:
            
            graph = nx.DiGraph(nx.read_graphml(connection_graph_path))
            #graph = nx.DiGraph()
            already_present_nodes = nx.nodes(graph)            
            already_present_edges = nx.edges(graph)
        
        except Exception as e:
        
            print("Exception read ", e)
                    
    else:

        graph = nx.DiGraph()

    #print("Already present nodes ", already_present_nodes)      
    print("Already present edges ", already_present_edges)
    
    for user_contact in contact_degrees:
    
        if user_contact.user_contact_id:

            #pass
            #graph_nodes.append(user_contact.contact_degree_id)
            
            if (contact_id, user_contact.contact_degree_id) not in already_present_edges:
            
                graph_edges.append((contact_id, user_contact.contact_degree_id))
         
    if len(graph_edges) > 0:
    
        try:

            print("Adding edges ", graph_edges)

            graph.add_nodes_from(graph_nodes)    
            graph.add_edges_from(graph_edges)
            nx.write_graphml(graph, connection_graph_path)
            
        except Exception as e:

            print("Exception write ", e)
    
    return HttpResponse("Graph Update Operation")

