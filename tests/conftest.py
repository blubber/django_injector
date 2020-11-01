import django


def pytest_configure(config):
    from django.conf import settings

    settings.configure(
        DEBUG=True,
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={},
        SECRET_KEY='not so secret',
        ROOT_URLCONF='tests.test_django_injector',
        TEMPLATES=[
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    'debug': True,
                    'context_processors': [
                        'tests.test_django_injector.context_processor',
                    ],
                },
            },
        ],
        MIDDLEWARES=[
            'django.middleware.common.CommonMiddleware',
        ],
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'django_injector',
            'tests',
        ],
        USE_I18N=False,
        USE_L10N=False,
        INJECTOR_MODULES=[
            'tests.test_django_injector.configure_django_injector',
            'tests.test_django_injector.TestModule',
        ],
    )

    django.setup()
