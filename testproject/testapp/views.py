from django.http import HttpResponse
from django_injector import inject


@inject
def inject_works(request, content: str):
    assert content == 'this is an injected string'
    return HttpResponse()
