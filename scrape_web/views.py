from django.shortcuts import render
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import requests
from bs4 import BeautifulSoup
import json
import urllib.request as urllib2
from django.shortcuts import HttpResponse
import re
import datetime
from datetime import datetime
from datetime import timedelta
import urllib.parse as urlparse
from urllib.parse import parse_qs

from fake_useragent import UserAgent
import random
import spacy
from spacy import displacy

from django.contrib.auth.models import User
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from contacts_import.models import Contact, Job, School, Organization, Education, Tag, ContactTag, \
    SocialProfile, ContactDegree, PersonofInterest, ContactScrapeSource, ContactDescription
from contacts_import.views import school_method, organization_method
from .models import Sec
from .models import SecLinkScrape, SecDocumentScrape, BloomCompanyScrape
# Create your views here.

ua = UserAgent() # From here we generate a random user agent
proxies = [] # Will contain proxies [ip, port]

class Scrape:

    def __init__(self):
        pass

    def fetch_sec_listing_by_date_range(self):
        pass


def sec_link_scrape(request):
    latest_date_scrape= ''
    updated_scrape_date = ''
    from_scrape = ''
    to_scrape = ''
    try:
        update_days = timedelta(days=20)
        get_latest_scrape = SecLinkScrape.objects.latest('to_scrape')
        latest_date_scrape = get_latest_scrape.to_scrape
        convert_str = latest_date_scrape.strftime('%m/%d/%Y')
        convrt_strtime = datetime.strptime(convert_str, "%m/%d/%Y")
        updated_scrape_date= convrt_strtime + update_days
        start_date = latest_date_scrape.strftime('%Y-%m-%d')
        end_date = updated_scrape_date.strftime('%Y-%m-%d')

    except SecLinkScrape.DoesNotExist:
        latest_date_scrape = '2010-01-01 00:00:00'
        updated_scrape_date = '2010-01-01 00:00:00'
        start_date = '2010-01-01'
        end_date = '2010-01-01'

    sec_link_scrape, created = SecLinkScrape.objects.update_or_create(
        from_scrape=latest_date_scrape,
        to_scrape=updated_scrape_date,
    )
    get_sec_links(start_date, end_date)

def sec_document_scrape(request):

    try:
        get_latest_scrape = SecDocumentScrape.objects.latest('to_scrape')
        latest_doc_scrape = get_latest_scrape.to_scrape
        update_index = 5
        start_index = int(latest_doc_scrape)
        end_index = int(latest_doc_scrape) + int(update_index)
    except SecDocumentScrape.DoesNotExist:
        start_index = 1
        end_index = 10

    get_document_link = Sec.objects.filter(is_scraped = 0).order_by('id')[start_index:end_index]
    sec_document_scrape, created = SecDocumentScrape.objects.update_or_create(
        from_scrape=int(start_index),
        to_scrape=int(end_index),
    )
    print(start_index)
    scrape_sec_document(get_document_link)
    # return Sec.objects.all().order_by('id')[star_index:end_index]

def scrape_bloomberg_person (request):
    json_data = {}
    proxy = ''
    profile_data = False
    platform = 'bloomberg'
    person_profile_link = SocialProfile.objects.filter(platform = 'bloomberg').exclude(
        is_scraped=1).order_by('id')[0:1]

    for person in person_profile_link:
        if person.platform_link == '':
            continue
        else:
            proxies = get_proxies()
            print('************************Procy*************************************')
            print(len(proxies))
            proxy = random.choice(proxies)
            url = person.platform_link
            person_contact_id = person.contact_id
            socail_profiles_id = person.id

            print('---------------------------Person Link----------------------------')
            print(url)

            profile_data = scrape_bloomberg_person_data_page(url, proxy, person_contact_id)
            print('---------------------------person_contact_id----------------------------')
            print(profile_data)
            if profile_data is not False:
                json_data = json.dumps(profile_data)
                save_bloomberg_person_details(profile_data, socail_profiles_id)

def scrape_bloomberg_company (request):
    json_data = {}
    profile_data= False
    try:
        get_latest_scrape = BloomCompanyScrape.objects.latest('to_scrape')
        latest_doc_scrape = get_latest_scrape.to_scrape
        update_index = 50
        start_index = int(latest_doc_scrape)
        end_index = int(latest_doc_scrape) + int(update_index)
    except BloomCompanyScrape.DoesNotExist:
        start_index = 1
        end_index = 2

    bloom_comany_scrape, created = BloomCompanyScrape.objects.update_or_create(
        from_scrape=int(start_index),
        to_scrape=int(end_index),
    )

    organization_symbol = Organization.objects.exclude(organization_symbol__isnull=True).exclude(is_bloomberg_scraped=1).order_by('id')[start_index:end_index]
    proxies = get_proxies()
    proxy = random.choice(proxies)
    print("organization_symbol",organization_symbol)
    for symbol in organization_symbol:
        if symbol.organization_symbol == '':
            continue
    
        else:
            organization_symbol = symbol.organization_symbol
            print(organization_symbol)
            print('---------------------------Company Link----------------------------')
            print('https://www.bloomberg.com/profile/company/' + symbol.organization_symbol.strip() + ':US')
            url = ('https://www.bloomberg.com/profile/company/' + symbol.organization_symbol.strip() + ':US')
            #url = 'https://www.bloomberg.com/profile/company/BRMT:US'
            #organization_symbol = 'BRMT'
            print('Koi nahi chal riya')
            print(url)
            
            profile_data = scrape_bloomberg_company_data_page(url, proxy, organization_symbol)
            # print('*****************Profile Data***********************')
            print(profile_data)
            if profile_data is not False:
                json_data = json.dumps(profile_data)
                save_bloomberg_company_details(profile_data)
                return HttpResponse('hello')
def get_sec_links(start_date, end_date):
    page = 1
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # driver = webdriver.Chrome(executable_path=r"/home/ec2-user/aw/chrome/chromedriver")
    driver = webdriver.Chrome(executable_path='/home/ec2-user/aw/chrome/chromedriver', options=chrome_options)
    url = 'https://www.sec.gov/edgar/search/#/dateRange=custom&startdt='+ start_date +'&enddt='+ end_date +'&category=form-cat1&locationType=located&locationCode=all&forms=1-K%252C1-SA%252C1-U%252C1-Z%252C1-Z-W%252C10-D%252C10-K%252C10-KT%252C10-Q%252C10-QT%252C11-K%252C11-KT%252C13F-HR%252C13F-NT%252C15-12B%252C15-12G%252C15-15D%252C15F-12B%252C15F-12G%252C15F-15D%252C18-K%252C20-F%252C24F-2NT%252C25%252C25-NSE%252C40-17F2%252C40-17G%252C40-F%252C6-K%252C8-K%252C8-K12G3%252C8-K15D5%252CABS-15G%252CABS-EE%252CANNLRPT%252CDSTRBRPT%252CIRANNOTICE%252CN-30B-2%252CN-30D%252CN-CEN%252CN-CSR%252CN-CSRS%252CN-MFP%252CN-MFP1%252CN-MFP2%252CN-PX%252CN-Q%252CNPORT-EX%252CNSAR-A%252CNSAR-B%252CNSAR-U%252CNT%252010-D%252CNT%252010-K%252CNT%252010-Q%252CNT%252011-K%252CNT%252020-F%252CQRTLYRPT%252CSD%252CSP%252015D2&filter_forms=10-K&'
    print('--------------------sec Link------------------------------')
    print(url)
    print('--------------------sec Link------------------------------')
    data = []
    url = url + 'page=' + str(page)
    driver.get(url)
    driver.implicitly_wait(20)
    page_count = 1
    try:
        pagination = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "results-pagination")))
        # pagination = driver.find_element_by_id('results-pagination')
        if pagination.is_displayed():
            print(pagination)
            print(pagination.is_displayed())
            print('style::', pagination.get_attribute('style'))
            disabled_count = len(pagination.find_elements_by_class_name('d-none'))
            print(disabled_count)
            page_count = 10 - disabled_count
    except:
        print('no found')
        pass

    while page <= page_count:
        print('page:',page)
        print('count:', page_count)

        if page > 1:
            driver.find_element(By.LINK_TEXT, 'Next page').click()
            driver.implicitly_wait(10)
        WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.CSS_SELECTOR, "div.searching-overlay")))
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "col-cik"))).click()
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "col-located"))).click()

        grid = driver.find_element_by_id('hits')
        driver.implicitly_wait(5)
        for i, row in enumerate(grid.find_elements_by_tag_name('tr'), start=1):
            row_data = {}
            if i == 1:
                continue
            file_id = ''
            file_name = ''
            try:
                preview_file = row.find_element_by_class_name('preview-file')
                file_id = preview_file.get_attribute('data-adsh').replace('-', '')
                file_name = preview_file.get_attribute('data-file-name')
            except NoSuchElementException:
                print ('error in preview------------')

            cik = row.find_element_by_class_name('cik').text
            filed = row.find_element_by_class_name('filed').text
            entity_name = row.find_element_by_class_name('entity-name').text
            sec_file_link = 'https://www.sec.gov/Archives/edgar/data/'+cik[-10:]+'/'+file_id+'/'+file_name
            print('########')
            print(sec_file_link)
            print('########')
            located = row.find_element_by_class_name('located').text

            entity_list = entity_name.split(' (')
            entity_name = entity_list[0]
            symbol = ''
            if len(entity_list) > 1:
                symbol = entity_list[1][:-1]
                symbol = symbol.split(',')[0]

            row_data['entity_name'] = entity_name
            row_data['file_link'] = sec_file_link
            row_data['located'] = located
            row_data['filed'] = filed
            row_data['cik'] = cik
            row_data['symbol'] = symbol
            data.append(row_data)
            # print('#_#_#__#_#_#')
        page += 1
    print(data)
    save_sec_data(data)
    return data


def save_sec_data(data):
    for item in data:
        print(item)
        location = item['located'].split(',')
        city = location[0]
        state = ''
        if len(location) > 1:
            state = location[1].strip()


        organization, created = Organization.objects.get_or_create(
            defaults={'organization_name': item['entity_name'], 'city': city, 'state': state,
                      'organization_symbol': item['symbol']},
            organization_symbol=item['symbol']
        )

        sec, created = Sec.objects.get_or_create(
            defaults={'sec_link': item['file_link'], 'cik': item['cik'], 'filed_date': item['filed'],
                      'company': organization},
            sec_link=item['file_link'],
        )
        print('------done--------')

    return True

# company_name, company_ticker, bloomberg_url

def scrape_sec_document(get_document_link):
    # get urls from sec table
    file_urls = get_document_link
    a = 0
    b = 0
    data = []
    for item in file_urls:
        b += 1
        print('---NEW---', b)
        file_url = item.sec_link
        print('-------------------------------------------Item Start----------------------------------------------')
        print(file_url)
        print('-------------------------------------------Item End----------------------------------------------')
        # data['website_source'] = file_url
        # TODO: handle connection error
        page = requests.get(file_url).content
        #soup = BeautifulSoup(page, 'html.parser')
        soup = BeautifulSoup(page, 'lxml')

        age_text = get_age_cell(soup)


        if age_text:
            print('age text:::'+age_text)
            try:
                table_officers = age_text.find_parent("table")
            except NoSuchElementException:
                a += 1
                print('count a:', a)
                print('-----table not found-----')
                continue
        else:
            a += 1
            print('count a:', a)
            print('AGE text::', age_text)
            print('---NOT AGE---')
            Sec.objects.filter(sec_link=file_url).update(is_scraped=1)
            continue
        # get keys
        keys_list = get_table_data(table_officers, 0, 1)
        values_list = get_table_data(table_officers, 1)
        if len(keys_list) == 0:
            keys_list = get_table_data(table_officers, 1, 2)
            values_list = get_table_data(table_officers, 2)

        names = []
        print('*************************Key List**********************************')
        print(keys_list)
        print(values_list)
        print('*************************Key List end**********************************')
        for value in values_list:
            res = dict()
            res['from'] = ''
            res['to'] = ''

            position_since = ['date', 'period', 'since']
            position_till = ['term', 'expire']
            position = ['position', 'title', 'office']
            if keys_list and keys_list[0] and len(value) == len(keys_list[0]):
                for i, key in enumerate(keys_list[0], start=0):
                    # res[key] = value[i]
                    if 'name' in key.lower() or 'person' in key.lower():
                        res['name'] = value[i]
                        res['sec_desc'] = get_bio_by_name(table_officers, value[i])

                    elif 'Age' in key:
                        res['age'] = value[i]
                    elif any(pos_text in key.lower() for pos_text in position_since):
                        res['from'] = value[i]
                    elif any(term_text in key.lower() for term_text in position):
                        res['position'] = value[i]
                    elif any(term_text in key.lower() for term_text in position_till):
                        res['to'] = value[i]
                res['company'] = item.company_id
                res['document_link'] = file_url

            else:
                print('-----key list not found-----')
                continue
            if len(res) > 0:
                res['is_scraped'] = 1
                # res['last_scraped'] = datetime.now()
                data.append(res)
                save_data(res)
        print('********************************')
        print('IS SCRAPED')
        print('********************************')
        Sec.objects.filter(sec_link=file_url).update(is_scraped=1)
            # print(res)

        # print('---DATA---')

        # for record in data:
        #
        #     print(record)
        #     position_since = ['date', 'period', 'term', 'since']
        #     d = [w for w in record if any(x in w.lower() for x in position_since)]
        #     print(d)
        #     if d and len(d) > 0:
        #         print(record[d[0]])

    # print('count LAST:', a)


    return HttpResponse(json.dumps(data), content_type="application/json")


def get_table_data(table_element, start=1, offset=None):
    res = []
    for row in table_element.find_all("tr")[start:offset]:  # fetch rows from start to offset
        if row:
            # get all td values if they are not empty
            # table has some empty columns to create space between columns
            res.append([cell.get_text(strip=True).replace(u'\xa0', u' ').replace('\n', ' ') for cell in row.find_all("td")
                        if any(cell.get_text(strip=True))])
    # table in sec document has some empty rows to show space between rows or to show line etc,
    # we are going to remove empty rows
    res = [sublist for sublist in res if any(sublist)]

    return res

def get_age_cell(soup):
    try:
        age_elements = soup.find_all(text=re.compile("Age"))
    except None:
        return None

    for elem in age_elements:
        if re.fullmatch('Age', elem.strip()):
            print('full', elem)
            return elem
    return None


def get_bio_by_names(table_officers, list_of_names):
    from bs4 import NavigableString, Tag
    import os
    element_for_siblings = None
    try:
        element_for_siblings = table_officers.find_parent("div")
    except:
        print('parent not found')
    data = {}
    for name in list_of_names:
        text = ''
        if element_for_siblings:
            next_siblings = element_for_siblings.next_siblings
        else:
            next_siblings = table_officers.next_siblings
        for count, sibling in enumerate(next_siblings, start=0):

            if isinstance(sibling, Tag):
                sec = 'ITEM'
                #sibling = get_element_text(sibling)


                # print(sibling)

                item_section = sibling.find(text=re.compile(sec))

                if item_section:
                    #print(get_element_text(sibling))
                    print('new section has started-------------------------------------------------------------------------------------------')
                    break
                else:
                    item_section = sibling.find(text=re.compile('Item'))
                if item_section:
                    #print(get_element_text(sibling))
                    print('new section has started-------------------------------------------------------------------------------------------')
                    break

                # text = sibling.find(text=re.compile(name))
                name = name.strip().replace('\n', ' ')
                full_name = name
                last_name = name.split(' ')[-1]
                if sibling.find(text=re.compile(full_name)) or sibling.find(text=re.compile(last_name)):
                    print('name is::', name)
                    print(get_element_text(sibling))
                    print('---------------')
                    text += get_element_text(sibling)
                    text += os.linesep
        data[name] = text
        # try:
        #     elem = table_officers.parent().find_next_siblings(text="a")
        # except:
        #     print('name not found')

        #print(elem)
    print(json.dumps(data, sort_keys=True, indent=4))

    # print(data)


def get_bio_by_name(executives_soup, profile_name):
    from bs4 import NavigableString, Tag
    import os
    element_for_siblings = None
    try:
        element_for_siblings = executives_soup.find_parent("div")
    except:
        print('parent not found')
    data = {}
    # for name in list_of_names:
    text = ''
    if element_for_siblings:
        next_siblings = element_for_siblings.next_siblings
    else:
        next_siblings = executives_soup.next_siblings
    for count, sibling in enumerate(next_siblings, start=0):

        if isinstance(sibling, Tag):
            sec = 'ITEM'

            item_section = sibling.find(text=re.compile(sec))

            if item_section:
                print('new section has started-------------------------------------------------------------------------------------------')
                break
            else:
                item_section = sibling.find(text=re.compile('Item'))
            if item_section:
                #print(get_element_text(sibling))
                print('new section has started-------------------------------------------------------------------------------------------')
                break

            # text = sibling.find(text=re.compile(name))
            name = profile_name.strip().replace('\n', ' ')
            full_name = name
            last_name = name.split(' ')[-1]
            if sibling.find(text=re.compile(full_name)) or sibling.find(text=re.compile(last_name)):
                # print('name is::', name)
                # print(get_element_text(sibling))
                # print('---------------')
                text += get_element_text(sibling)
                text += os.linesep
    # data[name] = text
        # try:
        #     elem = table_officers.parent().find_next_siblings(text="a")
        # except:
        #     print('name not found')

        #print(elem)
    # print(json.dumps(data, sort_keys=True, indent=4))

    # print(data)
    # import nltk
    # from nltk.tokenize import word_tokenize
    # from nltk.tag import pos_tag
    # import spacy
    # from spacy import displacy
    # from collections import Counter
    # import en_core_web_sm
    # nlp = en_core_web_sm.load()
    # r = nlp(text)
    # print('#_#_#__#_#_##__#_#_#_#_#_#__#__#_#_#_#_#_#')
    # # print([(X.text, X.label_) for X in r.ents])
    # total_str = ''
    # for tok in r:
    #     # print(tok.text, "-->", tok.dep_, "-->", tok.pos_)
    #     if tok.pos_ in ['PROPN', 'NOUN', 'NUM'] or tok.dep_ == 'ROOT' or (tok.pos_ == 'PUNCT' and tok.text == '.'):
    #         total_str += tok.text
    #         total_str += ' '
    #         # print(tok.text)
    # print (total_str)
    # print('222222222222222222222222#_#_#__#_#_##__#_#_#_#_#_#__#__#_#_#_#_#_#')
    # preprocess(text)
    return text


def get_element_text(element):
    return element.text.strip().replace('\n', ' ')


def preprocess(sent):
    import nltk
    nlp()
    for tok in doc:
        print(tok.text, "-->", tok.dep_, "-->", tok.pos_)

    # sent = nltk.word_tokenize(sent)
    # sent = nltk.pos_tag(sent)
    print(sent)
    return sent


def save_data(data):
    print('------------------------------SAVING DATA Start-----------------------------------------------------------------')
    print(data['name'])
    print('------------------------------SAVING DATA End-----------------------------------------------------------------')
    name = data['name'].split(' ')
    # name = re.sub(" \d+", " ", " ".join(re.findall(r"[a-zA-Z0-9]+", name_split))).strip()
    first_name = name[0]
    middle_name = ''
    last_name = name[len(name)-1]

    if len(name) > 2:
        middle_name = ' '.join(name[1:len(name)-1])
    desc = ''
    if data['sec_desc']:
        desc = data['sec_desc']

    contact, created = Contact.objects.update_or_create(
        defaults={'user_id': '1', 'first_name': first_name, 'middle_name': middle_name,
                  'last_name': last_name, 'description': desc},
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
    )

    document_link = data['document_link']
    social_profiles, created = SocialProfile.objects.update_or_create(
        platform_link=document_link,
        platform='sec',
        is_scraped='1',
        contact_id=contact.id,
    )

    s_name = 'sec'
    contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
        source_name=s_name,
        # source_website=data['website_source'],
    )
    contact_description, created = ContactDescription.objects.update_or_create(
        source_id=contact_scrape_source.id,
        description=desc,
        contact_id=contact.id,
        platform_id=social_profiles.id
    )
    if data['position']:
        job_from = data['from'] if data['from'] else ''
        job_to = data['to'] if data['to'] else ''

        job, created = Job.objects.update_or_create(
            job_title=data['position'],
            job_start_date=job_from,
            job_end_date=job_to,
            contact_id=contact.id,
            source_id=contact_scrape_source.id,
            platform_id=social_profiles.id
        )
        job.organization.add(data['company'])

def scrape_bloomberg_company_data_page(url, proxy, organization_symbol):
    

    user_data = {} 

    # options = webdriver.ChromeOptions()
    # options.add_argument('--disable-gpu')
    # options.add_argument("--no-sandbox")
    #caps = DesiredCapabilities().CHROME
    #caps["pageLoadStrategy"] = "eager"  #  interactive
    # profile = webdriver.chromeProfile()
    # from selenium import webdriver
    # from selenium.webdriver.chrome.options import Options
    # chrome_options = Options()
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('--disable-dev-shm-usage')     
    # proxy_ip = proxy['ip'] + ':' + proxy['port']
    #chrome_options.add_argument('--proxy-server=http://%s' % proxy_ip)
    #chrome_options.add_argument('--proxy-server=http://139.99.102.114:80')	
    # options = webdriver.FirefoxOptions()
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    # options.add_argument("--no-sandbox")
    # caps = DesiredCapabilities().FIREFOX
    # caps["pageLoadStrategy"] = "normal"  # complete
    # caps["pageLoadStrategy"] = "eager"  # interactive
    # caps["pageLoadStrategy"] = "none"
    # profile = webdriver.FirefoxProfile()
    # proxy_ip = proxy['ip'] + ':' + proxy['port']
    # options.add_argument('--proxy-server=http://%s' % proxy_ip)
    # driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, executable_path=r"/home/ec2-user/aw/altworkz/geckodriver")
    
    
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    caps["pageLoadStrategy"] = "eager"
    
    profile = webdriver.FirefoxProfile()
    proxy_ip = proxy['ip'] + ':' + proxy['port']
    options.add_argument('--proxy-server=http://%s' % proxy_ip)

    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, firefox_binary='/home/ec2-user/aw/altworkz/firefox/firefox/firefox')
    
    data = {}
    executives = []
    board_members = []
    board_members_info = []
    executive_teams_info = []
    driver.get(url)     
    data['platform'] = 'Bloomberg'
    data['profile_url'] = url
    no_expansion = ''

    try:
        company_not_found = driver.find_element_by_class_name('securityNotFound__4027cb76')
        print('Company not found')
        driver.close()
        return False
    except NoSuchElementException:
        company_not_found = None

    try:
        executive_module = driver.find_element_by_class_name("module")
    except:
        print('Module Not Found')
        driver.close()
        
        return False

    try:
        executive_module = driver.find_element_by_class_name("module")
        expan_wrap = executive_module.find_element_by_class_name('expansionWrap__44006736')
        elem = expan_wrap.find_element_by_class_name('expansionControls__cebb2de7')
        # WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "expansionControls__cebb2de7"))).click()
        elem.click()
        # elem.find_element_by_class_name('expansionControls__cebb2de7').click()

    except:
        no_expansion = driver.find_element_by_class_name("noExpansion__6b22d7f1")
        print('View more not found')

     #= driver.find_element_by_class_name('companyProfileLink__1d2ded78').get_attribute("href")

    try:
        company_title = driver.find_element_by_class_name('info__d075c560')
    except NoSuchElementException:
        print ('Element not found')
        driver.close()
        company_title = None
        return False

    try:
        company_description = driver.find_element_by_class_name('info__d075c560')
    except NoSuchElementException:
        print('company description')
        driver.close()
        company_description = None

    about_company_name = company_title.find_element_by_tag_name('h1').text
    company_descriptions = company_description.find_element_by_class_name('description__ce057c5c').text

    company_detail_containers = driver.find_element_by_class_name("infoTable__96162ad6")
    company_detail = {}
    for i, company in enumerate(company_detail_containers.find_elements_by_class_name('infoTableItem__1003ce53'), start=1):
        executive_title = company.find_element_by_tag_name('h2').text.lower()
        executive_detail = company.find_element_by_class_name('infoTableItemValue__e188b0cb').text
        company_detail[executive_title] = executive_detail

    # driver.implicitly_wait(8)
    try:
        if no_expansion is None:
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.expanded__1f24689a div.boardContainer__c8751b40")))
        board_containers = driver.find_element_by_class_name("boardWrap__8a218670")
        board_members_info = bloomberg_comapny_board_details(board_containers)
    except NoSuchElementException:
        board_members_info = []

    try:
        if no_expansion is None:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "div.expanded__1f24689a div.executivesContainer__7f9fc250")))
        executive_containers = driver.find_element_by_class_name("executivesWrap__7da4e15b")
        executive_teams_info = bloomberg_comapny_executive_details(executive_containers)
    except NoSuchElementException:
        executive_teams_info = []

    executives_list = board_members_info + executive_teams_info
    data.update([('company_details', company_detail)])
    data['company_details']['description'] = company_descriptions
    data['company_details']['organization_name'] = about_company_name
    data['company_details']['organization_symbol'] = organization_symbol
    data.update([('executives', executives_list)])
    # data.update([('board_members', board_members_info)])
    user_data = data
    print('********************************')
    print(user_data)
    print('********************************')
    driver.close()
    return user_data

def scrape_bloomberg_person_data_page(url, proxy, person_contact_id):
    user_data = {}
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    caps["pageLoadStrategy"] = "eager"
    
    profile = webdriver.FirefoxProfile()
    proxy_ip = proxy['ip'] + ':' + proxy['port']
    # proxy_ip = '95.0.206.216:8080'
    options.add_argument('--proxy-server=http://%s' % proxy_ip)
    print('*************Start Proxy IP*********************')
    print(proxy_ip)
    print('***************End Proxy IP*******************')
    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, firefox_binary='/home/ec2-user/aw/altworkz/firefox/firefox/firefox')
    data = {}
    board_memberships = []
    other_memberships = []
    awards = []
    publications = []
    education = []
    job_history = []
    driver.get(url)
    data['platform'] = 'Bloomberg'
    data['profile_url'] = url

    data['contact_id'] = person_contact_id

    print('Driver Link'+ url)

    wait = WebDriverWait(driver, 20)
    try:        
        executive_summary = driver.find_element_by_class_name('executiveSummary__eb728b4e')
        # executive_summary = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "executiveSummary__eb728b4e")))
        print(executive_summary)
    except NoSuchElementException:
        print ('Element not found')
        driver.close()
        executive_summary = None
        return False
    # except TimeoutException:
    #     print("Alert not present")
    
    try:
        profile_image = executive_summary.find_element_by_tag_name('img')
        data['profile_image'] = profile_image.get_attribute('src')
    except NoSuchElementException:
        data['profile_image'] = 'https://via.placeholder.com/110x110'

    name = executive_summary.find_element_by_class_name('name__300c1393').text
    data['name'] = name

    try:
        company_profile = driver.find_element_by_class_name('companyProfileLink__1d2ded78').get_attribute("href")
        company_pro_about = company_profile.rpartition('?')
        company_profile_link = company_pro_about[0][:-3]
        company_symbol = company_profile_link.replace("https://www.bloomberg.com/profile/company/", "")
    except NoSuchElementException:
        # print ('Element not found')
        driver.close()
        company_symbol = None
    data['company_symbol'] = company_symbol
    info_containers = driver.find_elements_by_class_name("container__00452967")
    for x, container in enumerate(info_containers, start=1):
        # if x == 1:
        try:
            container.find_element_by_class_name('expansionControls__cebb2de7').click()
        except:
            print('View more not found')
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
    driver.close()
    return user_data

def bloomberg_comapny_board_details (board_containers):
    board_members_details = []
    for i, board in enumerate(board_containers.find_elements_by_class_name('personListItem__99ede78e'), start=1):
        board_members = {}
        try:
            t = board.find_element_by_xpath("..")
            link = t.get_attribute("href")
        except NoSuchElementException:
            link = None
        try:
            person_name = board.find_element_by_class_name('name__c96644d1').text
            for k in person_name.split("\n"):
                name = " ".join(re.findall(r"[a-zA-Z0-9]+", k))
        except NoSuchElementException:
            name = None
        try:
            company_name = board.find_element_by_class_name('company__7f8639ea').text
        except NoSuchElementException:
            company_name = None
        try:
            profile = board.find_element_by_class_name('headshot__e8c048ca').get_attribute("style")
            profile_image_link = profile.replace("background-image: url(", "")
            profile_image_links = profile_image_link[:-3]
            profile_img_link = profile_image_links[1:]
        except NoSuchElementException:
            profile = None
            profile_img_link = None

        board_members.update([('role', 'Board Member'), ('link', link), ('name', name), ('designation', company_name), ('profile', profile_img_link)])
        board_members_details.append(board_members)
    return board_members_details

def bloomberg_comapny_executive_details(executive_containers):
    executive_members_details = []
    for i, executive in enumerate(executive_containers.find_elements_by_class_name('personListItem__99ede78e'), start=1):
        executive_details = {}
        try:
            t = executive.find_element_by_xpath("..")
            link = t.get_attribute("href")
        except NoSuchElementException:
            link = None
        try:
            profile = executive.find_element_by_class_name('headshot__e8c048ca').get_attribute("style")
            profile_image_link = profile.replace("background-image: url(", "")
            profile_image_links = profile_image_link[:-3]
            profile_img_link = profile_image_links[1:]
        except NoSuchElementException:
            profile = None
            profile_img_link = None

        try:
            person_name = executive.find_element_by_class_name('name__c96644d1').text
            for k in person_name.split("\n"):
                name = " ".join(re.findall(r"[a-zA-Z0-9]+", k))
        except NoSuchElementException:
            name = None
        try:
            designation = executive.find_element_by_class_name('title__cde0e39b').text
        except NoSuchElementException:
            designation = None
        executive_details.update([('role', 'Company Executive'),('link', link), ('profile', profile_img_link), ('name', name), ('designation', designation)])
        executive_members_details.append(executive_details)
    return executive_members_details

def save_bloomberg_person_details(data, socail_profiles_id):
    pers_name = data['name']
    final = re.sub(r'\W+', ' ', pers_name).strip()
    name = final.split(' ')
    first_name = name[0]
    middle_name = ''
    last_name = name[len(name) - 1]
    if len(name) > 2:
        middle_name = ' '.join(name[1:len(name) - 1])
    contact_id = data['contact_id']
    contact, created = Contact.objects.update_or_create(
        defaults={'user_id': '1', 'first_name': first_name, 'middle_name': middle_name,
                  'last_name': last_name, 'photo': data['profile_image']},
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
    )
    contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
        source_name='bloomberg',
    )
    source_id = contact_scrape_source.id
    organization_symbol = data['company_symbol']

    if len(data['education']) > 0:
        for education in data['education'][0]:
            school_bloomberg_person_method(education['institution'], education['title'], '', '', '', contact_id, source_id, socail_profiles_id)

    if len(data['job_history']) > 0:
        for job in data['job_history'][0]:
            organization_person_method(job['company'], organization_symbol, contact_id, source_id, socail_profiles_id, job['from'], job['to'], job['title'])

    if len(data['board_memberships']) > 0:
        for job in data['board_memberships'][0]:
            organization_person_board_memberships_method(job['company'], organization_symbol, contact_id, source_id, socail_profiles_id,
                                       job['from'], job['to'], job['title'])

    if len(data['other_memberships']) > 0:
        for job in data['other_memberships'][0]:
            organization_person_other_memberships_method(job['company'], organization_symbol, contact_id, source_id, socail_profiles_id,
                                       job['title'])

    SocialProfile.objects.filter(contact_id=contact_id).update(is_scraped=1)

def organization_person_method(organization_name, organization_symbol, contact_id, source_id, socail_profiles_id, job_start_date=None, job_end_date=None, job_title=None):
    if Organization.objects.filter(organization_name__iexact=organization_name).exists():
        email_error = 'Organization already exists'

    else:
        organization, created = Organization.objects.update_or_create(
            organization_name=organization_name
        )
        job, created = Job.objects.update_or_create(
            job_title=job_title,
            job_start_date=job_start_date,
            job_end_date=job_end_date,
            contact_id=contact_id,
            source_id=source_id,
            platform_id=socail_profiles_id
        )
        job.organization.add(organization.id)

def organization_person_board_memberships_method(organization_name, organization_symbol, contact_id, source_id, socail_profiles_id, job_start_date=None, job_end_date=None, job_title=None):
    if Organization.objects.filter(organization_name__iexact=organization_name).exists():
        email_error = 'Organization already exists'

    else:
        organization, created = Organization.objects.update_or_create(
            organization_name=organization_name
        )
        job, created = Job.objects.update_or_create(
            job_title=job_title,
            job_start_date=job_start_date,
            job_end_date=job_end_date,
            contact_id=contact_id,
            source_id=source_id,
            platform_id=socail_profiles_id
        )
        job.organization.add(organization.id)

def organization_person_other_memberships_method(organization_name, organization_symbol, contact_id, source_id, socail_profiles_id, job_title=None):
    if Organization.objects.filter(organization_name__iexact=organization_name).exists():
        email_error = 'Organization already exists'

    else:
        organization, created = Organization.objects.update_or_create(
            organization_name=organization_name
        )
        job, created = Job.objects.update_or_create(
            job_title=job_title,
            job_start_date='',
            job_end_date='',
            contact_id=contact_id,
            source_id=source_id,
            platform_id=socail_profiles_id
        )
        job.organization.add(organization.id)

def school_bloomberg_person_method(school_name, degree, school_start_year, school_end_year, abbreviation, contact_id, source_id, socail_profiles_id):
    school, created = School.objects.get_or_create(
        school_name=school_name,
        school_abbreviation=abbreviation,
        source_id=source_id,
        platform_id=socail_profiles_id
    )
    education, created = Education.objects.update_or_create(
        school_start_year=school_start_year,
        school_end_year=school_end_year,
        degree=degree,
        contact_id=contact_id,
        source_id=source_id,
        platform_id=socail_profiles_id
    )
    education.school.add(school.id)

def save_bloomberg_company_details(data):
    # name = data['name'].split(' ')
    # first_name = name[0]
    # middle_name = ''
    # last_name = name[len(name) - 1]
    #
    # if len(name) > 2:
    #     middle_name = ' '.join(name[1:len(name) - 1])
    #
    # SocialProfile.objects.update_or_create(
    #     contact_id=contact.id,
    #     bloomberg_profile_url=data['profile_url'],
    # )
    if len(data['company_details']) > 0:
        company_details = data['company_details']
        org_id =bloomberg_organization_method(company_details)
    if len(data['executives']) > 0:

        executives = data['executives']
        bloomberg_executives_members_method(executives, org_id)


    # if len(data['board_members']) > 0:
    #     board_members = data['board_members']
    #     bloomberg_board_members_method(board_members, org_id)
    # if len(data['executives']) > 0:
    #     executives = data['executives']
    #     bloomberg_executives_method(executives, org_id)


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
        else:
            row.update([('title', cols[0].text), ('company', cols[1].text)])
        data.append(row)

    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    return data

def bloomberg_organization_method(company_details=None):
    print('********************************')
    print(company_details)
    print('********************************')
    sector = None
    industry = None
    sub_industry = None
    address = None
    phone = None
    website = None
    organization_name = None
    no_of_employees = None
    founded = None
    if company_details is not None:
        organization_name = company_details['organization_name']
        sector = company_details['sector']
        industry = company_details['industry']
        sub_industry = company_details['sub-industry']
        address = company_details['address']
        phone = company_details['phone']
        website = company_details['website']
        number_of_employees = company_details['no. of employees']
        organization_symbol = company_details['organization_symbol']
        founded = company_details['founded']

    if Organization.objects.filter(organization_symbol=organization_symbol).exists():
        Organization.objects.filter(organization_symbol=organization_symbol).update(
            sector=sector,
            industry=industry,
            sub_industry=sub_industry,
            address=address,
            phone=phone,
            website=website,
            is_bloomberg_scraped='1',
            number_of_employees=number_of_employees,
            founded=founded,
        )
        organization_id = Organization.objects.filter(organization_symbol=organization_symbol).values('id')[0]['id']
        return organization_id

def bloomberg_executives_members_method(executives, org_id):
    first_name = None
    middle_name = None
    last_name = None
    photo = None
    bloomberg_url = None
    job_title = None
    if executives is not None:

        for index, executives in enumerate(executives, start=1):

            person_name = executives['name']
            name = person_name.split(' ')
            first_name = name[0]
            middle_name = ''
            last_name = name[len(name) - 1]
            if len(name) > 2:
                middle_name = ' '.join(name[1:len(name) - 1])

            bloomberg_url = executives['link']
            if executives['designation'] is not None:
                job_title = executives['designation']
            else:
                job_title = 'executives'
            photo = executives['profile']

            contact, created = Contact.objects.update_or_create(
                defaults={'user_id': '1', 'first_name': first_name, 'middle_name': middle_name,
                          'last_name': last_name, 'photo': photo},
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
            )

            contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                source_name='bloomberg',
            )
            source_id = contact_scrape_source.id

            if bloomberg_url:
                SocialProfile.objects.update_or_create(
                    defaults={'platform_link': bloomberg_url, 'platform': 'bloomberg','is_scraped':'0'},
                    contact_id=contact.id,
                    platform_link__iexact=bloomberg_url,

                )
            # else:
            #     job_title = executives['role']
            #     job, created = Job.objects.update_or_create(
            #         defaults={'job_title': job_title},
            #         job_title__iexact=job_title,
            #         contact_id=contact.id,
            #         source_id=source_id
            #     )
            #     job.organization.add(org_id)

def scrape_yahoo_links(request):

    get_organization_symbol = Organization.objects.exclude(organization_symbol__isnull=True).exclude(
        is_yahoo_scraped=1).order_by('id')[0:50]
    print('***********************scrape yahoo')

    for symbol in get_organization_symbol:
        if symbol.organization_symbol == '':
            print(symbol.organization_symbol)
            continue
        else:

            organization_symbol = symbol.organization_symbol
            organization_id = symbol.id
            print('---------------------------Company Link----------------------------')
            print('https://finance.yahoo.com/quote/' + symbol.organization_symbol.strip() + '/profile/')
            url = 'https://finance.yahoo.com/quote/' + symbol.organization_symbol.strip() + '/profile/'
            # url = 'https://finance.yahoo.com/quote/KSHB/profile/'
            # organization_symbol = 'KSHB'
            # organization_id = '4'
            Organization.objects.filter(organization_symbol=organization_symbol).update(is_yahoo_scraped=1)

            profile_data = scrape_yahoo_page(url, organization_symbol)

            if profile_data is not False:
                print(profile_data)
                save_yahoo_details(profile_data, organization_id)


def scrape_yahoo_page(url, organization_symbol):
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    caps["pageLoadStrategy"] = "eager"

    profile = webdriver.FirefoxProfile()
    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, firefox_binary='/home/ec2-user/aw/altworkz/firefox/firefox/firefox')

    data = {}
    executives = []
    driver.get(url)
    data['platform'] = 'yahoo'
    data['profile_url'] = url
    # driver.implicitly_wait(10)
    try:
        info_containers = driver.find_element_by_class_name("quote-subsection")
    except:
        driver.close()
        return False

    executives_details = []
    for i, executives in enumerate(info_containers.find_elements_by_tag_name('tbody tr'), start=1):
        row = {}
        cols = executives.find_elements_by_tag_name('td')
        # row.update([('name', cols[0].text), ('title', cols[1].text), ('pay', cols[2].text), ('exercised', cols[3].text), ('born', cols[4].text)])
        row.update([('name', cols[0].text), ('title', cols[1].text)])
        executives_details.append(row)
    data.update([('executives', executives_details)])
    user_data = data
    driver.close()
    return user_data

def save_yahoo_details(data, organization_id):
    platform_link = data['profile_url']
    if len(data['executives']) > 0:
        executives = data['executives']
        yahoo_executives_members_method(executives, platform_link, organization_id)

def yahoo_executives_members_method(executives, platform_link, organization_id):
    first_name = None
    middle_name = None
    last_name = None
    photo = None
    yahoo_url = None
    job_title = None
    for index, executives in enumerate(executives, start=1):
        person_name = executives['name']

        nlp = spacy.load("en_core_web_sm")
        doc = nlp(person_name)

        # document level
        # ents = [(e.text, e.label_, e.kb_id_) for e in doc.ents]
        persons = [ent.text for ent in doc.ents if ent.label_ == 'PERSON']
        person_str = ""
        for person in persons:
            person_str += person
        pers_name = person_str
        final = re.sub(r'\W+', ' ', pers_name).strip()
        full_name = final.split(' ')
        first_name = full_name[0]
        middle_name = ''
        last_name = full_name[len(full_name) - 1]
        if len(full_name) > 2:
            middle_name = ' '.join(full_name[1:len(full_name) - 1])
        if full_name is not None:
            contact, created = Contact.objects.update_or_create(
                defaults={'user_id': '1', 'first_name': first_name, 'middle_name': middle_name,
                          'last_name': last_name},
                first_name=first_name,
                middle_name=middle_name,
                last_name=last_name,
            )

            contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                source_name='yahoo',
            )
            source_id = contact_scrape_source.id

            yahoo_url = platform_link
            social_profiles, created = SocialProfile.objects.update_or_create(
                # defaults={'platform_link': yahoo_url, 'platform': 'yahoo', 'is_scraped': '1', 'contact_id':contact.id},
                # platform_link__iexact=yahoo_url,
                platform_link=yahoo_url,
                platform='yahoo',
                is_scraped='1',
                contact_id=contact.id,
            )
            job_title = executives['title']
            job, created = Job.objects.update_or_create(
                # defaults={'job_title': job_title},
                # job_title__iexact=job_title,
                # contact_id=contact.id,
                # source_id=source_id
                job_title=job_title,
                source_id=source_id,
                job_start_date='',
                job_end_date='',
                contact_id=contact.id,
                platform_id=social_profiles.id
            )
            job.organization.add(organization_id)

def scrape_csv_contacts (id):
    user = User.objects.get(id=id)
    contacts = user.contacts.all()

    for contact in contacts:
        contact_id = contact.id
        first_name = contact.first_name
        middle_name = contact.middle_name
        last_name = contact.last_name
        name = first_name + ' ' + middle_name + ' ' + last_name
        social_profiles = SocialProfile.objects.filter(contact_id=contact_id)
        for social in social_profiles:
            social_platform_id = social.id
            if (social.platform not in ['bloomberg'] or social.is_scraped != 1):
                print('***********************Bloomberg///////////////////')
                print(social_platform_id)
                scrape_contacts_from_bloomberg(first_name, last_name, name, contact_id)
            if (social.platform not in ['sec'] or social.is_scraped != 1):
                print('***********************SEC///////////////////')
                person_jobs = Job.objects.filter(platform_id=social_platform_id)
                for job in person_jobs:
                    person_job = job.job_title
                    person_job_id = job.id
                    organizations = job.organization.all()
                    for organization in organizations:
                        person_org_name = organization.organization_name
                        print('*****************person org name*********************')
                        print(person_org_name)
                        scrape_contacts_from_sec(name, person_org_name)
            # else:
            #     print('CSV Contacts scrapped')

def scrape_contacts_from_bloomberg(first_name, last_name, name, contact_id):
    csv_name = name
    csv_first_name= first_name
    csv_last_name = last_name
    contact_id = contact_id
    proxies = get_proxies()
    proxy = random.choice(proxies)

    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    caps["pageLoadStrategy"] = "eager"

    profile = webdriver.FirefoxProfile()
    proxy_ip = proxy['ip'] + ':' + proxy['port']
    options.add_argument('--proxy-server=http://%s' % proxy_ip)

    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, firefox_binary='/home/ec2-user/aw/altworkz/firefox/firefox/firefox')

    url = 'https://www.bloomberg.com'
    driver.get(url)
    wait = WebDriverWait(driver, 20)
    user_data = []

    try:
        search_button = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "navi-bar__button--search"))).click()
        search_input = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "navi-search__input")))
        search_input.send_keys(csv_name)
    except NoSuchElementException:
        print('Search not found')
        driver.close()

    try:
        element_present = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "td.navi-search-results__section.navi-search-results__section--companies.navi-search-results__section--hide")))

    except TimeoutException:
        print("Alert not present")

    finally:
        search_person = driver.find_element_by_class_name('navi-search-results__section--people')
        search_person_details = search_person.find_element_by_class_name("navi-search-results__item")
        data = []
        for x, container in enumerate(search_person.find_elements_by_class_name('navi-search-results__item'), start=1):
            row = {}
            link = container.find_element_by_class_name('navi-search-results__link').get_attribute("href")
            name = container.find_element_by_class_name('navi-search-results__link').text
            row.update([('link', link), ('name', name)])
            data.append(row)

    driver.close()
    print('get Person data from search')
    if data is not None:
        for index, person in enumerate(data, start=1):
            person_name = person['name']
            person_link = person['link']
            final = re.sub(r'\W+', ' ', person_name).strip()
            person_full_name = final.split(' ')
            person_first_name = person_full_name[0]
            person_middle_name = ''
            person_last_name = person_full_name[len(person_full_name) - 1]
            if len(person_full_name) > 2:
                person_middle_name = ' '.join(person_full_name[1:len(person_full_name) - 1])
            person_first_last_name = person_first_name + person_last_name
            csv_first_last_name = csv_first_name + csv_last_name
            print('************************Person Name************************')
            print(person_first_name)
            print(person_last_name)
            print('************************CSV Name************************')
            print(csv_first_name)
            print(csv_last_name)
            if person_name is not None:
                if csv_first_last_name in person_first_last_name:
                    print('Person Name Matched')
                    profile_data = scrape_contacts_from_bloomberg_data_page(person_link, proxy, contact_id)
                    print(profile_data)
                    if profile_data is not False:
                        save_bloomberg_person_details_for_csv(profile_data)
                else:
                    print('Person Name not Matched')

def scrape_contacts_from_bloomberg_data_page(url, proxy, person_contact_id):
    user_data = {}
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument("--no-sandbox")
    caps = DesiredCapabilities().FIREFOX
    caps["pageLoadStrategy"] = "eager"

    profile = webdriver.FirefoxProfile()
    proxy_ip = proxy['ip'] + ':' + proxy['port']
    options.add_argument('--proxy-server=http://%s' % proxy_ip)

    # driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, firefox_binary='/home/ec2-user/aw/altworkz/firefox/firefox/firefox')
    driver = webdriver.Firefox(firefox_profile=profile, desired_capabilities=caps, options=options, firefox_binary='/home/ec2-user/aw/altworkz/firefox/firefox/firefox')
    data = {}
    board_memberships = []
    other_memberships = []
    awards = []
    publications = []
    education = []
    job_history = []
    driver.get(url)
    data['platform'] = 'Bloomberg'
    data['profile_url'] = url

    data['contact_id'] = person_contact_id

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

    try:
        company_profile = driver.find_element_by_class_name('companyProfileLink__1d2ded78').get_attribute("href")
        company_pro_about = company_profile.rpartition('?')
        company_profile_link = company_pro_about[0][:-3]
        company_symbol = company_profile_link.replace("https://www.bloomberg.com/profile/company/", "")
    except NoSuchElementException:
        # print ('Element not found')
        driver.close()
        company_symbol = None
    data['company_symbol'] = company_symbol
    info_containers = driver.find_elements_by_class_name("container__00452967")
    for x, container in enumerate(info_containers, start=1):
        # if x == 1:
        try:
            container.find_element_by_class_name('expansionControls__cebb2de7').click()
        except:
            print('View more not found')
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
    driver.close()
    return user_data

def save_bloomberg_person_details_for_csv(data):
    print('in Bloomberg save')
    contact_id = data['contact_id']
    organization_symbol = data['company_symbol']
    person_profile_id = SocialProfile.objects.filter(
        contact_id=contact_id)
    for profile in person_profile_id:
        print(profile.platform)
        if(profile.platform == 'CSV'):
            platform_id = profile.id
            print(platform_id)
            print('Platform id in csv save bloomberg details')

            if len(data['job_history']) > 0:
                for job in data['job_history'][0]:
                    organization_person_csv_method(job['company'], organization_symbol, contact_id, platform_id, data, job['from'], job['to'], job['title'])

            if len(data['board_memberships']) > 0:
                for job in data['board_memberships'][0]:
                    organization_person_board_memberships_csv_method(job['company'], organization_symbol, contact_id, platform_id, data, job['from'], job['to'], job['title'])

            if len(data['other_memberships']) > 0:
                for job in data['other_memberships'][0]:
                    organization_person_memberships_csv_method(job['company'], organization_symbol, contact_id, platform_id, data, job['title'])
            SocialProfile.objects.filter(contact_id=contact_id).update(is_scraped=1)

        elif (profile.platform == 'Google Contact'):
            platform_id = profile.id
            print('Platform id in Google contact save bloomberg details')

            if len(data['job_history']) > 0:
                for job in data['job_history'][0]:
                    organization_person_csv_method(job['company'], organization_symbol, contact_id, platform_id, data, job['from'], job['to'], job['title'])

            if len(data['board_memberships']) > 0:
                for job in data['board_memberships'][0]:
                    organization_person_board_memberships_csv_method(job['company'], organization_symbol, contact_id, platform_id, data, job['from'], job['to'], job['title'])

            if len(data['other_memberships']) > 0:
                for job in data['other_memberships'][0]:
                    organization_person_memberships_csv_method(job['company'], organization_symbol, contact_id, platform_id, data, job['title'])
            SocialProfile.objects.filter(contact_id=contact_id).update(is_scraped=1)

        else:
            print('Contact scrapped')

def school_bloomberg_person_csv_method(school_name, degree, school_start_year, school_end_year, abbreviation, contact_id, source_id, socail_profiles_id):

    school, created = School.objects.get_or_create(
        school_name=school_name,
        school_abbreviation=abbreviation,
        source_id=source_id,
        platform_id = socail_profiles_id
    )
    education, created = Education.objects.update_or_create(
        school_start_year=school_start_year,
        school_end_year=school_end_year,
        degree=degree,
        contact_id=contact_id,
        source_id=source_id,
        platform_id = socail_profiles_id
    )
    education.school.add(school.id)

def organization_person_csv_method(organization_name, organization_symbol, contact_id, platform_id, data, job_start_date=None, job_end_date=None, job_title=None ):
    print('In job_history section')
    person_jobs = Job.objects.filter(platform_id=platform_id)
    for job in person_jobs:
        person_job = job.job_title
        person_job_id = job.id
        organizations = job.organization.all()
        for organization in organizations:
            person_org_name = organization.organization_name
            print('*****************person org name*********************')
            print(person_org_name)
            if job_title is not None:
                if(person_job in [job_title] or person_org_name in [organization_name]):
                    print('in Job section')
                    contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                        source_name='bloomberg',
                    )
                    source_id = contact_scrape_source.id
                    organization_symbol = data['company_symbol']
                    person_link = data['profile_url']

                    social_profiles, created = SocialProfile.objects.update_or_create(
                        defaults={'platform_link': person_link, 'platform': 'bloomberg',
                                  'is_scraped': 0, 'contact_id': contact_id},
                        platform_link__iexact=person_link,
                    )
                    person_profile_link = SocialProfile.objects.filter(platform='bloomberg').filter(
                        platform_link=person_link)

                    for person in person_profile_link:
                        socail_profiles_id = person.id
                        if len(data['education']) > 0:
                            for education in data['education'][0]:
                                school_bloomberg_person_csv_method(education['institution'], education['title'], '', '', '',
                                                                   contact_id, source_id, socail_profiles_id)
                        if organization_symbol is None:
                            organization_symbol= ''
                        organization, created = Organization.objects.update_or_create(
                            defaults={'organization_name': organization_name, 'organization_symbol': organization_symbol},
                            organization_name=organization_name,

                        )
                        job, created = Job.objects.update_or_create(
                            job_title=job_title,
                            job_start_date=job_start_date,
                            job_end_date=job_end_date,
                            contact_id=contact_id,
                            source_id=source_id,
                            platform_id=socail_profiles_id
                        )
                        job.organization.add(organization.id)

def organization_person_board_memberships_csv_method(organization_name, organization_symbol, contact_id, platform_id, data, job_start_date=None, job_end_date=None, job_title=None):
    print('In board_memberships section')
    person_jobs = Job.objects.filter(platform_id=platform_id)
    for job in person_jobs:
        person_job = job.job_title
        person_job_id = job.id
        organizations = job.organization.all()
        for organization in organizations:
            person_org_name = organization.organization_name
            print('*****************person org name*********************')
            print(person_org_name)
            if job_title is not None:
                if (person_job in [job_title] or person_org_name in [organization_name]):
                    print('in Job section')
                    contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                        source_name='bloomberg',
                    )
                    source_id = contact_scrape_source.id
                    organization_symbol = data['company_symbol']
                    person_link = data['profile_url']

                    social_profiles, created = SocialProfile.objects.update_or_create(
                        defaults={'platform_link': person_link, 'platform': 'bloomberg',
                                  'is_scraped': 0, 'contact_id': contact_id},
                        platform_link__iexact=person_link,
                    )
                    person_profile_link = SocialProfile.objects.filter(platform='bloomberg').filter(
                        platform_link=person_link)

                    for person in person_profile_link:
                        socail_profiles_id = person.id
                        if len(data['education']) > 0:
                            for education in data['education'][0]:
                                school_bloomberg_person_csv_method(education['institution'], education['title'], '', '',
                                                                   '',
                                                                   contact_id, source_id, socail_profiles_id)
                        if organization_symbol is None:
                            organization_symbol = ''
                        organization, created = Organization.objects.update_or_create(
                            defaults={'organization_name': organization_name,
                                      'organization_symbol': organization_symbol},
                            organization_name=organization_name,

                        )
                        job, created = Job.objects.update_or_create(
                            job_title=job_title,
                            job_start_date=job_start_date,
                            job_end_date=job_end_date,
                            contact_id=contact_id,
                            source_id=source_id,
                            platform_id=socail_profiles_id
                        )
                        job.organization.add(organization.id)

def organization_person_memberships_csv_method(organization_name, organization_symbol, contact_id, platform_id, data, job_title=None):
    print(' In other_memberships section')
    person_jobs = Job.objects.filter(platform_id=platform_id)
    for job in person_jobs:
        person_job = job.job_title
        person_job_id = job.id
        organizations = job.organization.all()
        for organization in organizations:
            person_org_name = organization.organization_name
            print('*****************person org name*********************')
            print(person_org_name)
            if job_title is not None:
                if (person_job in [job_title] or person_org_name in [organization_name]):
                    print('in Job section')
                    contact_scrape_source, created = ContactScrapeSource.objects.update_or_create(
                        source_name='bloomberg',
                    )
                    source_id = contact_scrape_source.id
                    organization_symbol = data['company_symbol']
                    person_link = data['profile_url']

                    social_profiles, created = SocialProfile.objects.update_or_create(
                        defaults={'platform_link': person_link, 'platform': 'bloomberg',
                                  'is_scraped': 0, 'contact_id': contact_id},
                        platform_link__iexact=person_link,
                    )
                    person_profile_link = SocialProfile.objects.filter(platform='bloomberg').filter(
                        platform_link=person_link)

                    for person in person_profile_link:
                        socail_profiles_id = person.id
                        if len(data['education']) > 0:
                            for education in data['education'][0]:
                                school_bloomberg_person_csv_method(education['institution'], education['title'], '', '',
                                                                   '',
                                                                   contact_id, source_id, socail_profiles_id)
                        if organization_symbol is None:
                            organization_symbol = ''
                        organization, created = Organization.objects.update_or_create(
                            defaults={'organization_name': organization_name,
                                      'organization_symbol': organization_symbol},
                            organization_name=organization_name,

                        )
                        job, created = Job.objects.update_or_create(
                            job_title=job_title,
                            job_start_date='',
                            job_end_date='',
                            contact_id=contact_id,
                            source_id=source_id,
                            platform_id=socail_profiles_id
                        )
                        job.organization.add(organization.id)

def scrape_contacts_from_sec(name, person_org_name):
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(executable_path='/home/ec2-user/aw/chrome/chromedriver', options=chrome_options)
    # url = 'https://www.sec.gov/edgar/search/#/q=%2522' + name + '%2522&category=custom&forms=10-K'
    url = 'https://www.sec.gov/edgar/search/#/q=%2522' + name + '%2522&category=custom&entityName=%2522' + person_org_name + '%2522&forms=10-K'
    print(url)
    data = []
    url = url
    driver.get(url)
    driver.implicitly_wait(20)

    WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.CSS_SELECTOR, "div.searching-overlay")))
    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "col-cik"))).click()
    except:
        print('no found')
        pass
    try:
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "col-located"))).click()
    except:
        print('no found')
        pass
    grid = driver.find_element_by_id('hits')
    for i, row in enumerate(grid.find_elements_by_tag_name('tr'), start=1):
        row_data = {}
        if i == 1:
            continue
        file_id = ''
        file_name = ''
        try:
            preview_file = row.find_element_by_class_name('preview-file')
            file_id = preview_file.get_attribute('data-adsh').replace('-', '')
            file_name = preview_file.get_attribute('data-file-name')
        except NoSuchElementException:
            print('error in preview------------')

        cik = row.find_element_by_class_name('cik').text
        filed = row.find_element_by_class_name('filed').text
        entity_name = row.find_element_by_class_name('entity-name').text
        sec_file_link = 'https://www.sec.gov/Archives/edgar/data/' + cik[-10:] + '/' + file_id + '/' + file_name
        print('########')
        print(sec_file_link)
        print('########')
        located = row.find_element_by_class_name('located').text

        entity_list = entity_name.split(' (')
        entity_name = entity_list[0]
        symbol = ''
        if len(entity_list) > 1:
            symbol = entity_list[1][:-1]
            symbol = symbol.split(',')[0]

        row_data['entity_name'] = entity_name
        row_data['file_link'] = sec_file_link
        row_data['located'] = located
        row_data['filed'] = filed
        row_data['cik'] = cik
        row_data['symbol'] = symbol
        # scrape_sec_contacts(row_data['file_link'], row_data['symbol'], name)
        data.append(row_data)
    save_sec_link_details_for_csv(data)

def save_sec_link_details_for_csv(data):
    for item in data:
        print(item)
        location = item['located'].split(',')
        city = location[0]
        state = ''
        if len(location) > 1:
            state = location[1].strip()

        organization, created = Organization.objects.get_or_create(
            defaults={'organization_name': item['entity_name'], 'city': city, 'state': state,
                      'organization_symbol': item['symbol']},
            organization_symbol=item['symbol']
        )

        sec, created = Sec.objects.get_or_create(
            defaults={'sec_link': item['file_link'], 'cik': item['cik'], 'filed_date': item['filed'],
                      'company': organization},
            sec_link=item['file_link'],
        )
        get_document_link = Sec.objects.filter(is_scraped=0).filter(sec_link=item['file_link'])
        scrape_sec_document(get_document_link)
        print('------done--------')

    return True


def get_proxies():
    # proxies_req = urllib2.Request('https://www.sslproxies.org/')
    proxies_req = urllib2.Request('https://free-proxy-list.net/')
    proxies_req.add_header('User-Agent', ua.random)
    proxies_doc = urllib2.urlopen(proxies_req).read().decode('utf8')
   

    soup = BeautifulSoup(proxies_doc, 'html.parser')
    pro = soup.find_all("td")
    #print("show",pro[0]).string
    proxies_table = soup.find("table", {"class": "table table-striped table-bordered"})
    #proxies_table = soup.find_all("table",_class='table table-striped table-bordered')
   

    #sel = soup.find('option', attrs={'name': 'proxylisttable_length'})
    # sel['selected'] = '80'

    
    # Save proxies in the array
    for row in proxies_table.tbody.find_all('tr'):
        proxies.append({
            'ip': row.find_all('td')[0].string,
            'port': row.find_all('td')[1].string
        })
    
    return proxies
