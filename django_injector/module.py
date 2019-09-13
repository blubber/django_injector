import threading
import weakref

from django.conf import Settings, settings
from django.http import HttpRequest

from injector import Module, singleton


class DjangoInjectorModule(Module):

    def __init__(self):
        self._local = threading.local()

    def set_request(self, request):
        self._local.request = request

        if request:
            weakref.finalize(request, self.set_request, None)

    def configure(self, binder) -> None:
        binder.bind(Settings, to=settings, scope=singleton)
        binder.bind(HttpRequest, to=lambda: self._local.request)
