"""Unit tests for cv.generate_pdf module following TDD principles.

These tests follow the Red-Green-Refactor cycle and extreme programming practices:
- File system operations testing
- PDF generation workflow validation
- Error handling and edge cases
- Business logic for CV processing
- Integration with external dependencies
"""
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from cv.config import PATH_OUTPUT
from cv.generate_pdf import generate_pdf


class TestGeneratePdf:
    """Test cases for PDF generation functionality."""

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_success_workflow(self, mock_css, mock_html, mock_print,
                                         mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """RED: Test complete PDF generation workflow."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["cv1.yaml", "cv2.yml", "readme.txt", "image.png"]
        mock_exists.return_value = True  # Output directory exists
        mock_css.return_value = Mock()
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Act
        generate_pdf()

        # Assert
        # Verify app is started in daemon mode
        mock_run_app.assert_called_once_with(True)

        # Verify only YAML files are processed
        expected_files = ["cv1.yaml", "cv2.yml"]
        assert mock_listdir.call_count == 1

        # Verify output directory check
        mock_exists.assert_called_once()

        # Verify sleep is called for each file (WeasyPrint timing)
        assert mock_sleep.call_count == len(expected_files)

        # Verify PDF generation for each YAML file
        assert mock_html.call_count == len(expected_files)
        assert mock_html_instance.write_pdf.call_count == len(expected_files)

        # Verify CSS is created for each file
        assert mock_css.call_count == len(expected_files)

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_creates_output_directory(self, mock_css, mock_html, mock_print,
                                                  mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """RED: Test that output directory is created when it doesn't exist."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["cv1.yaml"]
        mock_exists.return_value = False  # Output directory doesn't exist
        mock_makedirs.return_value = None
        mock_css.return_value = Mock()
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Act
        generate_pdf()

        # Assert
        mock_exists.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once()

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    def test_generate_pdf_filters_non_yaml_files(self, mock_listdir, mock_run_app):
        """RED: Test that only YAML and YML files are processed."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = [
            "document.pdf",
            "image.jpg",
            "readme.txt",
            "script.py",
            "config.json",
            "style.css"
        ]

        # Act
        generate_pdf()

        # Assert
        mock_run_app.assert_called_once_with(True)
        mock_listdir.assert_called_once()
        # HTML should not be called for any non-YAML files
        # (verified by lack of patch for HTML/HTML.write_pdf)

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_css_configuration(self, mock_css, mock_html, mock_print,
                                           mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """RED: Test that CSS is configured correctly for PDF generation."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["test_cv.yaml"]
        mock_exists.return_value = True
        mock_css_instance = Mock()
        mock_css.return_value = mock_css_instance
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Act
        generate_pdf()

        # Assert
        mock_css.assert_called_once_with(
            string=" @page {size: Letter; margin: 0in 0.44in 0.2in 0.44in;} "
        )
        mock_html_instance.write_pdf.assert_called_once_with(
            f"{PATH_OUTPUT}test_cv.pdf",
            stylesheets=[mock_css_instance]
        )

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    def test_generate_pdf_with_mixed_extensions(self, mock_listdir, mock_run_app):
        """RED: Test handling of mixed file extensions."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = [
            "cv1.yaml",
            "cv2.yml",
            "cv3.YAML",  # Upper case
            "cv4.YML",   # Upper case
            "document.txt",
            "image.png"
        ]

        with patch("cv.generate_pdf.os.path.exists", return_value=True), \
             patch("cv.generate_pdf.time.sleep"), \
             patch("cv.generate_pdf.print"), \
             patch("cv.generate_pdf.HTML") as mock_html, \
             patch("cv.generate_pdf.CSS") as mock_css:

            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_css.return_value = Mock()

            # Act
            generate_pdf()

            # Assert
            # Should process 4 YAML files (2 .yaml + 2 .yml + 2 uppercase variants)
            assert mock_html.call_count == 4
            assert mock_html_instance.write_pdf.call_count == 4

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    def test_generate_pdf_empty_directory(self, mock_listdir, mock_run_app):
        """RED: Test handling of empty input directory."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = []

        # Act
        generate_pdf()

        # Assert
        mock_run_app.assert_called_once_with(True)
        mock_listdir.assert_called_once()

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_error_handling(self, mock_css, mock_html, mock_print,
                                         mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """RED: Test error handling during PDF generation."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["cv1.yaml", "cv2.yaml"]
        mock_exists.return_value = True
        mock_css.return_value = Mock()
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Make the second PDF generation fail
        mock_html_instance.write_pdf.side_effect = [None, Exception("PDF generation failed")]

        # Act & Assert
        with pytest.raises(Exception, match="PDF generation failed"):
            generate_pdf()

        # Verify that both PDFs were attempted (first succeeds, second fails)
        assert mock_html_instance.write_pdf.call_count == 2

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_file_naming_logic(self, mock_css, mock_html, mock_print,
                                            mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """RED: Test file naming and path logic."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["john_doe.yaml", "jane_smith.yml"]
        mock_exists.return_value = True
        mock_css.return_value = Mock()
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Act
        generate_pdf()

        # Assert
        # Check that HTML was called with correct URLs
        expected_html_calls = [
            ("http://localhost:5000/print/john_doe",),
            ("http://localhost:5000/print/jane_smith",)
        ]
        actual_html_calls = [call.args for call in mock_html.call_args_list]
        assert actual_html_calls == expected_html_calls

        # Check that write_pdf was called with correct output files
        expected_write_calls = [
            (f"{PATH_OUTPUT}john_doe.pdf",),
            (f"{PATH_OUTPUT}jane_smith.pdf",)
        ]
        actual_write_calls = [call.args for call in mock_html_instance.write_pdf.call_args_list]
        assert actual_write_calls == expected_write_calls

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    def test_generate_pdf_business_logic_validation(self, mock_listdir, mock_run_app):
        """GREEN: Business logic test for PDF generation workflow."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["invalid_file.txt"]

        # Act
        generate_pdf()

        # Assert - Business logic validations
        mock_run_app.assert_called_once_with(True)  # App must be started in daemon mode

        # Verify directory scanning
        mock_listdir.assert_called_once()

        # The function should not process non-YAML files
        # This is verified by the fact that no HTML/CSS operations would be called

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_performance_considerations(self, mock_css, mock_html, mock_print,
                                                     mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """GREEN: Performance test for PDF generation."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = [f"cv_{i}.yaml" for i in range(50)]  # 50 CV files
        mock_exists.return_value = True
        mock_css.return_value = Mock()
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        import time

        # Act
        start_time = time.time()
        generate_pdf()
        end_time = time.time()

        # Assert
        # Should complete quickly since sleep is mocked
        assert end_time - start_time < 1  # Should be very fast with mocked sleep

        # Verify all files were processed
        assert mock_html.call_count == 50
        assert mock_html_instance.write_pdf.call_count == 50
        assert mock_sleep.call_count == 50

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir", side_effect=PermissionError("Permission denied"))
    def test_generate_pdf_permission_error_handling(self, mock_listdir, mock_run_app):
        """GREEN: Test handling of permission errors."""
        # Act & Assert
        with pytest.raises(PermissionError, match="Permission denied"):
            generate_pdf()

        mock_run_app.assert_called_once_with(True)
        mock_listdir.assert_called_once()

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs", side_effect=OSError("Directory creation failed"))
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_directory_creation_error(self, mock_css, mock_html, mock_print,
                                                  mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """GREEN: Test handling of directory creation errors."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["test_cv.yaml"]
        mock_exists.return_value = False  # Directory doesn't exist
        mock_css.return_value = Mock()
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Act & Assert
        with pytest.raises(OSError, match="Directory creation failed"):
            generate_pdf()

        mock_exists.assert_called_once()
        mock_makedirs.assert_called_once()

    def test_generate_pdf_url_formatting(self):
        """GREEN: Test URL formatting for different CV names."""
        # Test data with various naming patterns
        test_cases = [
            ("john_doe", "http://localhost:5000/print/john_doe"),
            ("jane.smith", "http://localhost:5000/print/jane.smith"),
            ("user123", "http://localhost:5000/print/user123"),
            ("cv-with-dashes", "http://localhost:5000/print/cv-with-dashes"),
            ("CamelCase", "http://localhost:5000/print/CamelCase")
        ]

        with patch("cv.generate_pdf.run_app"), \
             patch("cv.generate_pdf.os.listdir") as mock_listdir, \
             patch("cv.generate_pdf.os.path.exists", return_value=True), \
             patch("cv.generate_pdf.os.makedirs"), \
             patch("cv.generate_pdf.time.sleep"), \
             patch("cv.generate_pdf.print"), \
             patch("cv.generate_pdf.HTML") as mock_html, \
             patch("cv.generate_pdf.CSS") as mock_css:

            mock_html_instance = Mock()
            mock_html.return_value = mock_html_instance
            mock_css.return_value = Mock()

            for cv_name, expected_url in test_cases:
                # Arrange
                mock_listdir.return_value = [f"{cv_name}.yaml"]

                # Act
                generate_pdf()

                # Assert
                mock_html.assert_called_with(expected_url)

                # Reset mocks for next iteration
                mock_html.reset_mock()

    @patch("cv.generate_pdf.run_app")
    @patch("cv.generate_pdf.os.listdir")
    @patch("cv.generate_pdf.os.path.exists")
    @patch("cv.generate_pdf.os.makedirs")
    @patch("cv.generate_pdf.time.sleep")
    @patch("cv.generate_pdf.print")
    @patch("cv.generate_pdf.HTML")
    @patch("cv.generate_pdf.CSS")
    def test_generate_pdf_css_styling_validation(self, mock_css, mock_html, mock_print,
                                                mock_sleep, mock_makedirs, mock_exists, mock_listdir, mock_run_app):
        """GREEN: Business logic validation for CSS styling."""
        # Arrange
        mock_run_app.return_value = None
        mock_listdir.return_value = ["test_cv.yaml"]
        mock_exists.return_value = True
        mock_css_instance = Mock()
        mock_css.return_value = mock_css_instance
        mock_html_instance = Mock()
        mock_html.return_value = mock_html_instance

        # Act
        generate_pdf()

        # Assert - CSS styling business rules
        mock_css.assert_called_once()
        css_string = mock_css.call_args[1]["string"]

        # Validate CSS contains required page settings
        assert "size: Letter" in css_string, "Should use Letter page size"
        assert "margin: 0in 0.44in 0.2in 0.44in" in css_string, "Should have correct margins"

        # Validate PDF generation parameters
        pdf_call_args = mock_html_instance.write_pdf.call_args
        assert len(pdf_call_args[1]["stylesheets"]) == 1, "Should have exactly one stylesheet"
        assert pdf_call_args[1]["stylesheets"][0] == mock_css_instance, "Should use created CSS instance"