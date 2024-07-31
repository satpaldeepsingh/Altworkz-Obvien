from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse, FileResponse
from django.shortcuts import render, redirect
import csv
import io
import re
from csv import DictReader
from django.contrib import messages
from contacts_import.forms import ImportCSVForm
from accounts.models import Profile
from contacts_import.models import Contact, Job, School, ContactScrapeSource, ContactDescription, Organization, \
    Education, Tag, ContactTag, SocialProfile, ContactDegree, PersonofInterest, ContactEmail, ContactNumber, \
    ContactSocialPlatform
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import quote
from io import TextIOWrapper
from querystring_parser import parser
from scrape_web.views import scrape_csv_contacts
import threading
import requests
import tweepy

from django.conf import settings
from django.http import HttpResponseRedirect

from contextlib import redirect_stdout
from pprint import pprint

# oauth_token = '2bqgyafUPQSSRDB9IFLN1I7Ah'
# oauth_token_secret ='Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24'
auth = tweepy.OAuth1UserHandler('2bqgyafUPQSSRDB9IFLN1I7Ah','Ucq599xJI8sdgBEM6atoHR21m9xla4ibtSn5Pj14BUpVFjYK24' )
oauth_callback_confirmed=True
def index(request):
    # return HttpResponse("sdfsd",request)
    
    redirect(request,auth.get_authorization_url(signin_with_twitter=True))

  
    print("auth ", auth)
    #print("request oauth_token ", request.GET.get('oauth_token'))
    #print("request oauth_token_secret ", request.GET.get('oauth_verifier'))

    return HttpResponse("Look into console index<br>")

    
    
    


def twitter_callback__(request):

    print("access token ", auth.get_access_token(request.GET.get('oauth_verifier')))
    
   
    #url = auth.get_authorization_url(signin_with_twitter=True)

    #print("URL ", url)
    print("request oauth_token ", request.GET.get('oauth_token'))
    print("request oauth_verifier ", request.GET.get('oauth_verifier')) 

    # access_token, access_token_secret = auth.get_access_token(request.GET.get('oauth_verifier'))

    api = tweepy.API(auth)
    
    print("api ", api.get_friends())
    
    #if 'access_token' in request.session:

    
  
    
    return HttpResponse("Look into console<br>")
    
def twitter_callback(request):

    from contextlib import redirect_stdout
    print("TRYING here")
    print("TOKEN", request.GET.get('oauth_verifier'))

    context = {}
    
    friends_cursor = -1 if request.GET.get('cursor', None) is None else request.GET.get('cursor')

    oauth_token = request.GET.get('oauth_verifier')
    oauth_token_secret = request.GET.get('oauth_verifier')
        # if 'request_token' in request.session:

    prev_oauth_verifier = ''
    prev_oauth_token = ''
    
    if request.GET.get('oauth_token'):
        prev_oauth_token = request.GET.get('oauth_token')
    
    if request.GET.get('oauth_verifier'):
        prev_oauth_verifier = request.GET.get('oauth_verifier')
    
    for key, value in request.session.items():
        print('{} => {}'.format(key, value))    
    print("Request Session ", (request.session))
    pprint(request.session)
    print("\n-----------------------------------------\n")

    print("trying to run tweepy API................")

    api = tweepy.API(auth)
    
    try:
        for friend in api.get_friends():
            print("friend ", friend._json['name'])  
            
        twitter_friends, prev_next_friends_cursor = get_friends_list(auth, friends_cursor)
        twitter_followers = get_followers_list(auth)
        

        for twitter_friend in twitter_friends:
        
            twitter_friend['connection_strength'] = '<span style="color:#fd6e6e">Out of Network</span> (Followed by you)' 
        
            for twitter_follower in twitter_followers:
            
                if twitter_follower['id'] == twitter_friend['id']:
                
                    twitter_friend['connection_strength'] = '<span style="color:#56b36a">1st</span> (Followed and following)' 
                    break

                    
        context['twitter_friends'] = twitter_friends
        context['twitter_followers'] = twitter_followers
        context['friends_cursor'] = prev_next_friends_cursor
        context['current_cursor'] = friends_cursor
            
        return render(request, "twitter/index.html", context)        
    except Exception as e:
        return HttpResponse(e)
           
def get_friends_list (auth, cursor):
    import tweepy
    
    friends_list = []
    
    api = tweepy.API(auth)
    
    print("cursor ", cursor)
    user_friends = api.get_friends(cursor=cursor)
    
    if len(user_friends) > 1:
        
        for user_friend in user_friends[0]:
        
            friend_info = user_friend._json
        
            #friends_list.append(friend_info)

            friends_list.append({'id': friend_info['id'], 'name': friend_info['name'], 'description': friend_info['description'], 'photo': friend_info['profile_image_url_https'], 'org': '', 'job_title': '', 'screen_name': friend_info['screen_name'], 'location': friend_info['location']})
        
        prev_next_cursors = user_friends[1]
        
    
    
    return friends_list, prev_next_cursors

def get_followers_list (auth):
    import tweepy
    
    followers_list = []
    
    api = tweepy.API(auth)
        
    for user_follower in api.get_followers():
    
        user_follower = user_follower._json
    
        # friends_list.append({'name': friend_info['name']})
        # friends_list.append(friend_info)
            
        followers_list.append({'id': user_follower['id'], 'name': user_follower['name'], 'photo': user_follower['profile_image_url_https'], 'org': '', 'job_title': '', 'screen_name': user_follower['screen_name'], 'location': user_follower['location']})
                
    return followers_list    
    
    
    
    
    