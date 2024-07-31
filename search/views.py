from django.conf.global_settings import STATIC_ROOT
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt
from django import template
from django.template.defaultfilters import register

from altworkz.settings import ES_INDEX_URL

from .websearch import WebSearch
from .elasticsearch import ElasticSearch
from .graph import *
from .utilities import *

import edgar
from edgar import Company, TXTML
from bs4 import BeautifulSoup
from altworkz.settings import BASE_DIR
from querystring_parser import parser

import os
import json
import requests

from contacts_import.models import Tag, CSVTag, ContactDegree, PersonofInterest, Education, Job, Contact, Organization
from django.contrib.auth.models import User
from search_history.models import SearchTerm, ContactViewHistory

from accounts.models import Profile

from search_history.models import SearchHistory


@login_required
def index(request):

    user = User.objects.get(id=request.user.id)
    page_obj = user.search_terms.all().order_by('-id')
    
    context = {}
    
    if user.profile.is_first_login == 1:

        Profile.objects.filter(user_id=request.user.id).update(is_first_login=0)         
        request.session['first_time_login'] = True
        contact_id = Profile.objects.get(user_id=request.user.id).contact_id
        return redirect('userboard/update_profile/'+str(contact_id))
  
    user_contacts = []
    user_organization = []

    # query = 'SELECT id, DISTINCT(search_term), filters, filter_weights FROM search_history WHERE user_id = ' + str(request.user.id) + ' ORDER BY created_at DESC'
    # print(query)
    search_history = list(ContactViewHistory.objects.raw('SELECT id, search_term, filters, filter_weights FROM search_history WHERE user_id = ' + str(request.user.id) + ' ORDER BY updated_at DESC'))[:4]

    # search_history = SearchHistory.objects.filter(user_id=request.user.id).order_by('-created_at').values('search_term').distinct()[:4]
    # context['search_history'] = search_history
    # print("-------------------- USER SEARCH HISTORY -------------------- \n")
    # print(search_history)
    # for shi in search_history:
    #     print(shi.search_term + ' | ' + str(shi.filters) + ' | ' + str(shi.filter_weights))
    # print(search_history[0].search_term + " | " + str(search_history[0].filters) + " | " + str(search_history[0].filter_weights) + " | " + str(search_history[0].created_at))
    # print(search_history[1].search_term + " | " + str(search_history[1].filters) + " | " + str(search_history[1].filter_weights) + " | " + str(search_history[1].created_at))
    # print(search_history[2].search_term + " | " + str(search_history[2].filters) + " | " + str(search_history[2].filter_weights) + " | " + str(search_history[2].created_at))
    # print(search_history[3].search_term + " | " + str(search_history[3].filters) + " | " + str(search_history[3].filter_weights) + " | " + str(search_history[3].created_at))
    # print("\n-------------------- USER SEARCH HISTORY -------------------- \n")

    user_contact_id = Profile.objects.filter(user_id=request.user.id).values()[0]
    user_job_title = Job.objects.filter(contact_id=user_contact_id['contact_id'])
    if user_job_title:
        related_job_title = Job.objects.filter(job_title=user_job_title[0].job_title).exclude(
            contact_id=user_contact_id['contact_id'])[:4]
        # job_title = user_job_title[0].job_title
        # related_job_title = Job.objects.raw('select * from jobs where job_title = job_title  group  by contact_id')
        if related_job_title:
            for job_title in related_job_title:
                user_contacts.append(Contact.objects.filter(id=job_title.contact_id))
            context["related_contacts_details"] = user_contacts
            context["related_job_title"] = related_job_title
        else:
            current_job_title = []
            context["related_contacts"] = Contact.objects.all().order_by('-id')[:4]
            for related_contacts in context["related_contacts"]:
                current_job_title.append(Job.objects.filter(contact_id=related_contacts.id))
            context["related_job_title"] = current_job_title
    else:
        current_job_title = []
        context["related_contacts"] = Contact.objects.all().order_by('-id')[:4]
        for related_contacts in context["related_contacts"]:
            current_job_title.append(Job.objects.filter(contact_id=related_contacts.id)[:1])
        context["related_job_title"] = current_job_title
    # results = json.loads(open(os.path.join(BASE_DIR, 'search/static/search/json/data.json'), "r").read())
    # context['results'] = results
    # context['first_result_detail'] = results['search_results'][0] if results['search_results'] else results['web_results'][0]
    #
    # return HttpResponse(context['first_result_detail']['name'])

    # print('Request')
    # print(request.GET.get('msg'))

    browsed_history = []

    if request.method == "POST":

        '''
        results['search_results'] = search_results
        results['web_results'] = web_results   
        '''

        # results = json.loads(
        #     open(os.path.join(BASE_DIR, 'search/static/search/json/data.json'), "r").read())
        # context['results'] = results

    else:

        browsed_history = list(ContactViewHistory.objects.raw('SELECT DISTINCT(user_contact_view_history.contact_id) as id, contacts.first_name, contacts.middle_name, contacts.last_name, photo, jobs.job_title FROM `user_contact_view_history` JOIN `contacts` ON `contacts`.`id` = `user_contact_view_history`.`contact_id` JOIN `jobs` ON `contacts`.`id` = `jobs`.`contact_id` WHERE user_contact_view_history.user_id = ' + str(request.user.id) + ' GROUP BY id ORDER BY `user_contact_view_history`.`created_at` DESC LIMIT 4'))

    context['tags'] = Tag.objects.all()

    return render(request, "search/search_results.html", {'page_obj':page_obj, 'context':context, 'browsed_history': browsed_history, 'search_history': search_history})

def es_search(request):

    # os.system('cls')  # clear screen to refresh console messages

    context = {}

    # search_type = 'web'
    search_type = 'elastic'

    search = {}
    params_dict = parser.parse(request.GET.urlencode())

    print("here ------- PARAMS -------")
    print('params_dict :',params_dict)
    try:
        filters = params_dict.get('filters', None)
        print("filters ------- PARAMS -------" , filters)
        filter_weights = params_dict.get('filter_weights', None)
    except Exception as e:
        print('error : %s' % e)

    if filter_weights:
        context['filter_weights'] = filter_weights
        filter_weights_new = {filter_key.replace("_weightage", ""): (float(filter_weights[filter_key]) / 5) * 100 for filter_key in filter_weights}
        filter_weights = filter_weights_new

    print('----- FILTERS ------\n')
    print(filters)
    print('----- FILTER WEIGHTS ------\n')
    print(filter_weights)

    # filter_weights = params_dict.get('filter_weights', None)
    function_type = 'default'
    # filter_weights_list = ['job_title', 'location', 'company']
    # filter_weights = {'job_title': 25, 'location': 25, 'company': 25, 'education': 25}
    # filter_weights = {'job_title': 25, 'company': 25}
    # filter_weights = {}
    if filter_weights:
        function_type = 'user_defined'
        print('----------Here---------')

    if request.method == "GET" and request.GET.get('search_str', False):

        if search_type == 'web':

            search = WebSearch()

        if search_type == 'elastic':

            search = ElasticSearch(request.user.id)
            save_search = SearchHistory()
            save_search.search_term = request.GET.get('search_str', False).strip()
            save_search.filters = json.dumps(filters) if filters else None
            save_search.filter_weights = json.dumps(context['filter_weights']) if 'filter_weights' in context else None
            save_search.user_id = request.user.id
            print('-----Here------' ,save_search.user_id)

            if request.GET.get('first_search_after_pageload') == 'true':

                save_search.save()
                request.session['search_history_id'] = save_search.id
                print("------------------------- FIRST TIME SEARCH TRUE -------------------------\n ")

            elif 'search_history_id' in request.session:

                last_search = SearchHistory.objects.filter(id=request.session['search_history_id']).first()

                print(request.GET.get('search_str', False).strip() == last_search.search_term)

                if last_search:

                    if request.GET.get('search_str', False).strip() == last_search.search_term:

                        last_search.filters = json.dumps(filters) if filters else None
                        last_search.filter_weights = json.dumps(context['filter_weights']) if 'filter_weights' in context else None
                        last_search.save()
                        # request.session['search_history_id'] = save_search.id

                    else:

                        save_search.save()
                        request.session['search_history_id'] = save_search.id

        #     print('first_search_after_page_load')
        #     print(request.GET.get('first_search_after_pageload'))
        #     print("------------------------- SEARCH HISTORY ID -------------------------\n " + str(save_search.id))
        #     print(request.GET.get(''))
        # ws = WebSearch()
        page_num = request.GET.get('page_num', 1)
        print("page num in view ", page_num)
        additional_values_to_be_forwarded = {}
        print('here the values to be forwarded' ,additional_values_to_be_forwarded)
        context['results'] = search.query(request.GET.get('search_str', False), function_type, filters, filter_weights, page_num, additional_values_to_be_forwarded) # {'location': 'Manchester', 'industry': 'Engineering'} with filters
        context['total_results'] = additional_values_to_be_forwarded['total_results']
        print('yes:' , context['total_results'])
        if request.GET.get('view_saved_search', False):
            context['view_saved_search'] = True
            

    # if filters != params_dict.get('filters', None):
        first_degree = []
        second_degree = []
        third_degree = []
        persons_of_interest = []
        # query_filters = filters
        # print("query filters")
        # print(query_filters)        

        # return HttpResponse(json.dumps(context), content_type="application/json")

        # return HttpResponse(context['results'])

        # print(json.dumps(context['results'][:10], sort_keys=False, indent=4))

        # print(request.user.id)
        context['mutual_connections'] = {}
        mutual_connection_ids = []
        current_user_id = request.user.id
        firstDegreeArray = []
        secondDegreeArray = []
        thirdDegreeArray = []
        
        context['mutual_connections'] = {}
        print(" -------------------- FIRST DEGREE CONNECTIONS --------------------\n ")
        first_degree_connections = ContactDegree.objects.filter(user_id=current_user_id)
        # print(list(first_degree_connections.values('contact_degree_id')))
        fdc_contact_id_list = list(first_degree_connections.values('contact_degree_id'))
        ids_list = [id_dict_item['contact_degree_id'] for id_dict_item in fdc_contact_id_list]
        print( " IDS LIST \n")
        print(len(ids_list))
        cil = ElasticSearch(request.user.id)
        cil = cil.get_contacts_by_id(ids_list)
        # print(cil)
        cil = cil['hits']['hits']

        context['first_degree_connections_details'] = {contact_detail['_source']['contact_id']: contact_detail['_source'] for contact_detail in cil}

        print(" -------------------- CONNECTION GRAPH  -------------------- \n")

        print(" Searching user contact id graph\n")
        user_contact_id = Profile.objects.filter(user_id=request.user.id).values()[0]['contact_id']
        print(user_contact_id)
        
        ###################################################### CONNECTION GRAPH ######################################################     
        
        context['connection_graph'] = {}
        
        # get_contact_connections(context, request.user.id, user_contact_id)
        
        if os.path.exists('/home/ec2-user/aw/altworkz/static/json/graphs/' + str(user_contact_id) + '.json'):
        
            print("file present \n")
            
            connection_graph = json.loads(open("/home/ec2-user/aw/altworkz/static/json/graphs/" + str(user_contact_id) + ".json", "r").read())
            context['connection_graph'] = connection_graph 
            context['second_degree_connection_details'] = {} 
            second_degree_contact_list = set()

            for dest_node, cg in connection_graph.items():

                second_degree_contact_list.add(dest_node)    

                print("cg", cg)

                for path in cg[1:]:

                    for node in path:

                        second_degree_contact_list.add(node)
                        
                        if node not in context['second_degree_connection_details']:
                        
                            context['second_degree_connection_details'][node] = {} 

            cil = ElasticSearch(request.user.id)
            cil = cil.get_contacts_by_id(list(second_degree_contact_list))
            # print(cil)
            cil = cil['hits']['hits']

            context['sec_degree_connection_details'] = {contact_detail['_source']['contact_id']: contact_detail['_source'] for contact_detail in cil}
        
            # print(json.dumps(context['sec_degree_connection_details'], sort_keys=False, indent=4))



            user_connections_details = {};
                   
        else:
        
            print("file not present \n")
        
        ###################################################### CONNECTION GRAPH ######################################################     
            

        print(" -------------------- CONNECTION GRAPH  -------------------- \n")

        # print(len(context['first_degree_connections_details']))
        # print(cil)
        
        #print(" \n-------------------- FIRST DEGREE CONNECTIONS -------------------- ")
        
        for first_degree_connection in first_degree_connections:
            firstDegreeArray.append(first_degree_connection.contact_degree_id)
            first_degree_contact_id = first_degree_connection.contact_degree_id
            first_degree_user_id = first_degree_connection.user_id
            user_contact_id_first = first_degree_connection.user_contact_id
            check_second_degree_connections = ContactDegree.objects.filter(user_contact_id=first_degree_contact_id)
            for second_degree_connection in check_second_degree_connections:
                contact_degree_ids = second_degree_connection.contact_degree_id
                
                if contact_degree_ids in context['mutual_connections']:
                    context['mutual_connections'][contact_degree_ids].append(first_degree_contact_id)
                else:
                    context['mutual_connections'][contact_degree_ids] = [first_degree_contact_id]
                
                secondDegreeArray.append(second_degree_connection.contact_degree_id)
                third_degree_connections = ContactDegree.objects.filter(user_contact_id=contact_degree_ids)
                for third_degree_connection in third_degree_connections:
                    thirdDegreeArray.append(third_degree_connection.contact_degree_id)
                # second_degree_connections = ContactDegree.objects.filter(user_id=second_degree_user_id)

                # for second_degree_connection in second_degree_connections:
                #     if second_degree_connection.contact_degree_id != first_degree_contact_id:
                #         secondDegreeArray.append(second_degree_connection.contact_degree_id)
                #         second_degree_contact_id = second_degree_connection.contact_degree_id
                #         check_third_degree_connections = ContactDegree.objects.filter(
                #             contact_degree_id=second_degree_contact_id).exclude(
                #             user_id=second_degree_user_id)
                #
                #         for third_degree_connection in check_third_degree_connections:
                #             third_degree_user_id = third_degree_connection.user_id
                #             print('*******************************************************')
                #             print(check_third_degree_connections)
                #             third_degree_connections = ContactDegree.objects.filter(user_id=third_degree_user_id)
                #
                #             for third_degree_connection in third_degree_connections:
                #                 if third_degree_connection.contact_degree_id != second_degree_contact_id:
                #                     print('*******************************')
                #                     thirdDegreeArray.append(third_degree_connection.contact_degree_id)

        poi_connections = PersonofInterest.objects.filter(user_id=request.user.id).values_list('poi_id', flat=True)
        poiArray = []
        for poi_connection in poi_connections:
            poiArray.append(poi_connection)

        context.update([('first_degree', firstDegreeArray)])
        context.update([('second_degree', secondDegreeArray)])
        context.update([('third_degree', thirdDegreeArray)])

        context.update([('persons_of_interest', poiArray)])

        # context['file_tags'] = CSVTag.objects.filter(user_id=request.user.id).values('name').distinct()

        print("======================== FILE TAG SUGGESTIONS ======================== \n")
        context['file_tags_suggestions'] = list(CSVTag.objects.filter(user_id=request.user.id).values_list('name', flat=True).distinct())
        # print(file_tags.query)
        # print("Mutual Connections..............")
        # print(context['mutual_connections'])
        # for result in context['results']:
        #     print("-----------------\n")
        #     print(result['full_name'])
        #     print(result['occurance_fields'])
        #     print(result['weightage'])
        #     print("-----------------\n")

        # for result_item in context['results']:
        #     fields = result_item['_source']
        #     print(fields['first_name'] + ' ' + fields['last_name'] + ' | ' + fields['industry'] + fields['location'])

    # return render(request, 'search/simple_query_form.html', context)
    # return render(request, 'search/search_results.html', context)
    # return render(request, 'search/web_results.html', context)
    context['staff'] = User.objects.get(id=request.user.id).is_staff    
    return HttpResponse(json.dumps(context, sort_keys=False, indent=4))

@csrf_exempt
def get_contact_details (request):

    print(request.POST.get('f-deg'))
    print(request.POST.get('s-deg'))

    return HttpResponse(json.dumps(request, sort_keys=False, indent=4))


@csrf_exempt
def es_search_json(request):

    context = {}

    if request.method == "POST" and request.POST.get('query', False):

        es = ElasticSearch()
        results = es.query(request.POST.get('query', False), 'default', {})
        # print(results)

        # for result_item in context['results']:
        #     fields = result_item['_source']
        #     print(fields['first_name'] + ' ' + fields['last_name'] + ' | ' + fields['industry'] + fields['location'])

    return HttpResponse(json.dumps(results, sort_keys=False, indent=4))

def es_compare(request):

    context = {}

    if request.method == "GET" and request.GET.get('query', False):

        es = ElasticSearch()       
        context['results'] = es.query(request.GET.get('query', False))

    return render(request, 'search/simple_query_form.html', context)


@csrf_exempt
def es_search_json_compare(request):

    context = {}
    results = {}

    if request.method == "POST" and request.POST.get('query', False):

        es = ElasticSearch()
        results = es.query_compare_results(request.POST.get('query', False))

        # for result_item in context['results']:
        #     fields = result_item['_source']
        #     print(fields['first_name'] + ' ' + fields['last_name'] + ' | ' + fields['industry'] + fields['location'])

    return HttpResponse(json.dumps(results, sort_keys=False, indent=4))


@register.filter(name='get')
def get(d, k):
    return d.get(k, None)


def F10K(request):

    format = 'xbrl'
    format = 'xml'

    sec_companies = {
        "oracle": {
            "name": "Oracle Corp",
            "cik":  "0001341439"
        },
        "google": {
            "name": "Alphabet Inc",
            "cik":  "0001652044"
        },
        "apple": {
            "name": "Apple Inc.",
            "cik": "0000320193"
        },
        "ibm": {
            "name": "INTERNATIONAL BUSINESS MACHINES CORP",
            "cik": "0000051143"
        },
        "dell": {
            "name": "Dell Technologies Inc.",
            "cik":  "0001571996"
        }
    }

    company_sec = sec_companies[request.GET[company]]

    company = Company(company_sec.get('name'), company_sec.get('cik'))

    tree = company.get_all_filings(filing_type="10-K")
    docs = Company.get_documents(tree, no_of_documents=1)
    doc_html = BeautifulSoup(TXTML.to_xml(docs), 'html.parser')

    table_headers = ('Name', 'Title', 'Date')
    person_list = []

    # tables_list
    for t_num, table in enumerate(doc_html.find_all('table')[-2:]):

        thtml = str(table)

        if ("Name" in thtml or "Signature" in thtml) and ("Title" in thtml):

            non_empty_tr = 1
            for tr in table.find_all('tr')[1:]:  # tr_list

                # print("Starting row "+str(tr_i))

                person = {}
                col_index = 0

                if (tr.get_text().strip() != ''):

                    for td_i, td in enumerate(tr.find_all('td')):  # td_list

                        td_txt = td.get_text().strip()

                        if (td_txt != ''):

                            # print(td_txt + ' ('+ str(td_i) + ') ', end = " | ")

                            if (non_empty_tr % 2 == 0):

                                if (col_index == 0):

                                    person_list[len(person_list) - 1][table_headers[col_index]] = td_txt

                            else:

                                if (col_index > 0):

                                    person[table_headers[col_index]] = td_txt

                            col_index += 1

                    non_empty_tr += 1

                    if (len(person) != 0):

                        person_list.append(person)

    context = {
        'person_list': person_list,
        'Company': company_sec
    } 

    return render(request, 'scr/scrape_results.html', context)

def test(request):

    # user_profile = Profile.objects.get(user_id=17)
    #
    # print(Education.objects.filter())

    es_response = requests.delete(ES_INDEX_URL + '/_doc/' + str(28071))
    es_response = requests.delete('http://localhost:9200/ml_test_2_copy/_doc/2002')
    print(ES_INDEX_URL + '/_doc/' + str(2002))
    print(es_response)

    # print(es.delete_elastic_index_doc(28071))

    return HttpResponse(" ---- Look into Console ---- ")

    with open(os.path.join(BASE_DIR, 'static/json/locations/countries+states+cities.json'), encoding="utf8") as countries_states_cities:

        for country_detail in json.loads(countries_states_cities.read()):
            country_name = country_detail['name'].lower()
            country = os.path.join(BASE_DIR, 'static/json/locations/countries/'+country_name+'.json')
            if not os.path.isfile(country):

                if country_name == 'united states':

                    with open(os.path.join(BASE_DIR, 'static/json/US-states-and-cities/list.json'), 'r') as US_selected_cities:

                        US_selected_cities = json.loads(US_selected_cities.read())
                        print(US_selected_cities)

                    total_found_states = 0

                    for state in country_detail['states']:

                        city_list = []
                    #
                        for US_selected_cities_state in US_selected_cities:

                            if state['name'] == str(US_selected_cities_state):

                                for US_selected_city in US_selected_cities[US_selected_cities_state]:

                                    city = {}

                                    city['name'] = US_selected_city
                                    city['state'] = US_selected_cities_state

                                    city_list.append(city)

                                    print(US_selected_city)

                                total_found_states += 1

                        state['cities'] = city_list
                        print(state['name'] + ' found')
                        print(state['cities'])

                            # else:
                            #
                            #     print('state name ' + state['name'])
                            #     print('US_selected_cities_state ' + str(US_selected_cities_state))



                    #
                    #         print(US_selected_cities_state)

                            # if state['name'] == US_selected_cities_state.keys()[0]:
                            #
                            #     print('state found')
                            #
                            #     break

                else:

                    for state in country_detail['states']:
                        # print(type(state['cities']))
                        for city in state['cities']:
                            city['state'] = state['name']
                            del city['id']
                            del city['latitude']
                            del city['longitude']

                        # city['state'] = state['name']
                        # print(city['name'] + '\n')

                with open(os.path.join(BASE_DIR, 'static/json/locations/countries/'+country_detail['name'].lower()+'.json'), 'w') as country_cities:
                    # print(country_detail)
                    json.dump(country_detail, country_cities)
                country_cities.close()

                print(os.path.join(BASE_DIR, 'static/json/locations/countries/'+country_detail['name'].lower()+'.json'))

    return HttpResponse("See console")

    # return JsonResponse(json.loads(open(os.path.join(BASE_DIR, 'static/json/locations/countries+states+cities.json'), encoding="utf8").read()), safe=False)


def get_countries_list (request):

    # countries_list = requests.get('https://api.countrystatecity.in/v1/countries', headers = {'X-CSCAPI-KEY': 'YzY1aDVtNzhIOFp0UjR3OUxmTmtQVThXQzI3ZEZVUldleFMzeWJEaw=='})
    # return HttpResponse(requests.get('https://api.countrystatecity.in/v1/countries', headers = {'X-CSCAPI-KEY': 'YzY1aDVtNzhIOFp0UjR3OUxmTmtQVThXQzI3ZEZVUldleFMzeWJEaw=='}))

    return JsonResponse(json.loads(open(os.path.join(BASE_DIR, 'static/json/locations/countries.json'), encoding="utf8").read()), safe=False)

def get_cities_list (request):

    country = request.GET.get('country', None)
    if country is not None:

        country_file = os.path.join(BASE_DIR, 'static/json/locations/countries/' + country.lower() + '.json')

        if os.path.isfile(country_file):

            with open(os.path.join(BASE_DIR, 'static/json/locations/countries/'+country.lower()+'.json'), 'r') as country_states_cities:

                # print(os.path.join(BASE_DIR, 'static/json/locations/countries/'+country.lower()+'.json'))
                return JsonResponse(json.loads(country_states_cities.read()), safe=False)

    return JsonResponse([])
    
def get_filters_suggestions (request):
    print("Getting filters...")
    context = {}
    search_type = 'elastic'
    search = {}
    params_dict = parser.parse(request.GET.urlencode())
    print(params_dict)
    print("------- PARAMS -------")
    print(params_dict)

    filters = params_dict.get('filters', None)
    try:
        if request.method == "GET" and request.GET.get('search_str', False):

            if search_type == 'elastic':
                function_type = 'user_defined'
                print("Here also in ELASTICSEARCH")  
                search = ElasticSearch(request.user.id)  
                context['filter_suggestions'] = search.fetch_filter_suggestions(request.GET.get('search_str', False), filters)['hits']['hits'] # {'location': 'Manchester', 'industry': 'Engineering'} with filters
                    
                context['filter_suggestions'] = map(lambda es_result : es_result['_source'], context['filter_suggestions'])
                print("CONTEXT : " , context['filter_suggestions'] )
                
        return HttpResponse(json.dumps(list(context['filter_suggestions']), sort_keys=False, indent=4))
    except Exception as e:
        return HttpResponse(json.dumps(list(context[e]), sort_keys=False, indent=4)) 