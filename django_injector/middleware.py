from django.apps import apps as django_apps

from django_injector.scope import RequestScope


def inject_request_middleware(get_response):
    app = django_apps.get_app_config('django_injector')

    def middleware(request):
        app.module.set_request(request)

        request_scope = app.injector.get(RequestScope)
        request_scope.prepare()

        try:
            return get_response(request)
        finally:
            request_scope.cleanup()

    return middleware
