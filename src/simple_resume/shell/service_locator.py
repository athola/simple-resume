"""Service locator pattern for dependency injection.

This module provides a clean way to inject shell-layer dependencies
into core functions without using late-bound imports.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ServiceLocator:
    """Simple service locator for dependency injection."""

    def __init__(self) -> None:
        """Initialize the service locator."""
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service

    def register_factory(self, name: str, factory: Callable[[], Any]) -> None:
        """Register a factory function for lazy service creation."""
        self._factories[name] = factory

    def get(self, name: str, service_type: type[T]) -> T:
        """Get a service by name, ensuring it matches the expected type."""
        if name in self._services:
            service = self._services[name]
            if not isinstance(service, service_type):
                raise TypeError(f"Service {name} is not of type {service_type}")
            return service

        if name in self._factories:
            service = self._factories[name]()
            if not isinstance(service, service_type):
                raise TypeError(f"Service {name} is not of type {service_type}")
            self._services[name] = service  # Cache the instance
            return service

        raise ValueError(f"Service {name} not registered")

    def has(self, name: str) -> bool:
        """Check if a service is registered."""
        return name in self._services or name in self._factories


@lru_cache(maxsize=1)
def get_service_locator() -> ServiceLocator:
    """Get the global service locator instance without module globals."""
    return ServiceLocator()


def register_service(name: str, service: Any) -> None:
    """Register a service with the global locator."""
    get_service_locator().register(name, service)


def register_service_factory(name: str, factory: Callable[[], Any]) -> None:
    """Register a service factory with the global locator."""
    get_service_locator().register_factory(name, factory)


def get_service(name: str, service_type: type[T]) -> T:
    """Get a service from the global locator."""
    return get_service_locator().get(name, service_type)


__all__ = [
    "ServiceLocator",
    "get_service_locator",
    "register_service",
    "register_service_factory",
    "get_service",
]
