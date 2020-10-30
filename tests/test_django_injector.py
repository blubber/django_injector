from unittest.mock import Mock, call, patch

from django.http import HttpResponse
from django.template import Template, engines
from django.template.response import TemplateResponse
from django.test import SimpleTestCase
from django.template.backends.django import Template as DjangoTemplate
from django.urls import path
from django.urls.resolvers import RegexPattern, URLPattern, URLResolver
from django.views.generic import View as GenericView

from injector import Module, inject, singleton
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from django_injector import process_resolver


STRING = 'Fortytwo'
NUMBER = 42
CONTENT = '%s %s' % (STRING, NUMBER)


@patch('django_injector.wrap_fun')
def test_process_resolver_wraps_resolver_callback(wrap_fun):
    resolver = URLResolver(RegexPattern(r'^$'), [])
    cb = Mock()
    resolver.callback = cb
    injector = Mock()
    process_resolver(resolver, injector)
    wrap_fun.assert_has_calls([call(cb, injector)])


@patch('django_injector.wrap_fun')
def test_process_resolver_wraps_pattern_callbacks(wrap_fun):
    cb1 = Mock()
    pattern1 = URLPattern('', cb1)
    cb2 = Mock()
    pattern2 = URLPattern('', cb2)

    resolver = URLResolver(RegexPattern(r'^$'), [pattern1, pattern2])

    injector = Mock()
    process_resolver(resolver, injector)
    wrap_fun.assert_has_calls([
        call(cb1, injector),
        call(cb2, injector),
    ])


@patch('django_injector.wrap_fun')
def test_process_resolver_recurses_for_nested_resolvers(wrap_fun):
    cb = Mock()
    resolver = URLResolver(RegexPattern(r'^foo/$'), [])
    resolver.callback = cb

    injector = Mock()
    process_resolver(URLResolver(RegexPattern(r'^$'), [resolver]), injector)
    wrap_fun.assert_has_calls([call(cb, injector)])


def test_process_resolver_repopulates_resolver():
    resolver = URLResolver(RegexPattern(r'^$'), [])
    resolver._populate()

    with patch.object(resolver, '_populate') as populate:
        process_resolver(resolver, Mock())
        populate.assert_called_once_with()


class TestViewInjection(SimpleTestCase):

    def test_view_fun_called_with_injection(self):
        response = self.client.get('/fun/')
        assert response.content.decode('utf-8') == CONTENT

    def test_view_init_receives_injection(self):
        response = self.client.get('/class/')
        assert response.content.decode('utf-8') == CONTENT

    def test_instance_method_called_with_injection(self):
        response = self.client.get('/instance/')
        assert response.content.decode('utf-8') == CONTENT

    def test_drf_generic_view_receives_injection(self):
        response = self.client.get('/api/')
        assert response.content.decode('utf-8') == '"%s"' % CONTENT

    def test_drf_viewset_receives_injection(self):
        response = self.client.get('/viewset/')
        assert response.content.decode('utf-8') == '"%s"' % CONTENT


class TestContextProcessor(SimpleTestCase):

    def test_context_processor(self):
        response = self.client.get('/context_processor/')
        assert response.content.decode('utf-8') == CONTENT


def context_processor(request, string: str, number: int):
    return {
        'string': string,
        'number': number,
    }


def view(request, string: str, number: int):
    return HttpResponse('%s %s' % (string, number))


def context_processor_view(request):
    backend = engines.all()[0]
    template = Template('{{ string }} {{ number }}')
    return TemplateResponse(
        request=request,
        template=DjangoTemplate(template, backend),
    )


class View(GenericView):

    @inject
    def __init__(self, string: str, number: int):
        super().__init__()
        self.string = string
        self.number = number

    def get(self, request):
        return HttpResponse('%s %s' % (self.string, self.number))


class InstanceView:

    def view(self, request, string: str, number: int):
        return HttpResponse('%s %s' % (string, number))


class Api(APIView):

    @inject
    def __init__(self, string: str, number: int):
        super().__init__()
        self.string = string
        self.number = number

    def get(self, request):
        return Response('%s %s' % (self.string, self.number))


class ApiViewSet(ViewSet):

    @inject
    def __init__(self, string: str, number: int):
        super().__init__()
        self.string = string
        self.number = number

    def list(self, request):
        return Response('%s %s' % (self.string, self.number))


def configure_django_injector(binder):
    binder.bind(str, to=STRING, scope=singleton)


class TestModule(Module):

    def configure(self, binder):
        binder.bind(int, to=NUMBER, scope=singleton)


urlpatterns = [
    path('fun/', view),
    path('context_processor/', context_processor_view),
    path('class/', View.as_view()),
    path('instance/', InstanceView().view),
    path('api/', Api.as_view()),
    path('viewset/', ApiViewSet.as_view({'get': 'list'})),
]
