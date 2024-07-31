import requests
import json

import re
import inflect
import os

from datetime import datetime

from django.http import HttpResponse
from django.contrib.auth.models import User
from spellchecker import SpellChecker
from nltk import word_tokenize
from altworkz.settings import  ES_SEARCH_URL

from contacts_import.models import UserFeedback, ContactDegree
from spellchecker import SpellChecker
from .search import Search
from .utilities import *
from .location import Location

# ================================== #
#         ELASTIC SEARCH             #
# ================================== #
from accounts.models import Profile

''' BEGIN ELASTIC SEARCH CLASS '''


class ElasticSearch(Search):
    print("INSIDE ELASTIC SEARCH CLASS")
    def __init__(self, user_id=''):

        super().__init__() 

        self.user_id = user_id
        user_profile = Profile.objects.filter(user_id=self.user_id)
        if not list(user_profile):
            self.contact_id = 0
        else:
            self.contact_id = user_profile[0].contact_id

        self.request_url = ES_SEARCH_URL
        
        self.elastic_query = ''
        
        self.applied_elastic_filters = {
            'job_profile': False,
            'edu_profile': False
        }

    # passes request to ElasticSearch instance

    def get_contacts_by_id (self, contact_id_list):

        elastic_query_data = {
            "size":"2000",
            "query": {
                "bool": {
                    "must": [
                        {
                            "terms": {
                                "contact_id": contact_id_list
                            }
                        }
                    ]
                }
            },
            "_source": ["full_name", "photo", "job_title", "organization_name", "contact_id"],
        }

        es_response = requests.get(self.request_url,
                                   headers={'Content-Type': 'application/json'},
                                   data=json.dumps(elastic_query_data))

        return json.loads(es_response.text)
                
    def build_filtered_elastic_query(self, elastic_result_from):
    
        nested_filters = {
            'job': {
                'added': False,
                'index': 0,
                'filter_key_replacements': {
                    'organization_name': 'job_profile.organization_',
                    'job_title': 'job_profile.organization_title_'
                }
            },
            'edu': {
                'added': False,
                'index': 0,
                'filter_key_replacements': {
                    'school_name': 'edu_profile.school_',
                    'degree': 'edu_profile.degree_'                    
                }            
            }
        }    
     
        add_multi_field_filter = lambda multi_field_filter_name : {"nested":{"path":multi_field_filter_name,"score_mode":"max","query":{"bool":{"must":[]}}}}
        add_nested_filter = lambda key, val : {"match_phrase":{key:val}}
  
        def add_nested_filter_query (nested_filter_path, filter_type, filter_key, filter_val="val"):
            
            if not nested_filters[filter_type]['added']:
            
                self.elastic_query['query']['bool']['must'].append(add_multi_field_filter(nested_filter_path))
                nested_filters[filter_type]['added'] = True
                nested_filters[filter_type]['index'] = len(self.elastic_query['query']['bool']['must']) - 1               
                self.applied_elastic_filters[filter_type] = True 
            
            self.elastic_query['query']['bool']['must'][nested_filters[filter_type]['index']]['nested']['query']['bool']['must'].append(add_nested_filter(filter_key, filter_val))
          
        for elastic_filter in self.filters:
        
            if elastic_filter in ['organization_name', 'job_title']:
            
                add_nested_filter_query('job_profile', 'job', nested_filters['job']['filter_key_replacements'][elastic_filter], self.filters[elastic_filter])
        
            elif elastic_filter in ['school_name', 'degree']:

                add_nested_filter_query('edu_profile', 'edu', nested_filters['edu']['filter_key_replacements'][elastic_filter], self.filters[elastic_filter])    
                
        #print(f"Filtered Elastic Generated Query ", self.elastic_query)    
    
        return self.elastic_query
        
    def has_multi_field_weighted_filters(self):
    
        elastic_filters_list = []
        
        for filter in self.filters:
        
            if filter == 'organization_name' and (not self.filter_weights or (self.filter_weights and 'organization_name' not in self.filter_weights)):
            
                elastic_filters_list.append({'organization_': self.filters['organization_name']})
                        
                return True
                
            elif filter == 'job_title' and (not self.filter_weights or (self.filter_weights and 'job_title' not in self.filter_weights)):
            
                elastic_filters_list.append({'organization_title_': self.filters['job_title']})
                        
                return True                
            
            elif filter == 'school_name' and (not self.filter_weights or (self.filter_weights and 'school_name' not in self.filter_weights)):
            
                elastic_filters_list.append({'school_': self.filters['school_name']})
                        
                return True
                
            elif filter == 'degree' and (not self.filter_weights or (self.filter_weights and 'degree' not in self.filter_weights)):
            
                elastic_filters_list.append({'degree_': self.filters['degree']})
                        
                return True                
    
        return False
    
    def build_elastic_query_data(self):
         
        elastic_result_size = 20            
        elastic_result_from = (int(self.page_num) - 1) * elastic_result_size
        
        self.elastic_query  = {
            "from":elastic_result_from,
            "size":"20",
            "query": {
                "bool": {
                    "must": [{'multi_match': {'query': self.user_query}}],
                    "must_not": [{"term": {"contact_id": self.contact_id}}],
                }
            },
            "_source": True,
            "highlight": {
                "fields": {
                    "*": {}
                }
            }
        } 
                        
        if self.filters and self.has_multi_field_weighted_filters():
        
            self.elastic_query = self.build_filtered_elastic_query(elastic_result_from)
            
        if self.filters and 'member_of_platform' in self.filters:

            if self.applied_elastic_filters['job_profile'] == True:  

                if len(self.elastic_query['query']['bool']['must']) > 0:
                    
                    app_filter_count = 0
                    
                    for app_filter in self.elastic_query['query']['bool']['must']:
                    
                        if 'nested' in app_filter and 'job_profile' in app_filter['nested']:
                        
                            self.elastic_query['query']['bool']['must'][app_filter_count]['nested']['query']['bool']['must'].append({"match": {"job_profile.job_platform_": self.filters['member_of_platform']}})
                        
                        app_filter_count += 1        
                        
            else:

                self.elastic_query['query']['bool']['must'].append({"nested": {"path": "job_profile","score_mode": "max","query": {"bool": {"must": [{"match": {"job_profile.job_platform_": self.filters['member_of_platform']}}]}}}})
                                    
        return json.dumps(self.elastic_query)
        
    # assigns weightage and sorts results
    def fetch_filter_suggestions(self, user_query, filters):
    
        self.user_query = user_query
        self.filters = self.re_evaluate_filters_values(filters)

        es_response = requests.get(self.request_url, headers={'Content-Type': 'application/json'},data=self.build_elastic_suggestions_query())
                                   
        #print("Elastic Suggestions Response ", es_response)
                                   
        return json.loads(es_response.text)
        
    def build_elastic_suggestions_query(self):
                 
        self.elastic_query  = {
            "from":0,
            "size":10000,
            "query": {
                "bool": {
                    "must": [{'multi_match': {'query': self.user_query}}],
                    "must_not": [{"term": {"contact_id": self.contact_id}}],
                }
            },
            "_source": [
                "job_profile.organization_", "job_profile.organization_title_", 
                "job_profile.organization_city_",  "job_profile.organization_area_",  "job_profile.organization_country_",                   
                "edu_profile.school_", "edu_profile.degree_"
            ]
        }        
        
        if self.filters and self.has_multi_field_weighted_filters():
        
            self.elastic_query = self.build_filtered_elastic_query(0)
            
        print("Query generated query ")
        print(self.elastic_query)
                        
        return json.dumps(self.elastic_query)



    def rank_by_weightage(self, result_list, get_original_results=False):

        django_http_resp = {}

        if get_original_results:
            django_http_resp['original_order'] = result_list.copy()

            location_score = 0

            return HttpResponse('')

        result_list.sort(key=lambda result_item: result_item['_score'], reverse=True)

        django_http_resp['modified_order'] = result_list

        return django_http_resp

    def get_elastic_results(self):
        
        #print("Build elastic query ", self.build_elastic_query_data())
        es_response = requests.get(self.request_url,
                                   headers={'Content-Type': 'application/json'},
                                   data=self.build_elastic_query_data())
        print('es_response.text')
        return json.loads(es_response.text)

    # takes
    def query(self, query, search_function='default', filters=None, filter_weights=None, page_num=1, additional_pass_by_ref_params={}):

        os.system('cls')  # clear screen to refresh console messages

        self.user_query = query
        self.search_function = search_function
        self.filters = self.re_evaluate_filters_values(filters)
        # self.filter_weights = self.set_custom_filter_weights(filter_weights) # used for customizing user controlled weights WITHOUT filter values
        self.filter_weights = filter_weights
        self.page_num = int(page_num)

        results = self.get_elastic_results()
        additional_pass_by_ref_params['total_results'] = results['hits']['total']['value']
        
        extracted_terms = self.preproces_query()
        self.first_degree_connections = self.get_first_degree_connections()
        scored_results = self.filter_results_and_assign_weightage(extracted_terms, results)
        self.sort_results(scored_results)

        return scored_results

    def query_compare_results(self, query):

        request_url = ES_SEARCH_URL

        self.query_str = query
        result_list = self.get_elastic_results()
        resp = self.rank_by_weightage(result_list, True)

        return resp

    ###############################################################################################

    def filter_result(self, result_item):

        print("Filters")
        print(self.filters)

        def correct_spelling (filter_string):

            spell = SpellChecker()
            misspelled = spell.unknown(filter_value.split())

            for word in misspelled:

                corrected_word = spell.correction(word)
                filter_string = filter_string.lower().replace(word.lower(), corrected_word.lower())

            return filter_string

        for filter_key, filter_value in self.filters.items():

            print("Checking key " + filter_key + " " + result_item['first_name'] + " " + result_item['last_name'])

            result_key_existence = False
            filter_key_ = filter_key
            # temp code start: to be refactored later

                    # return True

            if filter_key in ['school_name', 'organization_name', 'job_title', 'degree']:

                if filter_key == 'job_title':
                    filter_value = correct_spelling(filter_value)

                    for itr in range(4):
                        result_item_key = 'organization_title_'+str(itr)
                        if result_item_key in result_item and result_item[result_item_key] is not None:
                            filter_key_ = 'organization_title_'+str(itr)
                            result_key_existence = True
                            break

                if filter_key == 'organization_name':
                    for itr in range(4):
                        result_item_key = 'organization_'+str(itr)
                        if result_item_key in result_item and result_item[result_item_key] is not None:
                            filter_key_ = 'organization_'+str(itr)
                            result_key_existence = True
                            break

                if filter_key == 'school_name':
                    for itr in range(4):
                        result_item_key = 'school_'+str(itr)
                        if result_item_key in result_item and result_item[result_item_key] is not None:
                            filter_key_ = 'school_'+str(itr)
                            # print('school ' + result_item[result_item_key] + " : " + result_item_key)
                            result_key_existence = True
                            break

            else:

                result_key_existence = True

            # temp code end

            if filter_key_ in result_item and result_item[filter_key_] is not None and result_key_existence:

                print("OK if")

                filter_value = filter_value.strip().lower()
                current_result_item_value = result_item[filter_key_].strip().lower()

                if filter_key in ['job_title', 'organization_name']:

                    counter = 1

                    while 'organization_' + str(counter) in result_item and result_item['organization_' + str(counter)] is not None:

                        if 'job_title' in self.filters and 'organization_name' in self.filters:

                            filter_job_title = self.filters['job_title'].strip().lower()
                            filter_org = self.filters['organization_name'].strip().lower()

                            if result_item['organization_title_'+str(counter)] is not None and result_item['organization_title_'+str(counter)] is not None:

                                org_job_title = result_item['organization_title_'+str(counter)].strip().lower()
                                org_name = result_item['organization_'+str(counter)].strip().lower()

                                if filter_org in org_name and filter_job_title in org_job_title:

                                    return True

                        else:

                            if filter_key == 'job_title':

                                current_result_item_value = result_item['organization_title_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    return True

                            if filter_key == 'organization_name':

                                current_result_item_value = result_item['organization_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    return True

                        counter += 1

                    return False

                elif filter_key in ['degree', 'school_name']:

                    print("OK elif")

                    counter = 1

                    while 'school_' + str(counter) in result_item and result_item['school_' + str(counter)] is not None:

                        if 'degree' in self.filters and 'school_name' in self.filters:

                            filter_degree = self.filters['degree'].strip().lower()
                            filter_school = self.filters['school_name'].strip().lower()

                            if 'degree' in result_item['degree'+str(counter)]:

                                degree_title = result_item['degree'+str(counter)].strip().lower()

                                school_name = result_item['school_'+str(counter)].strip().lower()

                                if (filter_school in school_name) and (filter_degree in degree_title):

                                    return True
                            else:

                                return False

                        else:

                            if filter_key == 'degree':

                                current_result_item_value = result_item['degree_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:
 
                                    return True
                        
                            if filter_key == 'school_name':

                                current_result_item_value = result_item['school_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    return True

                        counter += 1

                    return False

                else:

                    if filter_key in ['industry', 'sub_industry']:

                        filter_value = correct_spelling(filter_value)

                    if filter_value != current_result_item_value and filter_value not in current_result_item_value:

                        return False

            else:

                if filter_key in ['search_feedback']:

                    if int(self.filters['search_feedback']) > 0:

                        for feedback in self.user_feedback:

                            if result_item['contact_id'] == feedback['contact']:

                                if str(feedback['feedback']) == self.filters['search_feedback']:

                                    return True

                                else:

                                    return False

                    else:

                        for feedback in self.user_feedback:

                            if str(result_item['contact_id']) == str(feedback['contact']):

                                return False

                        return True

                return False

        return True

    def tag_filter (self, result_item, filter_name):

        if filter_name:

            tag_lookup = {
                'tag': 'ctags',
                'file_tag': 'csv_tags'
            }

            if filter_name in tag_lookup:

                if tag_lookup[filter_name] in result_item:

                    if tag_lookup[filter_name] and result_item[tag_lookup[filter_name]] is not None:

                        if filter_name == 'file_tag' and ',' in self.filters[filter_name]:

                            csv_filters = self.filters[filter_name].split(',')

                            for cf in csv_filters:

                                if cf.lower() in result_item[tag_lookup[filter_name]].lower():

                                    return True

                        else:

                            if self.filters[filter_name].lower() in result_item[tag_lookup[filter_name]].lower():

                                return True

        return False


    def has_result_item_org_type_filter (self, result_item):

        if 'org_job_to_from_count' in result_item:

            itr = 1

            while itr <= result_item['org_job_to_from_count']:

                if 'organization_type_'+str(itr) in result_item and result_item['organization_type_'+str(itr)]:

                    if self.filters['organization_type'] and result_item['organization_type_'+str(itr)] and self.filters['organization_type'].strip().lower() in result_item['organization_type_'+str(itr)].lower():

                        return True

                itr += 1

        return False

    def member_of_platform_filter (self, result_item):
    
        if self.filters['member_of_platform'].lower() in ['sec', 'bloomberg', 'yahoo', 'twitter']:
        
            print("MEMBER OF PLATFORM SEC ")
        
            return True

        if 'edu_to_from_count' in result_item:

            itr_count = 1

            while itr_count <= result_item['edu_to_from_count']:
            
                if 'scool_profile_link_' + str(itr_count) in result_item and result_item['scool_profile_link_' + str(itr_count)] is not None and result_item['scool_profile_link_' + str(itr_count)].strip():

                    if self.filters['member_of_platform'].lower() + '.' in result_item['scool_profile_link_' + str(itr_count)].strip().lower():

                        return True

                itr_count += 1

        if 'org_job_to_from_count' in result_item:

            itr_count = 1

            while itr_count <= result_item['org_job_to_from_count']:

                if 'job_profile_link_' + str(itr_count) in result_item and result_item['job_profile_link_' + str(itr_count)] is not None and result_item['job_profile_link_' + str(itr_count)].strip():
                        
                    if self.filters['member_of_platform'].lower() + '.'  in result_item['job_profile_link_' + str(itr_count)].strip().lower():

                        #print("Person for link found ..... " + result_item['full_name'])
                        #print(result_item['job_profile_link_' + str(itr_count)])

                        return True

                itr_count += 1

        if 'social_contact_description_count' in result_item:

            itr_count = 1

            while itr_count <= result_item['social_contact_description_count']:

                # if 'social_profile_link_' + str(itr_count) in result_item and result_item['social_profile_link_' + str(itr_count)] is not None and result_item['social_profile_link_' + str(itr_count)].strip():
                if 'des_profile_link_' + str(itr_count) in result_item and result_item['des_profile_link_' + str(itr_count)] is not None and result_item['des_profile_link_' + str(itr_count)].strip():

                    if self.filters['member_of_platform'].lower() + '.' in result_item['des_profile_link_' + str(itr_count)].strip().lower():

                        print("Person for link found ..... " + result_item['full_name'])
                        print(result_item['des_profile_link_' + str(itr_count)])
                        
                        return True
                            
                                        
                itr_count += 1


        return False

    def filter_results_and_assign_weightage (self, query_word_list, results):

        field_weightages = self.weightage_type.get(self.search_function, self.default_weightage)
        filtered_and_weighted_list = []

        for result_item_index, result_item in enumerate(results['hits']['hits']):

            elastic_score = result_item['_score']
            highlights = result_item['highlight'] if 'highlight' in result_item else []
            result_item = result_item['_source']
            self.expand_experience_fields(result_item)
            self.expand_education_fields(result_item)
            self.expand_contact_description(result_item)
            # self.expand_multivalued_fields('edu_to_from', result_item)
            self.expand_multivalued_fields('contact_numbers', 'contact_no_', result_item)
            self.expand_multivalued_fields('contact_emails', 'contact_email_',  result_item)

            result_item['weightage'] = {}
            result_item['weightage']['occurance_weightage'] = 0
            result_item['weightage']['alias_weightage'] = 0
            result_item['weightage']['field_weightage'] = 0
            result_item['weightage']['rel_weightage'] = 0
            result_item['weightage']['experience_weightage'] = 0
            result_item['weightage']['first_degree_weightage'] = 0
            result_item['weightage']['warmth_of_relationship_weightage'] = 0
            result_item['weightage']['function_weightage'] = 0
            result_item['weightage']['filters_weightage'] = 0
            result_item['weightage']['elastic_weightage'] = elastic_score
            result_item['weightage']['total'] = elastic_score
            result_item['occurance_fields'] = []
            result_item['confidence_score'] = {'filters_matched': 0, 'total_filters_applied': 0, 'search_terms_matched': 0, 'matched_keywords': [], 'total_search_terms': len(query_word_list), 'calculated_score': 0}
            result_item['weightage']['neg_weightage'] = 0
            result_item['common_institutions'] = {'education': [], 'organization': []} # for warmth of relationship
            result_item['common_features'] = {'education': [], 'organization': []} # for displaying intersecting elements

            result_item['twitter_profile'] = ''

            # FILTERS START #
            
            if self.filters:
            
                result_item['confidence_score']['total_filters_applied'] = len(self.filters)

                # ************************** TEMP code comment start ************************** #

                # if not self.filter_weights:

                # if not self.filter_result(result_item):

                # print("Skipping " + str(result_item['first_name']) + ' ' + str(result_item['last_name']))

                # continue

                # else:

                # **************************  TEMP code comment end  ************************** #


                # ************************** TEMP tag filter ************************** #

                if 'organization_type' in self.filters and not self.has_result_item_org_type_filter(result_item):

                    continue

                if 'tag' in self.filters and not self.tag_filter(result_item, 'tag'):

                    print(f"Skipping {str(result_item['first_name'])}  {str(result_item['last_name'])} for not having required tag")

                    continue

                if 'file_tag' in self.filters and not self.tag_filter(result_item, 'file_tag'):

                    print(f"Skipping {str(result_item['first_name'])}  {str(result_item['last_name'])} for not having required tag")

                    continue

                if 'member_of_platform' in self.filters and not self.member_of_platform_filter(result_item):

                    # print(f"Member of platform....")

                    continue

                if 'degree_of_connection' in self.filters:

                    if self.filters['degree_of_connection'] == '1st':

                        if not self.is_first_degree_connection(result_item['contact_id']):
                            # print(result_item['full_name'])
                            # print("...... 1st degree filter ......")
                            # print(self.is_first_degree_connection(result_item['contact_id']))
                            continue

                    elif self.filters['degree_of_connection'] == '2nd':

                        # print(" .................... CHECKING 2ND DEGREE CONNECTION .................... ")

                        # temporary adjustment to be changed once suitable
                        first_degree_connections = ContactDegree.objects.filter(user_id=self.user_id)
                        # print(first_degree_connections)
                        second_degree_not_found = True

                        for first_degree_connection in first_degree_connections:

                            first_degree_contact_id = first_degree_connection.contact_degree_id
                            check_second_degree_connections = ContactDegree.objects.filter(user_contact_id=first_degree_contact_id)
                            # print(" 2nd DEGREE CONNECTION ")
                            # print(check_second_degree_connections)

                            if int(first_degree_contact_id) == result_item['contact_id']:
                                # print("  ............. FOUND 1ST DEGREE CONNECTION IN 2ND ............. \n")
                                # print(result_item['full_name'])
                                # print(bool(second_degree_not_found))
                                second_degree_not_found = True
                                break

                            for second_degree_connection in check_second_degree_connections:

                                contact_degree_ids = second_degree_connection.contact_degree_id

                                if int(contact_degree_ids) == result_item['contact_id']:
                                    # print(contact_degree_ids)
                                    # print(" found for 2nd degree connection ")
                                    second_degree_not_found = False
                                    break

                        if second_degree_not_found:
                            # print("  ............. SKIPPING RESULTS ............. \n")
                            # print(result_item['full_name'])

                            # print(" first degree connection \n")

                            continue

                    elif self.filters['degree_of_connection'] == '3rd':

                        first_degree_connections = ContactDegree.objects.filter(user_id=self.user_id)
                        # print(first_degree_connections)
                        third_degree_not_found = True
                        first_degree_connection = False
                        second_degree_connection = False
                        third_degree_connection = False

                        for first_degree_connection in first_degree_connections:

                            first_degree_contact_id = first_degree_connection.contact_degree_id
                            check_second_degree_connections = ContactDegree.objects.filter(user_contact_id=first_degree_contact_id)
                            # print(" 2nd DEGREE CONNECTION ")
                            # print(check_second_degree_connections)

                            if int(first_degree_contact_id) == result_item['contact_id']:
                                # print(contact_degree_ids)
                                # print(" found for 2nd degree connection ")
                                first_degree_connection = True
                                break

                            for second_degree_connection in check_second_degree_connections:

                                contact_degree_ids = second_degree_connection.contact_degree_id
                                third_degree_connections = ContactDegree.objects.filter(user_contact_id=contact_degree_ids)

                                if int(contact_degree_ids) == result_item['contact_id']:
                                    # print(contact_degree_ids)
                                    # print(" found for 2nd degree connection ")
                                    second_degree_connection = True
                                    break

                                for third_degree_connection in third_degree_connections:

                                    contact_degree_ids = third_degree_connection.contact_degree_id

                                    if int(contact_degree_ids) == result_item['contact_id']:
                                        # print(contact_degree_ids)
                                        # print(" found for 2nd degree connection ")
                                        second_degree_connection = True
                                        third_degree_not_found = False
                                        break
                                        
                            if second_degree_connection:
                                
                                break

                        if third_degree_not_found:

                            continue

                    elif self.filters['degree_of_connection'] == '3rd+':

                        first_degree_connections = ContactDegree.objects.filter(user_id=self.user_id)
                        # print(first_degree_connections)
                        is_first_degree_connection = False
                        is_second_degree_connection = False
                        is_third_degree_connection = False

                        first_to_third_degree_connection_found = False

                        for first_degree_connection in first_degree_connections:

                            first_degree_contact_id = first_degree_connection.contact_degree_id

                            if int(first_degree_contact_id) == result_item['contact_id']:
                                # print("  ............. FOUND 1ST DEGREE CONNECTION ............. \n");
                                is_first_degree_connection = True
                                first_to_third_degree_connection_found = True
                                break

                            check_second_degree_connections = ContactDegree.objects.filter(user_contact_id=first_degree_contact_id)

                            # print(" 2nd DEGREE CONNECTION ")
                            # print(ContactDegree.objects.filter(user_contact_id=first_degree_contact_id).query)

                            for second_degree_connection in check_second_degree_connections:
                                # print("  ............. FOUND 2ND DEGREE CONNECTION ............. \n")
                                    
                                contact_degree_ids = second_degree_connection.contact_degree_id

                                if int(contact_degree_ids) == result_item['contact_id']:
                                    is_second_degree_connection = True
                                    first_to_third_degree_connection_found = True
                                    break
                                # else:                                  
                                #    print(result_item['full_name'])
                                #    print('contact_id ' + str(result_item['contact_id']))
                                #    print('contact_degree_id ' + str(contact_degree_ids))

                                third_degree_connections = ContactDegree.objects.filter(user_contact_id=contact_degree_ids)

                                for third_degree_connection in third_degree_connections:

                                    # print("  ............. FOUND 3RD DEGREE CONNECTION ............. \n");

                                    contact_degree_ids = third_degree_connection.contact_degree_id

                                    if int(contact_degree_ids) == result_item['contact_id']:
                                        is_third_degree_connection = True
                                        first_to_third_degree_connection_found = True
                                        break

                                if is_third_degree_connection:
                                    # print(" third_degree_connection \n")
                                    # print(result_item['full_name'])
                                    break

                            if is_second_degree_connection or is_third_degree_connection:
                                # print(" second_degree_connection or third_degree_connection \n")
                                # print(result_item['full_name'])
                                break

                        if first_to_third_degree_connection_found:
                            # print("BROKEN AT \n")
                            # print(result_item['full_name'])
                            continue

                    # print(f"Member of platform....")

                    # continue

                # ************************** TEMP tag filter ************************** #

                self.add_custom_filter_weights(result_item)
                    # print("------ AFTER SETTING WEIGHT WEIGHTS ------ ")
                    # print(result_item['weightage']['filters_weightage'])



            # FILTERS END #

            for ri_field, ri_value in result_item.items():

                # evaluate only fields with weightage for now
                if (ri_field in field_weightages or re.search('^' + self.fields['organization_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_title_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['school_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['education_degree_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_city_n'] + '[0-9]$', ri_field) or re.search('^' + self.fields['organization_country_n'] + '[0-9]$', ri_field)) and (ri_value is not None and type(ri_value) is str):

                    ri_value = to_lower_and_split_if_name_field(ri_field, ri_value, self.fields)
                    self.search_query_terms_in_field_values_and_assign_weightage(query_word_list, ri_field, ri_value, result_item, field_weightages)
                    # warmth of relationship weightage

                    # if 'warmth_of_relationship' in self.filters:

                        # pass                        # print(self.filters['warmth_of_relationship'])

                    self.search_common_attrs_and_assign_weightage(ri_field, ri_value, result_item, field_weightages)
                    # if 'warmth_of_relationsihp' in self.filters and self.filters['warmth_of_relationship'].lower() == 'on': # temporary check to demonstrate warmth of relationship
                    #

                # neglected fields area
                else:

                    pass

            result_item['weightage']['total'] += result_item['weightage'].get('field_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('rel_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('alias_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('experience_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('filters_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('warmth_of_relationship_weightage', 0)

            # print(result_item['full_name'])
            # print(result_item['weightage'])

            if result_item['weightage']['total'] > 0 and self.is_first_degree_connection(result_item['contact_id']):
                result_item['weightage']['first_degree_weightage'] = self.default_weightage['1st_degree_connection']
                print("Adding 1st degree weightage for .................." + result_item['full_name'])

            result_item['weightage']['total'] += result_item['weightage'].get('first_degree_weightage', 0)
                # result_item['weightage']['total'] += self.default_weightage['first_degree_weightage']

            # print("Total weightage so far for " + result_item['full_name'] + " : " + str(result_item['weightage']['total']))

            result_item['weightage']['total'] += result_item['weightage'].get('neg_weightage', 0)

            result_item['highlights'] = highlights

            
            # print("Total weightage after adjustment " + result_item['full_name'] + " : " + str(result_item['weightage']['total']))
            #
            if result_item['weightage']['total'] > 0:
                
                filtered_and_weighted_list.append(result_item)

        print(" -------------------------------- TWITTER PROFILES -------------------------------- \n") 

        self.twitter_profiles = list(set(self.twitter_profiles))

        if len(self.twitter_profiles) > 0:
        
            print("Getting twitter profiles list ..... \n")
            
            # print(self.twitter_profiles)
            
            # twitter_url = 'https://api.twitter.com/2/tweets/search/recent?query=Pakistan (from:OfficialDGISPR OR from:GovtofPakistan) -is:retweet&expansions=author_id&user.fields=username&max_results=100'

            # twitter_url = 'https://api.twitter.com/2/tweets/search/recent?query=()
            # twitter_profiles_list = self.twitter_profiles.join(' OR ')
            
            twitter_profiles_list = ' OR '.join(self.twitter_profiles)
            
            # twitter_url = 'https://api.twitter.com/2/tweets/search/recent?query='+self.user_query+' ('+twitter_profiles_list+') -is:retweet&expansions=author_id&user.fields=username&max_results=10'
            twitter_url = 'https://api.twitter.com/2/tweets/search/recent?query='+self.user_query+' ('+twitter_profiles_list+') &expansions=author_id&user.fields=username&max_results=10'
             
            print(twitter_profiles_list)

            twitter_response = requests.request("GET", twitter_url, headers={"Authorization": "Bearer {}".format('AAAAAAAAAAAAAAAAAAAAAKVQOQEAAAAA3xwlreCOqXcQ8FG2Nd4F8tZX13U%3D0gfJiakJ8PmlILD1oF7bjwasSeB6kHIQ1tEOK3WhDMubwBPkOm')})
            
            # print(response.status_code)
            
            if twitter_response.status_code == 200: 
            
                twitter_users_dict = {}
                
                twitter_response = json.loads(twitter_response.text)
                
                print("twitter response ", twitter_response)
                
                if 'includes' in twitter_response:
            
                    for twitter_users in twitter_response['includes']:
                    
                        if 'users' in twitter_response['includes']:
                        
                            for twitter_user in twitter_response['includes']['users']:
                           
                                twitter_users_dict[twitter_user['username']] = twitter_user['id']
                    
                    # print('twitter users dict ', twitter_users_dict)
                    
                    for result_item_ in filtered_and_weighted_list:
                    
                        twitter_tweets = []
                        
                        for twitter_tweet in twitter_response['data']:
                                        
                            if result_item_['twitter_profile'] != '' and result_item_['twitter_profile'] in twitter_users_dict and twitter_users_dict[result_item_['twitter_profile']] == twitter_tweet['author_id']:
                            
                                # print('Appending tweet .....\n')
                                # print(twitter_tweet['text'])
                            
                                twitter_tweets.append({'id': twitter_tweet['id'], 'text': twitter_tweet['text']})
                        
                        result_item_['twitter_tweets'] = twitter_tweets
                #print(response.text)

            # twitter_url = 'https://api.twitter.com/2/tweets/search/recent?query=()

        return filtered_and_weighted_list


    def expand_experience_fields(self, result_item):

        counter = 1

        try:

            for job_experience in json.loads(result_item['org_job_to_from']):

                for experience_field, experience_value in job_experience.items():
                    result_item[experience_field + str(counter)] = experience_value

                counter += 1

            result_item['org_job_to_from_count'] = counter - 1

        except:

            if 'org_job_to_from' in result_item:
                print("Invalid json")
                print((result_item['org_job_to_from']))
            else:
                print('org_job_to_from does not exist')

    def expand_education_fields(self, result_item):

        counter = 1

        try:

            for education in json.loads(result_item['edu_to_from']):

                for edu_field, edu_value in education.items():
                    result_item[edu_field + str(counter)] = edu_value

                counter += 1

            result_item['edu_to_from_count'] = counter - 1

        except:

            if 'edu_to_from' in result_item:
                print("Invalid json")
                print((result_item['edu_to_from']))
            else:
                print('edu_to_from does not exist')

            # result_item['experience_fields'] = job_experience_information

    def expand_contact_description(self, result_item):

        if 'social_contact_description' in result_item:

            counter = 1

            try:

                for contact_description in json.loads(result_item['social_contact_description']):

                    for contact_des_field, contact_des_value in contact_description.items():
                        result_item[contact_des_field + str(counter)] = contact_des_value

                    counter += 1

                result_item['social_contact_description_count'] = counter - 1


            except:

                if 'social_contact_description' in result_item:
                    print("Invalid json")
                    print((result_item['social_contact_description']))
                else:
                    print('org_job_to_from does not exist')

    def re_evaluate_filters_values(self, filters):

        if filters and 'search_feedback' in filters:

            filters['search_feedback'] = {'liked': '1', 'disliked': '2', 'maybe': '3'}.get(filters['search_feedback'].lower(), '0')
            #
            if int(filters['search_feedback']) > 0:
            #
                #self.user_feedback = list(UserFeedback.objects.filter(feedback=filters['search_feedback']).filter(user=self.user_id).filter(feedback_search_term__search_term=self.user_query).values('contact', 'feedback'))
                self.user_feedback = list(UserFeedback.objects.filter(feedback=filters['search_feedback']).filter(user=self.user_id).filter(feedback_search_term__search_term=self.user_query).values('contact', 'feedback'))

            #
            #
            else:
            #
                print("............... FEEDBACK NOT PROVIDED ...............")
                self.user_feedback = list(UserFeedback.objects.filter(user=self.user_id).filter(feedback_search_term__search_term=self.user_query).values('contact', 'feedback'))
            #
            #
            #
            # print(self.user_feedback)

        return filters

        # print("------------------------------------------------------ Result Item ------------------------------------------------------")

        # print(result_item)

        # print("------------------------------------------------------ Result Item ------------------------------------------------------")



