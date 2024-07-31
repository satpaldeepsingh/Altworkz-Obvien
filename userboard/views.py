import requests
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound, Http404, JsonResponse
from contacts_import.models import Contact, Job, School, Organization, Education, Tag, ContactEmail, ContactNumber,\
    SocialProfile, ContactDegree, PersonofInterest, ContactTag, ContactDescription, ContactScrapeSource
from accounts.models import Profile
from django.contrib import messages
from django.contrib.auth.models import User
from altworkz.settings import ES_INDEX_URL
# Create your views here.

from . models import UserTag

def index(request):
    context = {}
    user = User.objects.get(id=request.user.id)
    contacts = user.contacts.all().order_by('-id')
    # print(contacts)
    
    user_contacts_with_tags = '''SELECT contacts.id, contacts.first_name, contacts.last_name, GROUP_CONCAT(DISTINCT CONCAT("#", tags.name)) AS ctags, GROUP_CONCAT(DISTINCT CONCAT("#", csvt.name)) AS file_tags, GROUP_CONCAT(DISTINCT CONCAT(contact_emails.contact_email_primary)) AS primary_email, GROUP_CONCAT(DISTINCT CONCAT(contact_numbers.contact_number_secondary)) AS primary_phone FROM contacts 
                                 LEFT JOIN   contact_tags ct ON  contacts.id = ct.contact_id 
                                 LEFT JOIN   csv_tags csvt ON  contacts.id = csvt.contact_id                                         
                                 LEFT JOIN   tags 			ON  ct.tag_id   = tags.id
                                 LEFT JOIN contact_emails 	ON contacts.id = contact_emails.contact_id
                                 LEFT JOIN contact_numbers 	ON contacts.id = contact_numbers.contact_id                                                 
                                 WHERE       contacts.id IN (SELECT      contacts.id           FROM contacts                                               
                                 JOIN        contacts_users cu 	ON cu.contact_id = contacts.id    
                                 JOIN        unactivated_account_codes ap ON ap.user_id    = cu.user_id                           
                                 JOIN        auth_user 			ON auth_user.id  = ap.user_id                              
                                 WHERE       auth_user.id = ''' + str(request.user.id) + ''')                                     
                                 GROUP BY    contacts.id                                                                                                  
                                 ORDER BY    contacts.id'''    
                                     
    context['contacts'] = Contact.objects.raw(user_contacts_with_tags)

    emails = []
    phone = []
    contacts_emails = {}
    contact_numbers = {}
    for index, contacts_row in enumerate(contacts):
        contact_id = contacts_row.id
        contacts_all_emails = ContactEmail.objects.filter(contact_id=contact_id)
        if contacts_all_emails.exists():
            emails.append(contacts_all_emails)
        else:
            continue
    for index, contacts_row in enumerate(contacts):
        contact_id = contacts_row.id
        contacts_all_phone = ContactNumber.objects.filter(contact_id=contact_id)
        if contacts_all_phone.exists():
            phone.append(contacts_all_phone)
        else:
            continue
    context['contacts_emails'] = emails
    context['contacts_phone'] = phone
    return render(request, "index.html", {'context': context})

def multidelete_contacts (request):

    if request.is_ajax():

        contact_id_list = request.POST.getlist('contact_id_list[]')

        contacts = Contact.objects.filter(id__in=contact_id_list)
        contacts.delete()

        print('contact_id_list ', contact_id_list)

        # dict = {
        #     "query": {
        #         "bool": {
        #             "must": [
        #                 {"terms": {"contact_id": contact_id_list}}
        #             ]
        #         }
        #     }
        # }
        #
        # print(dict)

        # print(dquery)

        es_response = requests.post(ES_INDEX_URL + '/_delete_by_query',
                                   headers={'Content-Type': 'application/json'},
                                   data=json.dumps({
                                                        "query": {
                                                            "bool": {
                                                                "must": [
                                                                    {"terms": {"contact_id": contact_id_list}}
                                                                ]
                                                            }
                                                        }
                                                   }))

        elastic_response = json.loads(es_response.text)

        print(elastic_response)

        delete_msg = "Could not delete for some reason(s)"

        if 'total' in elastic_response:

            delete_msg = f"{elastic_response['total']} contact(s) successfully deleted"

        return JsonResponse({"msg": delete_msg})

    raise Http404('Invalid request')

def update_user_contact_tags (request):

    if request.is_ajax():
    
        user_id = request.user.id
        contact_id = request.POST.get('contact_id')
        tags = request.POST.get('tags[]')
        
        print("tags ", tags)
        
        
        for tag in tags:
        
            contact, created = UserTag.objects.update_or_create(defaults={'name': tag,
                                                                          'user_id': request.user.id,
                                                                          'contact_id': contact_id})       
            
        msg = 'Tags added'
        return JsonResponse({"msg": msg})
    raise Http404('Invalid request')



def edit(request, id):

    try:
        context = {}
        user = User.objects.get(id=request.user.id)
        context["contact"] = user.contacts.get(id=id)
        print('****************************User Details******************************')
        print(user)
        # context["contact"] = Contact.objects.get(
        #     id=id)

    except:
        raise Http404
    try:
        context["educations"] = context["contact"].educations.all()

        context["jobs"] = context["contact"].jobs.all()
    except:
        pass

    try:
        social_profiles = context["contact"].social_profiles.all()
        for index, social in enumerate(social_profiles, start=1):
            if social.platform == 'facebook':
                context['social_fb'] = social.platform_link
            if social.platform == 'twitter':
                context['social_tw'] = social.platform_link
            if social.platform == 'linkedin':
                context['social_linkedin'] = social.platform_link
            if social.platform == 'bloomberg':
                context['social_bloomberg'] = social.platform_link

    except:
        pass
    try:
        context["contact_email"] = ContactEmail.objects.filter(contact_id=id)

    except:
        pass
    try:
        context["contact_number"] = ContactNumber.objects.filter(contact_id=id)
    except:
        pass
    try:
        context["contact_description"] = context["contact"].contact_description.all()
    except:
        pass
    try:
        contact_tag=[]
        tag_name = {}
        contact_tag_id = context["contact"].contact_tags.all()
        for index, contacts_row in enumerate(contact_tag_id):
            tag_id = contacts_row.tag_id
            tag = Tag.objects.filter(id=tag_id)
            contact_tag.append(tag)
        context['tags'] = contact_tag
    except:
        pass
    return render(request, 'edit.html', {'context': context})

import json
def update(request, id):
    if request.is_ajax():

        user_contact_id = 0
        is_request_update_profile = request.POST.get('update_profile_request', None)
        print('hgfb----------:' ,is_request_update_profile)

        if is_request_update_profile is not None and is_request_update_profile == 'true':
            print('hgfb----------:' ,is_request_update_profile is not None and is_request_update_profile == 'true')
            user_contact_id = Profile.objects.get(user_id=request.user.id).contact_id
        details = json.loads(request.POST.get('user_update_details'))
        educations = json.loads(request.POST.get('schools'))
        jobs = json.loads(request.POST.get('organizations'))
        first_name = details['first_name']
        middle_name = details['middle_name']
        last_name = details['last_name']
        email = details['email']
        phone = details['phone']
        country = details['country']
        description = details['description']
        contact_id = details['contact_id']
        fb_profile_url = details['fb_profile_url']
        twitter_profile_url = details['twitter_profile_url']
        linkedin_profile_url = details['linkedin_profile_url']
        bloomberg_profile_url = details['bloomberg_profile_url']
        tags =  details['tags']
        email_error = ''
        print('here')

        if first_name.strip() is not None:
            print('-------------')
            contact , created = Contact.objects.update_or_create(
                defaults={'user_id': request.user.id, 'first_name': first_name,
                        'middle_name': middle_name,
                        'last_name': last_name,
                        'country': country,
                        'description': description,
                        },
                id=id,
            )
        
            contact.users.add(request.user.id)
            print(contact.users.add(request.user.id))
 
        if email.strip() != '' and email is not None:
            if ContactEmail.objects.filter(contact_email_primary__iexact=email).exists() and is_request_update_profile != 'true':
                email_error = 'Email already exists'
            else:
                ContactEmail.objects.update_or_create(
                    defaults={'contact_email_primary': email},
                    contact_id=contact.id
                )
        else:
            ContactEmail.objects.filter(contact_id=contact_id).delete()

        if description.strip() != '' and description is not None:
            source_name = ContactDescription.objects.filter(contact_id=id)
            print('-------ContactDescription-----:' ,description.strip() )
            print('--------------------------------:',source_name)

            if source_name:
                for source in source_name:
                    source_id = source.source_id
                    contact_description, created = ContactDescription.objects.update_or_create(
                        defaults={'description': description,
                                  'contact_id': contact.id},
                        source_id=source_id,
                        contact_id=contact.id
                    )
            else:
                contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                    source_name='self update',
                )
                contact_description, created = ContactDescription.objects.update_or_create(
                    defaults={'description': description,
                              'contact_id': contact.id},
                    source_id=contact_scrape_source.id,
                    contact_id=contact.id,
                    platform_id=52131
                )
        else:
            ContactDescription.objects.filter(contact_id=contact_id).delete()

        if phone.strip() != '' and phone is not None:
            ContactNumber.objects.update_or_create(
                defaults={'contact_number_primary': phone},
                contact_id=contact.id
            )
        else:
            ContactNumber.objects.filter(contact_id=contact_id).delete()

        if fb_profile_url.strip() != '':
            SocialProfile.objects.update_or_create(
                defaults={'platform_link': fb_profile_url, 'is_scraped': '0'},
                contact_id=contact.id,
                platform='facebook',
            )
        else:
            SocialProfile.objects.filter(contact_id=contact_id, platform='facebook').delete()

        if twitter_profile_url.strip() != '':
            SocialProfile.objects.update_or_create(
                defaults={'platform_link': twitter_profile_url, 'is_scraped':'0'},
                contact_id=contact.id,
                platform='twitter',
            )

        if linkedin_profile_url.strip() != '':
            SocialProfile.objects.update_or_create(
                defaults={'platform_link': linkedin_profile_url, 'is_scraped': '0'},
                contact_id=contact.id,
                platform='linkedin',
            )
        if bloomberg_profile_url.strip() != '':
            SocialProfile.objects.update_or_create(
                defaults={'platform_link': bloomberg_profile_url, 'is_scraped': '0'},
                contact_id=contact.id,
                platform='bloomberg',
            )

        for index, education in enumerate(educations, start=1):
            global school_abbreviation
            if education:
                print('------EDU HERE ------')
                if 'school_id' in education and education['school_id'] != '':
                    school_name = education['school_name'].strip()
                    school_id = education['school_id']
                    school_abbreviation = education['school_abbr'].strip()
                    print("school_abbreviation: " , school_abbreviation)
                    if school_name != '':
                        School.objects.filter(id=school_id).update(school_name=school_name, school_abbreviation=school_abbreviation)
                else:
                    print('Education ', education)
                    school_name = education['school_name'].strip()

                    if school_name != '':
                        try:
                            edu_obj, created = School.objects.update_or_create(
                                school_name=school_name,
                                school_abbreviation=school_abbreviation,
                                defaults={'source_id':6,'platform_id':52131}
                            )
                            
                            if education['school_name'] != '':
                                school_name = education['school_name'].strip()
                                school_abbreviation = education['school_abbr'].strip()
                                school_start_year = education['school_start'].strip()
                                school_end_year = education['school_end'].strip()
                                degree = education['degree'].strip()
                                if school_name != '':
                                    new_edu = Education.objects.create(degree=degree,school_start_year=school_start_year, school_end_year=school_end_year,contact_id=user_contact_id,source_id=6,platform_id=52131)
                                    new_edu.school.add(edu_obj.id)
                                              
                        except Exception as e:
                            print('Exception occurred while school creation \n')
                            print(e)

                        print("created ", created)


                if 'education_id' in education and education['education_id'] != '':
                    print("Updating Education ")
                    education_id = education['education_id']
                    school_start_year = education['school_start'].strip()
                    school_end_year = education['school_end'].strip()
                    degree = education['degree'].strip()
                    if school_start_year != '':
                        Education.objects.filter(id=education_id).update(degree=degree,
                            school_start_year=school_start_year, school_end_year=school_end_year)

        for index, job in enumerate(jobs, start=1):

            if job:
                if 'organization_id' in job and job['organization_id'] != '':
                    organization_name = job['organization_name'].strip()
                    if organization_name != '':
                        Organization.objects.filter(id=job['organization_id']).update(organization_name=organization_name)
                else:
                    organization_name = job['organization_name'].strip()

                    if organization_name != '':
                        org_obj, created = Organization.objects.update_or_create(
                            organization_name=organization_name,
                            defaults={'source_id':6,'platform_id':52131}
                        )
                        print("org_obj ", org_obj)
                        print("created ", created)

                    if job['organization_job'] != '':
                        job_title = job['organization_job'].strip()
                        job_start_date = job['organization_start'].strip()
                        job_end_date = job['organization_end'].strip()
                        if job_title != '':
                            new_job = Job.objects.create(
                                job_title=job_title, job_start_date=job_start_date, job_end_date=job_end_date, contact_id=user_contact_id, source_id=6, platform_id=52131)

                            new_job.organization.add(org_obj.id)

                if 'job_id' in job and job['job_id'] != '':
                    job_title = job['organization_job'].strip()
                    job_start_date = job['organization_start'].strip()
                    job_end_date = job['organization_end'].strip()
                    if job_title != '':
                        Job.objects.filter(id=job['job_id']).update(
                            job_title=job['organization_job'], job_start_date=job_start_date, job_end_date=job_end_date)

            contact_tag_method(tags, contact_id)

        return JsonResponse({"data": True, "email_error": email_error})
    else:
        print("else: ")
    return JsonResponse(True, safe=False)

def destroy(request , id):
    if request.is_ajax():
        contact = Contact.objects.get(id=id)
        contact.delete()
        requests.delete(ES_INDEX_URL + '/_doc/' + str(id))
        # es = ElasticSearch()
        # es.delete_elastic_index_doc(id)
        # DELETE /ml_test_2/_doc/330
        return JsonResponse({"data": True})
    else:
        print("else: ")
    return JsonResponse(True, safe=False)

def contact_tag_method(tags, contact_id):
    ContactTag.objects.filter(contact_id=contact_id).delete()
    tags = tags.split(',')

    for tag in tags:
        tag, created = Tag.objects.update_or_create(
            name=tag.strip()
        )
        contact_tags, created = ContactTag.objects.update_or_create(
            contact_id=contact_id,
            tag_id=tag.id)



def update_profile (request, id):
    print("----working----")

    # user = User.objects.get(id=request.user.id)
    # profile = Profile.objects.filter(user_id=request.user.id).values()[0]
        
    # print("profile ", profile)

    # return HttpResponse('----------------------- 4444 -----------------------')

    try:
        context = {}
        user = User.objects.get(id=request.user.id)
        profile = Profile.objects.filter(user_id=request.user.id).values()[0]

        # if 'first_time_login' in request.session and request.session['first_time_login'] == True:
        #
        #     context['first_time_login'] = True
        #
        #     print('................ first time login ................\n')
        #
        # else:
        #
        #     print('................ Ususal login ................\n')

        
        # print("profile ", profile['contact_id'])
        
        # context["contact"] = user.contacts.get(id=id)
        
        contact = Contact.objects.get(id=profile['contact_id'])
        
        context["contact"] = contact
                
        print("contact ", context["contact"])
        
        if request.session.get('first_time_login', None) and request.session['first_time_login'] == True:
            context["first_time_login"] = True
            messages.success(request , "Either you are providing invalid username or password OR your access to this system is approved by admin. In case you belive that you are supplying correct credentials, please contact rak@bridges.com for activation of your account.")
            context['success_redirect_url'] = 'http://127.0.0.1:8001/contacts/'
            print(context)

    except:
        raise Http404
    
    try:
        context["educations"] = contact.educations.all()
        
        print("edu ", context['educations'])

        context["jobs"] = contact.jobs.all()

        for job in context['jobs']:
            print("job ", job.organization.all())
        
        print("jobs ", context['jobs'])
        
    except:
        pass

    try:
        social_profiles = contact.social_profiles.all()
        for index, social in enumerate(social_profiles, start=1):
            if social.platform == 'facebook':
                context['social_fb'] = social.platform_link
            if social.platform == 'twitter':
                context['social_tw'] = social.platform_link
            if social.platform == 'linkedin':
                context['social_linkedin'] = social.platform_link
            if social.platform == 'bloomberg':
                context['social_bloomberg'] = social.platform_link

    except:
        pass
    try:
        context["contact_email"] = ContactEmail.objects.filter(contact_id=profile['contact_id'])

    except:
        pass
    try:
        context["contact_number"] = ContactNumber.objects.filter(contact_id=profile['contact_id'])
    except:
        pass
    try:
        context["contact_description"] = contact.contact_description.all()
    except:
        pass
    try:
        contact_tag=[]
        tag_name = {}
        contact_tag_id = contact.contact_tags.all()
        for index, contacts_row in enumerate(contact_tag_id):
            tag_id = contacts_row.tag_id
            tag = Tag.objects.filter(id=tag_id)
            contact_tag.append(tag)
        context['tags'] = contact_tag
    except:
        pass
    return render(request, 'update_profile.html', {'context': context})


def view_profile(request, id):
    try:
        try:
            context = {}
            new_profile = Profile.objects.filter(user_id=id).values()[0]
            
            print('new_profile ', new_profile)
            
            context["contact"] = Contact.objects.filter(id=new_profile['contact_id'])[0]
            
            print('contact id ', new_profile['contact_id'])
            print('contact ', context['contact'])
            
            
        except:
            raise Http404
        try:
            context["educations"] = context["contact"].educations.all()
            context["jobs"] = context["contact"].jobs.all()
        except:
            pass
        try:
            print('******************************new_profile**************************************')
            new_profile = Profile.objects.filter(user_id=id).values()[0]

            print(new_profile['contact_id'])
            context["contact_email"] = ContactEmail.objects.filter(contact_id=new_profile['contact_id'])

        except:
            pass
        try:
            context["contact_number"] = ContactNumber.objects.filter(contact_id=new_profile['contact_id'])
        except:
            pass
        try:
            context["contact_description"] = context["contact"].contact_description.all()
        except:
            pass

        return render(request, "view_profile.html", {'context': context})
    except Exception as e:
        print("not updated due to", e)