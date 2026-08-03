from collections.abc import Callable

from .base import FVNAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], FVNAdapter]] = {}

    def register(self, adapter_id: str, factory: Callable[[], FVNAdapter]) -> None:
        if adapter_id in self._factories:
            raise ValueError(f"Adapter already registered: {adapter_id}")
        self._factories[adapter_id] = factory

    def create(self, adapter_id: str) -> FVNAdapter:
        try:
            return self._factories[adapter_id]()
        except KeyError as exc:
            raise KeyError(f"Unknown adapter: {adapter_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))


def default_registry() -> AdapterRegistry:
    from .demo.adapter import DemoAdapter
    from .renpy import RenPyAdapter

    registry = AdapterRegistry()
    registry.register("demo", DemoAdapter)
    registry.register("renpy", RenPyAdapter)
    return registry
