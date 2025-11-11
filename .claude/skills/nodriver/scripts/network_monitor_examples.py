"""
Comprehensive examples for using the NetworkMonitor module.

This file demonstrates practical patterns for network monitoring with CDP,
including request interception, performance analysis, and failure tracking.

Note: These examples require an active Chrome/Chromium browser instance
connected via Chrome DevTools Protocol.
"""

import asyncio
import json
from typing import Dict, Any
from network_monitor import NetworkMonitor, MonitoringPatterns, NetworkInterceptor


# Example 1: Basic network monitoring with metrics
async def example_basic_monitoring():
    """Monitor all network traffic and collect basic metrics."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Network Monitoring")
    print("=" * 60)

    monitor = NetworkMonitor()
    monitor.enable()

    # In a real scenario, you would navigate to a page here
    # This example shows the structure
    example_request = {
        "requestId": "123.1",
        "request": {
            "url": "https://api.example.com/users",
            "method": "GET",
            "headers": {"User-Agent": "Chrome", "Accept": "application/json"},
        },
        "type": "xhr",
        "initiator": {"type": "script"},
    }

    example_response = {
        "requestId": "123.1",
        "response": {
            "status": 200,
            "statusText": "OK",
            "headers": {"content-type": "application/json"},
            "mimeType": "application/json",
        },
    }

    # Process events
    monitor.on_request_will_be_sent(example_request)
    monitor.on_response_received(example_response)
    monitor.on_loading_finished({"requestId": "123.1", "encodedDataLength": 2048})

    # Get metrics
    metrics = monitor.get_metrics()
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Total responses: {metrics['total_responses']}")
    print(f"Total bytes: {metrics['total_bytes']}")
    print(f"Average response time: {metrics['average_response_time']:.4f}s")
    print(f"By resource type: {metrics['by_resource_type']}")


# Example 2: Request interception and modification
async def example_request_interception():
    """Intercept and modify requests before they're sent."""
    print("\n" + "=" * 60)
    print("Example 2: Request Interception and Modification")
    print("=" * 60)

    monitor = NetworkMonitor()
    monitor.enable()

    # Add custom request handler
    async def add_auth_header(request: Dict[str, Any]) -> None:
        """Inject authentication headers into requests."""
        url = request.get("url", "")
        if "api.example.com" in url:
            # In real scenario, modify the request object
            print(f"Adding auth header to: {url}")

    async def log_requests(request: Dict[str, Any]) -> None:
        """Log all outgoing requests."""
        url = request.get("url", "")
        method = request.get("method", "GET")
        print(f"Request: {method} {url}")

    monitor.interceptor.add_request_handler(add_auth_header)
    monitor.interceptor.add_request_handler(log_requests)

    # Simulate request processing
    test_request = {
        "requestId": "req-001",
        "url": "https://api.example.com/data",
        "method": "POST",
    }

    await monitor.interceptor.process_request(test_request)


# Example 3: Response body extraction
async def example_response_body_extraction():
    """Extract and analyze response bodies."""
    print("\n" + "=" * 60)
    print("Example 3: Response Body Extraction")
    print("=" * 60)

    monitor = NetworkMonitor(max_response_bodies=100)
    monitor.enable()

    # Add response handler that extracts body
    async def extract_json_responses(response: Dict[str, Any]) -> None:
        """Extract JSON responses for analysis."""
        status = response.get("status", 0)
        mime_type = response.get("mimeType", "")

        if status == 200 and "application/json" in mime_type:
            print(f"JSON Response detected: {mime_type}")

    monitor.interceptor.add_response_handler(extract_json_responses)

    # Simulate response
    test_response = {
        "requestId": "req-002",
        "status": 200,
        "mimeType": "application/json",
    }

    await monitor.interceptor.process_response(test_response)

    # Store body
    await monitor.set_response_body("req-002", '{"users": []}')
    response = monitor.get_response("req-002")
    if response:
        print(f"Stored body: {response.body}")


# Example 4: Performance metrics and slowest requests
async def example_performance_analysis():
    """Analyze performance metrics and identify slow requests."""
    print("\n" + "=" * 60)
    print("Example 4: Performance Analysis")
    print("=" * 60)

    monitor = NetworkMonitor()
    monitor.enable()

    # Simulate multiple requests with different timings
    requests_data = [
        {
            "requestId": "perf-001",
            "url": "https://example.com/api/users",
            "duration": 0.150,
            "status": 200,
        },
        {
            "requestId": "perf-002",
            "url": "https://example.com/api/posts",
            "duration": 2.500,
            "status": 200,
        },
        {
            "requestId": "perf-003",
            "url": "https://example.com/assets/image.png",
            "duration": 0.050,
            "status": 200,
        },
    ]

    for req_data in requests_data:
        req = {
            "requestId": req_data["requestId"],
            "request": {
                "url": req_data["url"],
                "method": "GET",
                "headers": {},
            },
            "type": "fetch",
            "initiator": {"type": "script"},
        }

        resp = {
            "requestId": req_data["requestId"],
            "response": {
                "status": req_data["status"],
                "statusText": "OK",
                "headers": {},
                "mimeType": "application/json",
            },
        }

        monitor.on_request_will_be_sent(req)
        monitor.on_response_received(resp)
        monitor.on_loading_finished(
            {"requestId": req_data["requestId"], "encodedDataLength": 1024}
        )

    metrics = monitor.get_metrics()
    print(f"Average response time: {metrics['average_response_time']:.4f}s")
    if metrics["slowest_requests"]:
        print("Slowest requests:")
        for req in metrics["slowest_requests"]:
            print(f"  {req['url']}: {req['time']:.4f}s")


# Example 5: Failed request tracking
async def example_failed_request_tracking():
    """Track and analyze failed requests."""
    print("\n" + "=" * 60)
    print("Example 5: Failed Request Tracking")
    print("=" * 60)

    monitor = NetworkMonitor()
    monitor.enable()

    # Simulate failed requests
    failed_requests = [
        {
            "requestId": "fail-001",
            "url": "https://api.example.com/missing",
            "status": 404,
        },
        {
            "requestId": "fail-002",
            "url": "https://api.example.com/error",
            "status": 500,
        },
        {
            "requestId": "fail-003",
            "url": "https://blocked-domain.com/resource",
            "status": 0,
            "error": "Network error",
        },
    ]

    for fail_req in failed_requests:
        req = {
            "requestId": fail_req["requestId"],
            "request": {
                "url": fail_req["url"],
                "method": "GET",
                "headers": {},
            },
            "type": "fetch",
            "initiator": {"type": "script"},
        }

        monitor.on_request_will_be_sent(req)

        if fail_req["status"] == 0:
            # Network error
            monitor.on_loading_failed(
                {
                    "requestId": fail_req["requestId"],
                    "errorText": fail_req.get("error", "Unknown error"),
                }
            )
        else:
            # HTTP error
            resp = {
                "requestId": fail_req["requestId"],
                "response": {
                    "status": fail_req["status"],
                    "statusText": "Error",
                    "headers": {},
                    "mimeType": "text/html",
                },
            }
            monitor.on_response_received(resp)

    metrics = monitor.get_metrics()
    print(f"Failed requests: {len(metrics['failed_requests'])}")
    for failed in metrics["failed_requests"]:
        print(f"  {failed['method']} {failed['url']}")
        print(f"    Status: {failed['status']} {failed['status_text']}")


# Example 6: URL blocking and security monitoring
async def example_security_monitoring():
    """Block unwanted requests and monitor security."""
    print("\n" + "=" * 60)
    print("Example 6: Security Monitoring")
    print("=" * 60)

    monitor = MonitoringPatterns.create_security_monitor()
    monitor.enable()

    # Check if domains are blocked
    test_urls = [
        "https://tracker.example.com/tracking.js",
        "https://analytics.google.com/analytics.js",
        "https://api.example.com/data",
    ]

    for url in test_urls:
        should_block = monitor.interceptor.should_block(url)
        status = "BLOCKED" if should_block else "ALLOWED"
        print(f"{status}: {url}")


# Example 7: API call monitoring
async def example_api_monitoring():
    """Monitor and analyze API calls specifically."""
    print("\n" + "=" * 60)
    print("Example 7: API Call Monitoring")
    print("=" * 60)

    monitor = MonitoringPatterns.create_api_monitor()
    monitor.enable()

    # Simulate API requests
    api_requests = [
        {
            "requestId": "api-001",
            "url": "https://api.example.com/users",
            "method": "GET",
        },
        {
            "requestId": "api-002",
            "url": "https://api.example.com/users",
            "method": "POST",
        },
        {
            "requestId": "res-001",
            "url": "https://example.com/image.png",
            "method": "GET",
        },
    ]

    for api_req in api_requests:
        req = {
            "requestId": api_req["requestId"],
            "request": api_req,
            "type": "fetch",
            "initiator": {"type": "script"},
        }
        print(f"\nProcessing: {api_req['method']} {api_req['url']}")
        await monitor.interceptor.process_request(req)


# Example 8: Filtering and analyzing requests
async def example_request_filtering():
    """Filter requests by various criteria."""
    print("\n" + "=" * 60)
    print("Example 8: Request Filtering")
    print("=" * 60)

    monitor = NetworkMonitor()
    monitor.enable()

    # Simulate various requests
    test_requests = [
        ("req-001", "https://api.example.com/users", "GET", "xhr", 200),
        ("req-002", "https://api.example.com/posts", "POST", "fetch", 201),
        ("req-003", "https://example.com/image.png", "GET", "image", 200),
        ("req-004", "https://api.example.com/missing", "GET", "xhr", 404),
    ]

    for req_id, url, method, resource_type, status in test_requests:
        req = {
            "requestId": req_id,
            "request": {
                "url": url,
                "method": method,
                "headers": {},
            },
            "type": resource_type,
            "initiator": {"type": "script"},
        }

        resp = {
            "requestId": req_id,
            "response": {
                "status": status,
                "statusText": "OK" if status < 400 else "Error",
                "headers": {},
                "mimeType": "application/json",
            },
        }

        monitor.on_request_will_be_sent(req)
        monitor.on_response_received(resp)

    # Filter examples
    print("\nAll POST requests:")
    post_requests = monitor.filter_requests(method="POST")
    for req in post_requests:
        print(f"  {req['request']['url']}")

    print("\nAll failed requests (4xx/5xx):")
    failed = monitor.filter_requests(status=404)
    for req in failed:
        print(f"  {req['request']['url']}")

    print("\nXHR requests:")
    xhr = monitor.filter_requests(resource_type="xhr")
    for req in xhr:
        print(f"  {req['request']['url']}")


# Example 9: Creating a custom monitoring pattern
async def example_custom_pattern():
    """Create a custom monitoring pattern for specific use cases."""
    print("\n" + "=" * 60)
    print("Example 9: Custom Monitoring Pattern")
    print("=" * 60)

    # Create a monitor for e-commerce tracking
    ecommerce_monitor = NetworkMonitor()
    ecommerce_monitor.enable()

    async def track_cart_operations(request: Dict[str, Any]) -> None:
        """Track shopping cart related requests."""
        url = request.get("url", "")
        if "cart" in url or "checkout" in url:
            print(f"Cart operation: {url}")

    async def track_product_views(response: Dict[str, Any]) -> None:
        """Track product data responses."""
        status = response.get("status", 0)
        if status == 200:
            print(f"Product data loaded successfully")

    ecommerce_monitor.interceptor.add_request_handler(track_cart_operations)
    ecommerce_monitor.interceptor.add_response_handler(track_product_views)

    # Simulate e-commerce requests
    cart_request = {
        "requestId": "ecom-001",
        "url": "https://shop.example.com/api/cart/add",
        "method": "POST",
    }

    cart_response = {
        "requestId": "ecom-001",
        "status": 200,
        "mimeType": "application/json",
    }

    print("\nE-commerce transaction:")
    await ecommerce_monitor.interceptor.process_request(cart_request)
    await ecommerce_monitor.interceptor.process_response(cart_response)


# Example 10: Comprehensive session monitoring
async def example_comprehensive_session():
    """Monitor a complete browsing session."""
    print("\n" + "=" * 60)
    print("Example 10: Comprehensive Session Monitoring")
    print("=" * 60)

    monitor = NetworkMonitor(max_response_bodies=50)
    monitor.enable()

    # Simulate a complete page load session
    session_events = [
        {
            "type": "request",
            "id": "doc-001",
            "url": "https://example.com",
            "method": "GET",
            "resource_type": "document",
        },
        {
            "type": "response",
            "id": "doc-001",
            "status": 200,
            "size": 50000,
        },
        {
            "type": "request",
            "id": "css-001",
            "url": "https://example.com/styles.css",
            "method": "GET",
            "resource_type": "stylesheet",
        },
        {
            "type": "response",
            "id": "css-001",
            "status": 200,
            "size": 15000,
        },
        {
            "type": "request",
            "id": "js-001",
            "url": "https://example.com/app.js",
            "method": "GET",
            "resource_type": "script",
        },
        {
            "type": "response",
            "id": "js-001",
            "status": 200,
            "size": 100000,
        },
        {
            "type": "request",
            "id": "api-001",
            "url": "https://api.example.com/config",
            "method": "GET",
            "resource_type": "xhr",
        },
        {
            "type": "response",
            "id": "api-001",
            "status": 200,
            "size": 5000,
        },
    ]

    # Process session events
    for event in session_events:
        if event["type"] == "request":
            req = {
                "requestId": event["id"],
                "request": {
                    "url": event["url"],
                    "method": event["method"],
                    "headers": {},
                },
                "type": event["resource_type"],
                "initiator": {"type": "script"},
            }
            monitor.on_request_will_be_sent(req)

        elif event["type"] == "response":
            resp = {
                "requestId": event["id"],
                "response": {
                    "status": event["status"],
                    "statusText": "OK",
                    "headers": {},
                    "mimeType": "application/json",
                },
            }
            monitor.on_response_received(resp)
            monitor.on_loading_finished(
                {"requestId": event["id"], "encodedDataLength": event["size"]}
            )

    # Generate final report
    metrics = monitor.get_metrics()
    print("\nSession Summary:")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Total bytes transferred: {metrics['total_bytes']} bytes")
    print(f"Average response time: {metrics['average_response_time']:.4f}s")
    print(f"\nBy resource type:")
    for rtype, count in metrics["by_resource_type"].items():
        print(f"  {rtype}: {count}")


async def main():
    """Run all examples."""
    examples = [
        example_basic_monitoring,
        example_request_interception,
        example_response_body_extraction,
        example_performance_analysis,
        example_failed_request_tracking,
        example_security_monitoring,
        example_api_monitoring,
        example_request_filtering,
        example_custom_pattern,
        example_comprehensive_session,
    ]

    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
