# Django injector

Django injector is an app for Django that integrates [injector](https://github.com/alecthomas/injector)
with Django.

Injector is a simple and easy to use dependency injection framework.


## Installation

```
$ pip install django_injector
```

Then add `django_injector` to `INSTALLED_APPS` and `'django_injector.middleware.DjangoInjectorMiddleware'`
to `MIDDLEWARE` in your Django configuration.


## Configuration
`django_injector` uses the module mechanism from injector. Desired modules should be
listed in the `INJECTOR_MODULES` setting, each item must be either a subclass of `injector.Module`
or a callable that can receive a binder as its only argument.

Modules are loaded when the app is loaded.


## Usage

To use the injector decorate functions or methods with `injector.inject`. Decorated
methods or functions can receive additional, non-injected, arguments, they should be listed
**before** injected arguments.

Previously there was a custom `inject` decorator in `django_injector` – it's no longer
required and has been removed.

## Example
This is an example of a view function that receives a `request` from Django and
an injected argument.

```python
from injector import inject

from my_app.services import SomeService


@inject
def my_view(request, some_service: SomeService):
    """Will receive a `request` from Django and `some_service` from the injector."""
    return some_service.do_something(request)
```
