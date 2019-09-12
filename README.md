# Django injector

Django injector is an app for Django that integrates [injector](https://github.com/alecthomas/injector)
with Django.

Injector is a simple and easy to use dependency injection framework.


## Installation

```
$ pip install django_injector
```

Then add `django_injector` to `INSTALLED_APPS` and `'django_injector.middleware.inject_request_middleware'`
to `MIDDLEWARE` in your Django configuration.


## Configuration
`django_injector` uses the module mechanism from injector. Desired modules should be
listed in the `INJECTOR_MODULES` setting, each item must be either a subclass of `injector.Module`
or a callable that can receive a binder as its only argument.

Modules are loaded when the app is loaded.


## Usage

To use the injector decorate functions or methods with `django_injector.inject`. Decorated
methods or functions can receive additional, non-injected, arguments, they should be listed
**before** injected arguments.


## Example
This is an example of a view function that receives a `request` from Django and
an injected argument.

```python
from django_injector import inject

from my_app.services import SomeService


@inject
def my_view(request, some_service: SomeService):
    """Will receive a `request` from Django and `some_service` from the injector."""
    return some_service.do_something(request)
```

## Request scope

A custom [Injector scope](https://injector.readthedocs.io/en/latest/terminology.html#scope) is provided –
it's the request scope. Types bound in the request scope share instances during handling a single request
but don't cross request handling boundary. It's similar to
[Flask-Injector's request scope](https://github.com/alecthomas/flask_injector).

The request scope depends on only single request being handled by a single thread (green threads,
when gevent or Eventlet monkey patching is used, are also supported) at a time.

Example:

```python
from django_injector import request_scope
from django_injector import inject

class Service:
    pass


class RequiresService:
    @inject
    def __init__(self, service: Service):
        self.service = service


class AlsoRequiresService:
    @inject
    def __init__(self, service: Service):
        self.service = service


@inject
def my_view(request, service: Service, rs: RequiresService, ars: AlsoRequiresService):
    # The same Service instance everywhere
    assert service is rs.service
    assert rs.service is ars.service
    # ...
```


## Builtin bindings

One can inject `django.http.HttpRequest` and it'll be the same object as the `request` argument inside
the views. The binding can be used to provide `HttpRequest` deep in the object hierarchy without
having to pass it manually.

Example:

```python
from django.http import HttpRequest
from django_injector import inject


class RequiresRequest:
    @inject
    def __init__(self, request: HttpRequest):
        self.request = request


@inject
def my_view(request, rr: RequiresRequest):
    # The same request everywhere
    assert rr.request is request
    # ...
```
