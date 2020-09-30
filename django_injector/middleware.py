from django.apps import apps as django_apps
from django.utils.deprecation import MiddlewareMixin

from django_injector.scope import RequestScope


class DjangoInjectorMiddleware(MiddlewareMixin):
    def process_request(self, request):
        app = django_apps.get_app_config('django_injector')
        app.injector_module.set_request(request)

        request_scope = app.injector.get(RequestScope)
        request_scope.prepare()

        try:
            return self.get_response(request)
        finally:
            request_scope.cleanup()