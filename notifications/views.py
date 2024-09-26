from django.shortcuts import render
from django.http import HttpResponse
from .tasks import test_task
# Create your views here.
def test(request):
    test_task.delay()
    return HttpResponse("Done")