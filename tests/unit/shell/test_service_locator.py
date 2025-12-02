"""Tests for shell/service_locator.py module."""

from __future__ import annotations

import pytest

from simple_resume.shell.service_locator import (
    ServiceLocator,
    get_service,
    get_service_locator,
    register_service,
    register_service_factory,
)


class TestServiceLocator:
    """Test ServiceLocator class."""

    def test_register_and_get_service(self) -> None:
        """Test basic service registration and retrieval."""
        locator = ServiceLocator()
        locator.register("test_service", "test_value")
        result = locator.get("test_service", str)
        assert result == "test_value"

    def test_register_factory_creates_on_first_access(self) -> None:
        """Test factory registration and lazy creation."""
        locator = ServiceLocator()
        call_count = [0]

        def factory() -> str:
            call_count[0] += 1
            return "factory_created"

        locator.register_factory("factory_service", factory)

        # Factory not called yet
        assert call_count[0] == 0

        # First access triggers factory
        result = locator.get("factory_service", str)
        assert result == "factory_created"
        assert call_count[0] == 1

        # Second access uses cached value
        result = locator.get("factory_service", str)
        assert result == "factory_created"
        assert call_count[0] == 1  # Still only 1 call

    def test_get_raises_type_error_for_wrong_type(self) -> None:
        """Test type checking on service retrieval."""
        locator = ServiceLocator()
        locator.register("string_service", "a_string")

        with pytest.raises(TypeError, match="is not of type"):
            locator.get("string_service", int)

    def test_get_factory_raises_type_error_for_wrong_type(self) -> None:
        """Test type checking on factory-created service."""
        locator = ServiceLocator()
        locator.register_factory("factory_service", lambda: "string_value")

        with pytest.raises(TypeError, match="is not of type"):
            locator.get("factory_service", int)

    def test_get_raises_value_error_for_unknown_service(self) -> None:
        """Test error when service not registered."""
        locator = ServiceLocator()

        with pytest.raises(ValueError, match="not registered"):
            locator.get("unknown", str)

    def test_has_returns_true_for_registered_service(self) -> None:
        """Test has method for direct registration."""
        locator = ServiceLocator()
        locator.register("service", "value")
        assert locator.has("service") is True

    def test_has_returns_true_for_factory(self) -> None:
        """Test has method for factory registration."""
        locator = ServiceLocator()
        locator.register_factory("factory", lambda: "value")
        assert locator.has("factory") is True

    def test_has_returns_false_for_unknown(self) -> None:
        """Test has method for unknown service."""
        locator = ServiceLocator()
        assert locator.has("unknown") is False


class TestModuleLevelFunctions:
    """Test module-level convenience functions."""

    def test_get_service_locator_returns_singleton(self) -> None:
        """Test that get_service_locator returns the same instance."""
        locator1 = get_service_locator()
        locator2 = get_service_locator()
        assert locator1 is locator2

    def test_register_service_adds_to_global_locator(self) -> None:
        """Test register_service function."""
        register_service("global_test_service", "global_value")
        locator = get_service_locator()
        result = locator.get("global_test_service", str)
        assert result == "global_value"

    def test_register_service_factory_adds_to_global_locator(self) -> None:
        """Test register_service_factory function."""
        register_service_factory("global_factory", lambda: 42)
        locator = get_service_locator()
        result = locator.get("global_factory", int)
        assert result == 42

    def test_get_service_retrieves_from_global_locator(self) -> None:
        """Test get_service function."""
        register_service("get_service_test", ["list", "value"])
        result = get_service("get_service_test", list)
        assert result == ["list", "value"]
