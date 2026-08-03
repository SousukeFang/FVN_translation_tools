from collections.abc import Callable

from .base import FVNProfile


class ProfileRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], FVNProfile]] = {}

    def register(self, profile_id: str, factory: Callable[[], FVNProfile]) -> None:
        if profile_id in self._factories:
            raise ValueError(f"Profile already registered: {profile_id}")
        self._factories[profile_id] = factory

    def create(self, profile_id: str) -> FVNProfile:
        try:
            return self._factories[profile_id]()
        except KeyError as exc:
            raise KeyError(f"Unknown profile: {profile_id}") from exc

    def all(self) -> list[FVNProfile]:
        return [self._factories[key]() for key in sorted(self._factories)]


def default_profile_registry() -> ProfileRegistry:
    from .remember_the_flowers import RememberTheFlowersProfile

    registry = ProfileRegistry()
    registry.register("remember-the-flowers-ii", RememberTheFlowersProfile)
    return registry
