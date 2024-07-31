import json
from datetime import datetime

import requests
import re
import inflect
import os

from spellchecker import SpellChecker
from nltk import word_tokenize
from altworkz.settings import BASE_DIR

from . search import Search
from .utilities import *
from .location import Location

# ================================== #
#             WEB SEARCH             #
# ================================== #

''' BEGIN WEB SEARCH CLASS '''


class WebSearch (Search):

    def __init__(self, user_query=''):

        super().__init__()

    def query(self, query):

        os.system('cls')  # clear screen to refresh console messages

        self.user_query = query

        return self.search(self.user_query)

    def search(self, query):

        extracted_query_terms = self.preproces_query(self.user_query)

        sample_data = self.get_test_results()

        scored_results = self.assign_weightage(extracted_query_terms, sample_data)

        sorted_results = self.sort_results(scored_results)

        filtered_results = list(filter(lambda result_item: result_item['weightage']['total'] > 0, sorted_results))  # exclude results with score 0

        # print(len(filtered_results))

        # filtered_results = self.post_filteration(sorted_results)

        return filtered_results

    def post_filteration(self, results):

        return results

    def sort_results(self, results, sort_by='SCORE'):

        if sort_by == 'SCORE':  # sort by total score/weigtage

            # print(json.dumps(results['results'], sort_keys=False, indent=4))
            results['results'].sort(key=lambda result_item: result_item['weightage']['total'], reverse=True)

        return results['results']

    def get_test_results(self):

        results = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/weightage/results_test_2.json'), "r").read())

        return results

    ###############################################################################################

    def assign_weightage(self, query_word_list, results, type='default'):

        field_weightages = self.weightage_type.get(type, self.default_weightage)

        related_entities = {}
        inflct = inflect.engine()

        # begin : for result_item_index, result_item in enumerate(results['results']):

        for result_item_index, result_item in enumerate(results['results']):

            result_item['weightage'] = {}
            result_item['weightage']['occurance_weightage'] = 0
            result_item['weightage']['alias_weightage'] = 0
            result_item['weightage']['field_weightage'] = 0
            result_item['weightage']['rel_weightage'] = 0
            result_item['weightage']['experience_weightage'] = 0
            result_item['weightage']['total'] = 0
            result_item['occurance_fields'] = []
            result_item['weightage']['neg_weightage'] = 0

            # print("Checking result for " + result_item['Full name'])

            # begin : for ri_field, ri_value in result_item.items():

            for ri_field, ri_value in result_item.items():

                # begin: if ri_field in field_weightages:

                # evaluate only fields with weightage for now

                if ri_field in field_weightages or re.search('^' + self.fields['organization_title_n'] + '[0-9]$', ri_field):

                    # begin : if ri_value is not None:

                    if ri_value is not None:

                        if type(ri_value) is str:

                            ri_value = ri_value.lower()

                            if ri_field == self.fields['first_name'] or ri_field == self.fields['last_name'] or ri_field == self.fields['full_name']:

                                ri_value = ri_value.split(' ')

                                # search each word/term of query in field value

                        # begin : for query_term in query_word_list:

                        for query_term in query_word_list:

                            # search for singluar or plural form of query term in field value

                            if query_term in ri_value or inflct.plural(query_term) in ri_value:

                                # if same term exists multiple times in same field
                                # (except skills in which occurance frequency is calculated single time only and then multiplied by weight)
                                # then only assign weight point 1 otherwise default weight point of that field

                                if self.already_in_occurance_fields(ri_field, result_item['occurance_fields']):

                                    if ri_field != self.fields['skills']:

                                        result_item['weightage']['field_weightage'] += 1

                                else:

                                    if ri_field == 'skills':

                                        result_item['weightage']['field_weightage'] += 0.50 * ri_value.count(query_term)  # multiply skill weight by no. of occurances that exists in query term

                                    elif re.search('^' + self.fields['organization_title_n'] + '[0-9]$', ri_field):

                                        field_words = ri_field.split(' ')
                                        field_num = field_words[len(field_words) - 1]

                                        try:

                                            org_start_time = convert_to_format(result_item[self.fields['organization_start_n'] + field_num])
                                            org_end_time = convert_to_format(result_item[self.fields['organization_end_n'] + field_num])

                                            result_item['weightage']['experience_weightage'] += months_bw_date_intervals(org_end_time, org_start_time) * self.per_month_experience_weightage
                                            result_item['occurance_fields'].append({ri_field: query_term})

                                        except:

                                            print("No proper date format.....")

                                        # print(result_item[self.fields['full_name']] + " (" + ri_value + ")")
                                        # print(convert_datediff_to_months(org_start_time, org_end_time))

                                    else:

                                        result_item['weightage']['field_weightage'] += field_weightages.get(ri_field, self.sec_field_def_weight)  # if field is among field_weightages then assign its weightage otherwise set default weight

                                result_item['occurance_fields'].append({ri_field: query_term})

                            else:  # if exact term is not present find related ones, nest 'find related terms' inside else when else is uncommented

                                # find related entries if the exact match doesn't exist and assign weightage accordingly

                                ''' find related terms (start) '''

                                if ri_field == self.fields['skills'] or ri_field == self.fields['industry'] or ri_field == self.fields['headline']:

                                    skills_list = [skill.lower() for skill in list(set(word_tokenize(ri_value)).difference(self.query_str_exclusion_list))]

                                    if not bool(related_entities):

                                        related_entities = self.get_related_entities()

                                    if ri_field == self.fields['industry'] or ri_field == self.fields['headline']:

                                        if related_entities.get(query_term):

                                            if 'related' in related_entities:

                                                alias_terms = related_entities[query_term]['related']

                                                for query_alias_term in alias_terms:

                                                    if query_alias_term in ri_value or inflct.plural(query_term) in ri_value:

                                                        # assign weightage according to proximity to the term

                                                        result_item['weightage']['rel_weightage'] += 1  # right now set to fix weightage of one

                                    elif ri_field == self.fields['skills']:

                                        for skill in skills_list:

                                            skill = re.sub('[^A-Za-z0-9]+', '', skill)

                                            if skill in related_entities or inflct.plural(skill) in related_entities:

                                                if skill in related_entities:

                                                    entity = related_entities[skill]
                                                    # print(entity)

                                                else:

                                                    entity = related_entities[inflct.plural(skill)]

                                                if 'aliases' in entity:

                                                    if query_term in entity['aliases'] or inflct.plural(query_term) in entity['aliases']:

                                                        result_item['weightage']['rel_weightage'] += 0.50

                                                if 'related' in entity:

                                                    if query_term in entity['related'] or inflct.plural(query_term) in entity['related']:

                                                        result_item['weightage']['rel_weightage'] += 0.45

                                elif ri_field == self.fields['location']:

                                    # process only if current query term being matched with ri_field is of type Location (ignore other terms)

                                    # begin : if 'Location' in self.field_query_term and self.field_query_term['Location'] == query_term:

                                    if 'Location' in self.field_query_term and self.field_query_term['Location'] == query_term:

                                        # begin: if self.query_terms_categories[query_term]['parent'] != ri_value:

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

                                                    print("Country " + location_value['country'] + " Adding -ve weightage " + result_item['Full name'])

                                                # print('location')
                                                # print(location_value)


                                        else:

                                            pass

                                        # end: if self.query_terms_categories[query_term]['parent'] != ri_value:

                                    # end: if 'Location' in self.field_query_term and self.field_query_term['Location'] == query_term:

                                    # end: if ri_value in self.query_terms_categoires:

                                ''' find related terms (end) '''

                        # end : for query_term in query_word_list:

                    else:

                        pass
                        # print(result_item['Full name'] + ' : no value match')

                    # end : if ri_value is not None:

                # end: if ri_field in field_weightages:

            result_item['weightage']['total'] += result_item['weightage'].get('field_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('rel_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('alias_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('experience_weightage', 0)

            print("Exp weightage so far for " + result_item['Full name'] + " : " + str(result_item['weightage']['experience_weightage']))

            # print("Total weightage so far for " + result_item['Full name'] + " : " + str(result_item['weightage']['total']))

            result_item['weightage']['total'] += result_item['weightage'].get('neg_weightage', 0)

            print("Total weightage after adjustment " + result_item['Full name'] + " : " + str(result_item['weightage']['total']))

            if result_item['weightage']['total'] == 0:

                print("Weight " + str(results['results'][result_item_index]['weightage']['total']) + "; Deleting " + results['results'][result_item_index]['Full name'])

                # print("-------- BEFORE --------")

                # print(json.dumps(results['results'][result_item_index], sort_keys=False, indent=4))

                # # del results['results'][result_item_index]

                # print("-------- AFTER --------")

                # print(json.dumps(results['results'][result_item_index], sort_keys=False, indent=4))

            # begin : for ri_field, ri_value in result_item.items():

        # end : for result_item_index, result_item in enumerate(results['results']):

        # results['results'].sort(key=lambda result_item: result_item['weightage']['total'], reverse=True)

        # for result_item in results['results'][:10]:

        #     if result_item['weightage']['total'] > 0:

        #         print(json.dumps(result_item, sort_keys=False, indent=4))

        return results

    ###############################################################################################






