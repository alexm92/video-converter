from django.http import HttpResponse
from django.template import RequestContext, loader

def home(request):
    # View code here...
    t = loader.get_template('templates/base.html')
    c = RequestContext(request, {'foo': 'bar'})
    return HttpResponse(t.render(c))
