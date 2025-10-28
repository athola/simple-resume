"""Unit tests for cv.index module following TDD principles.

These tests follow the Red-Green-Refactor cycle and extreme programming practices:
- Test-driven development approach
- Edge case coverage
- Business logic validation
- Web application behavior testing
- Route handling and response validation
"""

import threading
import time
from unittest.mock import Mock, patch

from cv.index import APP, execute_app, run_app


class TestFlaskApp:
    """Test cases for Flask application routes and behavior."""

    @patch("cv.index.get_content")
    @patch("cv.index.render_template")
    def test_show_route_with_valid_name(
        self, mock_render: Mock, mock_get_content: Mock
    ) -> None:
        """RED: Test that show route renders correct template with data."""
        # Arrange
        mock_data = {
            "template": "cv_no_bars",
            "full_name": "John Doe",
            "description": "<p>Test description</p>",
        }
        mock_get_content.return_value = mock_data
        mock_render.return_value = "Rendered HTML content"

        # Act
        with APP.test_client() as client:
            response = client.get("/v/john_doe")

        # Assert
        assert response.status_code == 200
        mock_get_content.assert_called_once_with("john_doe")
        mock_render.assert_called_once_with(
            "cv_no_bars.html", preview=True, **mock_data
        )

    @patch("cv.index.get_content")
    @patch("cv.index.render_template")
    def test_show_route_with_empty_name(
        self, mock_render: Mock, mock_get_content: Mock
    ) -> None:
        """RED: Test that show route with empty name uses default."""
        # Arrange
        mock_data = {"template": "cv_no_bars", "full_name": "Default User"}
        mock_get_content.return_value = mock_data
        mock_render.return_value = "Default HTML content"

        # Act
        with APP.test_client() as client:
            response = client.get("/v/")

        # Assert
        assert response.status_code == 200
        mock_get_content.assert_called_once_with("")
        mock_render.assert_called_once_with(
            "cv_no_bars.html", preview=True, **mock_data
        )

    @patch("cv.index.get_content")
    @patch("cv.index.render_template")
    def test_show_route_view_alias(
        self, mock_render: Mock, mock_get_content: Mock
    ) -> None:
        """RED: Test that /view/ route works the same as /v/ route."""
        # Arrange
        mock_data = {"template": "cv_no_bars", "full_name": "Jane Doe"}
        mock_get_content.return_value = mock_data
        mock_render.return_value = "View HTML content"

        # Act
        with APP.test_client() as client:
            response = client.get("/view/jane_doe")

        # Assert
        assert response.status_code == 200
        mock_get_content.assert_called_once_with("jane_doe")
        mock_render.assert_called_once_with(
            "cv_no_bars.html", preview=True, **mock_data
        )

    @patch("cv.index.show")
    def test_print_route_calls_show_with_preview_false(self, mock_show: Mock) -> None:
        """RED: Test that print route calls show with preview=False."""
        # Arrange
        mock_show.return_value = "Print-friendly HTML"

        # Act
        with APP.test_client() as client:
            response = client.get("/print/john_doe")

        # Assert
        assert response.status_code == 200
        mock_show.assert_called_once_with("john_doe", preview=False)

    @patch("cv.index.mprint")
    def test_print_sample_route_calls_mprint(self, mock_mprint: Mock) -> None:
        """RED: Test that print.html route calls mprint function."""
        # Arrange
        mock_mprint.return_value = "Sample print HTML"

        # Act
        with APP.test_client() as client:
            response = client.get("/print.html")

        # Assert
        assert response.status_code == 200
        mock_mprint.assert_called_once()

    @patch("cv.index.show")
    def test_root_route_calls_show_with_empty_name(self, mock_show: Mock) -> None:
        """RED: Test that root route calls show with empty name."""
        # Arrange
        mock_show.return_value = "Root HTML content"

        # Act
        with APP.test_client() as client:
            response = client.get("/")

        # Assert
        assert response.status_code == 200
        mock_show.assert_called_once()

    @patch("cv.index.get_content")
    def test_show_route_with_invalid_cv_data(self, mock_get_content: Mock) -> None:
        """RED: Test handling of invalid CV data."""
        # Arrange
        mock_get_content.side_effect = FileNotFoundError("CV file not found")

        # Act & Assert
        with APP.test_client() as client:
            response = client.get("/v/nonexistent")
            assert response.status_code == 500  # Should result in server error

    def test_app_configuration(self) -> None:
        """GREEN: Test Flask app configuration."""
        # Assert
        assert APP is not None
        assert APP.name == "cv.index"
        assert hasattr(APP, "route")

    @patch("cv.index.render_template")
    @patch("cv.index.get_content")
    def test_show_route_response_content_type(
        self, mock_get_content: Mock, mock_render: Mock
    ) -> None:
        """GREEN: Test that response has correct content type."""
        # Arrange
        mock_get_content.return_value = {"template": "cv_no_bars"}
        mock_render.return_value = "<html><body>Test</body></html>"

        # Act
        with APP.test_client() as client:
            response = client.get("/v/test")

        # Assert
        assert response.status_code == 200
        assert response.content_type == "text/html; charset=utf-8"

    @patch("cv.index.render_template")
    @patch("cv.index.get_content")
    def test_show_route_with_different_templates(
        self, mock_get_content: Mock, mock_render: Mock
    ) -> None:
        """GREEN: Test that different templates are handled correctly."""
        # Arrange
        test_cases = [
            ("cv_no_bars", "cv_no_bars.html"),
            ("cv_with_bars", "cv_with_bars.html"),
            ("cover", "cover.html"),
        ]

        for template, expected_template_file in test_cases:
            mock_get_content.return_value = {"template": template}
            mock_render.return_value = f"Content for {template}"

            # Act
            with APP.test_client() as client:
                response = client.get(f"/v/test_{template}")

            # Assert
            assert response.status_code == 200
            mock_render.assert_called_with(
                f"{expected_template_file}", preview=True, **{"template": template}
            )


class TestAppExecution:
    """Test cases for app execution and threading functionality."""

    @patch("cv.index.APP")
    @patch.dict("os.environ", {"FLASK_DEBUG": "true"})
    def test_execute_app_calls_flask_run(self, mock_flask_app: Mock) -> None:
        """RED: Test that execute_app calls Flask run with correct parameters."""
        # Act
        execute_app()

        # Assert
        mock_flask_app.run.assert_called_once_with(debug=True, use_reloader=False)

    @patch("cv.index.execute_app")
    @patch("cv.index.Thread")
    def test_run_app_with_daemon_true(
        self, mock_thread: Mock, mock_execute: Mock
    ) -> None:
        """RED: Test that run_app with daemon=True creates thread correctly."""
        # Act
        run_app(daemon=True)

        # Assert
        mock_thread.assert_called_once_with(
            name="flask_app", target=mock_execute, daemon=True
        )
        mock_thread.return_value.start.assert_called_once()

    @patch("cv.index.execute_app")
    def test_run_app_with_daemon_false(self, mock_execute: Mock) -> None:
        """RED: Test that run_app with daemon=False calls execute directly."""
        # Act
        run_app(daemon=False)

        # Assert
        mock_execute.assert_called_once()

    @patch("cv.index.execute_app")
    def test_run_app_default_daemon_false(self, mock_execute: Mock) -> None:
        """RED: Test that run_app defaults to daemon=False."""
        # Act
        run_app()

        # Assert
        mock_execute.assert_called_once()

    @patch("cv.index.execute_app")
    @patch("cv.index.Thread")
    def test_run_app_thread_configuration(
        self, mock_thread: Mock, mock_execute: Mock
    ) -> None:
        """GREEN: Test that thread is configured correctly for daemon mode."""
        # Act
        run_app(daemon=True)

        # Assert
        thread_instance = mock_thread.return_value
        assert mock_thread.call_count == 1
        assert mock_thread.call_args[1]["daemon"] is True
        assert mock_thread.call_args[1]["name"] == "flask_app"
        assert mock_thread.call_args[1]["target"] == mock_execute
        thread_instance.start.assert_called_once()


class TestBusinessLogic:
    """Test cases for business logic and edge cases."""

    @patch("cv.index.get_content")
    @patch("cv.index.render_template")
    def test_show_route_business_logic_validation(
        self, mock_render: Mock, mock_get_content: Mock
    ) -> None:
        """GREEN: Business logic test for CV data validation in routes."""
        # Arrange
        valid_cv_data = {
            "template": "cv_no_bars",
            "full_name": "John Doe",
            "description": "<p>Valid description</p>",
            "email": "john@example.com",
        }
        mock_get_content.return_value = valid_cv_data
        mock_render.return_value = "Valid CV content"

        # Act
        with APP.test_client() as client:
            response = client.get("/v/john_doe")

        # Assert
        assert response.status_code == 200

        # Business logic validations
        assert "template" in valid_cv_data
        assert "full_name" in valid_cv_data
        assert valid_cv_data["template"].strip() != ""
        assert len(valid_cv_data["full_name"].strip()) > 1

        # Verify template rendering with correct parameters
        mock_render.assert_called_once()
        call_args = mock_render.call_args
        assert call_args[0][0] == "cv_no_bars.html"  # Template name
        assert call_args[1]["preview"] is True  # Preview mode
        assert call_args[1]["full_name"] == "John Doe"

    @patch("cv.index.get_content")
    @patch("cv.index.render_template")
    def test_show_route_handles_missing_template_field(
        self, mock_render: Mock, mock_get_content: Mock
    ) -> None:
        """GREEN: Test handling of CV data missing template field."""
        # Arrange
        invalid_cv_data = {
            "full_name": "John Doe",
            "description": "Description but no template",
        }
        mock_get_content.return_value = invalid_cv_data
        mock_render.return_value = "Rendered HTML with default template"

        # Act
        with APP.test_client() as client:
            response = client.get("/v/invalid")

        # Assert
        assert response.status_code == 200
        mock_get_content.assert_called_once_with("invalid")
        # Should use default template when 'template' field is missing
        mock_render.assert_called_once_with(
            "cv_no_bars.html", preview=True, **invalid_cv_data
        )

    @patch("cv.index.render_template")
    @patch("cv.index.get_content")
    def test_show_route_with_special_characters_in_name(
        self, mock_get_content: Mock, mock_render: Mock
    ) -> None:
        """GREEN: Test handling of special characters in CV names."""
        # Arrange
        special_names = [
            "john-doe_2024",
            "maria.silva.dev",
            "user@domain",
            "cv_with-123-numbers",
        ]

        mock_data = {"template": "cv_no_bars", "full_name": "Test User"}
        mock_get_content.return_value = mock_data
        mock_render.return_value = "Special name content"

        for name in special_names:
            # Act
            with APP.test_client() as client:
                response = client.get(f"/v/{name}")

            # Assert
            assert response.status_code == 200
            mock_get_content.assert_called_with(name)

    @patch("cv.index.render_template")
    @patch("cv.index.get_content")
    def test_show_route_performance_with_large_cv_data(
        self, mock_get_content: Mock, mock_render: Mock
    ) -> None:
        """GREEN: Performance test with large CV data."""
        # Arrange
        large_cv_data = {
            "template": "cv_no_bars",
            "full_name": "John Doe",
            "description": "A" * 10000,  # Large description
            "body": {
                "Experience": [
                    {"title": f"Job {i}", "description": "B" * 1000}
                    for i in range(100)  # 100 experience entries
                ]
            },
        }
        mock_get_content.return_value = large_cv_data
        mock_render.return_value = "Large CV content"

        # Act
        start_time = time.time()
        with APP.test_client() as client:
            response = client.get("/v/large_cv")
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert end_time - start_time < 1.0  # Should respond within 1 second

    def test_route_not_found_handling(self) -> None:
        """GREEN: Test handling of non-existent routes."""
        # Act
        with APP.test_client() as client:
            response = client.get("/nonexistent/route")

        # Assert
        assert response.status_code == 404

    @patch("cv.index.render_template")
    @patch("cv.index.get_content")
    def test_concurrent_requests_handling(
        self, mock_get_content: Mock, mock_render: Mock
    ) -> None:
        """GREEN: Test handling of multiple concurrent requests."""
        # Arrange
        mock_data = {"template": "cv_no_bars", "full_name": "Concurrent User"}
        mock_get_content.return_value = mock_data
        mock_render.return_value = "Concurrent content"

        results = []

        def make_request() -> None:
            with APP.test_client() as client:
                response = client.get("/v/concurrent")
                results.append(response.status_code)

        # Act - Create multiple threads making requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Assert
        assert len(results) == 10
        assert all(status == 200 for status in results)
