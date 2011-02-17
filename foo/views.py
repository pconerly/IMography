from django.shortcuts import render_to_response
from django.http import HttpResponse
import time

def default(request):
    return render_to_response('index.html')

def success(request):
    now = time.time()
    html = "<html><body>It is now %s.</body></html>" % now
    return HttpResponse(html)

