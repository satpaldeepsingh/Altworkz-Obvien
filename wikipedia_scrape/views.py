from bs4 import BeautifulSoup
from django.http import HttpResponse , HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render
import requests
from .models import *
import pprint 
pp = pprint.PrettyPrinter(indent=4)
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

#------------------------------------------------------#
@csrf_exempt
def function_Search(request):
    if request.method == 'POST':
        search_str =request.POST.get('search')
        print("search_str===================>" , search_str)
        scrape_results_type(request , search_str)
        # return render(reverse('try_wiki_app:search-results', args=(search_str,)))

    return render(request , "searchcon.html")









# function Called from main function for type and Industry

def gettypeIndustryAndSave(labels,data,keyword,model):
  
   

    count = 0
    name = ''
    for label in labels:
        if label.get_text()==keyword:
         name = data[count].get_text()
        count +=1
         
    id = None
    if keyword=='Type' and name!='':
        type = model()
        type.type_name = name
        type.save()
        id = type.id
    elif keyword=='Industry' and name!='':
        industry = model()
        industry.industry_name = name
        industry.save()
        id = industry.id
    return id
    
# Main Function


def scrape_results_type( request , search_str ):

            print("search_str===================>" , search_str)
            res = requests.get( url=f'https://en.wikipedia.org/wiki/{search_str}')
            res.encoding = "utf-8"
            soup = BeautifulSoup(res.text  , 'html.parser')

            search_type={}
            search_type['label']= soup.select(".infobox-label")
            search_type['data']= soup.select(".infobox-data")
            
            typeId = gettypeIndustryAndSave(search_type['label'],search_type['data'],'Type',Type)
            industryId = gettypeIndustryAndSave(search_type['label'],search_type['data'],'Industry',Industry)
            scrape_results_information(request,soup,typeId,industryId)

            print("typeId===================",typeId)
            print("industryId===================",industryId)
            return
        




def scrape_results_information(request , soup ,typeId=None , industryId=None):
####################  NAME AND IMAGE ############################
    name = {}
    name['Name'] = soup.select("#firstHeading > span ")
    for name_of in name['Name']:
        name['Name'] = name_of.get_text()

    image = {}
    image['Image'] = soup.select("table.infobox a.image img[src]")
    for cov_img in image['Image']:
        name['Img'] = cov_img["src"]

    type_id2 = Type.objects.filter(id = typeId).values('id')
    industry_id2 = Type.objects.filter(id = industryId).values('id')


    if Information.objects.filter(name=name["Name"]):
        return HttpResponse(request, "The Data is already saved")
    else:
        Information_sa = Information.objects.create(name = name["Name"] , image = name['Img'] ,industry_key = None, type_key = None)
        Information_sa.save()
        Information_Id  = Information_sa.id
        scrape_results_Content_sub(request , soup , Information_Id)

    print("Industry===================>" , industry_id2)
    print("Type===================>" , type_id2)



 
def scrape_results_Content_sub(request , soup , Information_Id):

    object = dict()
    info_key=''
    obj_list2 = []
    obj_list1 = []


    i = ''
    toc2 = soup.findAll('span' , {'class': 'tocnumber'})

    for filter_data in toc2:
        key = filter_data.text
        info_key = key.replace('.' , "_")
        obj_list1.append(info_key)


    toc = soup.findAll('span' , {'class': 'toctext'})
    for info in toc:
        obj_list2.append(info.text)
    count = 0
    for i in obj_list1:
        object[i] = obj_list2[count]

        count += 1
    Info_ID = Information.objects.get(id = Information_Id)
    print("Information_Id===================>" , Info_ID)

    
    # '''---------------------------------------------------------<<<???>>>'''


    headingValue3 = ''
    headingValue4 = ''
    headingValue2 = ''
    foundH3 = False
    foundH4 = False
    foundH2 = False
    dict3 = {}

    about = {}
    dict3['Try'] = soup.select(".mw-parser-output >  h4 , h3 , h2 , p ")
    for para in dict3['Try']:

        #h3
        if para.name == 'h3':
            
            headingValue3 = para.get_text()
            about[headingValue3]  = ''
            foundH3 = True  

        # h4
        if para.name == 'h4':
            headingValue4 = para.get_text()
            about[headingValue4] = ''
            foundH4 = True  
            
        if para.name == 'h2':
            headingValue2 = para.get_text()
            about[headingValue2] = ''
            foundH2 = True  
        if para.name=='p' :
            if foundH3:
                about[headingValue3] += para.get_text()

            if foundH4:
                about[headingValue4] += para.get_text() 

            if foundH2 and not foundH3 and not foundH4:
                about[headingValue2] += para.get_text() 

    
    for keys , value in object.items():
        if len(keys)==1:
            sve_Content = Content_type.objects.create(keyID = keys , keyValue = value ,Info_Key = Info_ID)
            save_Content.save()
            save_content_ID = save_Content.id
            
        if len(keys)>=1:
            for keyss , values  in about.items():
                if keyss==value:
                    if values != '':
                        # print()
                        print("keyss===================>" , keyss ,  "VALUES================>" , value)
                        content_type =  Content_type.objects.all().get(id=save_content_ID)
                        level_length = len(keys.split("_"))
                        SubContent_sa = SubContent_type.objects.create(Sub_keyID = keys , Sub_keyValue = keyss , SubKey_Description = values  , level_Info =level_length,Content_Key = content_type)
                        SubContent_sa.save()
   