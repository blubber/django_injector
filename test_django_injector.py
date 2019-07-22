import os
import sys

import django
from django.test import Client


def test_inject_works():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    not_set = object()
    original_settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', not_set)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'
    try:
        django.setup()
        test_client = Client()
        response = test_client.get('/inject-works')
        assert response.status_code == 200
    finally:
        # Let's restore the global state to what was there before the test as much as we can
        sys.path.pop(0)
        if original_settings_module is not_set:
            del os.environ['DJANGO_SETTINGS_MODULE']
        else:
            os.environ['DJANGO_SETTINGS_MODULE'] = original_settings_module
