from django.apps import apps as django_apps

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
            try:
                return app_injector.call_with_injection(view_func, args=view_args, kwargs=view_kwargs)
            finally:
                request_scope.cleanup()
        return view_func(*view_args, **view_kwargs)
