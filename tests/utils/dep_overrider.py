from typing import Callable, Mapping, Any

from fastapi import FastAPI


class DependencyOverrider:
    """Temporarily override fastapi dependencies inside a context"""

    def __init__(
        self, app: FastAPI, overrides: Mapping[Callable, Callable]
    ) -> None:
        self.overrides = overrides
        self._app = app
        self._old_overrides = {}

    def __enter__(self):
        for dep, new_dep in self.overrides.items():
            if dep in self._app.dependency_overrides:
                # Save existing overrides
                self._old_overrides[dep] = self._app.dependency_overrides[dep]

            self._app.dependency_overrides[dep] = new_dep
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        for dep in self.overrides.keys():
            if dep in self._old_overrides:
                # Restore previous overrides
                self._app.dependency_overrides[dep] = self._old_overrides.pop(
                    dep
                )
            else:
                # Just delete the entry
                del self._app.dependency_overrides[dep]
