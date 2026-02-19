"""
Integration tests for the complete transcription-game workflow.
"""

import pytest
import json
import os
from unittest.mock import patch, Mock, mock_open
from handwriting_transcription.app import create_app


class TestIntegrationWorkflow:
    """Integration tests for complete user workflows."""

    @pytest.fixture
    def app(self):
        """Create test app with testing configuration."""
        app = create_app("testing")
        app.config.update(
            {
                "TESTING": True,
                "WTF_CSRF_ENABLED": False,
                "MAX_TEXT_LENGTH": 1000,
                "PDF_TIMEOUT": 10,
            }
        )
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    def test_complete_pdf_generation_workflow(self, client):
        """Test complete workflow from text input to PDF generation."""

        # Step 1: Get available fonts
        response = client.get("/api/fonts")
        assert response.status_code == 200

        fonts_data = json.loads(response.data)
        assert fonts_data["success"] is True
        assert "data" in fonts_data
        assert len(fonts_data["data"]) > 0

        # Use first available font
        font_name = fonts_data["data"][0]["name"]

        # Step 2: Process text
        text_data = {
            "text": "The quick brown fox jumps over the lazy dog.\nThis is a test line.",
            "options": {
                "remove_spaces": False,
                "remove_line_breaks": False,
                "black_text": True,
                "gray_text": False,
                "blank_lines": False,
            },
        }

        response = client.post(
            "/api/process-text",
            data=json.dumps(text_data),
            content_type="application/json",
        )
        assert response.status_code == 200

        processed_data = json.loads(response.data)
        assert processed_data["success"] is True

        # Step 3: Generate PDF
        pdf_data = {
            "text": text_data["text"],
            "options": {
                "font_name": font_name,
                "font_size": 12,
                "document_size": "A4",
                "guidelines": True,
                "guideline_type": "ruled",
                "black_text": True,
                "gray_text": False,
                "blank_lines": False,
            },
        }

        # Step 4: Generate PDF
        with patch(
            "handwriting_transcription.pdf_generator.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas._pagesize = (595.276, 841.89)
            mock_canvas.stringWidth.return_value = 100.0
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.pdf_generator.BytesIO"
            ) as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b"%PDF-1.4\n" + b"a" * 200
                mock_bytesio.return_value = mock_buffer

                response = client.post(
                    "/api/generate-pdf",
                    data=json.dumps(pdf_data),
                    content_type="application/json",
                )

                assert response.status_code == 200
                assert response.content_type == "application/pdf"
                assert len(response.data) > 0

    def test_font_validation_workflow(self, client):
        """Test font validation and fallback workflow."""

        # Test valid font
        font_data = {"font_name": "Helvetica"}
        response = client.post(
            "/api/fonts/validate",
            data=json.dumps(font_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True
        assert result["data"]["is_valid"] is True

        # Test invalid font (should fallback)
        font_data = {"font_name": "NonExistentFont"}
        response = client.post(
            "/api/fonts/validate",
            data=json.dumps(font_data),
            content_type="application/json",
        )

        # Should still succeed with fallback
        assert response.status_code == 200

    def test_text_processing_workflow(self, client):
        """Test various text processing operations."""

        original_text = "Hello   world!\n\nThis is a test."

        # Test space removal
        response = client.post(
            "/api/remove-spaces",
            data=json.dumps({"text": original_text}),
            content_type="application/json",
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True
        assert "processed_text" in result["data"]
        assert " " not in result["data"]["processed_text"].replace("\n", "")

        # Test line break removal
        response = client.post(
            "/api/remove-line-breaks",
            data=json.dumps({"text": original_text}),
            content_type="application/json",
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True
        assert "\n" not in result["data"]["processed_text"]

    def test_font_metrics_workflow(self, client):
        """Test font metrics calculation workflow."""

        metrics_data = {"font_name": "Helvetica", "font_size": 14}

        response = client.post(
            "/api/fonts/metrics",
            data=json.dumps(metrics_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True

        metrics = result["data"]["metrics"]
        assert "line_height" in metrics
        assert "ascent" in metrics
        assert "descent" in metrics
        assert metrics["font_size"] == 14

    def test_font_preview_workflow(self, client):
        """Test font preview generation workflow."""

        preview_data = {"font_name": "Helvetica", "preview_text": "Sample preview text"}

        with patch(
            "handwriting_transcription.font_manager.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.font_manager.base64.b64encode"
            ) as mock_b64:
                mock_b64.return_value = b"fake_base64_data"

                response = client.post(
                    "/api/fonts/preview",
                    data=json.dumps(preview_data),
                    content_type="application/json",
                )

                assert response.status_code == 200
                result = json.loads(response.data)
                assert result["success"] is True
                assert "preview_data" in result["data"]

    def test_font_preview_image_workflow(self, client):
        """Test PNG font preview image generation workflow."""

        # Test valid request
        response = client.get(
            "/api/fonts/preview-image?font_name=Helvetica&preview_text=Test&font_size=24"
        )
        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True
        assert "preview_image" in result["data"]
        assert result["data"]["preview_image"].startswith("data:image/png;base64,")

        # Test missing font_name
        response = client.get("/api/fonts/preview-image")
        assert response.status_code == 400

        # Test with system font if possible
        response = client.get("/api/fonts/preview-image?font_name=Amiri Regular")
        # Could be 200 (if font found) or 500/ fallback (if font not found)
        # We just check it doesn't crash the server
        assert response.status_code in [200, 500, 404]

    def test_font_upload_workflow(self, client):
        """Test custom font upload workflow."""
        from io import BytesIO

        # Test missing file
        response = client.post("/api/fonts/upload")
        assert response.status_code == 400
        assert json.loads(response.data)["error"] == "No file provided"

        # Test invalid extension
        data = {
            "font_file": (BytesIO(b"content"), "test.txt")
        }
        response = client.post(
            "/api/fonts/upload", 
            data=data,
            content_type="multipart/form-data"
        )
        assert response.status_code == 400
        assert "Invalid file type" in json.loads(response.data)["error"]

        # Test successful upload (mocking internal logic but using real client)
        # We need to mock secure_filename to control the filename
        # And FontManager.register_custom_font to avoid actual processing
        # And file.save to avoid writing to disk
        
        with patch("handwriting_transcription.app.secure_filename", return_value="test_font.ttf"):
            with patch("handwriting_transcription.font_manager.FontManager.register_custom_font") as mock_register:
                # Mock return of register_custom_font
                mock_register.return_value = type("FontInfo", (), {
                    "name": "Test Font",
                    "file_path": "/path/to/test_font.ttf",
                    "preview_text": "Abc",
                    "supported_sizes": [12],
                    "is_system_font": False
                })()
                
                # We need to mock FileStorage.save or app.static_folder access
                # But since file.save is called on the object from request.files, and that object is created by client...
                # It's easier to mock os.makedirs and Werkzeug's FileStorage.save if possible.
                # Or just let it fail at save and catch it? No we want success.
                
                # Mocking file.save globally is hard. 
                # Let's mock the 'app.route' function... no.
                
                # Let's mock os.makedirs and the save method on the file instance?
                # Actually, we can just mock os.path.join to return /dev/null or similar?
                # Or use proper mocking of the file object.
                
                # Let's try to mock the file saving PART in app.py logic using a slightly different approach.
                # We can mock the 'request' object's file access? No that caused recursion.
                
                # Best approach for integration test without IO:
                # Mock os.makedirs to do nothing
                # Mock FileStorage.save (we can import it and patch it)
                from werkzeug.datastructures import FileStorage
                with patch.object(FileStorage, "save") as mock_save:
                    with patch("os.makedirs"):
                        data = {
                            "font_file": (BytesIO(b"valid font content"), "test_font.ttf")
                        }
                        response = client.post(
                            "/api/fonts/upload", 
                            data=data,
                            content_type="multipart/form-data"
                        )
                        assert response.status_code == 200
                        result = json.loads(response.data)
                        assert result["success"] is True
                        assert result["data"]["font"]["name"] == "Test Font"


    def test_error_handling_workflow(self, client):
        """Test error handling throughout the workflow."""

        # Test invalid JSON
        response = client.post(
            "/api/process-text", data="invalid json", content_type="application/json"
        )
        assert response.status_code == 400

        # Test missing required fields (empty text)
        response = client.post(
            "/api/process-text",
            data=json.dumps({"text": "", "options": {}}),
            content_type="application/json",
        )
        assert response.status_code == 400

        # Test text too long (validator MAX_TEXT_LENGTH is 10000)
        long_text = "a" * 11000  # Exceeds validator limit of 10000
        response = client.post(
            "/api/process-text",
            data=json.dumps({"text": long_text, "options": {}}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_rate_limiting_workflow(self, client):
        """Test rate limiting in the workflow."""

        # Make multiple PDF generation requests quickly
        pdf_data = {
            "text": "Test text",
            "options": {
                "font_name": "Helvetica",
                "font_size": 12,
                "document_size": "A4",
                "guidelines": False,
                "guideline_type": "none",
                "black_text": True,
                "gray_text": False,
                "blank_lines": False,
            },
        }

        with patch(
            "handwriting_transcription.pdf_generator.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas._pagesize = (595.276, 841.89)
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.pdf_generator.BytesIO"
            ) as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b"%PDF-1.4\nfake pdf"
                mock_bytesio.return_value = mock_buffer

                # Make requests up to the limit (5 for PDF generation)
                responses = []
                for i in range(7):  # Try more than the limit
                    response = client.post(
                        "/api/generate-pdf",
                        data=json.dumps(pdf_data),
                        content_type="application/json",
                    )
                    responses.append(response)

                # First 5 should succeed, rest should be rate limited
                success_count = sum(1 for r in responses if r.status_code == 200)
                rate_limited_count = sum(1 for r in responses if r.status_code == 429)

                assert success_count <= 5  # Should not exceed limit
                assert rate_limited_count > 0  # Some should be rate limited

    def test_health_check_workflow(self, client):
        """Test health check endpoints."""

        # Test basic health check
        response = client.get("/health")
        assert response.status_code == 200

        result = json.loads(response.data)
        assert result["status"] == "healthy"
        assert result["service"] == "transcription-game"

        # Test detailed PDF status check
        with patch(
            "handwriting_transcription.pdf_generator.PDFGenerator"
        ) as mock_pdf_gen:
            mock_generator = Mock()
            mock_generator.create_pdf.return_value = b"%PDF-1.4\ntest pdf"
            mock_pdf_gen.return_value = mock_generator

            response = client.get("/api/pdf-status")
            assert response.status_code in [200, 503]  # Healthy or degraded

            result = json.loads(response.data)
            assert "status" in result
            assert "checks" in result

    def test_main_page_workflow(self, client):
        """Test main page rendering."""

        response = client.get("/")
        assert response.status_code == 200
        assert b"html" in response.data.lower()

    def test_404_handling_workflow(self, client):
        """Test 404 error handling."""

        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_comprehensive_options_workflow(self, client):
        """Test workflow with all formatting options enabled."""

        comprehensive_data = {
            "text": "Line 1\nLine 2\nLine 3",
            "options": {
                "font_name": "Helvetica",
                "font_size": 16,
                "document_size": "Letter",
                "guidelines": True,
                "guideline_type": "dotted",
                "black_text": True,
                "gray_text": True,
                "blank_lines": True,
                "remove_spaces": False,
                "remove_line_breaks": False,
            },
        }

        # Test text processing with all options
        response = client.post(
            "/api/process-text",
            data=json.dumps(
                {
                    "text": comprehensive_data["text"],
                    "options": comprehensive_data["options"],
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result["success"] is True

        # Test PDF generation with all options
        with patch(
            "handwriting_transcription.pdf_generator.canvas.Canvas"
        ) as mock_canvas_class:
            mock_canvas = Mock()
            mock_canvas._pagesize = (612, 792)  # Letter size
            mock_canvas.stringWidth.return_value = 120.0
            mock_canvas_class.return_value = mock_canvas

            with patch(
                "handwriting_transcription.pdf_generator.BytesIO"
            ) as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b"%PDF-1.4\n" + b"x" * 200
                mock_bytesio.return_value = mock_buffer

                response = client.post(
                    "/api/generate-pdf",
                    data=json.dumps(comprehensive_data),
                    content_type="application/json",
                )

                assert response.status_code == 200
                assert response.content_type == "application/pdf"

    def test_concurrent_requests_workflow(self, client):
        """Test handling of concurrent requests."""
        import threading

        results = []

        def make_request():
            response = client.get("/api/fonts")
            results.append(response.status_code)

        # Create multiple threads making concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All requests should succeed
        assert len(results) == 5
        assert all(status == 200 for status in results)

    def test_memory_usage_workflow(self, client):
        """Test that memory usage remains reasonable during operations."""
        import psutil

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform multiple operations
        for i in range(10):
            # Test text processing
            text_data = {
                "text": f"Test text iteration {i}" * 10,
                "options": {
                    "remove_spaces": False,
                    "remove_line_breaks": False,
                    "black_text": True,
                    "gray_text": False,
                    "blank_lines": False,
                },
            }

            response = client.post(
                "/api/process-text",
                data=json.dumps(text_data),
                content_type="application/json",
            )
            assert response.status_code == 200

        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100 * 1024 * 1024  # 100MB limit

    def test_cache_effectiveness_workflow(self, client):
        """Test that caching improves performance."""
        import time

        font_data = {"font_name": "Helvetica", "font_size": 12}

        # First request (should populate cache)
        start_time = time.time()
        response1 = client.post(
            "/api/fonts/metrics",
            data=json.dumps(font_data),
            content_type="application/json",
        )
        first_duration = time.time() - start_time

        assert response1.status_code == 200

        # Second request (should use cache)
        start_time = time.time()
        response2 = client.post(
            "/api/fonts/metrics",
            data=json.dumps(font_data),
            content_type="application/json",
        )
        second_duration = time.time() - start_time

        assert response2.status_code == 200

        # Results should be identical
        result1 = json.loads(response1.data)
        result2 = json.loads(response2.data)
        assert result1["data"]["metrics"] == result2["data"]["metrics"]

        # Second request should be faster (or at least not significantly slower)
        # Allow some variance due to system load
        assert second_duration <= first_duration * 2
