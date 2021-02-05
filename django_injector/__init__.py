import functools
from importlib import import_module
from inspect import ismethod
import logging
import threading
from typing import Any, Callable, List, Optional, cast, get_type_hints
import warnings

from django.apps import AppConfig, apps
from django.conf import Settings, settings
from django.core import management
from django.core.handlers.asgi import ASGIRequest
from django.http import HttpRequest
from django.template.engine import Engine
from django.urls import URLPattern, URLResolver, get_resolver
from django.utils.module_loading import import_string
from django.views.decorators.csrf import csrf_exempt

from injector import (
    Binder,
    Injector,
    Module,
    Provider,
    ScopeDecorator,
    ThreadLocalScope,
    inject,
    singleton,
)


__version__ = '0.2.1'
__all__ = ['RequestScope', 'request']
default_app_config = 'django_injector.DjangoInjectorConfig'
logger = logging.getLogger(__name__)


class DjangoInjectorConfig(AppConfig):

    name = 'django_injector'

    def ready(self) -> None:
        self.django_module = DjangoModule()
        self.injector = Injector([self.django_module])

        for mod_str in getattr(settings, 'INJECTOR_MODULES', []):
            module = import_string(mod_str)
            if isinstance(module, type) and issubclass(module, Module):
                module = module()
            self.injector.binder.install(module)

        resolver = get_resolver()
        process_resolver(resolver, self.injector)

        engine = Engine.get_default()
        engine.template_context_processors = tuple(process_list(
            engine.template_context_processors,
            self.injector
        ))

        patch_command_loader(self.injector)


def inject_request_middleware(get_response: Callable) -> Callable:
    app = apps.get_app_config('django_injector')

    def middleware(request: HttpRequest) -> Any:
        app.django_module.set_request(request)
        return get_response(request)

    return middleware


inject_request_middleware.async_callable = True  # type: ignore


def DjangoInjectorMiddleware(get_response: Callable) -> Callable:
    warnings.warn(
        'django_injector.DjangoInjectorMiddleware is deprecated. Please update your settings '
        'to use djangoo_injector.inject_request_middleware instead',
        DeprecationWarning,
    )
    return inject_request_middleware(get_response)


def wrap_function(fun: Callable, injector: Injector) -> Callable:
    @functools.wraps(fun)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return injector.call_with_injection(callable=fun, args=args, kwargs=kwargs)
    return wrapper


def wrap_drf_view_set(fun: Callable, injector: Injector) -> Callable:
    cls = cast(Any, fun).cls
    actions = cast(Any, fun).actions
    initkwargs = cast(Any, fun).initkwargs

    # Code copied from DRFs ViewSet.as_view
    def view(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
        self = injector.create_object(cls, additional_kwargs=initkwargs)

        if 'get' in actions and 'head' not in actions:
            actions['head'] = actions['get']

        # We also store the mapping of request methods to actions,
        # so that we can later set the action attribute.
        # eg. `self.action = 'list'` on an incoming GET request.
        self.action_map = actions

        # Bind methods to actions
        # This is the bit that's different to a standard view
        for method, action in actions.items():
            handler = getattr(self, action)
            setattr(self, method, handler)

        self.request = request
        self.args = args
        self.kwargs = kwargs

        # And continue as usual
        return self.dispatch(request, *args, **kwargs)

    cast(Any, view).actions = actions
    cast(Any, view).cls = cls
    cast(Any, view).initkwargs = initkwargs

    # Django Rest Framework views are exempt from CSRF checks through the CSRF
    # middlware. Selective auth backends (session based authentication in particular)
    # may selectively enforce csrf protection.
    return csrf_exempt(view)


def wrap_class_based_view(fun: Callable, injector: Injector) -> Callable:
    cls = cast(Any, fun).view_class

    try:
        initkwargs = cast(Any, fun).view_initkwargs
    except AttributeError:
        return fun

    # Code copied from Django's django.views.generic.base.View
    # to enable injection into class based view constructors.
    def view(request: Any, *args: Any, **kwargs: Any) -> Any:
        self = injector.create_object(cls, additional_kwargs=initkwargs)
        self.setup(request, *args, **kwargs)
        if not hasattr(self, 'request'):
            raise AttributeError(
                "%s instance has no 'request' attribute. Did you override "
                "setup() and forget to call super()?" % cls.__name__
            )
        return self.dispatch(request, *args, **kwargs)

    cast(Any, view).view_class = cls
    cast(Any, view).view_initkwargs = initkwargs

    if hasattr(fun, 'cls'):
        # Django Rest Framework APIView's as_view returns a callable with a cls attribute
        # instead of view_class. If the original callable has a cls attribute, assume it's
        # DRF. In addition, DRF views are csrf exempt by default, the SessionAuthentication
        # auth backend will selectively apply CSRF protection.
        cast(Any, view).cls = cls
        view = csrf_exempt(view)

    return view


def instance_method_wrapper(im: Callable) -> Callable:
    @functools.wraps(im)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return im(*args, **kwargs)
    return wrapper


def wrap_fun(fun: Callable, injector: Injector) -> Callable:

    if ismethod(fun):
        fun = instance_method_wrapper(fun)

    # This blockes needs to come before the block that checks for __call__
    # to prevent infinite recursion.
    if hasattr(fun, '__bindings__'):
        return wrap_function(fun, injector)

    if hasattr(fun, '__call__') and not isinstance(fun, type):
        try:
            type_hints = get_type_hints(fun)
        except (AttributeError, TypeError):
            # Some callables are not supported by get_type_hints:
            # https://github.com/alecthomas/flask_injector/blob/master/flask_injector/__init__.py#L75
            wrap_it = False
        else:
            type_hints.pop('return', None)
            wrap_it = type_hints != {}
        if wrap_it:
            return wrap_fun(inject(fun), injector)

    if hasattr(fun, 'view_class'):
        return wrap_class_based_view(fun, injector)
    elif hasattr(fun, 'cls'):
        # Django Rest Framework ViewSet's as_view returns a callable that
        # does NOT have a view_class attribute. Instead it has a cls attribute.
        return wrap_drf_view_set(fun, injector)

    return fun


def process_resolver(resolver: URLResolver, injector: Injector) -> None:
    if resolver.callback:
        resolver.callback = wrap_fun(resolver.callback, injector)

    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLPattern) and pattern.callback:
            pattern.callback = wrap_fun(pattern.callback, injector)
        elif isinstance(pattern, URLResolver):
            process_resolver(pattern, injector)

    if resolver._populated:
        resolver._populate()


def patch_command_loader(injector: Injector) -> None:
    ''' Patches the management command loader to allow injection into management commands. '''
    # Original at:
    # https://github.com/django/django/blob/master/django/core/management/__init__.py#L33

    def load_command_class(app_name: str, name: str) -> None:
        module = import_module('%s.management.commands.%s' % (app_name, name))
        return injector.create_object(cast(Any, module).Command)

    management.load_command_class = load_command_class


def process_list(lst: List, injector: Injector) -> List:
    return [wrap_fun(f, injector) for f in lst]


class RequestScope(ThreadLocalScope):
    """A scope whose object lifetime is tied to a request."""

    def get(self, key: Any, provider: Provider) -> Any:
        app = apps.get_app_config('django_injector')
        request = app.django_module.get_request()

        if request is None:
            raise RuntimeError(
                'RequestScope.get was called without binding to a request. '
                'In order for RequestScope to work make sure '
                'django_injector.inject_request_middleware is in your MIDDLEWARES settings '
                'and make sure you are not running on an ASGI container like daphne. '
                'ASGI containers are not supported currently.'
            )
        return super().get(key, provider)


request = ScopeDecorator(RequestScope)


class DjangoModule(Module):

    def __init__(self, request_scope_class: type = RequestScope) -> None:
        self.request_scope_class = request_scope_class
        self._local = threading.local()

    def set_request(self, request: HttpRequest) -> None:
        if isinstance(request, ASGIRequest):
            if settings.DEBUG:
                logger.warning(
                    'Calling DjangoModule.set_request with a ASGIRequest will lead to '
                    'bad results because the asgi handler does not spawn a thread per '
                    'request. Ignoring call to set_request'
                )
            self._local.request = None
            return
        self._local.request = request

    def get_request(self) -> Optional[HttpRequest]:
        try:
            return self._local.request
        except AttributeError:
            return None

    def configure(self, binder: Binder) -> None:
        binder.bind(Settings, to=settings, scope=singleton)
        binder.bind(HttpRequest, to=lambda: self.get_request())
