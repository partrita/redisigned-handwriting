#!/usr/bin/env python3
"""
Performance benchmark script to demonstrate caching improvements.
"""

import time
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from handwriting_transcription.font_manager import FontManager
from handwriting_transcription.text_processor import TextProcessor


def benchmark_font_operations():
    """Benchmark font operations with and without caching."""
    print("=== Font Manager Performance Benchmark ===")

    manager = FontManager()

    # Test data
    test_texts = [
        "The quick brown fox jumps over the lazy dog",
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit",
        "Hello World! This is a test string for benchmarking",
        "Performance testing with various text lengths and content",
        "Caching should improve response times significantly",
    ]

    font_names = ["Helvetica", "Times-Roman", "Courier"]
    font_sizes = [10, 12, 14, 16, 18]

    # Benchmark text dimension calculations
    print("\n1. Text Dimension Calculations:")

    # First run (populate cache)
    start_time = time.time()
    for text in test_texts:
        for font in font_names:
            for size in font_sizes:
                manager.calculate_text_dimensions(text, font, size)
    first_run_time = time.time() - start_time

    # Second run (use cache)
    start_time = time.time()
    for text in test_texts:
        for font in font_names:
            for size in font_sizes:
                manager.calculate_text_dimensions(text, font, size)
    second_run_time = time.time() - start_time

    print(f"   First run (no cache):  {first_run_time:.4f} seconds")
    print(f"   Second run (cached):   {second_run_time:.4f} seconds")
    print(f"   Speed improvement:     {first_run_time / second_run_time:.2f}x faster")

    # Benchmark font metrics
    print("\n2. Font Metrics Calculations:")

    # Clear cache for fair test
    manager.clear_cache()

    # First run
    start_time = time.time()
    for font in font_names * 10:  # Repeat to get measurable time
        for size in font_sizes:
            manager.get_font_metrics(font, size)
    first_run_time = time.time() - start_time

    # Second run (cached)
    start_time = time.time()
    for font in font_names * 10:
        for size in font_sizes:
            manager.get_font_metrics(font, size)
    second_run_time = time.time() - start_time

    print(f"   First run (no cache):  {first_run_time:.4f} seconds")
    print(f"   Second run (cached):   {second_run_time:.4f} seconds")
    print(f"   Speed improvement:     {first_run_time / second_run_time:.2f}x faster")


def benchmark_text_processing():
    """Benchmark text processing operations."""
    print("\n=== Text Processor Performance Benchmark ===")

    # Generate test data
    small_text = "Hello world! " * 10
    medium_text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50
    large_text = "This is a longer text for performance testing. " * 200

    test_cases = [
        ("Small text", small_text),
        ("Medium text", medium_text),
        ("Large text", large_text),
    ]

    operations = [
        ("Remove spaces", TextProcessor.remove_spaces),
        ("Remove line breaks", TextProcessor.remove_line_breaks),
        ("Sanitize input", TextProcessor.sanitize_input),
        ("Normalize text", TextProcessor.normalize_text),
    ]

    for text_name, text in test_cases:
        print(f"\n{text_name} ({len(text)} characters):")

        for op_name, operation in operations:
            # Warm up
            for _ in range(5):
                operation(text)

            # Benchmark
            start_time = time.time()
            iterations = 100
            for _ in range(iterations):
                operation(text)
            end_time = time.time()

            avg_time = (end_time - start_time) / iterations
            print(f"   {op_name:20}: {avg_time * 1000:.3f} ms/operation")


def benchmark_memory_usage():
    """Benchmark memory usage of caching."""
    print("\n=== Memory Usage Benchmark ===")

    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"Initial memory usage: {initial_memory:.2f} MB")

        # Create font manager and populate cache
        manager = FontManager()

        # Add many items to cache
        for i in range(1000):
            text = f"Test text {i}"
            manager.calculate_text_dimensions(text, "Helvetica", 12)
            manager.get_font_metrics("Helvetica", 12 + (i % 10))

        cached_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Memory with 1000+ cached items: {cached_memory:.2f} MB")
        print(f"Memory increase: {cached_memory - initial_memory:.2f} MB")

        # Clear cache
        manager.clear_cache()

        cleared_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"Memory after cache clear: {cleared_memory:.2f} MB")
        print(f"Memory recovered: {cached_memory - cleared_memory:.2f} MB")

    except ImportError:
        print("psutil not available, skipping memory benchmark")


def benchmark_rate_limiting():
    """Benchmark rate limiting performance."""
    print("\n=== Rate Limiting Performance Benchmark ===")

    from handwriting_transcription.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests=1000, window_seconds=60)

    # Benchmark rate limit checking
    start_time = time.time()
    iterations = 10000

    for i in range(iterations):
        client_id = f"client_{i % 100}"  # 100 different clients
        limiter.is_allowed(client_id)

    end_time = time.time()

    avg_time = (end_time - start_time) / iterations
    print(f"Rate limit check: {avg_time * 1000:.3f} ms/check")
    print(f"Throughput: {iterations / (end_time - start_time):.0f} checks/second")


def main():
    """Run all benchmarks."""
    print("Transcription Game Performance Benchmarks")
    print("=" * 50)

    benchmark_font_operations()
    benchmark_text_processing()
    benchmark_memory_usage()
    benchmark_rate_limiting()

    print("\n" + "=" * 50)
    print("Benchmark completed!")
    print("\nKey Performance Improvements:")
    print("- Font operations are cached for faster repeated access")
    print("- Text processing is optimized for various text sizes")
    print("- Rate limiting provides efficient request throttling")
    print("- Memory usage is controlled with cache size limits")


if __name__ == "__main__":
    main()
