from django.contrib.auth.models import User, Group
from rest_framework import viewsets
# from altworkz.serializers import UserSerializer, GroupSerializer
#from soupsieve.util import upper

from .serializers import UserSerializer, GroupSerializer
from django.conf import settings

import requests
import json
from datetime import datetime

import urllib.parse as urlparse
from urllib.parse import parse_qs
#########
import django
django.setup()
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render

#from .forms import ContactForm, ColorfulContactForm

from multiprocessing import Pool
from multiprocessing import freeze_support
import time
from bs4 import BeautifulSoup
import json
import urllib.request as urllib2
from django.shortcuts import HttpResponse
#import pickle
from selenium import webdriver
from Bloombergapi.models import SearchFilter



from multiprocessing import Queue, cpu_count
from threading import Thread
from selenium import webdriver
from time import sleep
from numpy.random import randint
import logging
from selenium.common.exceptions import NoSuchElementException
###########
# Create your views here.
from fake_useragent import UserAgent
import random
from selenium.webdriver.common.keys import Keys
from search.elasticsearch import ElasticSearch
from contacts_import.models import Contact, Job, School, Organization, Education, Tag, ContactTag, \
    SocialProfile, ContactDegree, PersonofInterest
from contacts_import.views import school_method, organization_method

ua = UserAgent() # From here we generate a random user agent
proxies = [] # Will contain proxies [ip, port]

logger = logging.getLogger(__name__)
class FilterViewSet(viewsets.ModelViewSet):
    queryset = SearchFilter.objects.all().order_by('order')
    #serializer_class = FilterSerializer


def search(request):
    results = {}
    if request.method == "GET" and request.GET.get('search_str', False):
        query = request.GET.get('search_str', False)
        # platform = request.GET.get('platform', False)
        # # search on google
        # google_search = do_google_search(query, platform)
        # results['web_results'] = google_search
        # search within database
        db_search = do_db_search(request, query)
        results['db_results'] = db_search
        print(results)
        return HttpResponse(json.dumps(results), content_type="application/json")


def do_google_search(query, platform):
    api_key = "AIzaSyB3dtqBhzm2BoMwsw9RMKImPOIHIEmZrO4"
    SEARCH_ENGINE_IDS = {'facebook': '527785719f0d583ee',
                         'yahoo': '008566010345248266130:3gvgp8unwjm',
                         'bloomberg': '008566010345248266130:wjnu19fbysg',
                         'linkedin': '008566010345248266130:gdf1s3zhbru',
                         'sec': '008566010345248266130:_9vyvfasrdy'}

    search_engine_id = SEARCH_ENGINE_IDS[platform]

    # using the first page
    page = 1
    start = (page - 1) * 10 + 1
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={search_engine_id}&q={query}&start={start}"

    data = requests.get(url).json()
    search_items = data.get("items")
    urls = []
    if search_items is not None and len(search_items) > 0:
        for i, search_item in enumerate(search_items, start=1):
            # # get the page title
            # title = search_item.get("title")
            # # page snippet
            # snippet = search_item.get("snippet")
            # # alternatively, you can get the HTML snippet (bolded keywords)
            # html_snippet = search_item.get("htmlSnippet")
            # extract the page url
            link = search_item.get("link")
            urls.append(link)
    #json_urls = json.dumps(urls) 
    return urls
    #return HttpResponse(json_urls, content_type="application/json")


def scrape(request):
    url = request.GET['url']
    platform = request.GET['platform']
    # before scrapping check if url was scrapped earlier, in that case skip it
    is_url_scrapped(url, platform)
    proxies = get_proxies()
    proxy = random.choice(proxies)
    json_data = {}
    profile_data = False
    if platform == 'bloomberg':
        profile_data = scrape_bloomberg(url, proxy)
    elif platform == 'sec':
        profile_data = scrape_sec(url)
    if profile_data is not False and platform == 'bloomberg':
        json_data = json.dumps(profile_data)
        do_db_save(profile_data)
    return HttpResponse(json_data, content_type="application/json")


def do_db_search(request, query):
    search_ = ElasticSearch(request.user.id)
    db_results = search_.query(query)
    return db_results

 
def do_db_save(data):

    name = data['name'].split(' ')
    first_name = name[0]
    middle_name = ''
    last_name = name[len(name)-1]

    if len(name) > 2:
        middle_name = ' '.join(name[1:len(name)-1])

    contact, created = Contact.objects.update_or_create(
        user_id=1,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        photo = data['profile_image'],
    )

    SocialProfile.objects.update_or_create(
        contact_id=contact.id,
        bloomberg_profile_url=data['profile_url'],

    )

    if len(data['education']) > 0:
        for education in data['education'][0]:
            school_method(education['institution'], '', '', '', contact.id)

    if len(data['job_history']) > 0:
        for a, job in enumerate( data['job_history'][0], start=1):
            company_details = None
            if a == 1:
                company_details =data['company_details']
            organization_method(job['company'], contact.id, job['from'], job['to'], job['title'], company_details)


def is_url_scrapped(url, platform):
    pass

def searchold(request):
    from search.search import ElasticSearch
    
    context = {}

    search_type = 'elastic'
    search_type = 'web'

    search_ = {}

    if request.method == "GET" and request.GET.get('search_str', False):

        # if search_type == 'web':
        #     search_ = WebSearch()

        if search_type == 'elastic':
            search_ = ElasticSearch()

        # ws = WebSearch()
        context['results'] = search_.query(request.GET.get('search_str', False))
        context['search_type'] = search_type
        print(context['results'])

        # for result_item in context['results']:
        #     fields = result_item['_source']
        #     print(fields['first_name'] + ' ' + fields['last_name'] + ' | ' + fields['industry'] + fields['location'])

    # return render(request, 'search/simple_query_form.html', context)
    # return render(request, 'search/search_results.html', context)
    return render(request, 'search/search_results.html', context)
    # return HttpResponse(json.dumps(context['results'], sort_keys=False, indent=4))

def welcome():
    return True


def Gsearch(request):
    if request.is_ajax():
        # now = datetime.now()
        # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        # print("reached gsearch =", dt_string)
        # Create the two queues to hold the data and the IDs for the selenium workers

        # global selenium_workers
        # global selenium_data_queue
        # global worker_queue
        # global worker_ids
        # selenium_data_queue = Queue()
        # worker_queue = Queue()
        # # Create Selenium processes and assign them a worker ID
        # # This ID is what needs to be put on the queue as Selenium workers cannot be pickled
        # # By default, make one selenium process per cpu core with cpu_count
        # # TODO: Change the worker creation code to be your webworker of choice e.g. PhantomJS
        # worker_ids = list(range(6))
        # selenium_workers = {
        #     i: webdriver.Firefox(options=set_options(), executable_path=r"C:\Users\farooq.akbar\Downloads\geckodriver.exe")
        #     for i in worker_ids}
        # print('seleniu workers::', selenium_workers)
        # for worker_id in worker_ids:
        #     worker_queue.put(worker_id)


        print ('gsearch')
        API_KEY = "AIzaSyB3dtqBhzm2BoMwsw9RMKImPOIHIEmZrO4"
        #SEARCH_ENGINE_ID = "008566010345248266130:gdf1s3zhbru"#linkedin
        SEARCH_ENGINE_ID = "008566010345248266130:3gvgp8unwjm"  # yahoo finance
        SEARCH_ENGINE_ID = "008566010345248266130:_9vyvfasrdy"#sec.gov
        SEARCH_ENGINE_ID = "008566010345248266130:wjnu19fbysg"  # bloomberg
        #SEARCH_ENGINE_ID = "527785719f0d583ee"#fb


        # the search query you want
        query = request.GET.get('search_str')
        # query = request.GET['search_str']
        # query= "Oil company"
        # using the first page
        page = 1
        start = (page - 1) * 10 + 1
        url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&start={start}"

        data = requests.get(url).json()
        search_items = data.get("items")
        # urls = []
        # for i, search_item in enumerate(search_items, start=1):
        #     b = {}
        #     # get the page title
        #     title = search_item.get("title")
        #     # page snippet
        #     snippet = search_item.get("snippet")
        #     # alternatively, you can get the HTML snippet (bolded keywords)
        #     html_snippet = search_item.get("htmlSnippet")
        #     # extract the page url
        #     link = search_item.get("link")
        #     # print the results
        #     print("=" * 10, f"Result #{i + start - 1}", "=" * 10)
        #     print("Title:", title)
        #     print("Description:", snippet)
        #     print("URL:", link, "\n")

            #b = "=" * 10, f"Result #{i + start - 1}", "=" * 10
            # b['title'] = title
            # b['Description'] = snippet
            # b['URL'] = link
            #
            # b['data'] = scrape_urls(SEARCH_ENGINE_ID, link)
            # urls.append(link)
        #a['data'] = scrape_linkedin('https://www.linkedin.com/in/rob-camping-615a5b13/')
        # a['data'] = scrape_facebook('https://www.facebook.com/ali.wetrill')
        #return render(request, 'search/search_results.html', json.dumps({'results':a}))
        #a['data'] = scrape_bloomberg('https://www.facebook.com/ali.wetrill')
        # print(type(a))
        # json_data = json.dumps(a)
        # print(json_data)
        #urls.append('STOP')
        # now = datetime.now()
        # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        # print("Got list of results =", dt_string)
        # users = []
        # proxies = get_proxies()
        # now = datetime.now()
        # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        # print("Got proxies =", dt_string)
        # for i, url in enumerate(urls, start=1):
        #     now = datetime.now()
        #     dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        #     print("Got proxies =", dt_string)
        #     print("i =", i)
        #     proxy = random.choice(proxies)
        #     users.append(scrape_bloomberg(url, proxy))
            # users.append(scrape_fb(url))
            #users.append(scrape_yahoo(url))

        # from joblib import Parallel, delayed
        # users = Parallel(n_jobs=1)(delayed(scrape_bloomberg)(url, proxy) for key, url in a.items())
        # for key, url in a.items():
        #
        #     print('u:', url)
        #     proxy_ip = random.choice(proxy)
        #     users[key] = scrape_bloomberg(url, proxy_ip)
        # now = datetime.now()
        # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        # print(" END =", dt_string)
        # json_data = json.dumps(users)
        # return HttpResponse(json_data, content_type="application/json")
        #return HttpResponse(json.dumps({'results':a}))
    return HttpResponse(json.dumps({'results':search_items}))


def get_proxies():
    proxies_req = urllib2.Request('https://www.sslproxies.org/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urllib2.urlopen(proxies_req).read().decode('utf8')

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    proxies_table = soup.find(id='proxylisttable')

    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })

    return proxies


def set_options():
    proxies = get_proxies()
    proxy = random.choice(proxies)
    options = webdriver.FirefoxOptions()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    # options.add_argument("--no-sandbox")
    proxy_ip = proxy['ip'] + ':' + proxy['port']
    options.add_argument('--proxy-server=http://%s' % proxy_ip)
    return options
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################


# def get_users_data(urls):
#     now = datetime.now()
#     dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
#     print("date and time at USER DAT START=", dt_string)
#     # Some example data to pass the the selenium processes, this will just cause a sleep of time i
#     # This data can be a list of any datatype that can be pickled
#     #selenium_data = [4, 2, 3, 3, 4, 3, 4, 3, 1, 2, 3, 2, 'STOP']
#     selenium_data = urls
#
#
#
#     # Create one new queue listener thread per selenium worker and start them
#     logger.info("Starting selenium background processes")
#     selenium_processes = [Thread(target=selenium_queue_listener,
#                                  args=(selenium_data_queue, worker_queue)) for _ in worker_ids]
#     now = datetime.now()
#     dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
#     print("date and time BEFORE processes start=", dt_string)
#     for p in selenium_processes:
#         p.daemon = True
#         p.start()
#     now = datetime.now()
#     dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
#     print("date and time AFTER processes start=", dt_string)
#     # Add each item of data to the data queue, this could be done over time so long as the selenium queue listening
#     # processes are still running
#     logger.info("Adding data to data queue")
#     for d in selenium_data:
#         selenium_data_queue.put(d)
#
#     # Wait for all selenium queue listening processes to complete, this happens when the queue listener returns
#     logger.info("Waiting for Queue listener threads to complete")
#     for p in selenium_processes:
#         p.join()
#
#     # Quit all the web workers elegantly in the background
#     logger.info("Tearing down web workers")
#     for b in selenium_workers.values():
#         b.quit()


# def selenium_task(worker, data):
#     """
#     This is a demonstration selenium function that takes a worker and data and then does something with the worker and
#     data.
#     TODO: change the below code to be whatever it is you want your worker to do e.g. scrape webpages or run browser tests
#     :param worker: A selenium web worker NOT a worker ID
#     :type worker: webdriver.XXX
#     :param data: Any data for your selenium function (must be pickleable)
#     :rtype: None
#     """
#     #proxy = random.choice(proxy)
#     now = datetime.now()
#     dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
#     print("date and time =", dt_string)
#     print('url in proxy:', data)
#     #print(' proxy:', proxy)
#     print(' #########')
#     user_data = {}
#     worker.set_window_size(randint(100, 200), randint(200, 400))
#     print("Getting URL", data)
#     worker.get(data)
#     logger.info("Sleeping")
#     try:
#         executive_summary = worker.find_element_by_class_name('executiveSummary__eb728b4e')
#     except NoSuchElementException:
#         print('Element not found')
#         return False
#     print('element found')
#     try:
#         profile_image = executive_summary.find_element_by_tag_name('img')
#         user_data['profile_image'] = profile_image.get_attribute('src')
#     except NoSuchElementException:
#         user_data['profile_image'] = ''
#
#     name = executive_summary.find_element_by_class_name('name__300c1393').text
#     user_data['name'] = name
#     job = executive_summary.find_element_by_class_name('job__5c09e33d').text
#     job_object = job.split(',')
#     user_data['job'] = job_object[0]
#     user_data['company'] = job_object[1]
#     print(name)
#     #worker.close()
#
#     return user_data
#
#
# def selenium_queue_listener(data_queue, worker_queue):
#     """
#     Monitor a data queue and assign new pieces of data to any available web workers to action
#     :param data_queue: The python FIFO queue containing the data to run on the web worker
#     :type data_queue: Queue
#     :param worker_queue: The queue that holds the IDs of any idle workers
#     :type worker_queue: Queue
#     :rtype: None
#     """
#     print("Selenium func worker started")
#     while True:
#         current_data = data_queue.get()
#         if current_data == 'STOP':
#             # If a stop is encountered then kill the current worker and put the stop back onto the queue
#             # to poison other workers listening on the queue
#             print("STOP encountered, killing worker thread")
#             data_queue.put(current_data)
#             break
#         else:
#             print(f"Got the item {current_data} on the data queue")
#         # Get the ID of any currently free workers from the worker queue
#         worker_id = worker_queue.get()
#         worker = selenium_workers[worker_id]
#         # Assign current worker and current data to your selenium function
#         selenium_task(worker, current_data)
#         # Put the worker back into the worker queue as  it has completed it's task
#         worker_queue.put(worker_id)
#     return














































#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################
#########################################################################################


def scrape_bloomberg(url, proxy):
    # now = datetime.now()
    # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # print("Got start of scrape bloomberg =", dt_string)


    user_data = {}
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.FirefoxOptions()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    #caps["pageLoadStrategy"] = "normal"  # complete
    caps["pageLoadStrategy"] = "eager"  #  interactive
    #caps["pageLoadStrategy"] = "none"
    profile = webdriver.FirefoxProfile()
    # profile.set_preference("browser.startup.homepage_override.mstone", "ignore")
    # profile.set_preference("startup.homepage_welcome_url.additional", "about:blank")
    # # Paint delay off
    # profile.set_preference('nglayout.initialpaint.delay', 0)
    # # Tabs animation
    # profile.set_preference('browser.tabs.animate', False)
    # # Gif animation off
    # profile.set_preference('image.animation_mode', 'none')
    # # Tabs memory off
    # profile.set_preference('browser.sessionhistory.max_total_viewer', 1)
    # profile.set_preference('browser.sessionhistory.max_entries', 3)
    # profile.set_preference('browser.sessionhistory.max_total_viewers', 1)
    # profile.set_preference('browser.sessionstore.max_tabs_undo', 0)
    # # Asynchronous requests to the server
    # profile.set_preference('network.http.pipelining', True)
    # profile.set_preference('network.http.pipelining.maxrequests', 8)
    # # Cache enabled
    # profile.set_preference('browser.cache.memory.enable', False)
    # profile.set_preference('browser.cache.disk.enable', True)
    # # Autosuggests
    # profile.set_preference('browser.search.suggest.enabled', False)
    # # Formfills
    # profile.set_preference('browser.formfill.enable', False)
    # # scan downloads
    # profile.set_preference('browser.download.manager.scanWhenDone', False)
    # # no bookmarks backup
    # profile.set_preference('browser.bookmarks.max_backups', 0)
    proxy_ip = proxy['ip'] + ':' + proxy['port']
    options.add_argument('--proxy-server=http://%s' % proxy_ip)
    # now = datetime.now()
    # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # print("stating webdriver =", dt_string)
    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, executable_path=r"C:\Users\Zaid.javeed\Documents\geckodriver.exe")
    #driver = webdriver.Opera( desired_capabilities=caps, options=options, executable_path=r"C:\Users\farooq.akbar\Downloads\operadriver.exe")

    #for i, url in enumerate(urls, start=1):
    # now = datetime.now()
    # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # print(" webdriver DONE=", dt_string)
    data = {}
    board_memberships = []
    other_memberships = []
    awards = []
    publications = []
    education = []
    job_history = []
    executives = []
    board_members = []
    # now = datetime.now()
    # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # print("before get url =", dt_string)
    # print ('url in proxy:', url)
    # #print(' proxy:', proxy)
    # print(' #########')

    driver.get(url)
    #webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    # now = datetime.now()
    # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    # print("after get url =", dt_string)
    data['platform'] = 'Bloomberg'
    data['profile_url'] = url
    # try:
    #     executive_summary = WebDriverWait(driver, 10).until(
    #         EC.visibility_of_element_located((By.CSS_SELECTOR, ".executiveSummary__eb728b4e"))
    #     )
    # except NoSuchElementException:
    #     print ('exception')
        #continue

    try:
        executive_summary = driver.find_element_by_class_name('executiveSummary__eb728b4e')
    except NoSuchElementException:
        # print ('Element not found')
        driver.close()
        executive_summary = None
        return False

    try:
        profile_image = executive_summary.find_element_by_tag_name('img')
        data['profile_image'] = profile_image.get_attribute('src')
    except NoSuchElementException:
        data['profile_image'] = 'https://via.placeholder.com/110x110'

    name = executive_summary.find_element_by_class_name('name__300c1393').text
    data['name'] = name

    # job = executive_summary.find_element_by_class_name('job__5c09e33d').text
    # job_object = job.split(',')
    # data['job'] = job_object[0]
    # data['company'] = job_object[1]
    #print(name)
    # get industry
    # summary_info_table = executive_summary.find_element_by_class_name('infoTable__5a50f5ff')
    # table_elements = summary_info_table.find_elements_by_class_name("infoTableItem__3008f79b")
    # for item in table_elements:
    #     label = item.find_element_by_tag_name('h2').text.lower()
    #     try:
    #         text = item.find_element_by_tag_name('div').text
    #     except NoSuchElementException:
    #         text = '-'
    #     #print ('label::', label)
    #     #print('text::', text)
    #     if 'current position' in label and 'tenure' not in label and text != '--':
    #         text = text.split(',')
    #         print ('label', text)
    #
    #         job_history.update([('position', text[0])])
    #         job_history.update([('company', text[1])])
    #     if 'tenure' in label:
    #         text = text.split('-')
    #         job_history.update([('from', text[0])])
    #         if len(text) == 1:
    #             job_history.update([('to', '--')])
    #         else:
    #             job_history.update([('to', text[1])])
    #
    #     #print (item.find_element_by_tag_name('h2').text)
    # data['jobs'] = job_history
    #main_content = driver.find_element(By.CSS_SELECTOR(".mainContent__8a485e7d > div.container__00452967"))

    info_containers = driver.find_elements_by_class_name("container__00452967")
    for x, container in enumerate(info_containers, start=1):
        #if x == 1:
        try:
            container.find_element_by_class_name('expansionControls__cebb2de7').click()
        except:
            print ('View more not found')
        title = container.find_element_by_tag_name('h2').text
        if title.lower() == 'board memberships':
            # iterate over board memberships and add in dict
            board_elem = container.find_element_by_class_name('container__170fc8e2')
            board_memberships.append(bloomberg_details(title, board_elem))
        if title.lower() == 'career history':
            # iterate over board memberships and add in dict
            board_elem = container.find_element_by_class_name('container__170fc8e2')
            job_history.append(bloomberg_details(title, board_elem))
        if title.lower() == 'education':
            # iterate over board memberships and add in dict
            board_elem = container.find_element_by_class_name('container__170fc8e2')
            education.append(bloomberg_details(title, board_elem))
        if title.lower() == 'other memberships':
            # iterate over other memberships and add in dict
            board_elem = container.find_element_by_class_name('container__170fc8e2')
            other_memberships.append(bloomberg_details(title, board_elem))
        if title.lower() == 'awards':
            # iterate over other memberships and add in dict
            board_elem = container.find_element_by_class_name('container__170fc8e2')
            awards.append(bloomberg_details(title, board_elem))
        if title.lower() == 'publications':
            # iterate over other memberships and add in dict
            board_elem = container.find_element_by_class_name('container__170fc8e2')
            publications.append(bloomberg_details(title, board_elem))

    data.update([('board_memberships', board_memberships)])
    data.update([('job_history', job_history)])
    data.update([('education', education)])
    data.update([('other_memberships', other_memberships)])
    data.update([('awards', awards)])
    data.update([('publications', publications)])
    user_data = data

    print(user_data)

     #= driver.find_element_by_class_name('companyProfileLink__1d2ded78').get_attribute("href")
    try:
        company_profile = driver.find_element_by_class_name('companyProfileLink__1d2ded78').get_attribute("href")
    except NoSuchElementException:
        # print ('Element not found')
        driver.close()
        company_profile = None
        return False

    company_pro_about = company_profile.rpartition('?')
    company_profile_link = company_pro_about[0]

    try:
        driver.find_element_by_class_name('companyProfileLink__1d2ded78').click()
    except:
        print('View more not found')

    try:
        company_title = driver.find_element_by_class_name('info__d075c560')
    except NoSuchElementException:
        # print ('Element not found')
        driver.close()
        company_title = None
        return False

    try:
        company_description = driver.find_element_by_class_name('info__d075c560')
    except NoSuchElementException:
        # print ('Element not found')
        driver.close()
        company_description = None
        return False

    about_company_name = company_title.find_element_by_tag_name('h1').text
    company_descriptions = company_description.find_element_by_class_name('description__ce057c5c').text

    company_detail_containers = driver.find_element_by_class_name("infoTable__96162ad6")
    company_detail = {}
    for i, company in enumerate(company_detail_containers.find_elements_by_class_name('infoTableItem__1003ce53'), start=1):
        executive_title = company.find_element_by_tag_name('h2').text.lower()
        executive_detail = company.find_element_by_class_name('infoTableItemValue__e188b0cb').text
        company_detail[executive_title] = executive_detail

    executive_module = driver.find_element_by_class_name("module")
    try:
        executive_module.find_element_by_class_name('expansionControls__cebb2de7').click()
    except:
        print('View more not found')

    executive_containers = driver.find_element_by_class_name("executivesWrap__7da4e15b")
    executive_teams_info = []
    for i, executive in enumerate(executive_containers.find_elements_by_class_name('link__f5415c25'), start=1):

        executive_details = {}
        try:
            link = executive.get_attribute("href")
        except NoSuchElementException:
            link = None
        try:
            profile = executive.find_element_by_class_name('headshot__e8c048ca').get_attribute("style")
        except NoSuchElementException:
            profile = None
        profile_image_link = profile.replace("background-image: url(", "")
        profile_image_links = profile_image_link[:-3]
        profile_img_link = profile_image_links[1:]
        try:
            name = executive.find_element_by_class_name('name__c96644d1').text
        except NoSuchElementException:
            name = None
        try:
            designation = executive.find_element_by_class_name('title__cde0e39b').text
        except NoSuchElementException:
            designation = None
        executive_details.update([('link', link), ('profile', profile_img_link), ('name', name), ('designation', designation)])
        executive_teams_info.append(executive_details)

    board_containers = driver.find_element_by_class_name("boardWrap__8a218670")
    board_members_info = []
    for i, board in enumerate(board_containers.find_elements_by_class_name('link__f5415c25'), start=1):
        board_members = {}
        try:
            link = board.get_attribute("href")
        except NoSuchElementException:
            link = None
        try:
            name = board.find_element_by_class_name('name__c96644d1').text
        except NoSuchElementException:
            name = None
        try:
            company_name = board.find_element_by_class_name('company__7f8639ea').text
        except NoSuchElementException:
            company_name = None
        board_members.update([('link', link), ('name', name), ('company_name', company_name)])
        board_members_info.append(board_members)

    data.update([('company_details', company_detail)])
    data['company_details']['description'] = company_descriptions
    data['company_details']['company_name'] = about_company_name
    data['company_details']['company_profile_link'] = company_profile_link
    data.update([('executives', executive_teams_info)])
    data.update([('board_members', board_members_info)])
    driver.close()
    return user_data


def scrape_bloomberg_company_page(url, proxy):

    pass

def scrape_bloomberg_person_page(url, proxy):

    pass


def bloomberg_details(container_title, container):
    data = []
    for i, membership in enumerate(container.find_elements_by_class_name('row__726e4534'), start=1):
        row = {}
        # print (membership.find_elements_by_class_name('cell__3cf444e7'))
        cols = membership.find_elements_by_class_name('cell__3cf444e7')
        if(container_title == 'Board Memberships' or container_title == 'Career History'):

            tenure = cols[2].text.split('–')
            member_from = tenure[0]
            if len(tenure) == 1:
                member_to = tenure[0]
            else:
                member_to = tenure[1]
            # print (cols[0].text)
            row.update([('title', cols[0].text), ('company', cols[1].text), ('from', member_from), ('to', member_to)])
        elif (container_title == 'Other Memberships'):
            row.update([('title', cols[0].text), ('company', cols[1].text)])
        elif (container_title == 'Education'):
            row.update([('title', cols[0].text), ('institution', cols[1].text)])
        elif (container_title == 'Awards'):
            row.update([('title', cols[0].text), ('detail', cols[1].text), ('on', cols[2].text)])
        elif (container_title == 'Publications'):
            row.update([('title', cols[0].text), ('role', cols[1].text),  ('on', cols[2].text)])
        elif (container_title == 'About'):
            row.update([('title', cols[0].text), ('description', cols[1].text)])
        else:
            row.update([('title', cols[0].text), ('company', cols[1].text)])
        data.append(row)

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    return data


def scrape_sec(url):
    print('sec')
    #url = 'https://www.sec.gov/edgar/search/#/q=oil%2520companies&dateRange=5y&startdt=2018-09-25&enddt=2020-09-25&category=all&locationType=located&locationCode=all&filter_forms=10-K'
    import re
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html5lib')
    data = dict()
    data['platform'] = 'Bloomberg'
    data['profile_url'] = url
    #print (soup)
    executives_text = soup.find_all(text=re.compile('Executive Officers', re.IGNORECASE))
    print (url)
    print(executives_text)
    print('######')
    data = []
    headers = []
    executive_text = ['executive_officers_of_the_registrant',
                      'directors_executive_officers_and_corporate_governance',
                      'directors_and_executive_officers_of_the_registrant',
                      'information_about_the_company’s_executive_officers']
    for item in executives_text:
        row_item = {}
        etext = item.lower()
        etext = etext.replace(' ', '_').replace(',', '')
        if etext in executive_text:
            print ('match found -- now get content')
            print(etext)
            # tab = item.find_next("table")
            # print (tab)
            for i, row in enumerate(item.find_next("table").find_all("tr"), start=1):
                print ([cell.get_text(strip=True) for cell in row.find_all("td")])
            print('#_#_#_##_#_#_#_')


# def get_sec_links(request):
#     page = 1
#     from selenium.webdriver.support.ui import WebDriverWait
#     from selenium.webdriver.common.by import By
#     from selenium.webdriver.support import expected_conditions as EC
#     driver = webdriver.Firefox(executable_path=r"C:\Users\farooq.akbar\Downloads\geckodriver.exe")
#     url = 'https://www.sec.gov/edgar/search/#/dateRange=custom&startdt=2011-09-25&enddt=2020-10-06&category=form-cat1&locationType=located&locationCode=all&forms=1-K%252C1-SA%252C1-U%252C1-Z%252C1-Z-W%252C10-D%252C10-K%252C10-KT%252C10-Q%252C10-QT%252C11-K%252C11-KT%252C13F-HR%252C13F-NT%252C15-12B%252C15-12G%252C15-15D%252C15F-12B%252C15F-12G%252C15F-15D%252C18-K%252C20-F%252C24F-2NT%252C25%252C25-NSE%252C40-17F2%252C40-17G%252C40-F%252C6-K%252C8-K%252C8-K12G3%252C8-K15D5%252CABS-15G%252CABS-EE%252CANNLRPT%252CDSTRBRPT%252CIRANNOTICE%252CN-30B-2%252CN-30D%252CN-CEN%252CN-CSR%252CN-CSRS%252CN-MFP%252CN-MFP1%252CN-MFP2%252CN-PX%252CN-Q%252CNPORT-EX%252CNSAR-A%252CNSAR-B%252CNSAR-U%252CNT%252010-D%252CNT%252010-K%252CNT%252010-Q%252CNT%252011-K%252CNT%252020-F%252CQRTLYRPT%252CSD%252CSP%252015D2&filter_forms=10-K&'
#     data = []
#     while page <= 2:
#         if page == 1:
#             url = url + 'page='+str(page)
#             print (url)
#             driver.get(url)
#         else:
#             driver.find_element(By.LINK_TEXT, 'Next page').click()
#             driver.implicitly_wait(10)
#         WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.CSS_SELECTOR, "div.searching-overlay")))
#         WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "col-cik"))).click()
#         WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "col-located"))).click()
#
#         grid = driver.find_element_by_id('hits')
#
#         driver.implicitly_wait(5)
#         for i, row in enumerate(grid.find_elements_by_tag_name('tr'), start=1):
#             row_data = {}
#             if i == 1:
#                 continue
#             file_id = ''
#             file_name = ''
#             try:
#                 preview_file = row.find_element_by_class_name('preview-file')
#                 file_id = preview_file.get_attribute('data-adsh').replace('-', '')
#                 file_name = preview_file.get_attribute('data-file-name')
#             except NoSuchElementException:
#                 print ('error in preview------------')
#
#             cik = row.find_element_by_class_name('cik').text
#             filed = row.find_element_by_class_name('filed').text
#             entity_name = row.find_element_by_class_name('entity-name').text
#             sec_file_link = 'https://www.sec.gov/Archives/edgar/data/'+cik[4:]+'/'+file_id+'/'+file_name
#             located = row.find_element_by_class_name('located').text
#
#             row_data['entity_name'] = entity_name
#             row_data['file_link'] = sec_file_link
#             row_data['located'] = located
#             row_data['filed'] = filed
#             row_data['cik'] = cik
#             data.append(row_data)
#             # print('#_#_#__#_#_#')
#         page += 1
#     print(data)
#     save_sec_data(data)
#     return data
#
# def save_sec_data(data):
#     for item in data:
#         print(item)


def scrape_urls(cse, page):
    search_engine = {"008566010345248266130:wjnu19fbysg":"bloomberg",
                     "008566010345248266130:_9vyvfasrdy":"sec.gov",
                     "008566010345248266130:3gvgp8unwjm":"yahoo"}

    # scrape_template = {}
    # scrape_template['yahoo'] = {"container":"section"}
    # scrape_template['yahoo']['container'] = {'attr': 'class__quote-subsection'}

    website_to_scrape = search_engine[cse]
    # if(website_to_scrape is "yahoo"):
    #     data = scrape_yahoo(page)
    if (website_to_scrape == "bloomberg"):
        data = scrape_bloomberg(page)


    return website_to_scrape


def scrape_yahoo(url):
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html5lib')
    company_data = dict()
    company_data['platform'] = 'Yahoo'
    executives_section = soup.find('section', attrs={'class': 'quote-subsection'})
    items_in_row = ['name', 'title', 'pay', 'exercised', 'dob']
    if executives_section:
        for x, item in enumerate(executives_section.find_all('tr'), start=1):
            td_list = item.find_all('td')
            person_data = {}
            for i, td in enumerate(td_list, start=1):
                if i in [1,2,3,5]:
                    index = items_in_row[i-1]
                    person_data[index] = td.text
                    #company_data.update([(items_in_row[i-1], td.text)])

            company_data.update([(x, person_data)])
        print('***********************company_data*************************')
        print(company_data)
        print('***********************company_data*************************')
    return company_data


def scrape_linkedin(url):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    #options = webdriver.ChromeOptions()
    options = webdriver.FirefoxOptions()
    # options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(options=options, executable_path=r"C:\Users\farooq.akbar\Downloads\geckodriver.exe")
    driver.get('https://www.linkedin.com/')
    driver.implicitly_wait(3)
    username = driver.find_element_by_id('session_key')
    username.send_keys('farukakbar@gmail.com')
    username = driver.find_element_by_id('session_password')
    username.send_keys('KVVL8g6f')
    driver.find_element_by_class_name('sign-in-form__submit-button').click()
    driver.implicitly_wait(3)
    driver.get(url)
    driver.implicitly_wait(3)
    profile_image = driver.find_element_by_class_name('pv-top-card__photo').get_attribute("src")
    profile_about_cont = driver.find_element_by_class_name('pv-about-section')
    profile_about_cont.find_element_by_class_name('lt-line-clamp__more').click()
    profile_about_cont = driver.find_element_by_class_name('pv-about-section').text
    #summary = profile_container.find_element_by_tag_name('h2').text
    print("Image:", profile_image)
    print("about:", profile_about_cont)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    #print("URL:", link, "\n")
    #driver.implicitly_wait(2)
    #search_box = driver.find_element_by_id('navi-search-input')
    #urls = []
    return True


def scrape_fb(url):
    url_about = 'about'
    if url[-1] != '/':
        url_about = '/about'
    import re

    url = url + url_about
    print('URL:', url)
    page = urllib2.urlopen(url)
    soup = BeautifulSoup(page, 'html5lib')
    content = soup.find('div', {'id': 'content_container'})
    map = content.find('a', attrs={'ajaxify': re.compile(r'/places/map/?')})
    print ('map::',map)
    if map:
        print ("Map found return false#############")
        return False

    sidebar = soup.find('div', {'id':'entity_sidebar'})

    about_tab = sidebar.find('div', {'data-key':'tab_about'})
    print(about_tab)


def scrape_facebook(url, proxy):
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("Got start of scrape bloomberg =", dt_string)

    user_data = {}
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.FirefoxOptions()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    # caps["pageLoadStrategy"] = "normal"  # complete
    caps["pageLoadStrategy"] = "eager"  # interactive
    # caps["pageLoadStrategy"] = "none"

    proxy_ip = proxy['ip'] + ':' + proxy['port']
    options.add_argument('--proxy-server=http://%s' % proxy_ip)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("stating webdriver =", dt_string)
    driver = webdriver.Firefox( desired_capabilities=caps, options=options,
                               executable_path=r"C:\Users\farooq.akbar\Downloads\geckodriver.exe")


    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("webdriver DONE=", dt_string)
    data = {}
    board_memberships = []
    other_memberships = []
    awards = []
    publications = []
    education = []
    about = []
    job_history = []
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("before get url =", dt_string)
    print('url in proxy:', url)
    # print(' proxy:', proxy)
    print(' #########')

    driver.get(url)
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("after get url =", dt_string)
    data['platform'] = 'Bloomberg'

    photo_cont = driver.find_element_by_class_name('photoContainer')
    img = photo_cont.find_element_by_tag_name('img').get_attribute("src")
    name = driver.find_element_by_id('fb-timeline-cover-name').text
    #name = photo_cont.find_element_by_tag_name('a').text
    print("Image:", img)
    print("name:", name)
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    return True


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


from django.core.mail import send_mail
from django.http import HttpResponse


def send_test_email(request):
    res = send_mail("Test Email", "Sending test email through django ", "paul@polo.com",
                    ["nadir.usman@powersoft19.com"])
    return HttpResponse('%s' % ("Email Sent " if res else "No Email Sent"))


def test_hit(request):
    r = requests.get('http://localhost:8000/rest-auth/user/?username=admin')
    return HttpResponse(r)


''' CLEAR BIT '''


def clearbit(request):
    #import clearbit

    clearbit.key = settings.CLEARBIT_API_KEY

    #response = clearbit.NameToDomain.find(name='Clearbit')
    html_response = ''
    response = clearbit.Person.find(email='nadirawan17@gmail.com')

    if response is not None:
        for value, key in enumerate(response):
            pass #print('{} : {}',upper(str(key)),upper(str(response[key])))

    return HttpResponse(response)
    # pass


def data_enrichment_email(request):
    pass
