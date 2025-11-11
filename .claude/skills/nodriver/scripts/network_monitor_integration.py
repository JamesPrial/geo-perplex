"""
Integration patterns and utilities for NetworkMonitor with browser automation.

This module provides practical integration examples for using NetworkMonitor
with various browser automation frameworks and CDP implementations.
"""

import json
import time
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
from network_monitor import NetworkMonitor, NetworkInterceptor


class CDPBridgeAdapter(ABC):
    """
    Abstract base for adapting various CDP implementations.

    Use this to integrate NetworkMonitor with your specific browser
    automation framework.
    """

    def __init__(self, monitor: NetworkMonitor):
        """Initialize the CDP bridge."""
        self.monitor = monitor

    @abstractmethod
    async def connect_network_events(self) -> None:
        """Connect monitor to browser CDP events."""
        pass

    @abstractmethod
    async def disconnect_network_events(self) -> None:
        """Disconnect monitor from browser CDP events."""
        pass

    async def enable_monitoring(self) -> None:
        """Enable network monitoring."""
        self.monitor.enable()
        await self.connect_network_events()

    async def disable_monitoring(self) -> None:
        """Disable network monitoring."""
        self.monitor.disable()
        await self.disconnect_network_events()


class NetworkMonitorSession:
    """
    Manages a monitoring session with clear lifecycle.

    Example:
        >>> session = NetworkMonitorSession()
        >>> async with session.start() as monitor:
        ...     # perform actions
        ...     metrics = monitor.get_metrics()
    """

    def __init__(self, name: str = "network_session"):
        """
        Initialize monitoring session.

        Args:
            name: Session name for logging.
        """
        self.name = name
        self.monitor = NetworkMonitor()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    async def __aenter__(self):
        """Start session."""
        self.start_time = time.time()
        self.monitor.enable()
        return self.monitor

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End session."""
        self.end_time = time.time()
        self.monitor.disable()

    def duration(self) -> float:
        """Get session duration in seconds."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary with metrics and duration."""
        metrics = self.monitor.get_metrics()
        return {
            "session_name": self.name,
            "duration_seconds": self.duration(),
            "metrics": metrics,
        }


class NetworkEventCapture:
    """
    Captures network events in a structured format.

    Useful for replaying, testing, and debugging network traffic.
    """

    def __init__(self):
        """Initialize event capture."""
        self._events: List[Dict[str, Any]] = []
        self._event_map: Dict[str, Dict[str, Any]] = {}

    def capture_request(self, event: Dict[str, Any]) -> None:
        """
        Capture a request event.

        Args:
            event: RequestWillBeSent event from CDP.
        """
        request_id = event.get("requestId")
        self._event_map[request_id] = {"request": event, "timestamp": time.time()}
        self._events.append({"type": "request", "data": event})

    def capture_response(self, event: Dict[str, Any]) -> None:
        """
        Capture a response event.

        Args:
            event: ResponseReceived event from CDP.
        """
        request_id = event.get("requestId")
        if request_id in self._event_map:
            self._event_map[request_id]["response"] = event
        self._events.append({"type": "response", "data": event})

    def capture_finished(self, event: Dict[str, Any]) -> None:
        """
        Capture a loading finished event.

        Args:
            event: LoadingFinished event from CDP.
        """
        self._events.append({"type": "finished", "data": event})

    def capture_failed(self, event: Dict[str, Any]) -> None:
        """
        Capture a loading failed event.

        Args:
            event: LoadingFailed event from CDP.
        """
        request_id = event.get("requestId")
        if request_id in self._event_map:
            self._event_map[request_id]["failed"] = event
        self._events.append({"type": "failed", "data": event})

    def get_events(self) -> List[Dict[str, Any]]:
        """Get all captured events."""
        return self._events.copy()

    def get_exchange(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get complete request/response exchange."""
        return self._event_map.get(request_id)

    def export_json(self) -> str:
        """Export captured events as JSON."""
        return json.dumps(self._events, indent=2, default=str)

    def clear(self) -> None:
        """Clear captured events."""
        self._events.clear()
        self._event_map.clear()


class RequestModificationChain:
    """
    Chain multiple request modifications together.

    Allows composing complex request modifications from simple rules.
    """

    def __init__(self):
        """Initialize modification chain."""
        self._modifications: List[Callable[[Dict], Dict]] = []

    def add_header(self, header_name: str, header_value: str) -> "RequestModificationChain":
        """
        Add header to all requests.

        Args:
            header_name: Header name.
            header_value: Header value.

        Returns:
            Self for chaining.
        """

        def modify(request: Dict) -> Dict:
            if "headers" not in request:
                request["headers"] = {}
            request["headers"][header_name] = header_value
            return request

        self._modifications.append(modify)
        return self

    def add_auth_token(self, token: str, scheme: str = "Bearer") -> "RequestModificationChain":
        """
        Add authentication token to requests.

        Args:
            token: Authentication token.
            scheme: Auth scheme (Bearer, Basic, etc.).

        Returns:
            Self for chaining.
        """
        return self.add_header("Authorization", f"{scheme} {token}")

    def add_custom_header_condition(
        self, condition: Callable[[str], bool], header_name: str, header_value: str
    ) -> "RequestModificationChain":
        """
        Add header conditionally based on URL.

        Args:
            condition: Function that takes URL and returns bool.
            header_name: Header name.
            header_value: Header value.

        Returns:
            Self for chaining.
        """

        def modify(request: Dict) -> Dict:
            url = request.get("url", "")
            if condition(url):
                if "headers" not in request:
                    request["headers"] = {}
                request["headers"][header_name] = header_value
            return request

        self._modifications.append(modify)
        return self

    def add_post_data_wrapper(self, wrapper_func: Callable) -> "RequestModificationChain":
        """
        Wrap POST data with custom function.

        Args:
            wrapper_func: Function that takes post_data and returns modified data.

        Returns:
            Self for chaining.
        """

        def modify(request: Dict) -> Dict:
            if "postData" in request and request["postData"]:
                request["postData"] = wrapper_func(request["postData"])
            return request

        self._modifications.append(modify)
        return self

    def apply(self, request: Dict) -> Dict:
        """
        Apply all modifications to request.

        Args:
            request: Request object to modify.

        Returns:
            Modified request.
        """
        for modification in self._modifications:
            request = modification(request)
        return request


class PerformanceAnalyzer:
    """Analyze performance data from NetworkMonitor."""

    def __init__(self, monitor: NetworkMonitor):
        """
        Initialize analyzer.

        Args:
            monitor: NetworkMonitor instance with collected data.
        """
        self.monitor = monitor

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Returns:
            Dictionary with performance metrics and analysis.
        """
        metrics = self.monitor.get_metrics()

        report = {
            "summary": {
                "total_requests": metrics["total_requests"],
                "total_bytes": metrics["total_bytes"],
                "average_response_time": metrics["average_response_time"],
            },
            "analysis": {
                "fastest_request": self._get_fastest(metrics),
                "slowest_request": self._get_slowest(metrics),
                "resource_distribution": metrics["by_resource_type"],
                "status_distribution": metrics["by_status_code"],
            },
            "issues": {
                "failed_requests": metrics["failed_requests"],
                "high_latency_requests": self._find_high_latency(metrics),
            },
        }

        return report

    def _get_fastest(self, metrics: Dict) -> Optional[Dict]:
        """Get fastest request."""
        if metrics["fastest_requests"]:
            return metrics["fastest_requests"][0]
        return None

    def _get_slowest(self, metrics: Dict) -> Optional[Dict]:
        """Get slowest request."""
        if metrics["slowest_requests"]:
            return metrics["slowest_requests"][0]
        return None

    def _find_high_latency(
        self, metrics: Dict, threshold: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Find requests exceeding latency threshold.

        Args:
            metrics: Metrics dictionary.
            threshold: Latency threshold in seconds.

        Returns:
            List of high-latency requests.
        """
        high_latency = []
        for req in metrics["slowest_requests"]:
            if req["time"] > threshold:
                high_latency.append(req)
        return high_latency

    def print_report(self) -> None:
        """Print formatted performance report."""
        report = self.get_performance_report()

        print("\n" + "=" * 60)
        print("PERFORMANCE REPORT")
        print("=" * 60)

        summary = report["summary"]
        print(f"\nSummary:")
        print(f"  Total Requests: {summary['total_requests']}")
        print(f"  Total Data: {summary['total_bytes']} bytes")
        print(f"  Avg Response Time: {summary['average_response_time']:.4f}s")

        analysis = report["analysis"]
        print(f"\nAnalysis:")
        if analysis["fastest_request"]:
            fastest = analysis["fastest_request"]
            print(f"  Fastest: {fastest['url']} ({fastest['time']:.4f}s)")
        if analysis["slowest_request"]:
            slowest = analysis["slowest_request"]
            print(f"  Slowest: {slowest['url']} ({slowest['time']:.4f}s)")

        print(f"\n  Resource Distribution:")
        for rtype, count in analysis["resource_distribution"].items():
            print(f"    {rtype}: {count}")

        issues = report["issues"]
        if issues["failed_requests"]:
            print(f"\nFailed Requests ({len(issues['failed_requests'])}):")
            for failed in issues["failed_requests"][:5]:
                print(f"  {failed['status']} {failed['url']}")

        if issues["high_latency_requests"]:
            print(f"\nHigh Latency Requests (> 1s):")
            for req in issues["high_latency_requests"][:5]:
                print(f"  {req['url']}: {req['time']:.4f}s")

        print("\n" + "=" * 60)


class SecurityAnalyzer:
    """Analyze security aspects of network traffic."""

    def __init__(self, monitor: NetworkMonitor):
        """
        Initialize security analyzer.

        Args:
            monitor: NetworkMonitor instance.
        """
        self.monitor = monitor

    def find_insecure_requests(self) -> List[Dict[str, str]]:
        """Find requests using HTTP instead of HTTPS."""
        insecure = []
        for request in self.monitor._requests.values():
            if request.url.startswith("http://") and not request.url.startswith(
                "http://localhost"
            ):
                insecure.append({"url": request.url, "type": "unencrypted"})
        return insecure

    def find_sensitive_data_patterns(self) -> List[Dict[str, Any]]:
        """Find requests that may expose sensitive data."""
        patterns = [
            r"password=",
            r"api_key=",
            r"token=",
            r"secret=",
            r"auth=",
        ]

        sensitive = []
        for request in self.monitor._requests.values():
            for pattern in patterns:
                import re

                if re.search(pattern, request.url):
                    sensitive.append(
                        {"url": request.url, "pattern": pattern, "location": "url"}
                    )

                if request.post_data and re.search(pattern, request.post_data):
                    sensitive.append(
                        {"url": request.url, "pattern": pattern, "location": "body"}
                    )

        return sensitive

    def analyze_cross_origin_requests(self) -> Dict[str, List[str]]:
        """Analyze cross-origin requests."""
        from urllib.parse import urlparse

        origins = {}
        for request in self.monitor._requests.values():
            parsed = urlparse(request.url)
            origin = f"{parsed.scheme}://{parsed.netloc}"

            if origin not in origins:
                origins[origin] = []
            origins[origin].append(request.url)

        return origins

    def get_security_report(self) -> Dict[str, Any]:
        """Generate security report."""
        return {
            "insecure_requests": self.find_insecure_requests(),
            "sensitive_data_patterns": self.find_sensitive_data_patterns(),
            "cross_origin_requests": self.analyze_cross_origin_requests(),
        }


# Utility Functions


def create_standard_interceptor(
    add_headers: Optional[Dict[str, str]] = None,
    block_patterns: Optional[List[str]] = None,
) -> NetworkInterceptor:
    """
    Create a standard interceptor with common configurations.

    Args:
        add_headers: Headers to add to all requests.
        block_patterns: URL patterns to block.

    Returns:
        Configured NetworkInterceptor.
    """
    interceptor = NetworkInterceptor()

    if add_headers:
        async def add_standard_headers(request: Dict) -> None:
            for header, value in add_headers.items():
                request.setdefault("headers", {})[header] = value

        interceptor.add_request_handler(add_standard_headers)

    if block_patterns:
        for pattern in block_patterns:
            interceptor.block_url_pattern(pattern)

    return interceptor


def create_logging_interceptor() -> NetworkInterceptor:
    """
    Create interceptor that logs all requests and responses.

    Returns:
        Configured NetworkInterceptor with logging.
    """
    interceptor = NetworkInterceptor()

    async def log_request(request: Dict) -> None:
        print(f"-> {request.get('method', 'GET')} {request.get('url', '')}")

    async def log_response(response: Dict) -> None:
        status = response.get("status", "?")
        print(f"<- Status: {status}")

    interceptor.add_request_handler(log_request)
    interceptor.add_response_handler(log_response)

    return interceptor


if __name__ == "__main__":
    print("Integration Utilities for NetworkMonitor")
    print("=" * 60)
    print("\nThis module provides integration helpers.")
    print("See docstrings for detailed usage examples.")
