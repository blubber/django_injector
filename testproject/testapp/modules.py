from injector import Module


class TestAppModule(Module):
    def configure(self, binder):
        binder.bind(str, to='this is an injected string')
