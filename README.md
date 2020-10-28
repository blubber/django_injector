# Django injector

Django injector is an app for Django that integrates [injector](https://github.com/alecthomas/injector)
with Django, enabling dependency inje tion.

Injector is a simple and easy to use dependency injection framework.


## Installation

```python
$ pip install django_injector
```

To enable injec tion of `HttpRequest` objects you must add 
`django_injector.inject_request_middleware` to `settings.MIDDLEWARES`:

```python
MIDDLEWARES = [
  ...
  'django_injector.inject_request_middleware',
]
```

**WARNING**: Request injection only works on WSGI application containers, enabling
it on ASGI containers such as dahpne will result in an error.


## Configuration
`django_injector` uses the module mechanism from injector. Desired modules should be
listed in the `INJECTOR_MODULES` setting, each item must be either a subclass of `injector.Module`
or a callable that can receive a binder as its only argument.

Modules are loaded in the order they are listed, when the app is loaded.


## Usage

`django_injector` will enable injection automatically for all view functions and
template context processors that have type hints. To enable injection on class based
views' `__init__` method decorate them with `injector.inject`. For example:


```python
class MyService:
    ...


def my_view(request, service: MyService) -> HttpResponse:
    ...
```

Will inject and insrtance of `MyService` into the view function, no decorator is needed. The
smae works for context processors.

Class based views need a decorated `__init__` method in order to work:

```python
from django.views.generic import View
from injector import inject


class MyView(View):

    @inject
    def __init__(self, service: MyService, **kwargs) -> None:
        ...
```


## Request scope

A custom [Injector scope](https://injector.readthedocs.io/en/latest/terminology.html#scope) is provided –
it's the request scope. Types bound in the request scope share instances during handling a single request
but don't cross request handling boundary. It's similar to
[Flask-Injector's request scope](https://github.com/alecthomas/flask_injector).

**WARNING**: Request scope uses a thread local to bind types to requests. This means the
scope is only available on WSGI containers, and not on ASGI containers such as daphne.
Attempting to set request scope for a type will yield a `RuntimeError` if the request
is handled by an ASGI container.


Example:

```python
from django_injector import request
from injector import inject


class MyService:
    ....


class RequiresService:
    @inject
    def __init__(self, service: Service):
        self.service = service


class AlsoRequiresService:
    @inject
    def __init__(self, service: Service):
        self.service = service


def my_view(request, service: Service, rs: RequiresService, ars: AlsoRequiresService):
    # The same Service instance everywhere
    assert service is rs.service
    assert rs.service is ars.service
    # ...
```


## Builtin bindings

`django_injector` comes with a built-in module that supports a couple Django types for
injection:

* `django.conf.Settings`: allows access to the current settings object (`django.conf.settings`);
* `django.http.HttpRequest`: allows access to the current request. **WARNING**: On ASGI
containers such as daphne this will be short circuited to `None`.
