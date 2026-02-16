"""Unit tests for the service locator registry – register, get, factory, facade."""

from __future__ import annotations

from typing import Any

import pytest

from simple_resume.shell.service_locator import (
    _REGISTRY,
    ServiceLocator,
    get_service,
    get_service_locator,
    has_service,
    register_service,
    register_service_factory,
)
from tests.bdd import Scenario


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Clear the module-level registry before each test."""
    _REGISTRY.clear()


# ============================================================================
# register_service / has_service
# ============================================================================


def test_register_service_stores_instance(story: Scenario) -> None:
    story.given("a service instance")
    story.when("registering it by name")
    register_service("db", {"host": "localhost"})
    story.then("has_service returns True")
    assert has_service("db") is True


def test_has_service_returns_false_when_missing(story: Scenario) -> None:
    story.given("an empty registry")
    story.when("checking for an unregistered service")
    story.then("has_service returns False")
    assert has_service("nonexistent") is False


def test_register_service_overwrites_existing(story: Scenario) -> None:
    story.given("a service already registered under a name")
    register_service("cache", "old")
    story.when("registering a new service with the same name")
    register_service("cache", "new")
    story.then("the new service replaces the old one")
    assert get_service("cache", str) == "new"


# ============================================================================
# get_service
# ============================================================================


def test_get_service_returns_typed_instance(story: Scenario) -> None:
    story.given("a registered list service")
    register_service("items", [1, 2, 3])
    story.when("getting the service with the correct type")
    result = get_service("items", list)
    story.then("the service is returned")
    assert result == [1, 2, 3]


def test_get_service_raises_value_error_when_missing(story: Scenario) -> None:
    story.given("an empty registry")
    story.when("getting a service that does not exist")
    story.then("ValueError is raised")
    with pytest.raises(ValueError, match="not registered"):
        get_service("missing", str)


def test_get_service_raises_type_error_when_wrong_type(story: Scenario) -> None:
    story.given("a registered string service")
    register_service("name", "Alice")
    story.when("getting it with the wrong type")
    story.then("TypeError is raised")
    with pytest.raises(TypeError, match="not of type"):
        get_service("name", int)


# ============================================================================
# register_service_factory (lazy instantiation)
# ============================================================================


def test_factory_is_called_lazily(story: Scenario) -> None:
    story.given("a factory function registered for a service")
    call_count = {"n": 0}

    def make_service() -> str:
        call_count["n"] += 1
        return "lazy_value"

    register_service_factory("lazy", make_service)
    story.when("the service has not been requested yet")
    story.then("the factory has not been called")
    assert call_count["n"] == 0

    story.when("getting the service for the first time")
    result = get_service("lazy", str)
    story.then("the factory is called and returns the value")
    assert result == "lazy_value"
    assert call_count["n"] == 1


def test_factory_result_replaces_factory_in_registry(story: Scenario) -> None:
    story.given("a factory that returns a dict")

    def make_config() -> dict[str, Any]:
        return {"debug": True}

    register_service_factory("config", make_config)
    story.when("getting the service twice")
    first = get_service("config", dict)
    second = get_service("config", dict)
    story.then("both calls return the same instance (factory called once)")
    assert first is second


def test_factory_type_mismatch_raises(story: Scenario) -> None:
    story.given("a factory that returns a string")
    register_service_factory("typed", lambda: "hello")
    story.when("getting the service with the wrong type")
    story.then("TypeError is raised after factory resolution")
    with pytest.raises(TypeError, match="not of type"):
        get_service("typed", int)


def test_has_service_true_for_factory(story: Scenario) -> None:
    story.given("a factory registered under a name")
    register_service_factory("pending", lambda: 42)
    story.when("checking if the service exists")
    story.then("has_service returns True (factory is present)")
    assert has_service("pending") is True


# ============================================================================
# ServiceLocator facade
# ============================================================================


def test_service_locator_register_and_get(story: Scenario) -> None:
    story.given("a ServiceLocator instance")
    locator = ServiceLocator()
    story.when("registering and getting a service via the facade")
    locator.register("counter", 42)
    result = locator.get("counter", int)
    story.then("the service is returned correctly")
    assert result == 42


def test_service_locator_has(story: Scenario) -> None:
    story.given("a ServiceLocator instance with a registered service")
    locator = ServiceLocator()
    locator.register("flag", True)
    story.when("checking via the facade")
    story.then("has returns True")
    assert locator.has("flag") is True
    assert locator.has("missing") is False


def test_service_locator_register_factory(story: Scenario) -> None:
    story.given("a ServiceLocator instance")
    locator = ServiceLocator()
    story.when("registering a factory via the facade")
    locator.register_factory("deferred", lambda: [1, 2])
    result = locator.get("deferred", list)
    story.then("the factory resolves correctly")
    assert result == [1, 2]


# ============================================================================
# get_service_locator singleton
# ============================================================================


def test_get_service_locator_returns_singleton(story: Scenario) -> None:
    story.given("the get_service_locator function")
    story.when("calling it twice")
    a = get_service_locator()
    b = get_service_locator()
    story.then("both return the same ServiceLocator instance")
    assert a is b


def test_get_service_locator_returns_service_locator_type(story: Scenario) -> None:
    story.given("the get_service_locator function")
    story.when("calling it")
    locator = get_service_locator()
    story.then("it returns a ServiceLocator instance")
    assert isinstance(locator, ServiceLocator)


# ============================================================================
# Cross-API consistency
# ============================================================================


def test_module_functions_and_facade_share_registry(story: Scenario) -> None:
    story.given("a service registered via the module function")
    register_service("shared", "from_module")
    locator = ServiceLocator()
    story.when("accessing it via the facade")
    result = locator.get("shared", str)
    story.then("the same value is returned")
    assert result == "from_module"


def test_facade_registration_visible_to_module_functions(story: Scenario) -> None:
    story.given("a service registered via the ServiceLocator facade")
    locator = ServiceLocator()
    locator.register("facade_item", 99)
    story.when("accessing it via the module function")
    result = get_service("facade_item", int)
    story.then("the same value is returned")
    assert result == 99
