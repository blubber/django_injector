import injector
from django.http import HttpRequest

from .scope import request_scope


class DjangoInjectorModule(injector.Module):
    def configure(self, binder) -> None:
        # We don't specify what we bind *to* here – that's because we don't have access to the actual request
        # here. Instead we just specify the scope *and* when preparing the scope in the
        # DjangoInjectorMiddleware we manually inject the request instance into the scope.
        binder.bind(HttpRequest, scope=request_scope)
