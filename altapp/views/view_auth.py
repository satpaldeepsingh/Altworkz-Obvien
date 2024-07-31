from django.http.response import HttpResponse

def auth(request):
    return HttpResponse("Auth")