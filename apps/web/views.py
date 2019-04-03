from django.http import HttpResponse

# Create your views here.


def home(request):
    # View code here...
    return HttpResponse('Hello')
