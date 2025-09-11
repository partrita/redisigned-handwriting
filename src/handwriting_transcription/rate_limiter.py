"""
Rate limiting module to prevent abuse of PDF generation.
"""

import time
import logging
from typing import Optional
from collections import defaultdict, deque
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API endpoints to prevent abuse."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)  # client_id -> deque of timestamps
        self.lock = Lock()

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a request from client_id is allowed.

        Args:
            client_id: Unique identifier for the client (IP address, user ID, etc.)

        Returns:
            True if request is allowed, False if rate limited
        """
        with self.lock:
            now = time.time()
            client_requests = self.requests[client_id]

            # Remove old requests outside the window
            while client_requests and client_requests[0] <= now - self.window_seconds:
                client_requests.popleft()

            # Check if under the limit
            if len(client_requests) < self.max_requests:
                client_requests.append(now)
                return True

            return False

    def get_reset_time(self, client_id: str) -> Optional[float]:
        """
        Get the time when the rate limit will reset for a client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            Timestamp when rate limit resets, or None if not rate limited
        """
        with self.lock:
            client_requests = self.requests[client_id]
            if client_requests and len(client_requests) >= self.max_requests:
                return client_requests[0] + self.window_seconds
            return None

    def get_remaining_requests(self, client_id: str) -> int:
        """
        Get the number of remaining requests for a client.

        Args:
            client_id: Unique identifier for the client

        Returns:
            Number of remaining requests in the current window
        """
        with self.lock:
            now = time.time()
            client_requests = self.requests[client_id]

            # Remove old requests outside the window
            while client_requests and client_requests[0] <= now - self.window_seconds:
                client_requests.popleft()

            return max(0, self.max_requests - len(client_requests))

    def clear_client(self, client_id: str):
        """Clear rate limit data for a specific client."""
        with self.lock:
            if client_id in self.requests:
                del self.requests[client_id]

    def clear_all(self):
        """Clear all rate limit data."""
        with self.lock:
            self.requests.clear()


class PDFRateLimiter:
    """Specialized rate limiter for PDF generation with different limits."""

    def __init__(self):
        """Initialize PDF rate limiter with appropriate limits."""
        # Different rate limits for different operations
        self.pdf_limiter = RateLimiter(
            max_requests=5, window_seconds=60
        )  # 5 PDFs per minute
        self.preview_limiter = RateLimiter(
            max_requests=30, window_seconds=60
        )  # 30 previews per minute
        self.api_limiter = RateLimiter(
            max_requests=100, window_seconds=60
        )  # 100 API calls per minute

    def check_pdf_generation(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if PDF generation is allowed for client.

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        is_allowed = self.pdf_limiter.is_allowed(client_id)

        rate_limit_info = {
            "allowed": is_allowed,
            "remaining": self.pdf_limiter.get_remaining_requests(client_id),
            "reset_time": self.pdf_limiter.get_reset_time(client_id),
            "limit_type": "pdf_generation",
        }

        if not is_allowed:
            logger.warning(f"PDF generation rate limit exceeded for client {client_id}")

        return is_allowed, rate_limit_info

    def check_preview_generation(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if preview generation is allowed for client.

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        is_allowed = self.preview_limiter.is_allowed(client_id)

        rate_limit_info = {
            "allowed": is_allowed,
            "remaining": self.preview_limiter.get_remaining_requests(client_id),
            "reset_time": self.preview_limiter.get_reset_time(client_id),
            "limit_type": "preview_generation",
        }

        if not is_allowed:
            logger.warning(
                f"Preview generation rate limit exceeded for client {client_id}"
            )

        return is_allowed, rate_limit_info

    def check_api_access(self, client_id: str) -> tuple[bool, dict]:
        """
        Check if general API access is allowed for client.

        Args:
            client_id: Client identifier

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        is_allowed = self.api_limiter.is_allowed(client_id)

        rate_limit_info = {
            "allowed": is_allowed,
            "remaining": self.api_limiter.get_remaining_requests(client_id),
            "reset_time": self.api_limiter.get_reset_time(client_id),
            "limit_type": "api_access",
        }

        if not is_allowed:
            logger.warning(f"API access rate limit exceeded for client {client_id}")

        return is_allowed, rate_limit_info


# Global rate limiter instance
pdf_rate_limiter = PDFRateLimiter()


def get_client_id(request) -> str:
    """
    Extract client identifier from Flask request.

    Args:
        request: Flask request object

    Returns:
        Client identifier string
    """
    # Try to get real IP address from headers (for reverse proxy setups)
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("X-Real-IP", "")
    if not client_ip:
        client_ip = request.remote_addr or "unknown"

    # Include user agent for additional uniqueness
    user_agent = request.headers.get("User-Agent", "")[:50]  # Limit length

    return f"{client_ip}:{hash(user_agent) % 10000}"


def rate_limit_decorator(limiter_method):
    """
    Decorator for rate limiting Flask routes.

    Args:
        limiter_method: Method from PDFRateLimiter to use for checking
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                from flask import request, jsonify
            except ImportError:
                # For testing without Flask context
                request = None

                def jsonify(x):
                    return x

            client_id = get_client_id(request)
            is_allowed, rate_info = limiter_method(client_id)

            if not is_allowed:
                response = {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Try again later.",
                    "rate_limit": rate_info,
                }

                # Add rate limit headers
                resp = jsonify(response)
                resp.status_code = 429
                resp.headers["X-RateLimit-Limit"] = str(
                    pdf_rate_limiter.pdf_limiter.max_requests
                )
                resp.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
                if rate_info["reset_time"]:
                    resp.headers["X-RateLimit-Reset"] = str(
                        int(rate_info["reset_time"])
                    )

                return resp

            # Add rate limit headers to successful responses
            response = func(*args, **kwargs)
            if hasattr(response, "headers"):
                response.headers["X-RateLimit-Limit"] = str(
                    pdf_rate_limiter.pdf_limiter.max_requests
                )
                response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])

            return response

        wrapper.__name__ = func.__name__
        return wrapper

    return decorator


# Convenience decorators
def pdf_rate_limit(func):
    """Rate limit decorator for PDF generation endpoints."""
    return rate_limit_decorator(pdf_rate_limiter.check_pdf_generation)(func)


def preview_rate_limit(func):
    """Rate limit decorator for preview generation endpoints."""
    return rate_limit_decorator(pdf_rate_limiter.check_preview_generation)(func)


def api_rate_limit(func):
    """Rate limit decorator for general API endpoints."""
    return rate_limit_decorator(pdf_rate_limiter.check_api_access)(func)
