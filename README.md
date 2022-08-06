# Django Injector

Add [Injector](https://github.com/alecthomas/injector) to Django.

Injector is a dependency-injection framework for Python, inspired by Guice. You can
[find Injector on PyPI](https://pypi.org/project/injector/) and
[Injector documentation on Read the Docs](https://injector.readthedocs.io/en/latest/). Django-Injector is
inspired by [Flask-Injector](https://github.com/alecthomas/flask_injector).

Django Injector support Django 3.2+ running on Python 3.7+ or Pypy 3.7+.

Django-Injector is compatiable with CPython 3.6+, Django 2.2+ and Django Rest Framework 3 (optional).

Github page: https://github.com/blubber/django_injector

PyPI package page: https://pypi.org/project/django-injector/


## Features

Django-Injector lets you inject dependencies into:

* Views (functions and class-based)
* Django template context processors
* Rest Framework views (functions and class-based)
* Rest Framework view sets

Injector uses Python type hints to define types.


## Installation

Django-Injector can be installed with pip:

`pip install django_injector`

After installation add `django_injector` to your `INSTALLED_APPS` and optionally enable
the request injection middleware.

``` python
INSTALLED_APPS = [
    ...
    'django_injector',
]

MIDDLEWARES = [
    ...
    'django_injector.inject_request_middleware',
]
```

The middleware enables the injection of the current request.

**WARNING:** The injection middleware only works on WSGI application containers. Enabling the
middleware on an ASGI container (like daphne) will result in an error.


## Example

``` python
from django.views.generic import View
from injector import inject
from rest_framework.views import APIView


class MyService:
    ...

def my_view(request, my_service: MyService):
    # Has access to an instance of MyService
    ...

class MyView(View):
    @inject
    def __init__(self, my_service: MyService):
        # Class based views require the @inject decorator to properly work with
        # Django-Injector. The injection also works on the setup method.
        self.my_service = my_service

class MyAPIView(APIView):  # Also works on ViewSet derivatives
    @inject
    def setup(self, request, my_service: MyService, **kwargs):
      # Injection on __init__ will result in a TypeError when using the HTML
      # renderer.
```

Context processors have the same signature as view functions and work in the same way. They should
be registered in the template options as usual.

It is also possible to use injection in management commands. In this case the injection
is done into the `__init__` method:

```python
from django.core.management import BaseCommand

from injector import inject

class Command(BaseCommand):

    @inject
    def __init__(self, my_service: MyService):
        self.my_service = my_service
        super().__init__()
```


## Injector Module support

Django Injector supports Injector modules, just add a `INJECTOR_MODULES` setting to your configuration
with a list of dotted paths to modules you want to load. The modules should either be callables that
accept a single argument, `binder` or subclasses of `injector.Module`. The modules will be loaded
when the injector Django app loads in the order they appear in the list. For example:

``` python
INJECTOR_MODULES = [
    'my_app.modules.configure_for_production',
    'my_app.modules.ServiceModule',
]
```


### DjangoModule

Django Injector comes with a built-in module named `DjangoModule` that is always loaded as the first
module. It provides a couple of bindings for Django built-in types, namely:

* `django.htt.HttpRequest`: The current request. This only works if `django_injector.inject_request_middleware`
is loaded and the application runs in a WSGI container.
* `django.conf.Settings`: Injects `django.conf.settings`.
