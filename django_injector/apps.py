from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string
from injector import Injector, Module
from inspect import isclass

from .module import DjangoInjectorModule


class DjangoInjectorConfig(AppConfig):
    name = 'django_injector'

    def ready(self):
        super().ready()

        self.injector_module = DjangoInjectorModule()
        modules = [self.injector_module]

        for mod_str in getattr(settings, 'INJECTOR_MODULES', []):
            mod = import_string(mod_str)

            if isclass(mod):
                assert issubclass(mod, Module)
                mod = mod()

            modules.append(mod)

        self.injector = Injector(modules)
