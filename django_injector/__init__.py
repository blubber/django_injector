from .scope import RequestScope, request_scope


__version__ = '0.0.2'


__all__ = ['RequestScope', 'request_scope']
default_app_config = 'django_injector.apps.DjangoInjectorConfig'
