from django.apps import apps as django_apps
from django.http import HttpRequest

import injector

from .scope import RequestScope


class DjangoInjectorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        view_args = (request,) + view_args
        app_injector = django_apps.get_app_config('django_injector').injector
        if injector.is_decorated_with_inject(view_func):
            request_scope = app_injector.get(RequestScope)
            request_scope.prepare()
            # We're calling request_scope.get for side effects here – we're relying on the fact,
            # that on the first get(HttpRequest, provider) call within a request scope the provided value
            # will be stored in the scope so that further injections of HttpRequest can work just fine.
            # This works in cooperation with DjangoInjectorModule doing binding of HttpRequest in the
            # request scope.
            request_scope.get(injector.BindingKey.create(HttpRequest), injector.InstanceProvider(request))
            try:
                return app_injector.call_with_injection(view_func, args=view_args, kwargs=view_kwargs)
            finally:
                request_scope.cleanup()
        return view_func(*view_args, **view_kwargs)
