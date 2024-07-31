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


class WebSearch(Search):

    def __init__(self, user_query=''):

        super().__init__()

    def query(self, query, search_function='education', filters=None):

        os.system('cls')  # clear screen to refresh console messages

        self.user_query = query
        self.search_function = search_function

        if filters:
            self.filters = filters

        return self.search(self.user_query)

    def search(self, query):

        extracted_query_terms = self.preproces_query()

        sample_data = self.get_test_results()

        scored_results = self.assign_weightage(extracted_query_terms, sample_data)

        self.sort_results(scored_results)

        print(json.dumps(scored_results[0:5], sort_keys=False, indent=4))

        return scored_results

    def get_test_results(self):

        # results = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/weightage/results_test_2.json'), "r").read())
        results = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/weightage/education_weights_test.json'), "r").read())

        return results

    def assign_weightage(self, query_word_list, results):

        field_weightages = self.weightage_type.get(self.search_function, self.default_weightage)
        filtered_and_weighted_list = []

        for result_item_index, result_item in enumerate(results['results']):

            # filters experimental
            # begin : apply filters
            if self.filter_values_not_present(result_item):

                continue
            # end : apply filters

            result_item['weightage'] = {}
            result_item['weightage']['occurance_weightage'] = 0
            result_item['weightage']['alias_weightage'] = 0
            result_item['weightage']['field_weightage'] = 0
            result_item['weightage']['rel_weightage'] = 0
            result_item['weightage']['experience_weightage'] = 0
            result_item['weightage']['function_weightage'] = 0
            result_item['weightage']['total'] = 0
            result_item['occurance_fields'] = []
            result_item['weightage']['neg_weightage'] = 0


            # print("Checking result for " + result_item['Full name'])

            for ri_field, ri_value in result_item.items():

                # evaluate only fields with weightage for now
                if (ri_field in field_weightages) and (ri_value is not None and type(ri_value) is str):

                    ri_value = to_lower_and_split_if_name_field(ri_field, ri_value, self.fields)
                    self.search_query_terms_in_field_values_and_assign_weightage(query_word_list, ri_field, ri_value, result_item, field_weightages)

            result_item['weightage']['total'] += result_item['weightage'].get('field_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('rel_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('alias_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('experience_weightage', 0)
            result_item['weightage']['total'] += result_item['weightage'].get('function_weightage', 0)

            # print("Total weightage so far for " + result_item['Full name'] + " : " + str(result_item['weightage']['total']))

            result_item['weightage']['total'] += result_item['weightage'].get('neg_weightage', 0)

            # print("Total weightage after adjustment " + result_item['Full name'] + " : " + str(result_item['weightage']['total']))
            #
            if result_item['weightage']['total'] > 0:

                filtered_and_weighted_list.append(result_item)
            #
            #     print("Weight " + str(results['results'][result_item_index]['weightage']['total']) + "; Deleting " + results['results'][result_item_index]['Full name'])

        return filtered_and_weighted_list

