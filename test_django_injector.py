import os
import sys

import django
import pytest
from django.test import Client


@pytest.fixture
def test_client():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    not_set = object()
    original_settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', not_set)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'
    django.setup()
    yield Client()
    # Let's restore the global state to what was there before the test as much as we can
    sys.path.pop(0)
    if original_settings_module is not_set:
        del os.environ['DJANGO_SETTINGS_MODULE']
    else:
        os.environ['DJANGO_SETTINGS_MODULE'] = original_settings_module


def test_inject_works(test_client):
    response = test_client.get('/inject-works')
    assert response.status_code == 200


def test_request_scope_works(test_client):
    response1 = test_client.get('/request-scope-works')
    assert response1.status_code == 200
    response2 = test_client.get('/request-scope-works')
    assert response2.status_code == 200
    # Let's make sure the request scope doesn't span multiple requests
    assert response1.content != response2.content
