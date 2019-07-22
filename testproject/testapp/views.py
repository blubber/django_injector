from django.http import HttpResponse
from injector import inject


@inject
def inject_works(request, content: str):
    assert content == 'this is an injected string'
    return HttpResponse()
