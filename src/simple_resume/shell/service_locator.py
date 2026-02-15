"""Service registry for dependency injection.

Simplified registry that stores shell-layer service instances.
Services are registered at startup and consumed via protocol-based
dependency injection (set_default_loaders), not via this locator.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, TypeVar

T = TypeVar("T")

# Module-private registry accessed through the public API functions below.
_REGISTRY: dict[str, Any] = {}


def register_service(name: str, service: Any) -> None:
    """Register a service instance by name."""
    _REGISTRY[name] = service


def register_service_factory(name: str, factory: Callable[[], Any]) -> None:
    """Register a factory function for lazy service creation."""
    _REGISTRY[name] = _LazyFactory(factory)


def get_service(name: str, service_type: type[T]) -> T:
    """Get a service by name, ensuring it matches the expected type."""
    if name not in _REGISTRY:
        raise ValueError(f"Service {name} not registered")
    service = _REGISTRY[name]
    if isinstance(service, _LazyFactory):
        service = service()
        _REGISTRY[name] = service
    if not isinstance(service, service_type):
        raise TypeError(f"Service {name} is not of type {service_type}")
    return service


def has_service(name: str) -> bool:
    """Check if a service is registered."""
    return name in _REGISTRY


class _LazyFactory:
    """Wraps a factory callable for deferred instantiation."""

    __slots__ = ("_factory",)

    def __init__(self, factory: Callable[[], Any]) -> None:
        self._factory = factory

    def __call__(self) -> Any:
        return self._factory()


# Backwards-compatible aliases
class ServiceLocator:
    """Thin facade over module-level registry for backward compatibility."""

    def register(self, name: str, service: Any) -> None:
        """Register a service instance by name."""
        register_service(name, service)

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a factory function for lazy service creation."""
        register_service_factory(name, factory)

    def get(self, name: str, service_type: type[T]) -> T:
        """Get a service by name, ensuring it matches the expected type."""
        return get_service(name, service_type)

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return has_service(name)


@lru_cache(maxsize=1)
def get_service_locator() -> ServiceLocator:
    """Get the global service locator instance."""
    return ServiceLocator()


__all__ = [
    "ServiceLocator",
    "get_service_locator",
    "register_service",
    "register_service_factory",
    "get_service",
    "has_service",
]
