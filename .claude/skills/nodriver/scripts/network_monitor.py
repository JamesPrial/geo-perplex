"""
Network Monitoring via Chrome DevTools Protocol (CDP)

This module provides comprehensive network monitoring capabilities using CDP,
including request/response interception, performance metrics, and failure tracking.

Example:
    Basic network monitoring with metrics collection:

    >>> async def monitor_website():
    ...     async with NetworkMonitor() as monitor:
    ...         driver = await start_browser()
    ...         await driver.get("https://example.com")
    ...         metrics = monitor.get_metrics()
    ...         print(f"Total requests: {metrics['total_requests']}")
    ...         print(f"Failed requests: {len(metrics['failed_requests'])}")
    ...         await driver.close()

Author: Claude
Date: 2024
"""

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
from collections import defaultdict


@dataclass
class NetworkRequest:
    """Represents a single network request."""
    request_id: str
    url: str
    method: str
    timestamp: float
    headers: Dict[str, str] = field(default_factory=dict)
    post_data: Optional[str] = None
    initiator: Optional[str] = None
    resource_type: str = "xhr"


@dataclass
class NetworkResponse:
    """Represents a response received for a request."""
    request_id: str
    status: int
    status_text: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    body_size: int = 0
    mime_type: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass
class NetworkMetrics:
    """Aggregated network performance metrics."""
    total_requests: int = 0
    total_responses: int = 0
    total_bytes: int = 0
    average_response_time: float = 0.0
    failed_requests: List[Dict[str, Any]] = field(default_factory=list)
    by_resource_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_status_code: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    slowest_requests: List[Dict[str, Any]] = field(default_factory=list)


class NetworkInterceptor:
    """Manages request/response interception and modification."""

    def __init__(self):
        """Initialize the network interceptor."""
        self._request_handlers: List[Callable] = []
        self._response_handlers: List[Callable] = []
        self._modified_requests: Dict[str, Dict[str, Any]] = {}
        self._blocked_patterns: List[str] = []

    def add_request_handler(self, handler: Callable) -> None:
        """
        Add a handler for outgoing requests.

        Args:
            handler: Async callable that receives request dict.
                    Can modify the request before it's sent.
        """
        self._request_handlers.append(handler)

    def add_response_handler(self, handler: Callable) -> None:
        """
        Add a handler for incoming responses.

        Args:
            handler: Async callable that receives response dict.
        """
        self._response_handlers.append(handler)

    def block_url_pattern(self, pattern: str) -> None:
        """
        Block URLs matching a pattern (e.g., *.analytics.js).

        Args:
            pattern: URL pattern to block.
        """
        self._blocked_patterns.append(pattern)

    def modify_request(self, request_id: str, modifications: Dict[str, Any]) -> None:
        """
        Modify a request before it's sent.

        Args:
            request_id: The request ID to modify.
            modifications: Dict with 'headers', 'postData', 'url', etc.
        """
        self._modified_requests[request_id] = modifications

    def should_block(self, url: str) -> bool:
        """Check if a URL matches any blocked patterns."""
        for pattern in self._blocked_patterns:
            if self._pattern_matches(url, pattern):
                return True
        return False

    @staticmethod
    def _pattern_matches(url: str, pattern: str) -> bool:
        """
        Check if URL matches a glob-style pattern.

        Args:
            url: URL to check.
            pattern: Glob pattern (e.g., '*.png').

        Returns:
            True if URL matches pattern.
        """
        import fnmatch
        return fnmatch.fnmatch(url, pattern)

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process request through handlers and modifications.

        Args:
            request: The request dictionary from CDP.

        Returns:
            Modified request or original if no modifications.
        """
        # Run custom handlers
        for handler in self._request_handlers:
            await handler(request)

        # Apply modifications if any
        request_id = request.get("requestId")
        if request_id in self._modified_requests:
            mods = self._modified_requests.pop(request_id)
            request.update(mods)

        return request

    async def process_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process response through handlers.

        Args:
            response: The response dictionary from CDP.

        Returns:
            Modified response or original if no modifications.
        """
        for handler in self._response_handlers:
            await handler(response)
        return response


class NetworkMonitor:
    """
    Comprehensive network monitoring via Chrome DevTools Protocol.

    Tracks requests, responses, performance metrics, and failures.
    Supports request/response interception and modification.

    Example:
        >>> async with NetworkMonitor() as monitor:
        ...     # Monitor network traffic
        ...     await monitor.enable()
        ...     # ... navigate and interact with page ...
        ...     metrics = monitor.get_metrics()
    """

    def __init__(self, max_response_bodies: int = 100):
        """
        Initialize the network monitor.

        Args:
            max_response_bodies: Maximum number of response bodies to store.
        """
        self._requests: Dict[str, NetworkRequest] = {}
        self._responses: Dict[str, NetworkResponse] = {}
        self._interceptor = NetworkInterceptor()
        self._max_response_bodies = max_response_bodies
        self._response_bodies_count = 0
        self._start_time: Optional[float] = None
        self._enabled = False
        self._request_timing: Dict[str, float] = {}

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disable()

    def enable(self) -> None:
        """Enable network monitoring."""
        self._enabled = True
        self._start_time = time.time()

    def disable(self) -> None:
        """Disable network monitoring."""
        self._enabled = False

    @property
    def interceptor(self) -> NetworkInterceptor:
        """Get the request/response interceptor."""
        return self._interceptor

    def on_request_will_be_sent(self, request_params: Dict[str, Any]) -> None:
        """
        Handle RequestWillBeSent CDP event.

        This event fires before a request is sent to the network.

        Args:
            request_params: Event parameters from CDP.
        """
        if not self._enabled:
            return

        request_id = request_params.get("requestId")
        request_data = request_params.get("request", {})

        # Record request timing
        self._request_timing[request_id] = time.time()

        # Create NetworkRequest object
        network_request = NetworkRequest(
            request_id=request_id,
            url=request_data.get("url", ""),
            method=request_data.get("method", "GET"),
            timestamp=time.time(),
            headers=request_data.get("headers", {}),
            post_data=request_data.get("postData"),
            initiator=request_params.get("initiator", {}).get("type", "unknown"),
            resource_type=request_params.get("type", "xhr"),
        )

        self._requests[request_id] = network_request

    def on_response_received(self, response_params: Dict[str, Any]) -> None:
        """
        Handle ResponseReceived CDP event.

        This event fires when a response is received.

        Args:
            response_params: Event parameters from CDP.
        """
        if not self._enabled:
            return

        request_id = response_params.get("requestId")
        response_data = response_params.get("response", {})

        network_response = NetworkResponse(
            request_id=request_id,
            status=response_data.get("status", 0),
            status_text=response_data.get("statusText", ""),
            headers=response_data.get("headers", {}),
            mime_type=response_data.get("mimeType", ""),
            timestamp=time.time(),
        )

        self._responses[request_id] = network_response

    def on_loading_finished(self, finished_params: Dict[str, Any]) -> None:
        """
        Handle LoadingFinished CDP event.

        This event fires when resource loading completes.

        Args:
            finished_params: Event parameters from CDP.
        """
        if not self._enabled:
            return

        request_id = finished_params.get("requestId")
        encoded_data_length = finished_params.get("encodedDataLength", 0)

        if request_id in self._responses:
            self._responses[request_id].body_size = encoded_data_length

    def on_loading_failed(self, failed_params: Dict[str, Any]) -> None:
        """
        Handle LoadingFailed CDP event.

        This event fires when resource loading fails.

        Args:
            failed_params: Event parameters from CDP.
        """
        if not self._enabled:
            return

        request_id = failed_params.get("requestId")
        error_text = failed_params.get("errorText", "Unknown error")

        if request_id in self._requests:
            req = self._requests[request_id]
            # Store error in response for tracking
            if request_id not in self._responses:
                self._responses[request_id] = NetworkResponse(
                    request_id=request_id,
                    status=0,
                    status_text=f"Failed: {error_text}",
                )
            else:
                self._responses[request_id].status_text = f"Failed: {error_text}"

    async def set_response_body(
        self, request_id: str, body: Optional[str], is_encoded: bool = False
    ) -> None:
        """
        Set or retrieve response body.

        Respects the max_response_bodies limit to avoid memory issues.

        Args:
            request_id: The request ID.
            body: The response body content.
            is_encoded: Whether the body is base64 encoded.
        """
        if not self._enabled:
            return

        if self._response_bodies_count >= self._max_response_bodies:
            return

        if request_id in self._responses:
            self._responses[request_id].body = body
            self._response_bodies_count += 1

    def get_request(self, request_id: str) -> Optional[NetworkRequest]:
        """
        Retrieve a recorded request by ID.

        Args:
            request_id: The request ID.

        Returns:
            NetworkRequest object or None if not found.
        """
        return self._requests.get(request_id)

    def get_response(self, request_id: str) -> Optional[NetworkResponse]:
        """
        Retrieve a recorded response by ID.

        Args:
            request_id: The response ID.

        Returns:
            NetworkResponse object or None if not found.
        """
        return self._responses.get(request_id)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Generate comprehensive network metrics.

        Returns:
            Dictionary containing aggregated metrics and analytics.

        Example:
            >>> metrics = monitor.get_metrics()
            >>> print(f"Total bytes: {metrics['total_bytes']}")
            >>> print(f"Avg response time: {metrics['average_response_time']:.2f}s")
        """
        metrics = {
            "total_requests": len(self._requests),
            "total_responses": len(self._responses),
            "total_bytes": 0,
            "average_response_time": 0.0,
            "failed_requests": [],
            "by_resource_type": defaultdict(int),
            "by_status_code": defaultdict(int),
            "by_domain": defaultdict(int),
            "slowest_requests": [],
            "fastest_requests": [],
        }

        response_times = []
        failed = []

        for request_id, request in self._requests.items():
            response = self._responses.get(request_id)

            # Track resource types
            metrics["by_resource_type"][request.resource_type] += 1

            # Extract domain
            from urllib.parse import urlparse
            domain = urlparse(request.url).netloc
            metrics["by_domain"][domain] += 1

            if response:
                # Track status codes
                metrics["by_status_code"][response.status] += 1
                metrics["total_bytes"] += response.body_size

                # Calculate response time
                if request_id in self._request_timing:
                    response_time = (
                        response.timestamp - self._request_timing[request_id]
                    )
                    response_times.append(
                        {
                            "url": request.url,
                            "time": response_time,
                            "status": response.status,
                        }
                    )

                # Track failed requests
                if response.status >= 400:
                    failed.append(
                        {
                            "url": request.url,
                            "status": response.status,
                            "status_text": response.status_text,
                            "method": request.method,
                            "timestamp": datetime.fromtimestamp(request.timestamp).isoformat(),
                        }
                    )
            elif response and "Failed" in response.status_text:
                failed.append(
                    {
                        "url": request.url,
                        "status": response.status,
                        "status_text": response.status_text,
                        "method": request.method,
                        "timestamp": datetime.fromtimestamp(request.timestamp).isoformat(),
                    }
                )

        # Calculate average response time
        if response_times:
            metrics["average_response_time"] = sum(
                r["time"] for r in response_times
            ) / len(response_times)
            response_times.sort(key=lambda x: x["time"], reverse=True)
            metrics["slowest_requests"] = response_times[:5]
            response_times.sort(key=lambda x: x["time"])
            metrics["fastest_requests"] = response_times[:5]

        metrics["failed_requests"] = failed
        metrics["by_resource_type"] = dict(metrics["by_resource_type"])
        metrics["by_status_code"] = dict(metrics["by_status_code"])
        metrics["by_domain"] = dict(metrics["by_domain"])

        return metrics

    def filter_requests(
        self,
        url_pattern: Optional[str] = None,
        method: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Filter recorded requests by various criteria.

        Args:
            url_pattern: Regex pattern to match URLs.
            method: HTTP method to filter (GET, POST, etc.).
            resource_type: Resource type to filter (xhr, fetch, etc.).
            status: HTTP status code to filter.

        Returns:
            List of matching requests with their responses.

        Example:
            >>> failed = monitor.filter_requests(status=404)
            >>> api_calls = monitor.filter_requests(method="POST", url_pattern="api.*")
        """
        import re

        results = []

        for request_id, request in self._requests.items():
            # Apply filters
            if url_pattern and not re.search(url_pattern, request.url):
                continue
            if method and request.method != method:
                continue
            if resource_type and request.resource_type != resource_type:
                continue

            response = self._responses.get(request_id)
            if status is not None:
                if not response or response.status != status:
                    continue

            results.append(
                {
                    "request": {
                        "id": request_id,
                        "url": request.url,
                        "method": request.method,
                        "headers": request.headers,
                        "post_data": request.post_data,
                    },
                    "response": {
                        "status": response.status if response else None,
                        "headers": response.headers if response else None,
                        "body": response.body if response else None,
                    }
                    if response
                    else None,
                }
            )

        return results

    def clear(self) -> None:
        """Clear all recorded requests and responses."""
        self._requests.clear()
        self._responses.clear()
        self._request_timing.clear()
        self._response_bodies_count = 0


# Example patterns for common monitoring tasks
class MonitoringPatterns:
    """Reusable patterns for common network monitoring tasks."""

    @staticmethod
    def create_api_monitor() -> NetworkMonitor:
        """
        Create a monitor focused on API calls.

        Example:
            >>> api_monitor = MonitoringPatterns.create_api_monitor()
            >>> api_calls = api_monitor.filter_requests(method="POST")
        """
        monitor = NetworkMonitor()

        async def log_api_request(request: Dict[str, Any]) -> None:
            """Log API requests with details."""
            url = request.get("url", "")
            method = request.get("method", "GET")
            if "api" in url:
                print(f"API {method}: {url}")

        monitor.interceptor.add_request_handler(log_api_request)
        return monitor

    @staticmethod
    def create_performance_monitor() -> NetworkMonitor:
        """
        Create a monitor focused on performance metrics.

        Example:
            >>> perf_monitor = MonitoringPatterns.create_performance_monitor()
            >>> metrics = perf_monitor.get_metrics()
            >>> print(f"Avg response: {metrics['average_response_time']:.2f}s")
        """
        monitor = NetworkMonitor()

        async def track_slow_response(response: Dict[str, Any]) -> None:
            """Log slow responses."""
            status = response.get("status", 0)
            if status >= 500:
                print(f"Server error: {status}")

        monitor.interceptor.add_response_handler(track_slow_response)
        return monitor

    @staticmethod
    def create_security_monitor() -> NetworkMonitor:
        """
        Create a monitor focused on security aspects.

        Example:
            >>> sec_monitor = MonitoringPatterns.create_security_monitor()
            >>> sec_monitor.interceptor.block_url_pattern("*.tracker.com")
        """
        monitor = NetworkMonitor()

        # Block common tracking domains
        tracking_domains = [
            "*.analytics.google.com",
            "*.doubleclick.net",
            "*.facebook.com/tr*",
        ]
        for domain in tracking_domains:
            monitor.interceptor.block_url_pattern(domain)

        async def check_insecure_requests(request: Dict[str, Any]) -> None:
            """Check for insecure requests."""
            url = request.get("url", "")
            if url.startswith("http://") and not url.startswith("http://localhost"):
                print(f"Warning: Insecure request: {url}")

        monitor.interceptor.add_request_handler(check_insecure_requests)
        return monitor

    @staticmethod
    def create_bandwidth_monitor() -> NetworkMonitor:
        """
        Create a monitor focused on bandwidth usage.

        Example:
            >>> bw_monitor = MonitoringPatterns.create_bandwidth_monitor()
            >>> metrics = bw_monitor.get_metrics()
            >>> print(f"Total: {metrics['total_bytes']} bytes")
        """
        return NetworkMonitor(max_response_bodies=50)


if __name__ == "__main__":
    # Example usage (requires active browser connection)
    print("Network Monitor Module")
    print("=" * 50)
    print("\nUsage patterns:")
    print("1. Create monitor: monitor = NetworkMonitor()")
    print("2. Enable: monitor.enable()")
    print("3. Set up event handlers")
    print("4. Get metrics: metrics = monitor.get_metrics()")
    print("\nSee docstrings for detailed examples.")
