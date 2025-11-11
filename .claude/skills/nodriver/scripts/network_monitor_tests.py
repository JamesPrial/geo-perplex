"""
Test patterns and examples for NetworkMonitor.

Demonstrates how to write tests and verify network monitoring behavior.
"""

import asyncio
from network_monitor import NetworkMonitor, MonitoringPatterns, NetworkRequest, NetworkResponse
from network_monitor_integration import (
    NetworkMonitorSession,
    NetworkEventCapture,
    PerformanceAnalyzer,
    SecurityAnalyzer,
)


class TestNetworkMonitorBasics:
    """Test basic NetworkMonitor functionality."""

    def test_request_tracking(self):
        """Test that requests are properly tracked."""
        monitor = NetworkMonitor()
        monitor.enable()

        request_data = {
            "requestId": "test-1",
            "request": {
                "url": "https://api.example.com/users",
                "method": "GET",
                "headers": {"Accept": "application/json"},
            },
            "type": "xhr",
            "initiator": {"type": "script"},
        }

        monitor.on_request_will_be_sent(request_data)

        # Verify request was recorded
        request = monitor.get_request("test-1")
        assert request is not None
        assert request.url == "https://api.example.com/users"
        assert request.method == "GET"
        print("✓ Request tracking test passed")

    def test_response_tracking(self):
        """Test that responses are properly tracked."""
        monitor = NetworkMonitor()
        monitor.enable()

        # First record the request
        request_data = {
            "requestId": "test-2",
            "request": {
                "url": "https://api.example.com/posts",
                "method": "POST",
                "headers": {},
            },
            "type": "xhr",
            "initiator": {"type": "script"},
        }
        monitor.on_request_will_be_sent(request_data)

        # Then record the response
        response_data = {
            "requestId": "test-2",
            "response": {
                "status": 201,
                "statusText": "Created",
                "headers": {"content-type": "application/json"},
                "mimeType": "application/json",
            },
        }
        monitor.on_response_received(response_data)

        # Verify response was recorded
        response = monitor.get_response("test-2")
        assert response is not None
        assert response.status == 201
        assert response.status_text == "Created"
        print("✓ Response tracking test passed")

    def test_failed_request_tracking(self):
        """Test tracking of failed requests."""
        monitor = NetworkMonitor()
        monitor.enable()

        request_data = {
            "requestId": "test-3",
            "request": {
                "url": "https://api.example.com/missing",
                "method": "GET",
                "headers": {},
            },
            "type": "xhr",
            "initiator": {"type": "script"},
        }
        monitor.on_request_will_be_sent(request_data)

        # Simulate 404 response
        response_data = {
            "requestId": "test-3",
            "response": {
                "status": 404,
                "statusText": "Not Found",
                "headers": {},
                "mimeType": "text/html",
            },
        }
        monitor.on_response_received(response_data)

        metrics = monitor.get_metrics()
        assert len(metrics["failed_requests"]) == 1
        assert metrics["failed_requests"][0]["status"] == 404
        print("✓ Failed request tracking test passed")

    def test_metrics_collection(self):
        """Test comprehensive metrics collection."""
        monitor = NetworkMonitor()
        monitor.enable()

        # Record multiple requests
        for i in range(5):
            req = {
                "requestId": f"metric-{i}",
                "request": {
                    "url": f"https://api.example.com/resource/{i}",
                    "method": "GET",
                    "headers": {},
                },
                "type": "xhr",
                "initiator": {"type": "script"},
            }
            resp = {
                "requestId": f"metric-{i}",
                "response": {
                    "status": 200,
                    "statusText": "OK",
                    "headers": {},
                    "mimeType": "application/json",
                },
            }
            monitor.on_request_will_be_sent(req)
            monitor.on_response_received(resp)
            monitor.on_loading_finished({"requestId": f"metric-{i}", "encodedDataLength": 1024})

        metrics = monitor.get_metrics()
        assert metrics["total_requests"] == 5
        assert metrics["total_responses"] == 5
        assert metrics["total_bytes"] == 5120  # 5 * 1024
        assert "xhr" in metrics["by_resource_type"]
        print("✓ Metrics collection test passed")

    def test_request_filtering(self):
        """Test request filtering by various criteria."""
        monitor = NetworkMonitor()
        monitor.enable()

        # Record different types of requests
        test_cases = [
            ("filter-1", "https://api.example.com/users", "POST", "xhr", 200),
            ("filter-2", "https://api.example.com/posts", "GET", "fetch", 200),
            ("filter-3", "https://example.com/image.png", "GET", "image", 200),
            ("filter-4", "https://api.example.com/error", "GET", "xhr", 500),
        ]

        for req_id, url, method, res_type, status in test_cases:
            req = {
                "requestId": req_id,
                "request": {
                    "url": url,
                    "method": method,
                    "headers": {},
                },
                "type": res_type,
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

        # Test filtering by method
        post_requests = monitor.filter_requests(method="POST")
        assert len(post_requests) == 1
        assert post_requests[0]["request"]["method"] == "POST"

        # Test filtering by resource type
        xhr_requests = monitor.filter_requests(resource_type="xhr")
        assert len(xhr_requests) == 2

        # Test filtering by status
        failed_requests = monitor.filter_requests(status=500)
        assert len(failed_requests) == 1

        print("✓ Request filtering test passed")


class TestNetworkInterception:
    """Test request/response interception."""

    async def test_request_modification(self):
        """Test modifying requests before they're sent."""
        monitor = NetworkMonitor()
        monitor.enable()

        # Add handler to modify requests
        async def add_custom_header(request):
            if "api.example.com" in request.get("url", ""):
                request.setdefault("headers", {})["X-Custom"] = "test-value"

        monitor.interceptor.add_request_handler(add_custom_header)

        test_request = {
            "requestId": "intercept-1",
            "url": "https://api.example.com/data",
            "method": "GET",
            "headers": {},
        }

        processed = await monitor.interceptor.process_request(test_request)
        assert processed["headers"].get("X-Custom") == "test-value"
        print("✓ Request modification test passed")

    def test_url_blocking(self):
        """Test URL pattern blocking."""
        monitor = NetworkMonitor()

        # Add blocking rules
        monitor.interceptor.block_url_pattern("*.analytics.js")
        monitor.interceptor.block_url_pattern("*.tracker.com")

        # Test blocking
        assert monitor.interceptor.should_block("https://script.analytics.js")
        assert monitor.interceptor.should_block("https://tracking.tracker.com/pixel.gif")
        assert not monitor.interceptor.should_block("https://api.example.com/data")

        print("✓ URL blocking test passed")


class TestMonitoringPatterns:
    """Test pre-built monitoring patterns."""

    def test_api_monitor_pattern(self):
        """Test API monitoring pattern."""
        api_monitor = MonitoringPatterns.create_api_monitor()
        api_monitor.enable()

        # Add sample API requests
        api_req = {
            "requestId": "api-pattern-1",
            "request": {
                "url": "https://api.example.com/users",
                "method": "POST",
                "headers": {},
            },
            "type": "fetch",
            "initiator": {"type": "script"},
        }

        api_monitor.on_request_will_be_sent(api_req)
        metrics = api_monitor.get_metrics()

        assert metrics["total_requests"] == 1
        print("✓ API monitor pattern test passed")

    def test_security_monitor_pattern(self):
        """Test security monitoring pattern."""
        sec_monitor = MonitoringPatterns.create_security_monitor()
        sec_monitor.enable()

        # Verify default blocklist
        assert sec_monitor.interceptor.should_block("https://analytics.google.com/ga.js")
        assert not sec_monitor.interceptor.should_block("https://safe.example.com/api")

        print("✓ Security monitor pattern test passed")

    def test_performance_monitor_pattern(self):
        """Test performance monitoring pattern."""
        perf_monitor = MonitoringPatterns.create_performance_monitor()
        perf_monitor.enable()

        # Add sample request with server error
        req = {
            "requestId": "perf-1",
            "request": {
                "url": "https://api.example.com/error",
                "method": "GET",
                "headers": {},
            },
            "type": "xhr",
            "initiator": {"type": "script"},
        }

        resp = {
            "requestId": "perf-1",
            "response": {
                "status": 500,
                "statusText": "Internal Server Error",
                "headers": {},
                "mimeType": "application/json",
            },
        }

        perf_monitor.on_request_will_be_sent(req)
        perf_monitor.on_response_received(resp)

        metrics = perf_monitor.get_metrics()
        assert len(metrics["failed_requests"]) == 1

        print("✓ Performance monitor pattern test passed")


class TestIntegrationUtilities:
    """Test integration utilities."""

    async def test_monitoring_session(self):
        """Test NetworkMonitorSession lifecycle."""
        session = NetworkMonitorSession(name="test_session")

        async with session as monitor:
            monitor.enable()

            req = {
                "requestId": "session-1",
                "request": {
                    "url": "https://example.com",
                    "method": "GET",
                    "headers": {},
                },
                "type": "document",
                "initiator": {"type": "other"},
            }
            monitor.on_request_will_be_sent(req)

        assert session.start_time is not None
        assert session.end_time is not None
        assert session.duration() > 0

        summary = session.get_summary()
        assert summary["session_name"] == "test_session"
        assert summary["metrics"]["total_requests"] == 1

        print("✓ Monitoring session test passed")

    def test_event_capture(self):
        """Test network event capture."""
        capture = NetworkEventCapture()

        request_event = {
            "requestId": "cap-1",
            "request": {
                "url": "https://api.example.com/data",
                "method": "GET",
                "headers": {},
            },
            "type": "xhr",
        }

        response_event = {
            "requestId": "cap-1",
            "response": {
                "status": 200,
                "statusText": "OK",
                "headers": {},
            },
        }

        capture.capture_request(request_event)
        capture.capture_response(response_event)

        events = capture.get_events()
        assert len(events) == 2
        assert events[0]["type"] == "request"
        assert events[1]["type"] == "response"

        exchange = capture.get_exchange("cap-1")
        assert exchange is not None
        assert "request" in exchange
        assert "response" in exchange

        print("✓ Event capture test passed")

    def test_performance_analyzer(self):
        """Test performance analysis."""
        monitor = NetworkMonitor()
        monitor.enable()

        # Create multiple requests with different timings
        for i in range(3):
            req = {
                "requestId": f"perf-analyze-{i}",
                "request": {
                    "url": f"https://api.example.com/resource/{i}",
                    "method": "GET",
                    "headers": {},
                },
                "type": "xhr",
                "initiator": {"type": "script"},
            }

            resp = {
                "requestId": f"perf-analyze-{i}",
                "response": {
                    "status": 200,
                    "statusText": "OK",
                    "headers": {},
                    "mimeType": "application/json",
                },
            }

            monitor.on_request_will_be_sent(req)
            monitor.on_response_received(resp)
            monitor.on_loading_finished(
                {"requestId": f"perf-analyze-{i}", "encodedDataLength": 1024}
            )

        analyzer = PerformanceAnalyzer(monitor)
        report = analyzer.get_performance_report()

        assert "summary" in report
        assert "analysis" in report
        assert "issues" in report
        assert report["summary"]["total_requests"] == 3

        print("✓ Performance analyzer test passed")

    def test_security_analyzer(self):
        """Test security analysis."""
        monitor = NetworkMonitor()
        monitor.enable()

        # Add insecure and secure requests
        insecure_req = {
            "requestId": "sec-1",
            "request": {
                "url": "http://example.com/api",  # Insecure
                "method": "GET",
                "headers": {},
                "postData": None,
            },
            "type": "xhr",
            "initiator": {"type": "script"},
        }

        secure_req = {
            "requestId": "sec-2",
            "request": {
                "url": "https://example.com/api",  # Secure
                "method": "GET",
                "headers": {},
                "postData": None,
            },
            "type": "xhr",
            "initiator": {"type": "script"},
        }

        monitor.on_request_will_be_sent(insecure_req)
        monitor.on_request_will_be_sent(secure_req)

        analyzer = SecurityAnalyzer(monitor)
        insecure = analyzer.find_insecure_requests()

        assert len(insecure) == 1
        assert insecure[0]["url"] == "http://example.com/api"

        print("✓ Security analyzer test passed")


async def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NETWORK MONITOR TEST SUITE")
    print("=" * 60 + "\n")

    # Basic functionality tests
    print("Running basic functionality tests...")
    basics = TestNetworkMonitorBasics()
    basics.test_request_tracking()
    basics.test_response_tracking()
    basics.test_failed_request_tracking()
    basics.test_metrics_collection()
    basics.test_request_filtering()

    # Interception tests
    print("\nRunning interception tests...")
    intercept = TestNetworkInterception()
    await intercept.test_request_modification()
    intercept.test_url_blocking()

    # Pattern tests
    print("\nRunning monitoring pattern tests...")
    patterns = TestMonitoringPatterns()
    patterns.test_api_monitor_pattern()
    patterns.test_security_monitor_pattern()
    patterns.test_performance_monitor_pattern()

    # Integration tests
    print("\nRunning integration utility tests...")
    integration = TestIntegrationUtilities()
    await integration.test_monitoring_session()
    integration.test_event_capture()
    integration.test_performance_analyzer()
    integration.test_security_analyzer()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
