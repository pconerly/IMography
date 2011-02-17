from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext, loader

def default(request):
    t = loader.get_template('index.html')

    c = RequestContext(request, {'foo': 'bar'})
    r = t.render(c)
    html = "<html><body><p>Test2</p></body></html>"
    return HttpResponse(r)
