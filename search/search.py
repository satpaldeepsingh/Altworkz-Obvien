import json
import os
import requests
import re
import inflect

from altworkz.settings import BASE_DIR
from contacts_import.models import Contact, ContactDegree, Education
from django.contrib.auth.models import User


from nltk import word_tokenize

from .location import Location
from .utilities import *


# ================================== #
#              SEARCH                #
# ================================== #
from accounts.models import Profile


class Search:

    def __init__(self):

        # query / query pre-processing

        self.user_query = ''
        self.query_str_exclusion_words = ['a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'if', 'in',
                                          'into', 'is', 'it', 'no', 'not', 'of', 'on', 'or', 'such', 'that', 'the',
                                          'their', 'then', 'there', 'these', 'they', 'this', 'to', 'was', 'will',
                                          'with']
        self.query_str_exclusion_symbols = ['&', ';', ',', '........', '\'']
        self.query_str_exclusion_list = self.query_str_exclusion_words + self.query_str_exclusion_symbols
        self.query_str = ''
        self.query_terms_categories = {}
        self.query_word_list = []
        self.field_query_term = {}
        self.user_feedback = []

        self.fields = {
            'first_name': 'first_name',
            'last_name': 'last_name',
            'full_name': 'full_name',
            'industry': 'industry',
            'headline': 'headline',
            'job_title': 'job_title', # same role as organization_title_n, might be used for filters purpose          # current job title
            'degree': 'degree',
            'summary': 'summary',
            'location': 'location',
            'ctags': 'ctags',
            'city': 'city',
            'country': 'country',
            'area': 'area',
            # 'member_of_platform': 'member_of_platform',
            'skills': 'skills',
            'school_n': 'school_',  # n denotes number against field school_1, school_2,
            'education_degree_n': 'degree_',
            'educatiion_start_n': 'education_start_',
            'education_end_n': 'education_end_',
            'education_grade_n': 'education_grade_',
            'education_description_n': 'education_description_',
            'organization_n': 'organization_', # n denotes number against field organization_1, organization_2,
            'organization_title_n': 'organization_title_', # n denotes number against field organization_title_1, organization_title_2,
            'organization_start_n': 'organization_start_',
            'organization_end_n': 'organization_end_',
            'organization_city_n': 'organization_city_',
            'organization_country_n': 'organization_country_',
        }

        self.related_entities = {}

        # weightages

        self.sec_field_def_weight = 0  # secondary fields default weight 1 | 0.5 | 0

        self.per_month_experience_weightage = 0.010
        # self.per_month_experience_weightage = 0.050


        # self.default_weightages = {self.fields['first_name']: 5, self.fields['last_name']: 5, self.fields['industry']: 3, self.fields['headline']: 3, self.fields['location']: 3, self.fields['skills']: 2}

        self.search_function = 'default'

        self.default_weightage = {
            # fields weightages
            self.fields['first_name']: 20,
            self.fields['last_name']: 15,
            self.fields['industry']: 10,
            self.fields['headline']: 10,
            self.fields['job_title']: 10,
            self.fields['location']: 10,
            self.fields['city']: 10,
            self.fields['country']: 10,
            self.fields['area']: 10,
            # self.fields['organization']: 10,
            # self.fields['school']: 10,
            self.fields['organization_n']: 10,
            self.fields['school_n']: 10,
            self.fields['degree']: 5,
            # self.fields['member_of_platform']: 5,
            self.fields['skills']: 2,
            # other weightages
            'time_relevancy': 5,  # set weight for terms which are currently present such as job
            '1st_degree_connection': 10,
        }

        # add weightages for user defined weightages for now
        self.user_defined_weightage = {
            self.fields['first_name']: 20,
            self.fields['last_name']: 15,
            self.fields['industry']: 10,
            self.fields['job_title']: 10,
            self.fields['city']: 10,
            self.fields['country']: 10,
            self.fields['area']: 10,
        }

        # Find a job, Learn a skill, Sell a product or service, Grow your network, Meet for coffee

        self.job_weightage = {self.fields['first_name']: 20, self.fields['last_name']: 15,
                              self.fields['industry']: 10, self.fields['headline']: 10,
                              self.fields['location']: 10, self.fields['skills']: 2}

        self.education_weightage = {self.fields['first_name']: 20, self.fields['last_name']: 15,
                                    self.fields['industry']: 10, self.fields['headline']: 10,
                                    self.fields['location']: 10, self.fields['skills']: 2}

        self.sale_weightage = {self.fields['first_name']: 20, self.fields['last_name']: 15,
                               self.fields['industry']: 10, self.fields['headline']: 10,
                               self.fields['location']: 10, self.fields['skills']: 2}

        self.grow_network_weightage = {self.fields['first_name']: 20, self.fields['last_name']: 15,
                                       self.fields['industry']: 5, self.fields['headline']: 5,
                                       self.fields['location']: 15, self.fields['skills']: 1}

        self.meeting_weightage = {self.fields['first_name']: 20, self.fields['last_name']: 15,
                                  self.fields['industry']: 10, self.fields['headline']: 10,
                                  self.fields['location']: 10, self.fields['skills']: 1}

        self.weightage_type = {
            'default': self.default_weightage,
            'user_defined': self.user_defined_weightage,
            'education': self.education_weightage,
            'sale': self.sale_weightage,
            'meeting': self.meeting_weightage,
            'network_growth': self.grow_network_weightage,
        }

        self.common_attrs_weightage = {}

        # First degree connections
        self.first_degree_connections = []
        self.second_degree_connections = []
        self.third_degree_connections = []
        self.persons_of_interests  = []
        self.third_degree_plus_connections = []

        # temp variables
        self.second_degree_connections_queried = False
        self.third_degree_connections_queried = False

        # filters
        self.filters = {}
        self.filter_weights = {}

        # self.user_profile = {}
        self.job_history = []
        self.education_history = []

        # temp variables
        self.user_profile_queried = False
        self.job_history_queried = False
        self.education_history_queried = False

        self.most_recently_attended_institutions = {
            'education': {
                'institute': '',
                'degree': '',
                'end_year': 0
            },
            'job': {
                'organization': '',
                'title': '',
                'end_date': ''
            }
        }

        # results

        self.results = []
        
        self.twitter_profiles = []
                
    #def update_confidence_score (self):

        # self.sort_options = {}

    def preproces_query(self):

        # spell_checker = SpellChecker()
        # disable spell corrector for now
        # query_word_list = [spell_checker.correction(x.strip()) for x in query.lower().split(' ')]
        query_word_list = [x.strip() for x in self.user_query.lower().split(' ')]  # convert to lower case and split each query word by space
        query_word_list = list(set(query_word_list).difference(self.query_str_exclusion_list))  # exclude stop words
        # query_word_list = list(set(query_word_list).symmetric_difference(set(self.query_str_exclusion_list)))
        # query_word_list = self.search_parsed_terms(query_word_list)
        
        print(query_word_list)
        # exit()

        self.query_terms_categories = self.categorize_query_terms(query_word_list)
        query_word_list = self.add_synonyms(query_word_list)

        print(query_word_list)
        print(self.query_terms_categories)

        return query_word_list

    def search_parsed_terms(self, parsed_terms):

        query_terms = []
        # parsed_terms = query_string.split()
        no_of_terms = len(parsed_terms)
        curr_term_no = 0

        while curr_term_no < no_of_terms:

            curr_term = parsed_terms[curr_term_no]
            next_term_no = curr_term_no + 1
            prev_term = curr_term
            last_term_index = no_of_terms - 1

            while next_term_no <= last_term_index + 1 and len(self.search_dictionary(curr_term)) > 0:

                prev_term = curr_term

                if next_term_no < no_of_terms:
                    curr_term += ' ' + parsed_terms[next_term_no]

                curr_term_no = next_term_no - 1
                next_term_no += 1

            else:

                query_terms.append(prev_term)
                curr_term_no += 1

        return query_terms

    def categorize_query_terms(self, query_word_list):

        qt_categories = {}

        field_categories = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/weightage/field_categories.json'), "r").read())

        for query_term in query_word_list:

            if query_term in field_categories:

                qt_categories[query_term] = {}
                qt_categories[query_term]['category'] = field_categories[query_term]

                self.field_query_term[qt_categories[query_term]['category']] = query_term

                if field_categories[query_term] == self.fields['location']:

                    loc = Location()
                    query_location_info = loc.search_location(query_term)

                    print('query location')
                    print(query_location_info)

                    if query_location_info is not None:
                        qt_categories[query_term]['parent'] = query_location_info['country'].lower()
                        qt_categories[query_term]['type'] = query_location_info['type'].lower()

                else:

                    qt_categories[query_term]['parent'] = ''

        return qt_categories

    def search_dictionary(self, term):

        # print("Searching term in wikipedia " + term)
        dictionary_terms = requests.get('https://en.wikipedia.org/w/api.php',
                                        params={'action': 'opensearch', 'namespace': '0', 'search': term, 'limit': '5',
                                        'format': 'json'}).json()
        # print(dictionary_terms)

        # if dictionary_terms[1] is not None and dictionary_terms[1][0].lower() == term:
        if len(dictionary_terms[1]) > 0 and term in dictionary_terms[1][0].lower():

            return dictionary_terms[1]

        return []

    def add_synonyms(self, query_terms_list):

        synonyms = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/weightage/alias_terms.json'), "r").read())

        for qt_index, query_term in enumerate(query_terms_list):

            if query_term in synonyms:

                query_terms_list[qt_index + 1:1] = synonyms[query_term]

        return query_terms_list

    def get_related_entities(self):

        entities = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/weightage/related_entities.json'), "r").read())

        return entities

    def already_in_occurance_fields(self, field, occurance_fields):

        for o_field in occurance_fields:

            if field in o_field:
                return True

        return False

    def term_presence_weightage(self, query_term, ri_field, ri_value, result_item, field_weightages):

        inflct = inflect.engine()

        if query_term in ri_value or inflct.plural(query_term) in ri_value:

            # if same term exists multiple times in same field
            # (except skills in which occurance frequency is calculated single time only and then multiplied by weight)
            # then only assign weight point 1 otherwise default weight point of that field

            # print("**********************\n")
            # print(re.search('^' + self.fields['organization_city_n'] + '[0-9]$', ri_field))
            # print(ri_field)
            # print("**********************\n")

            if self.already_in_occurance_fields(ri_field, result_item['occurance_fields']):

                if ri_field != self.fields['skills']:

                    result_item['weightage']['field_weightage'] += 1

            else:
            
                if query_term not in result_item['confidence_score']['matched_keywords']:
            
                    result_item['confidence_score']['matched_keywords'].append(query_term)
            
                    result_item['confidence_score']['search_terms_matched'] += 1
                    result_item['confidence_score']['calculated_score'] = (result_item['confidence_score']['search_terms_matched'] / result_item['confidence_score']['total_search_terms']) * 100 
                
                    if result_item['confidence_score']['calculated_score'] > 100:
                    
                        result_item['confidence_score']['calculated_score'] = 100
            
            
                if ri_field == 'skills':

                    result_item['weightage']['field_weightage'] += 0.50 * ri_value.count(query_term)  # multiply skill weight by no. of occurances that exists in query term

                elif re.search('^' + self.fields['organization_title_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_city_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_country_n'] + '[0-9]$', ri_field):

                    # if job title or organization is current or most recent then assign full points otherwise deduct 8 points to ensure time relevancy

                    field_num = ri_field[-1]

                    if ri_field == 'organization_title_1':

                        # print("----- ADDING JOB TITLE WEIGHTAGE " + str(field_weightages.get(self.fields['job_title'], self.sec_field_def_weight)) + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['job_title'], self.sec_field_def_weight)

                    else:

                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['job_title'], self.sec_field_def_weight) - 8

                    if ri_field == 'organization_1':

                        # print("----- ADDING ORGANIZATION 1 WEIGHTAGE " + str(field_weightages.get(self.fields['organization_n'], self.sec_field_def_weight)) + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['organization_n'], self.sec_field_def_weight)

                    else:

                        # print("----- ADDING ORGANIZATION WEIGHTAGE " + str(field_weightages.get(self.fields['organization_n'], self.sec_field_def_weight) - 8) + " for " + ri_value + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['organization_n'], self.sec_field_def_weight) - 8


                    # **************************************** #

                    if ri_field == 'organization_city_1':

                        # print(result_item['full_name'])
                        # print("----- ADDING JOB CITY WEIGHTAGE " + str(field_weightages.get(self.fields['city'], self.sec_field_def_weight)) + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['city'], self.sec_field_def_weight)

                    else:
                        # print(result_item['full_name'])
                        # print("----- ADDING JOB CITY WEIGHTAGE " + str(field_weightages.get(self.fields['city'], self.sec_field_def_weight) - 8) + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['city'], self.sec_field_def_weight) - 8


                    if ri_field == 'organization_country_1':
                        # print(result_item['full_name'])
                        # print("----- ADDING JOB COUNTRY WEIGHTAGE " + str(field_weightages.get(self.fields['country'], self.sec_field_def_weight)) + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['country'], self.sec_field_def_weight)

                    else:
                        # print(result_item['full_name'])
                        # print("----- ADDING JOB COUNTRY WEIGHTAGE " + str(field_weightages.get(self.fields['country'], self.sec_field_def_weight) - 8) + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['country'], self.sec_field_def_weight) - 8


                    # **************************************** #

                    try:

                        result_item['weightage']['experience_weightage'] += months_bw_date_intervals_fmt(result_item[self.fields['organization_end_n'] + field_num], result_item[self.fields['organization_start_n'] + field_num]) * self.per_month_experience_weightage
                        result_item['occurance_fields'].append({ri_field: ri_value})

                    except:

                        print("No proper date format..... ")

                    # print(result_item[self.fields['full_name']] + " (" + ri_value + ")")
                    # print(convert_datediff_to_months(org_start_time, org_end_time)


                elif re.search('^' + self.fields['school_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['education_degree_n'] + '[0-9]$', ri_field):

                    # if degree title or school is current or most recent then assign full points otherwise deduct 8 points to ensure time relevancy
                    field_num = ri_field[-1]

                    if ri_field == 'school_1':
                        # print(self.fields['school_n']+field_num)
                        # print("----- ADDING SCHOOL 1 WEIGHTAGE " + str(field_weightages.get(self.fields['school_n'], self.sec_field_def_weight)) + " -----\n")
                        # print(self.search_function)
                        # print(field_weightages)
                        result_item['weightage']['field_weightage'] += field_weightages.get(self.fields['school_n'], self.sec_field_def_weight)

                    if ri_field == 'degree_1':
                        # print("----- ADDING SCHOOL WEIGHTAGE " + str(field_weightages.get('degree_n', self.sec_field_def_weight)) - 8 + " -----\n")
                        result_item['weightage']['field_weightage'] += field_weightages.get('degree_n', self.sec_field_def_weight) - 8

                else:

                    # self, ri_field, ri_value, query_term, result_item
                    if self.search_function != 'default':

                        self.assign_search_function_weightage(result_item)

                    result_item['weightage']['field_weightage'] += field_weightages.get(ri_field, self.sec_field_def_weight)  # if field is among field_weightages then assign its weightage otherwise set default weight

            result_item['occurance_fields'].append({ri_field: query_term})

    def get_education_history (self):

        edu_history = []

        contact_edu_history = Contact.objects.raw('SELECT contacts.id, contacts.first_name, contacts.last_name, educations.degree, schools.school_name, educations.school_start_year, educations.school_end_year FROM contacts JOIN accounts_profile ON accounts_profile.contact_id 	= contacts.id JOIN educations ON contacts.id = educations.contact_id JOIN educations_school ON educations.id = educations_school.education_id JOIN schools ON schools.id = educations_school.school_id WHERE accounts_profile.user_id = ' + str(self.user_id))

        for edu_hist in contact_edu_history:

            edu_history.append({'degree': edu_hist.degree, 'school': edu_hist.school_name, 'start_year': edu_hist.school_start_year, 'end_year': edu_hist.school_end_year})

            if edu_hist.school_end_year.isdigit():

                if self.most_recently_attended_institutions['education']['end_year'] < int(edu_hist.school_end_year):

                    self.most_recently_attended_institutions['education']['institute'] = edu_hist.school_name
                    self.most_recently_attended_institutions['job']['degree'] = edu_hist.degree
                    self.most_recently_attended_institutions['education']['end_year'] = int(edu_hist.school_end_year)

            else:

                print("ALERT...... NON NUMERIC STRING IN EDU END DATE")
                print("END DATE ..... " + edu_hist.school_end_year)

        # print(self.most_recently_attended_institutions['education'])

        return edu_history

    def get_job_history (self):

        job_history = []

        contact_job_history = Contact.objects.raw('SELECT contacts.id, jobs.job_title, organizations.organization_name, jobs.job_start_date, job_end_date FROM contacts JOIN accounts_profile ON accounts_profile.contact_id = contacts.id JOIN jobs ON contacts.id = jobs.contact_id JOIN jobs_organization ON jobs_organization.job_id = jobs.id JOIN organizations ON organizations.id = jobs_organization.organization_id WHERE accounts_profile.user_id = ' +  str(self.user_id))

        # print("Contact Job History ", contact_job_history)

        for job_hist in contact_job_history:

            job_history.append({'job_title': job_hist.job_title, 'organization': job_hist.organization_name, 'start': job_hist.job_start_date, 'end': job_hist.job_end_date})
            #convert_to_format
            # if self.most_recently_attended_institutions['job']['end_date'] < convert_to_format(job_hist.job_end_date):
            if job_hist.job_end_date.lower() == 'present' or self.most_recently_attended_institutions['job']['end_date'] < job_hist.job_end_date:

                self.most_recently_attended_institutions['job']['organization'] = job_hist.organization_name
                self.most_recently_attended_institutions['job']['title']        = job_hist.job_title
                self.most_recently_attended_institutions['job']['end_date']     = job_hist.job_end_date

        # print(self.most_recently_attended_institutions['job'])

        return job_history

    def search_common_attrs_and_assign_weightage(self, ri_field, ri_value, result_item, field_weightages):

        # print(result_item['full_name'] + " ...... SEARCHING COMMON ATTRS ...... " )

        if not self.job_history_queried:

            self.job_history_queried = True
            self.job_history = self.get_job_history()
            # print("------------------------------ JOB HISTORY ------------------------------")
            # print(self.job_history)

        if not self.education_history_queried:

            self.education_history_queried = True
            self.education_history = self.get_education_history()
            # print("------------------------------ EDUCATION HISTORY ------------------------------")
            # print(self.education_history)

        # return True
        
        # print(json.dumps(result_item, indent=4, sort_keys=True))
        
        #if 'twitter_profile' in result_item and result_item['twitter_profile'].strip() != '':

        #    twitter_handle = result_item['twitter_profile_url'].split('/')
        #    self.twitter_profiles.append('from:' + twitter_handle[len(twitter_handle)-1])
        #    twitter_profile = twitter_handle[len(twitter_handle)-1]
        #    result_item['twitter_profile'] = twitter_profile

            
        
        if 'social_contact_description_count' in result_item:

            itr_count = 1
            
            while itr_count <= result_item['social_contact_description_count']:

                # if 'social_profile_link_' + str(itr_count) in result_item and result_item['social_profile_link_' + str(itr_count)] is not None and result_item['social_profile_link_' + str(itr_count)].strip():
                if 'des_profile_link_' + str(itr_count) in result_item and result_item['des_profile_link_' + str(itr_count)] is not None and result_item['des_profile_link_' + str(itr_count)].strip():

                    if 'twitter' in result_item['des_profile_link_' + str(itr_count)]:
                        
                        print("Twitter Profile Link ....... \n")
                        
                        #pass
                        
                        twitter_handle = result_item['des_profile_link_' + str(itr_count)].split('/')
                        self.twitter_profiles.append('from:' + twitter_handle[len(twitter_handle)-1])
                        twitter_profile = twitter_handle[len(twitter_handle)-1]
                        result_item['twitter_profile'] = twitter_profile



                    #if self.filters['member_of_platform'].lower() + '.' in result_item['des_profile_link_' + str(itr_count)].strip().lower():

                    #    print("Person for link found ..... " + result_item['full_name'])
                    #    print(result_item['des_profile_link_' + str(itr_count)])
                        
                                                                
                itr_count += 1  

            # if twitter_profile:

            #    result_item['twitter_profile'] = twitter_profile
        

        if re.search('^' + self.fields['organization_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_title_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['school_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['education_degree_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_city_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_country_n'] + '[0-9]$', ri_field):

            if re.search('^' + self.fields['organization_n'] + '[0-9]$', ri_field):

                itr = 1

                while (itr <= result_item['org_job_to_from_count']):

                    # print(result_item['full_name'] + " ...... SEARCHING COMMON ATTRS ...... " + str(result_item['organization_'+str(itr)]))
                    # print('user organization .... ' + self.most_recently_attended_institutions['job']['organization'])
                    # if result_item['organization_'+str(itr)].lower() == self.user_profile.organization.lower():
                    if result_item['organization_' + str(itr)] and result_item['organization_' + str(itr)].lower() == self.most_recently_attended_institutions['job']['organization'].lower():

                        print("... ADDING WOR WEIGHTAGE FOR SAME ORGANIZATION ... ")

                        if itr == 1 or result_item['organization_end_'+str(itr)].lower() == 'present': # if org. is current

                            result_item['weightage']['warmth_of_relationship_weightage'] += 5

                            result_item['common_institutions']['organization'].append(result_item['organization_' + str(itr)])

                            # print('---------------' + result_item['organization_title_'+str(exp_itr)].lower() + '---------------')
                            # print('---------------' + self.user_profile.job_title.lower() + '---------------')

                            # if result_item['organization_title_'+str(itr)].lower() in self.user_profile.job_title.lower() or self.user_profile.job_title.lower() in result_item['organization_title_'+str(itr)].lower():
                            
                            print('--------------- result_item["organization_title_"+str(exp_itr)].lower() ---------------\n')
                            print(result_item['organization_title_'+str(itr)])


                            print('--------------- self.most_recently_attended_institutions["job"]["title"] ---------------\n')                            
                            print(self.most_recently_attended_institutions['job']['title'])
                            
                            try:
                            
                                if result_item['organization_title_'+str(itr)] and ((result_item['organization_title_'+str(itr)].lower() in self.most_recently_attended_institutions['job']['title'].lower()) or (result_item['organization_title_'+str(itr)] and self.most_recently_attended_institutions['job']['title'].lower() in result_item['organization_title_'+str(itr)].lower())):

                                    print("... ADDING WOR WEIGHTAGE FOR SAME ORGANIZATION JOB TITLE ... ")

                                    result_item['weightage']['warmth_of_relationship_weightage'] += 1.25
                                    
                            except e as excpt:
                            
                                print("Exception : ", excpt)

                        else:

                            if result_item['organization_' + str(itr)] not in result_item['common_features']['organization']:
                                result_item['common_features']['organization'].append(result_item['organization_' + str(itr)])
                            result_item['weightage']['warmth_of_relationship_weightage'] += 1.25

                    else:

                        for user_job_history in self.job_history:

                            if user_job_history['organization'] == self.most_recently_attended_institutions['job']['organization'].lower():

                                continue

                            if result_item['organization_' + str(itr)] and user_job_history['organization'] == result_item['organization_' + str(itr)].lower():

                                if result_item['organization_' + str(itr)] not in result_item['common_features']['organization']:
                                    result_item['common_features']['organization'].append(result_item['organization_' + str(itr)])
                                result_item['weightage']['warmth_of_relationship_weightage'] += 1.25

                    itr += 1

            if re.search('^' + self.fields['school_n'] + '[0-9]$', ri_field):

                itr = 1

                while (itr <= result_item['edu_to_from_count']):

                    # print(result_item['full_name'] + " ...... SEARCHING COMMON ATTRS ...... " + str(result_item['organization_'+str(exp_itr)]))
                    # print('user organization .... ' + self.user_profile.organization.lower())
                    # if result_item['school_' + str(itr)].lower() == self.user_profile.organization.lower():
                    if result_item['school_' + str(itr)] and result_item['school_' + str(itr)].lower() == self.most_recently_attended_institutions['education']['institute'].lower():

                        print("... ADDING WOR WEIGHTAGE FOR SAME SCHOOL ... ")

                        if itr == 1 or result_item['school_end_'+str(itr)].lower() == 'present': # if org. is current:  # if org. is current

                            result_item['weightage']['warmth_of_relationship_weightage'] += 3

                            result_item['common_institutions']['education'].append(result_item['school_' + str(itr)])

                            if result_item['degree_'+str(itr)] and result_item['degree_'+str(itr)].lower() in self.most_recently_attended_institutions['education']['degree'].lower() or self.most_recently_attended_institutions['education']['degree'].lower() in result_item['degree_'+str(itr)].lower():

                                print("... ADDING WOR WEIGHTAGE FOR SAME ORGANIZATION JOB TITLE ... ")

                                result_item['weightage']['warmth_of_relationship_weightage'] += 0.5

                        else:

                            if result_item['school_' + str(itr)] not in result_item['common_features']['education']:
                                result_item['common_features']['education'].append(result_item['school_' + str(itr)])
                            result_item['weightage']['warmth_of_relationship_weightage'] += 1

                    else:

                        for user_edu_history in self.education_history:

                            if user_edu_history['school'] == self.most_recently_attended_institutions['education']['institute'].lower():

                                continue
                                
                                if result_item['school_' + str(itr)] and user_edu_history['school'] == result_item['school_' + str(itr)].lower():

                                    if result_item['school_' + str(itr)] not in result_item['common_features']['education']:
                                        result_item['common_features']['education'].append(result_item['school_' + str(itr)])
                                    result_item['weightage']['warmth_of_relationship_weightage'] += 1.25

                    itr += 1

                    pass

        return True

    def term_relation_weightage(self, query_term, ri_field, ri_value, result_item, field_weightages):

        inflct = inflect.engine()

        if ri_field == self.fields['skills'] or ri_field == self.fields['industry'] or ri_field == self.fields['headline']:

            skills_list = [skill.lower() for skill in list(set(word_tokenize(ri_value)).difference(self.query_str_exclusion_list))]

            if not bool(self.related_entities):

                self.related_entities = self.get_related_entities()

            if ri_field == self.fields['industry'] or ri_field == self.fields['headline']:

                if self.related_entities.get(query_term):

                    if 'related' in self.related_entities:

                        alias_terms = self.related_entities[query_term]['related']

                        for query_alias_term in alias_terms:

                            if query_alias_term in ri_value or inflct.plural(query_term) in ri_value:
                                # assign weightage according to proximity to the term
                                result_item['weightage']['rel_weightage'] += 1  # right now set to fix weightage of one

            elif ri_field == self.fields['skills']:

                for skill in skills_list:

                    skill = re.sub('[^A-Za-z0-9]+', '', skill)

                    if skill in self.related_entities or inflct.plural(skill) in self.related_entities:

                        if skill in self.related_entities:

                            entity = self.related_entities[skill]
                            # print(entity)

                        else:

                            entity = self.related_entities[inflct.plural(skill)]

                        if 'aliases' in entity:

                            if query_term in entity['aliases'] or inflct.plural(query_term) in entity['aliases']:
                                result_item['weightage']['rel_weightage'] += 0.50

                        if 'related' in entity:

                            if query_term in entity['related'] or inflct.plural(query_term) in entity['related']:
                                result_item['weightage']['rel_weightage'] += 0.45

        elif ri_field == self.fields['location'] or ri_field == self.fields['city'] or ri_field == self.fields['country']:

            # process only if current query term being matched with ri_field is of type Location (ignore other terms)

            if self.fields['location'] in self.field_query_term and self.field_query_term['location'] == query_term:

                if self.query_terms_categories[query_term]['parent'] != ri_value:

                    location = Location()
                    # loc = word_tokenize(ri_value)[0]
                    print("location to be searched ......" + ri_value)

                    location_value = location.search_location(ri_value)

                    if location_value is not None and 'country' in location_value:

                        if self.query_terms_categories[query_term]['parent'] == location_value['country'].lower():

                            result_item['weightage']['field_weightage'] += field_weightages.get(ri_field, self.sec_field_def_weight) - 0.50

                            result_item['occurance_fields'].append({ri_field: location_value['country']})

                            print("Same country .......")

                        else:

                            result_item['weightage']['neg_weightage'] += -field_weightages.get(ri_field, self.sec_field_def_weight) * 2

                            if 'full_name' in result_item:

                                print("Country " + location_value['country'] + " Adding -ve weightage " + result_item['full_name'])

                            else:

                                print("Country " + location_value['country'] + " Adding -ve weightage " + result_item['first_name'] + ' ' + result_item['last_name'])
                        # print('location')
                        # print(location_value)

                else:

                    pass

    def search_query_terms_in_field_values_and_assign_weightage(self, query_word_list, ri_field, ri_value, result_item, field_weightages):

        inflct = inflect.engine()

        for query_term in query_word_list:

            # search for singluar or plural form of query term in field value
            # if ri_value in 'paul':
            # print("query term " + query_term)
            # print("ri value " + ri_value)
            if query_term in ri_value or inflct.plural(query_term) in ri_value:
            
                print("Searching ri_value ")
                print(ri_value)
                print("Searching query_term " + query_term + "\n")

                self.term_presence_weightage(query_term, ri_field, ri_value, result_item, field_weightages)

            else:  # if exact term is not present find related ones, nest 'find related terms' inside else when else is uncommented

                # find related entries if the exact match doesn't exist and assign weightage accordingly
                self.term_relation_weightage(query_term, ri_field, ri_value, result_item, field_weightages)


    def assign_edu_function_weightage(self, result_item):

        edu_function_weightage = 0

        for field_name in result_item:

            if re.match('^' + self.fields['organization_n'] + '[0-9]$', field_name):

                field_num = field_name[-1]

                try:

                    edu_function_weightage_per_year = 10

                    # add weightage for present
                    if result_item[self.fields['organization_end_n'] + field_num].lower() == 'present':

                        edu_function_weightage += 10

                    edu_function_weightage += (months_bw_date_intervals_fmt(result_item[self.fields['organization_end_n'] + field_num], result_item[self.fields['organization_start_n'] + field_num]) / 12) * edu_function_weightage_per_year

                    # result_item['function_fields'].append({self.fields['organization_start_n'] + field_num: query_term})

                    print("try : PROPER DATE FORMAT")

                    print(result_item['headline'])

                except:

                    print("except : NO PROPER DATE FORMAT")

                    print(result_item['headline'])

                    print("start date " + self.fields['organization_end_n'] + field_num + " " + result_item[self.fields['organization_end_n'] + field_num])
                    print("end date " + self.fields['organization_start_n'] + field_num + " " + result_item[self.fields['organization_start_n'] + field_num])

        return edu_function_weightage

    def assign_search_function_weightage (self, result_item):

        # assign education function weightage if educational institution
        search_function_weightage = 0

        if self.search_function == 'education':

            search_function_weightage = self.assign_edu_function_weightage(result_item)

        result_item['weightage']['function_weightage'] += search_function_weightage if search_function_weightage else 0

    def filter_values_not_present(self, result_item):

        for filter_field in self.filters:

            if filter_field in result_item:

                print("Checking " + filter_field + " in " + result_item[filter_field])

                if self.filters[filter_field].lower() not in result_item[filter_field].lower():

                    print(self.filters[filter_field].lower() + " not found in ")
                    print(word_tokenize(result_item[filter_field].lower()))

                    # print(word_tokenize(result_item[filter_field].lower()))
                    # print('Deleting element ' + result_item['first_name'] + ' ' + result_item['last_name'] + ' (' + self.filters[filter_field] + ')' + ' not found in ' + result_item['location'])
                    # del results[result_item_index]

                    return True

                else:

                    print(self.filters[filter_field].lower() + " found in ")
                    print(word_tokenize(result_item[filter_field].lower()))

        return False

    # def filter_

    def sort_results(self, results, sort_by='SCORE'):

        # print(json.dumps(results, sort_keys=False, indent=4))

        if sort_by == 'SCORE':  # sort by total score/weigtage

            results.sort(key=lambda result_item: result_item['weightage']['total'], reverse=True)

    def expand_multivalued_fields(self, multi_val_field, expanded_field, result_item):

        if multi_val_field in result_item:
            # print(multi_val_field)
            # print(result_item[multi_val_field])

            counter = 1

            for json_obj in json.loads(result_item[multi_val_field]):
                result_item[expanded_field + str(counter)] = json_obj[expanded_field]
                counter += 1
                # print(json_obj[expanded_field])

            # counter = 1
            #
            # for field_key, field_val in :
            #
            #     result_item[field_key + str(counter)] = field_val
            #     counter += 1
            #
            # print("result item after " + multi_val_field + " expansion")
            # print(result_item)

        #
        # job_experience_information = {}
        #
        # try:
        #
        #     for decoded_information in json.loads(result_item[multi_val_field]):
        #
        #         print(decoded_information)
        #
        #         # for field_key, field_value in decoded_information.items():
        #
        #         counter += 1
        #
        # except:
        #
        #     print("Invalid json")
        #     print((result_item[multi_val_field]))

    # def set_custom_filter_weights (self, filter_weights):
    #
    #     total_user_controlled_weight = 25
    #
    #     if filter_weights:
    #
    #         if 'job_title' in filter_weights:
    #
    #             self.user_defined_weightage['job_title'] += (filter_weights['job_title'] / 100) * total_user_controlled_weight
    #
    #     return filter_weights

    def add_custom_filter_weights (self, result_item):

        total_user_controlled_weight = 25

        # print("........... FILTERS ...........")
        # print(self.filters)

        # print("........... FILTER WEIGHTS ...........")
        # print(self.filter_weights)

        applied_weights = {}

        if self.filter_weights:

            if 'job_title' in self.filter_weights:

                # applied_weights['job_title'] = 0

                for org_count in range(1, 5):

                    if f"organization_title_{org_count}" in result_item and result_item[f"organization_title_{org_count}"] is not None:

                        print("RESULT ORG " + str(f'RESULT ITEM {result_item[f"organization_title_{org_count}"]}'))

                    if 'job_title' in self.filters and f'organization_title_{org_count}' in result_item and result_item[f'organization_title_{org_count}'] is not None and self.filters['job_title'].lower() in str(result_item[f'organization_title_{org_count}'].lower()):

                        # applied_weights['job_title'] = ((self.filter_weights['job_title'] if org_count == 1 else self.filter_weights['job_title'] - 2) / 100) * total_user_controlled_weight
                        # applied_weights['job_title'] = ((self.filter_weights['job_title'] if org_count == 1 else self.filter_weights['job_title'] - 2) / 100) * self.default_weightage['job_title']
                        applied_weights['job_title'] = self.filter_weights['job_title'] if org_count == 1 else self.filter_weights['job_title'] - 2
                        break

                    #print(f"JOB TITLE FILTER WEIGHTAGE {result_item['weightage']['filters_weightage']}")

            if 'organization_name' in self.filter_weights:

                # filter_count = len([comp_filter for comp_filter in ['organization_name', 'industry', 'sub_industry', 'number_of_employees'] if comp_filter in self.filters])
                #
                # company_field_filter_weight = ((self.filter_weights['company'] / 100) * total_user_controlled_weight) / (filter_count or 1)

                print(result_item['full_name'])

                company_field_filter_weight = self.filter_weights['organization_name']

                for org_count in range(1, 5):

                    if f"organization_{org_count}" in result_item and result_item[f"organization_{org_count}"] is not None:

                        print("RESULT ORG " + str(f'RESULT ITEM {result_item[f"organization_{org_count}"]}'))

                    if 'organization_name' in self.filters and f'organization_{org_count}' in result_item and result_item[f'organization_{org_count}'] is not None and self.filters['organization_name'].lower() in str(result_item[f'organization_{org_count}'].lower()):

                        applied_weights['organization_name'] = company_field_filter_weight if org_count == 1 else company_field_filter_weight - 2
                        #print (f"COMPANY FILTER WEIGHTAGE {applied_weights['organization_name']}")
                        break


            if 'industry' in self.filter_weights:

                industry_field_filter_weight = 10

                applied_weights['organization_name'] = self.filter_weights['industry']

            if 'school_name' in self.filter_weights:

                # applied_weights['education'] = 0

                # filter_count = len([comp_filter for comp_filter in ['school_name', 'degree'] if comp_filter in self.filters])
                #
                education_field_filter_weight = self.filter_weights['school_name']

                print(result_item['full_name'])

                for org_count in range(1, 5):

                    if f"school_{org_count}" in result_item and result_item[f"school_{org_count}"] is not None:
                        print("RESULT ORG " + str(f'RESULT ITEM {result_item[f"school_{org_count}"]}'))

                    if 'school_name' in self.filters and f'school_{org_count}' in result_item and result_item[f'school_{org_count}'] is not None and self.filters['school_name'].lower() in str(result_item[f'school_{org_count}'].lower()):

                        applied_weights['school_name'] = education_field_filter_weight if org_count == 1 else education_field_filter_weight - 2
                        break

                    if 'degree' in self.filters and f'degree_{org_count}' in result_item and result_item[f'degree_{org_count}'] is not None and self.filters['degree'].lower() in str(result_item[f'degree_{org_count}'].lower()):

                        applied_weights['degree'] = education_field_filter_weight if org_count == 1 else education_field_filter_weight - 2
                        break

                        print(f"EDUCATION FILTER WEIGHTAGE {applied_weights['degree']}")

            # code comment start

            # if 'city' in self.filter_weights:
            #
            #     if 'city' in self.filters and 'city' in result_item and result_item['city'] is not None and self.filters['city'].lower() in str(result_item['city'].lower()):
            #
            #         applied_weights['city'] = self.filter_weights['city']
            #
            #         print(f"CITY FILTER WEIGHTAGE {applied_weights['country']}")
            #
            # if 'country' in self.filter_weights:
            #
            #     if 'country' in self.filters and 'country' in result_item and result_item['country'] is not None and self.filters['country'].lower() in str(result_item['country'].lower()):
            #
            #         applied_weights['country'] = self.filter_weights['country']
            #
            #         print(f"COUNTRY FILTER WEIGHTAGE {applied_weights['country']}")
            #
            # if 'area' in self.filter_weights:
            #
            #     if 'area' in self.filters and 'area' in result_item and result_item['area'] is not None and self.filters['area'].lower() in str(result_item['area'].lower()):
            #
            #         applied_weights['area'] = self.filter_weights['area']
            #
            #         print(f"AREA FILTER WEIGHTAGE {applied_weights['area']}")

            # code comment end

            if 'city' in self.filter_weights or 'country' in self.filter_weights or 'area' in self.filter_weights:

                for org_count in range(1, 5):

                    # if f"school_{org_count}" in result_item and result_item[f"school_{org_count}"] is not None:
                    #     print("RESULT ORG " + str(f'RESULT ITEM {result_item[f"school_{org_count}"]}'))

                    if 'city' in self.filters and f'organization_city_{org_count}' in result_item and result_item[f'organization_city_{org_count}'] is not None and self.filters['city'].lower() in str(result_item[f'organization_city_{org_count}'].lower()):

                        applied_weights['city'] = self.filter_weights['city'] if org_count == 1 else self.filter_weights['city'] - 2
                        break

                    if 'country' in self.filters and f'organization_country_{org_count}' in result_item and result_item[f'organization_country_{org_count}'] is not None and self.filters['country'].lower() in str(result_item[f'organization_country_{org_count}'].lower()):

                        applied_weights['country'] = self.filter_weights['country'] if org_count == 1 else self.filter_weights['country'] - 2
                        break

                    if 'area' in self.filters and f'organization_area_{org_count}' in result_item and result_item[f'organization_area_{org_count}'] is not None and self.filters['area'].lower() in str(result_item[f'organization_area_{org_count}'].lower()):

                        applied_weights['area'] = self.filter_weights['area'] if org_count == 1 else self.filter_weights['area'] - 2
                        break


            # code comment end


            for filter_key in applied_weights:

                result_item['weightage']['filters_weightage'] += applied_weights[filter_key]


    def get_first_degree_connections(self):

        # first_degree_connections = User.objects.get(id=self.user_id).contacts.values_list('id', flat=True)
        first_degree_connections = ContactDegree.objects.filter(user_id=self.user_id).values_list('contact_degree_id', flat=True)

        if bool(first_degree_connections):

            return first_degree_connections

        return []

    def is_first_degree_connection (self, contact_id):

        if self.first_degree_connections and self.first_degree_connections.filter(contact_degree_id=contact_id).exists() > 0:

            return True

        return False

    def get_second_degree_connections (self, contact_id):

        for first_degree_connection in self.first_degree_connections:
            first_degree_contact_id = first_degree_connection.contact_degree_id

            first_degree_connections = ContactDegree.objects.filter(user_id=self.user_id).values_list('contact_degree_id', flat=True)


        return []

    def is_second_degree_connection (self, contact_id):

        if not self.second_degree_connections_queried:

            self.second_degree_connections_queried = True
            self.second_degree_connections =  self.get_second_degree_connections(contact_id) # self.second_degree_connections =

        if self.second_degree_connections:

            pass

        # if self.first_degree_connections and self.second_degree_connections:

        return False

    def get_third_degree_connections (self, contact_id):

        return []

    def is_third_degree_connection (self, contact_id):

        if not self.third_degree_connections_queried:

            self.third_degree_connections_queried = True

        return []




