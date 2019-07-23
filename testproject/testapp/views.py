import random
from django.http import HttpRequest, HttpResponse
from django_injector import request_scope
from injector import inject


@inject
def inject_works(request, content: str):
    assert content == 'this is an injected string'
    return HttpResponse()


@request_scope
class RequestScopedService:
    def __init__(self):
        # We're using random numbers to make sure we can distinguish between services in
        # different scopes
        self.value = random.random()


@inject
def request_scope_works(request, service1: RequestScopedService, service2: RequestScopedService):
    # This makes sure that within a single request the scope will always return the same object
    assert service1 is service2

    # We return the id of the object we got in order for the code outside to verify that
    # objects change across requests
    return HttpResponse(str(service1.value))


class RequiresRequest:
    @inject
    def __init__(self, request: HttpRequest) -> None:
        self.request = request


@inject
def request_is_injectable(request, rr: RequiresRequest):
    assert rr.request is request
    return HttpResponse()
