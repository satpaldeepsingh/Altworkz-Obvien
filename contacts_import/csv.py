
from contacts_import.models import Contact, Job, School, ContactScrapeSource, ContactDescription, Organization, Education, Tag, CSVTag, ContactTag, SocialProfile, ContactDegree, PersonofInterest, ContactEmail, ContactNumber
from django.http import HttpResponse
import re

def school_method(school_name, school_start_year, school_end_year, abbreviation, contact_id, source_id, social_profiles_id):
    school, created = School.objects.get_or_create(
        school_name=school_name,
        school_abbreviation=abbreviation,
        source_id=source_id,
        platform_id=social_profiles_id
    )
    education, created = Education.objects.update_or_create(
        school_start_year=school_start_year,
        school_end_year=school_end_year,
        contact_id=contact_id,
        source_id=source_id,
        platform_id=social_profiles_id
    )
    education.school.add(school.id)

def tag_method(tags, contact_id):
    tags = tags.split(',')

    for tag in tags:
        tag, created = Tag.objects.update_or_create(
            name=tag

        )
        contact_tags, created = ContactTag.objects.update_or_create(
            contact_id=contact_id,
            tag_id=tag.id)
            
def csv_tag_method(csv_tags, user_id, contact_id):
    # tags = csv_tags.split(',')

    # for tag in tags:
        # c_tags, created = CSVTag.objects.update_or_create(
            # contact_id=contact_id,
            # user_id = user_id,
            # name=tag)
                   
        # print("created ", created)
        
    c_tags, created = CSVTag.objects.update_or_create(
        contact_id=contact_id,
        user_id = user_id,
        name=csv_tags)    
    
def emails_method(contact_email_primary, contact_email_secondary, contact_email_tertiary, contact_id):
    contact_emails, created = ContactEmail.objects.update_or_create(
        contact_email_primary = contact_email_primary,
        contact_email_secondary = contact_email_secondary,
        contact_email_tertiary = contact_email_tertiary,
        contact_id = contact_id,
    )

def organization_method(organization_name, contact_id, source_id, social_profiles_id, job_start_date=None, job_end_date=None, job_title=None):

    organization, created = Organization.objects.get_or_create(
        organization_name=organization_name,

    )
    job, created = Job.objects.update_or_create(
        job_title=job_title,
        job_start_date=job_start_date,
        job_end_date=job_end_date,
        contact_id=contact_id,
        source_id=source_id,
        platform_id=social_profiles_id
    )
    job.organization.add(organization.id)


def validate_csv_row (csv_row, **kwargs):

    rejection_reasons = []

    if 'first_name' not in csv_row:

        rejection_reasons.append({"field": "first_name", "msg": "First name column should be present"})

    elif not csv_row['first_name']:

        rejection_reasons.append({"field": "first_name", "msg": "First name should not be empty"})

    if 'last_name' not in csv_row:

        rejection_reasons.append({'field': 'last_name', 'msg': 'Last name column should be present'})

    elif not csv_row['last_name']:

        rejection_reasons.append({'field': 'last_name', 'msg': 'Last name should not be empty'})

    if not csv_row['organization_name'] and not csv_row['organization_job_title']:

        rejection_reasons.append({'field': 'organization_job_title/organization_name', 'msg': 'organization job title or organization name should not be empty'})

    if csv_row.get('email', None) and (re.search('^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', csv_row['email'])) is None:

        rejection_reasons.append({"field": 'email', 'value': csv_row['email'], "msg": "Email not in proper format"})

    if csv_row.get('mobile', None) and (re.search('^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$', csv_row['mobile'])) is None:

        rejection_reasons.append({"field": "mobile", 'value': csv_row['mobile'], "msg": "Number field should not contain alphabets"})

    if csv_row.get('phone', None) and (re.search('^[+]*[(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9]*$', csv_row['phone'])) is None:

        rejection_reasons.append({"field": "phone", "value": csv_row['phone'], "msg": "Number field should be a valid phone number"})

    for url_field in ['photo', 'fb_profile_url', 'twitter_profile_url', 'linkedin_profile_url', 'bloomberg_profile_url']:

        if csv_row.get(url_field, None) and (re.search("(([\w]+:)?//)?(([\d\w]|%[a-fA-f\d]{2,2})+(:([\d\w]|%[a-fA-f\d]{2,2})+)?@)?([\d\w][-\d\w]{0,253}[\d\w]\.)+[\w]{2,63}(:[\d]+)?(/([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)*(\?(&?([-+_~.\d\w]|%[a-fA-f\d]{2,2})=?)*)?(#([-+_~.\d\w]|%[a-fA-f\d]{2,2})*)?", csv_row[url_field])) is None:

            rejection_reasons.append({"field": url_field, "value": csv_row[url_field], "msg": url_field + " field must be valid URL"})

    # if len(rejection_reasons) > 0:
    #     rejected_row_info.append({'row_no': index + 2, 'reasons': rejection_reasons})

    if len(rejection_reasons) > 0:

        rejected_row_info = {'row':csv_row, 'reasons': rejection_reasons}

        if 'index' in kwargs:

            # rejected_row_info['row_no'] = kwargs.get('index') + 2
            rejected_row_info['row_no'] = kwargs.get('index') + 1

        return rejected_row_info

    else:

        return True


def add_csv_row (csv_row, contact_type, tags, request, index):

    csv_validation = validate_csv_row(csv_row, index=index)

    if csv_validation == True:

        school = csv_row['school'] if csv_row.get('school', None) else ''
        school_start_year = ''
        school_end_year = ''
        school_abbreviation = ''
        organization_name = csv_row['organization_name'] if csv_row.get('organization_name', None) else ''
        organization_start_date = ''
        organization_end_date = ''
        organization_job_title = csv_row['organization_job_title'] if csv_row.get('organization_job_title',
                                                                                  None) else ''
        contact_tags = csv_row['contact_tags'] if csv_row.get('contact_tags', None) else ''

        if Contact.objects.filter(first_name=csv_row['first_name'], middle_name=csv_row['middle_name'], last_name=csv_row['last_name']).exists():

            Contact.objects.filter(first_name=csv_row['first_name']).update(
                photo=csv_row['photo'] if csv_row.get('photo', None) else '')

        else:

            print('******************************Name Not exits***************************************')

            contact, created = Contact.objects.update_or_create(

                user_id=request.user.id,

                first_name=csv_row['first_name'],

                middle_name=csv_row['middle_name'] if csv_row.get('middle_name', None) else '',

                last_name=csv_row['last_name'] if csv_row.get('last_name', None) else '',

                photo=csv_row['photo'] if csv_row.get('photo', None) else '',

                country=csv_row['country'] if csv_row.get('country', None) else '',

                city=csv_row['city'] if csv_row.get('city', None) else '',

                description=csv_row['description'] if csv_row.get('description', None) else ''

            )

            contact.users.add(request.user.id)

            if csv_row['email'] != '' and csv_row['email'] is not None:

                if ContactEmail.objects.filter(contact_email_primary__iexact=csv_row['email']).exists():

                    return True

                else:

                    ContactEmail.objects.update_or_create(
                        contact_email_primary=csv_row['email'],
                        contact_id=contact.id
                    )

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

            contact_description, created = ContactDescription.objects.update_or_create(
                source_id=contact_scrape_source.id,
                description=csv_row['description'] if csv_row.get('description', None) else '',
                contact_id=contact.id,
                platform_id=social_profiles_id
            )

            school1 = school_method(school, school_start_year, school_end_year, school_abbreviation, contact.id, source_id, social_profiles_id)

            organization1 = organization_method(
                organization_name, contact.id, source_id, social_profiles_id, organization_start_date, organization_end_date,
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

            tag_method(contact_tags, contact.id)

            tag_method(tags, contact.id)

            if contact_type == "1st_degrees":

                ContactDegree.objects.update_or_create(
                    user_id=request.user.id,
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

    return csv_validation

def validate_csv_headers(headers):
    impo_csv_herders = set(import_csv_headers())
    print('impo_csv_herders',impo_csv_herders)
    upload_csv_headers = set(headers)
    print('upload_csv_headers:' ,upload_csv_headers)

    if impo_csv_herders.issubset(upload_csv_headers):
        CSV_HEADERS_CONSTANTS = get_csv_headers()
        csv_headers_cons = set(CSV_HEADERS_CONSTANTS)
        csv_headers = set(headers)
        print('CSV headers:', csv_headers)   
        if len(csv_headers) > 0:
            if not csv_headers.issubset(csv_headers_cons):
                return False
        return True
    else:
        return False

def validate_social_csv_header(headers):
    impo_social_csv_herders = set(import_social_csv_headers())
    print('impo_social_csv_herders:' , impo_social_csv_herders)
    upload_social_csv_headers = set(headers)
    print('upload_social_csv_headers:' , upload_social_csv_headers)
    print("Check:" ,impo_social_csv_herders.issubset(upload_social_csv_headers))

    if impo_social_csv_herders.issubset(upload_social_csv_headers):
        print('----------herejjjjjjj-----------')
        CSV_HEADERS_CONSTANTS = get_social_csv_headers()
        csv_headers_cons = set(CSV_HEADERS_CONSTANTS)
        csv_headers = set(headers)
        if len(csv_headers) > 0:
            if not csv_headers.issubset(csv_headers_cons):
                return False
        return True
    else:
        return False

def get_csv_headers ():

    return [
        "first_name","middle_name","last_name","email","phone","organization_name", "organization_job_title","photo","mobile","city","country","school",
        "fb_profile_url","twitter_profile_url","linkedin_profile_url","bloomberg_profile_url","description"
    ]
    
def get_social_csv_headers ():

    return [
        "first_name","middle_name","Email Address","phone","organization_name", "organization_job_title", "Connected On"
    ]

def get_csv_table_headings ():

    return {
        "first_name" : "First Name",
        "middle_name" : "Middle Name",
        "last_name" : "Last Name",
        "email" : "Email",
        "phone" : "Phone No.",
        "organization_name" : "Organization / Company",
        "organization_job_title" : "Job Title / Position",
        "photo" : "Photo URL",
        "mobile" : "Mobile No.",
        "city" : "City",
        "country" : "Country",
        "school" : "School",
        "fb_profile_url" : "Facebook Profile",
        "twitter_profile_url" : "Twitter Profile URL",
        "linkedin_profile_url" : "Linkedin Profile URL",
        "bloomberg_profile_url" : "Bloomberg Profile URL",
        "description" : "",
    }


def import_csv_headers ():

    return ['first_name', 'last_name', 'organization_name', 'organization_job_title']
    
def import_social_csv_headers ():

    return ['first_name' , 'middle_name' , 'organization_name' , 'organization_job_title']

def get_csv_headers_description ():

    return {
        "first_name" : "First Name of your contact (Required)",
        "middle_name" : "Middle Name your contact",
        "last_name" : "Last Name of your Contact",
        "email" : "Email of Contact",
        "photo" : "Valid Picture URL of contact",
        "phone" : "Valid Phono no. of contact",
        "mobile" : "Valid mobile no. of contact",
        "city" : "City name of contact",
        "country" : "Country name of contact",
        "school" : "Current / Most recent school",
        "organization_name" : "Current / Most recent organization / company",
        "organization_job_title" : "Previous organization / company job title",
        "fb_profile_url" : "Valid URL of Facebook profile",
        "twitter_profile_url" : "Valid URL of Twitter profile",
        "linkedin_profile_url" : "Valid URL of Twitter profile",
        "bloomberg_profile_url" : "Valid URL of Bloomberg profile",
        "description" : "",
        "tags" : ""
    }


