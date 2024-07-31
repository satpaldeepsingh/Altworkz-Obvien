from django.core import serializers
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, Http404
import json
from search_history.models import SearchTerm, ContactViewHistory
from django.contrib.auth.models import User
from contacts_import.models import Contact, FeedbackSearchTerm, UserFeedback
from querystring_parser import parser


def save_search(request):
    return render(request, "search/index.html")

def save_search_result(request):

    if request.is_ajax():

        search_str = request.GET.get('search_str', None)
        params_dict = parser.parse(request.GET.urlencode())
        filters = params_dict.get('filters', None)
        seach_name= request.GET.get('seachName', None)
        filter = json.dumps(filters)
        filter_weights = params_dict.get('filter_weights', None)

        # if filter_weights:
        #     filter_weights_new = {filter_key.replace("_weightage", ""): filter_weights[filter_key] for filter_key in filter_weights}
        #     filter_weights = filter_weights_new

        search_term, created = SearchTerm.objects.update_or_create(
            search_term=search_str,
            filters=filter,
            search_term_name=seach_name,
            filter_weights=json.dumps(filter_weights)
        )
        print(search_term.users.add(request.user.id))
        return JsonResponse({"data": True})
    else:
        print("else: ")
    return JsonResponse(True, safe=False)

def delete_search_result(request):
    if request.is_ajax():
        search_id = request.GET.get('seachId', None)
        SearchTerm.objects.filter(id=search_id).delete()

        return JsonResponse({"data": True})
    else:
        print("else: ")
    return JsonResponse(True, safe=False)

def get_search_feedback (request):

    if request.is_ajax():

        return JsonResponse(list(UserFeedback.objects.filter(user=request.user.id).filter(feedback_search_term__search_term=request.GET.get('search_str')).values('contact', 'feedback')), safe=False)

    raise Http404('Invalid request')

def search_like(request):
    if request.is_ajax():
        search_key = request.GET.get('search_key', None)
        contant_id = request.GET.get('contant_id', None)
        thumbs_up = request.GET.get('thumbs_up', None)
        thumbs_down = request.GET.get('thumbs_down', None)
        thumbs_maybe = request.GET.get('thumbs_maybe', None)


        feedback_search_term, created = FeedbackSearchTerm.objects.update_or_create(
            defaults={'search_term': search_key},
            search_term = search_key
        )
        if thumbs_up is not None:
            feedback = thumbs_up
        elif thumbs_down is not None:
            feedback = thumbs_down
        else:
            feedback = thumbs_maybe
        user_feedback, created = UserFeedback.objects.update_or_create(
            defaults={'feedback': feedback, 'contact_id':contant_id,
                      'feedback_search_term_id':feedback_search_term.id,'user_id':request.user.id},

            contact_id = contant_id,
            feedback_search_term_id = feedback_search_term.id,
            user_id = request.user.id,
        )

        return JsonResponse({"data": True})

    else:
        print("else: ")
    return JsonResponse(True, safe=False)

def save_viewed_contact (request):

    if request.is_ajax():

        user_id = request.user.id
        contact_id = request.GET.get('contact_id')

        cvh = ContactViewHistory(contact_id=contact_id, user_id=user_id)
        cvh.save()

        return JsonResponse({'contact_saved': True})

    raise Http404("Invalid page")
