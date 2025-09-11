"""
Unit tests for RateLimiter module.
"""

import time
from unittest.mock import Mock
from handwriting_transcription.rate_limiter import (
    RateLimiter,
    PDFRateLimiter,
    get_client_id,
    pdf_rate_limiter,
)


class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_init(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        assert limiter.max_requests == 5
        assert limiter.window_seconds == 60
        assert len(limiter.requests) == 0

    def test_is_allowed_first_request(self):
        """Test that first request is always allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        result = limiter.is_allowed("client1")
        assert result is True

    def test_is_allowed_within_limit(self):
        """Test requests within limit are allowed."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Make requests within limit
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True

    def test_is_allowed_exceeds_limit(self):
        """Test requests exceeding limit are denied."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        # Make requests up to limit
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is True

        # Next request should be denied
        assert limiter.is_allowed("client1") is False

    def test_is_allowed_different_clients(self):
        """Test that different clients have separate limits."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Each client should be allowed one request
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client2") is True

        # But second requests should be denied
        assert limiter.is_allowed("client1") is False
        assert limiter.is_allowed("client2") is False

    def test_window_expiration(self):
        """Test that requests expire after the time window."""
        limiter = RateLimiter(max_requests=1, window_seconds=0.1)  # Very short window

        # Make request
        assert limiter.is_allowed("client1") is True
        assert limiter.is_allowed("client1") is False  # Should be denied

        # Wait for window to expire
        time.sleep(0.2)

        # Should be allowed again
        assert limiter.is_allowed("client1") is True

    def test_get_remaining_requests(self):
        """Test getting remaining request count."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        # Initially should have full limit
        assert limiter.get_remaining_requests("client1") == 3

        # After one request
        limiter.is_allowed("client1")
        assert limiter.get_remaining_requests("client1") == 2

        # After two requests
        limiter.is_allowed("client1")
        assert limiter.get_remaining_requests("client1") == 1

        # After three requests
        limiter.is_allowed("client1")
        assert limiter.get_remaining_requests("client1") == 0

    def test_get_reset_time(self):
        """Test getting reset time for rate limit."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # No reset time initially
        assert limiter.get_reset_time("client1") is None

        # Make request to hit limit
        limiter.is_allowed("client1")
        limiter.is_allowed("client1")  # This should be denied

        # Should have reset time now
        reset_time = limiter.get_reset_time("client1")
        assert reset_time is not None
        assert isinstance(reset_time, float)
        assert reset_time > time.time()

    def test_clear_client(self):
        """Test clearing rate limit data for specific client."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Make request to create data
        limiter.is_allowed("client1")
        assert "client1" in limiter.requests

        # Clear client data
        limiter.clear_client("client1")
        assert "client1" not in limiter.requests

    def test_clear_all(self):
        """Test clearing all rate limit data."""
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        # Make requests for multiple clients
        limiter.is_allowed("client1")
        limiter.is_allowed("client2")

        assert len(limiter.requests) == 2

        # Clear all data
        limiter.clear_all()
        assert len(limiter.requests) == 0


class TestPDFRateLimiter:
    """Test cases for PDFRateLimiter class."""

    def test_init(self):
        """Test PDFRateLimiter initialization."""
        limiter = PDFRateLimiter()

        assert hasattr(limiter, "pdf_limiter")
        assert hasattr(limiter, "preview_limiter")
        assert hasattr(limiter, "api_limiter")

    def test_check_pdf_generation_allowed(self):
        """Test PDF generation check when allowed."""
        limiter = PDFRateLimiter()

        is_allowed, rate_info = limiter.check_pdf_generation("client1")

        assert is_allowed is True
        assert isinstance(rate_info, dict)
        assert "allowed" in rate_info
        assert "remaining" in rate_info
        assert "limit_type" in rate_info
        assert rate_info["limit_type"] == "pdf_generation"

    def test_check_pdf_generation_denied(self):
        """Test PDF generation check when denied."""
        limiter = PDFRateLimiter()

        # Exhaust the limit
        for _ in range(5):  # Default PDF limit is 5
            limiter.check_pdf_generation("client1")

        # Next request should be denied
        is_allowed, rate_info = limiter.check_pdf_generation("client1")

        assert is_allowed is False
        assert rate_info["allowed"] is False
        assert rate_info["remaining"] == 0

    def test_check_preview_generation_allowed(self):
        """Test preview generation check when allowed."""
        limiter = PDFRateLimiter()

        is_allowed, rate_info = limiter.check_preview_generation("client1")

        assert is_allowed is True
        assert rate_info["limit_type"] == "preview_generation"

    def test_check_api_access_allowed(self):
        """Test API access check when allowed."""
        limiter = PDFRateLimiter()

        is_allowed, rate_info = limiter.check_api_access("client1")

        assert is_allowed is True
        assert rate_info["limit_type"] == "api_access"

    def test_different_limits_independent(self):
        """Test that different rate limits are independent."""
        limiter = PDFRateLimiter()

        # Exhaust PDF limit
        for _ in range(5):
            limiter.check_pdf_generation("client1")

        # PDF should be denied
        pdf_allowed, _ = limiter.check_pdf_generation("client1")
        assert pdf_allowed is False

        # But preview should still be allowed
        preview_allowed, _ = limiter.check_preview_generation("client1")
        assert preview_allowed is True

        # And API should still be allowed
        api_allowed, _ = limiter.check_api_access("client1")
        assert api_allowed is True


class TestGetClientId:
    """Test cases for get_client_id function."""

    def test_get_client_id_basic(self):
        """Test basic client ID extraction."""
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.remote_addr = "192.168.1.1"

        client_id = get_client_id(mock_request)

        assert isinstance(client_id, str)
        assert "192.168.1.1" in client_id

    def test_get_client_id_with_forwarded_for(self):
        """Test client ID extraction with X-Forwarded-For header."""
        mock_request = Mock()
        mock_request.headers = {
            "X-Forwarded-For": "10.0.0.1, 192.168.1.1",
            "User-Agent": "Mozilla/5.0",
        }
        mock_request.remote_addr = "192.168.1.1"

        client_id = get_client_id(mock_request)

        assert "10.0.0.1" in client_id  # Should use first IP from X-Forwarded-For

    def test_get_client_id_with_real_ip(self):
        """Test client ID extraction with X-Real-IP header."""
        mock_request = Mock()
        mock_request.headers = {"X-Real-IP": "10.0.0.2", "User-Agent": "Mozilla/5.0"}
        mock_request.remote_addr = "192.168.1.1"

        client_id = get_client_id(mock_request)

        assert "10.0.0.2" in client_id  # Should use X-Real-IP

    def test_get_client_id_no_remote_addr(self):
        """Test client ID extraction when remote_addr is None."""
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.remote_addr = None

        client_id = get_client_id(mock_request)

        assert "unknown" in client_id

    def test_get_client_id_with_user_agent(self):
        """Test that user agent affects client ID."""
        mock_request1 = Mock()
        mock_request1.headers = {"User-Agent": "Mozilla/5.0"}
        mock_request1.remote_addr = "192.168.1.1"

        mock_request2 = Mock()
        mock_request2.headers = {"User-Agent": "Chrome/91.0"}
        mock_request2.remote_addr = "192.168.1.1"

        client_id1 = get_client_id(mock_request1)
        client_id2 = get_client_id(mock_request2)

        # Same IP but different user agents should produce different IDs
        assert client_id1 != client_id2


class TestRateLimitDecorators:
    """Test cases for rate limit decorators."""

    def test_get_client_id_function(self):
        """Test get_client_id function with mock request."""
        from handwriting_transcription.rate_limiter import get_client_id

        mock_request = Mock()
        mock_request.headers = {"User-Agent": "TestAgent"}
        mock_request.remote_addr = "192.168.1.1"

        client_id = get_client_id(mock_request)

        assert isinstance(client_id, str)
        assert "192.168.1.1" in client_id

    def test_rate_limit_decorator_exists(self):
        """Test that rate limit decorators can be imported."""
        from handwriting_transcription.rate_limiter import (
            pdf_rate_limit,
            preview_rate_limit,
            api_rate_limit,
        )

        assert pdf_rate_limit is not None
        assert preview_rate_limit is not None
        assert api_rate_limit is not None


class TestGlobalRateLimiter:
    """Test cases for global rate limiter instance."""

    def test_global_instance_exists(self):
        """Test that global rate limiter instance exists."""
        assert pdf_rate_limiter is not None
        assert isinstance(pdf_rate_limiter, PDFRateLimiter)

    def test_global_instance_functionality(self):
        """Test that global instance works correctly."""
        # Should be able to check limits
        is_allowed, rate_info = pdf_rate_limiter.check_pdf_generation("test_client")

        assert isinstance(is_allowed, bool)
        assert isinstance(rate_info, dict)

    def test_rate_limiter_thread_safety(self):
        """Test rate limiter thread safety with concurrent access."""
        import threading
        import time

        limiter = RateLimiter(max_requests=10, window_seconds=1)
        results = []

        def make_requests():
            for _ in range(5):
                result = limiter.is_allowed("concurrent_client")
                results.append(result)
                time.sleep(0.01)  # Small delay

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Should have some allowed and some denied requests
        assert len(results) == 15  # 3 threads * 5 requests each
        assert True in results  # Some should be allowed

        # Total allowed should not exceed limit
        allowed_count = sum(1 for r in results if r)
        assert allowed_count <= 10  # Should respect the limit
