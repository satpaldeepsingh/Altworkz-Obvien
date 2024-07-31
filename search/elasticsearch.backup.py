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
from altworkz.settings import ES_SEARCH_URL

from contacts_import.models import UserFeedback
from spellchecker import SpellChecker
from .search import Search
from .utilities import *
from .location import Location

# ================================== #
#         ELASTIC SEARCH             #
# ================================== #

''' BEGIN ELASTIC SEARCH CLASS '''


class ElasticSearch(Search):

    def __init__(self, user_id=''):

        super().__init__()

        self.user_id = user_id
        self.request_url = ES_SEARCH_URL

    # passes request to ElasticSearch instance

    def build_elastic_query_data(self):

        # if self.filters:
        #
        #     elastic_query_data = {
        #         "size":"200",
        #         "query": {
        #             "bool": {
        #                 "must": [{'multi_match': {'query': self.user_query}}] + [filter_key_value for filter_key_value in list(map(lambda filter: {'match': {filter[0]: filter[1]}}, self.filters.items()))]
        #             }
        #         },
        #         "_source": True,
        #         "highlight": {
        #             "fields": {
        #                 "*": {}
        #             }
        #         }
        #     }
        #
        # else:

            '''
             GET  /ml_test_2/_search
             {
               "query": {
                 "bool": {
                   "must": [{
                     "multi_match": {
                       "query": "frank"
                     }  
                   }],
                   "filter": [
                     {"term": { "user_id": 1 }}
                   ]
                 }
               }, 
               "_source": true, 
               "highlight": {
                 "fields": {
                   "*": {}
                 }
               }
             }                
             '''

            elastic_query_data = {
                #"size":"1000",
                # "size":"100",
                "size":"50",
                # "size":"5",
                "query": {
                    "bool": {
                        "must": [{'multi_match': {'query': self.user_query}}],
                        # "filter": [{"term": {"user_id": self.user_id}}]
                    }
                },
                "_source": True,
                "highlight": {
                    "fields": {
                        "*": {}
                    }
                }
            }

            # elastic_query_data = {
            #     "size": "200",
            #     "query": {
            #         "multi_match": {
            #             "query": self.user_query
            #         }
            #     },
            #     "_source": True,
            #     "highlight": {
            #         "fields": {
            #             "*": {}
            #         }
            #     }
            # }



            # print(self.request_url)
            # print(elastic_query_data)

            return json.dumps(elastic_query_data)

    # assigns weightage and sorts results



    def rank_by_weightage(self, result_list, get_original_results=False):

        django_http_resp = {}

        if get_original_results:
            django_http_resp['original_order'] = result_list.copy()

        # user_location = 'Lahore, Pakistan'.split(', ')

        # for result_item in result_list:
            # result_item_loc = result_item['_source']['location'].lower()

            location_score = 0

            # start weight

            # for location in user_location:
            #     if location.lower() in result_item_loc:
            #         location_score = 1
            #         result_item['_score'] += location_score
            #         # print(result_item)
            #         break

            # degree_rel = result_item['_source']['degree_poi']
            # result_item['_score'] += {1: 1, 2: 0.5, -1: 0.25}.get(degree_rel, 0)

            # end weight

            print(result_list)
            return HttpResponse('')

        result_list.sort(key=lambda result_item: result_item['_score'], reverse=True)

        django_http_resp['modified_order'] = result_list

        # print("--------------- MODIFIED ORDER ---------------\n")
        # print(json.dumps(django_http_resp['modified_order'], sort_keys=False, indent=4))
        # print("--------------- MODIFIED ORDER ---------------\n")

        return django_http_resp

    def get_elastic_results(self):

        es_response = requests.get(self.request_url,
                                   headers={'Content-Type': 'application/json'},
                                   data=self.build_elastic_query_data())

        # print("Elastic ")
        # print(es_response.text)

        return json.loads(es_response.text)

    # takes
    def query(self, query, search_function='default', filters=None, filter_weights=None):

        # os.system('cls')  # clear screen to refresh console messages

        self.user_query = query
        self.search_function = search_function
        self.filters = self.re_evaluate_filters_values(filters)
        # self.filter_weights = self.set_custom_filter_weights(filter_weights) # used for customizing user controlled weights WITHOUT filter values
        self.filter_weights = filter_weights

        results = self.get_elastic_results()

        # return results # temp line : remove

        # resp = self.rank_by_weightage(result_list)

        extracted_terms = self.preproces_query()
        self.first_degree_connections = self.get_first_degree_connections()
        scored_results = self.filter_results_and_assign_weightage(extracted_terms, results)
        self.sort_results(scored_results)

        # print(json.dumps(scored_results[0:5], sort_keys=False, indent=4))

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
                # print("..... STRING WITH REPLACED WORD .....")
                # print(filter_string)


            return filter_string

        for filter_key, filter_value in self.filters.items():

            print("Checking key " + filter_key + " " + result_item['first_name'] + " " + result_item['last_name'])

            result_key_existence = False
            filter_key_ = filter_key
            # temp code start: to be refactored later

                    # return True

            if filter_key in ['school_name', 'organization_name', 'job_title', 'degree']:


                # if filter_key == 'degree':
                #     for itr in range(4):
                #         result_item_key = 'school_'+str(itr)
                #         if result_item_key in result_item and result_item[result_item_key] is not None:
                #             filter_key_ = 'school_'+str(itr)
                #             # print('school ' + result_item[result_item_key] + " : " + result_item_key)
                #             result_key_existence = True
                #             break

                if filter_key == 'job_title':
                    filter_value = correct_spelling(filter_value)
                    # print(filter_value)
                    # print(filter_value.split())
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

                            # print("OK BOTH")

                            # print("Both filters set.....let's check")

                            filter_job_title = self.filters['job_title'].strip().lower()
                            filter_org = self.filters['organization_name'].strip().lower()

                            if result_item['organization_title_'+str(counter)] is not None and result_item['organization_title_'+str(counter)] is not None:

                                org_job_title = result_item['organization_title_'+str(counter)].strip().lower()
                                org_name = result_item['organization_'+str(counter)].strip().lower()

                            # if result_item['first_name'].lower() == 'andrew':

                                # print("filter job title " + filter_job_title)
                                # print("filter org " + filter_org)
                                #
                                # print("org job title " + result_item['organization_title_'+str(counter)])
                                # print("org " + result_item['organization_'+str(counter)])

                                if filter_org in org_name and filter_job_title in org_job_title:

                                    return True

                        else:

                            print("OK ELSE")

                            if filter_key == 'job_title':

                                print("OK filter_key job_title")

                                current_result_item_value = result_item['organization_title_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    print("filter value " + filter_value + " found in " + 'organization_title_'+str(counter))
                                    print(result_item['first_name'] + " " + result_item['last_name'])

                                    return True
                            #
                            if filter_key == 'organization_name':

                                # print("OK filter_key organization_name")
                                # print(filter_value + " == " + current_result_item_value + " : " + str(filter_value == current_result_item_value))

                                current_result_item_value = result_item['organization_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    # print("filter value " + filter_value + " found in " + 'organization_'+str(counter))
                                    # print(result_item['first_name'] + " " + result_item['last_name'])

                                    return True

                        counter += 1

                    return False

                elif filter_key in ['degree', 'school_name']:

                    print("OK elif")

                    counter = 1

                    while 'school_' + str(counter) in result_item and result_item['school_' + str(counter)] is not None:

                        if 'degree' in self.filters and 'school_name' in self.filters:

                            print("OK BOTH")

                            # print("Both filters set.....let's check")

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

                            print("OK ELSE")

                            if filter_key == 'degree':

                                # print("OK filter_key job_title")

                                current_result_item_value = result_item['degree_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    print("filter value " + filter_value + " found in " + 'degree'+str(counter))
                                    print(result_item['first_name'] + " " + result_item['last_name'])

                                    return True
                            #
                            if filter_key == 'school_name':

                                print("OK filter_key school_name")
                                print(filter_value + " == " + current_result_item_value + " : " + str(filter_value == current_result_item_value))

                                current_result_item_value = result_item['school_'+str(counter)].strip().lower()

                                if filter_value in current_result_item_value:

                                    print("filter value " + filter_value + " found in " + 'school_name'+str(counter))
                                    print(result_item['first_name'] + " " + result_item['last_name'])

                                    return True

                        counter += 1

                    return False

                else:

                    if filter_key in ['industry', 'sub_industry']:

                        filter_value = correct_spelling(filter_value)

                    if filter_value != current_result_item_value and filter_value not in current_result_item_value:

                        return False

                    else:
                        # pass
                        print("Accepting Result item for filter " + filter_key)
                        print(str(result_item['first_name']) + ' ' + str(result_item['last_name']))

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

    def tag_filter (self, result_item):

        if 'ctags' in result_item and result_item['ctags'] is not None:

            if self.filters['tag'].lower() not in result_item['ctags'].lower():

                return False

        else:

            return False

        return True

    def member_of_platform_filter (self, result_item):

        if 'edu_to_from_count' in result_item:

            itr_count = 1

            while itr_count <= result_item['edu_to_from_count']:

                if 'scool_profile_link_' + str(itr_count) in result_item and result_item['scool_profile_link_' + str(itr_count)] is not None and result_item['scool_profile_link_' + str(itr_count)].strip():

                    if self.filters['member_of_platform'].lower() in result_item['scool_profile_link_' + str(itr_count)].strip().lower():

                        # print("Person for link found ..... " + result_item['full_name'])
                        # print(result_item['social_profile_link_' + str(itr_count)])

                        return True

                    # else:

                        # print("Social profile link not found for person " + result_item['full_name'])
                        # print(result_item['social_profile_link_' + str(itr_count)])

                itr_count += 1

        if 'org_job_to_from' in result_item:

            itr_count = 1

            while itr_count <= result_item['org_job_to_from_count']:

                if 'job_profile_link_' + str(itr_count) in result_item and result_item['job_profile_link_' + str(itr_count)] is not None and result_item['job_profile_link_' + str(itr_count)].strip():

                    if self.filters['member_of_platform'].lower() in result_item['job_profile_link_' + str(itr_count)].strip().lower():

                        print("Person for link found ..... " + result_item['full_name'])
                        print(result_item['job_profile_link_' + str(itr_count)])

                        return True

                itr_count += 1

        if 'social_contact_description_count' in result_item:

            itr_count = 1

            while itr_count <= result_item['social_contact_description_count']:

                # if 'social_profile_link_' + str(itr_count) in result_item and result_item['social_profile_link_' + str(itr_count)] is not None and result_item['social_profile_link_' + str(itr_count)].strip():
                if 'des_profile_link_' + str(itr_count) in result_item and result_item['des_profile_link_' + str(itr_count)] is not None and result_item['des_profile_link_' + str(itr_count)].strip():

                    if self.filters['member_of_platform'].lower() in result_item['des_profile_link_' + str(itr_count)].strip().lower():

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
            highlights = result_item['highlight']
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
            result_item['weightage']['function_weightage'] = 0
            result_item['weightage']['filters_weightage'] = 0
            result_item['weightage']['elastic_weightage'] = elastic_score
            result_item['weightage']['total'] = elastic_score
            result_item['occurance_fields'] = []
            result_item['weightage']['neg_weightage'] = 0

            # FILTERS START #

            if self.filters:

                # ************************** TEMP code comment start ************************** #

                # if not self.filter_weights:

                # if not self.filter_result(result_item):

                # print("Skipping " + str(result_item['first_name']) + ' ' + str(result_item['last_name']))

                # continue

                # else:

                # **************************  TEMP code comment end  ************************** #


                # ************************** TEMP tag filter ************************** #

                if 'tag' in self.filters and not self.tag_filter(result_item):

                    print(f"Skipping {str(result_item['first_name'])}  {str(result_item['last_name'])} for not having required tag")

                    continue

                if 'member_of_platform' in self.filters and not self.member_of_platform_filter(result_item):

                    # print(f"Member of platform....")

                    continue

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

                # neglected fields area
                else:

                    pass

            result_item['weightage']['total'] += result_item['weightage'].get('field_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('rel_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('alias_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('experience_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('filters_weightage', 0)

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

            #
            #     print("Weight " + str(results['results'][result_item_index]['weightage']['total']) + "; Deleting " + results['results'][result_item_index]['Full name'])

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


