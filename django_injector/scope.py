import threading

import injector


# The original code comes from the Flask-Injector project by Alec Thomas.
# Flask-Injector is licensed under the BSD 3-clause license.
class RequestScope(injector.Scope):
    """A scope whose object lifetime is tied to a request."""

    def cleanup(self) -> None:
        del self._locals.scope

    def prepare(self) -> None:
        self._locals.scope = {}

    def configure(self) -> None:
        self._locals = threading.local()

    def get(self, key, provider):
        try:
            return self._locals.scope[key]
        except KeyError:
            new_provider = injector.InstanceProvider(provider.get(self.injector))
            self._locals.scope[key] = new_provider
            return new_provider


request_scope = injector.ScopeDecorator(RequestScope)
