# Network Monitor - Chrome DevTools Protocol Integration

A comprehensive Python library for network monitoring via Chrome DevTools Protocol (CDP). This module provides request/response interception, performance metrics collection, failure tracking, and security monitoring capabilities.

## Features

- **Request/Response Interception**: Intercept, inspect, and modify HTTP requests and responses
- **Event Handlers**: Built-in handlers for CDP events (RequestWillBeSent, ResponseReceived, LoadingFinished)
- **Response Body Extraction**: Extract and store response bodies with memory management
- **Request Modification**: Dynamically modify requests before they're sent
- **Performance Metrics**: Collect comprehensive network performance data
- **Failed Request Tracking**: Monitor and analyze failed requests
- **URL Blocking**: Block requests matching specific patterns
- **Request Filtering**: Filter recorded requests by URL, method, status, and resource type
- **Common Patterns**: Pre-built monitoring patterns for API, performance, and security use cases

## Installation

Place the `network_monitor.py` module in your project directory.

```python
from network_monitor import NetworkMonitor, MonitoringPatterns
```

## Quick Start

### Basic Usage

```python
import asyncio
from network_monitor import NetworkMonitor

async def monitor_traffic():
    monitor = NetworkMonitor()
    monitor.enable()

    # Your browser automation code here
    # Navigate to website, trigger requests, etc.

    # Get metrics
    metrics = monitor.get_metrics()
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Failed requests: {len(metrics['failed_requests'])}")

    monitor.disable()

asyncio.run(monitor_traffic())
```

### Using as Context Manager

```python
async with NetworkMonitor() as monitor:
    monitor.enable()

    # Your code here
    metrics = monitor.get_metrics()
```

## Core Components

### NetworkRequest
Represents a single network request with metadata.

```python
@dataclass
class NetworkRequest:
    request_id: str          # Unique request identifier
    url: str                 # Full request URL
    method: str              # HTTP method (GET, POST, etc.)
    timestamp: float         # Request timestamp
    headers: Dict            # Request headers
    post_data: Optional[str] # Request body
    initiator: Optional[str] # What initiated the request
    resource_type: str       # Resource type (xhr, fetch, script, etc.)
```

### NetworkResponse
Represents a response received for a request.

```python
@dataclass
class NetworkResponse:
    request_id: str         # Corresponding request ID
    status: int             # HTTP status code
    status_text: str        # Status text (OK, Not Found, etc.)
    headers: Dict           # Response headers
    body: Optional[str]     # Response body content
    body_size: int          # Response body size in bytes
    mime_type: str          # Response MIME type
    timestamp: float        # Response timestamp
```

### NetworkMonitor
Main monitoring class that coordinates request/response tracking.

```python
monitor = NetworkMonitor(max_response_bodies=100)

# Enable monitoring
monitor.enable()

# Register event handlers
monitor.on_request_will_be_sent(request_params)
monitor.on_response_received(response_params)
monitor.on_loading_finished(finished_params)
monitor.on_loading_failed(failed_params)

# Get metrics
metrics = monitor.get_metrics()

# Filter requests
failed_requests = monitor.filter_requests(status=404)
api_requests = monitor.filter_requests(method="POST")

# Clear data
monitor.clear()
```

### NetworkInterceptor
Handles request/response interception and modification.

```python
interceptor = monitor.interceptor

# Add custom request handler
async def log_request(request):
    print(f"Request: {request['url']}")

interceptor.add_request_handler(log_request)

# Add custom response handler
async def log_response(response):
    print(f"Response status: {response['status']}")

interceptor.add_response_handler(log_response)

# Block URLs by pattern
interceptor.block_url_pattern("*.analytics.js")
interceptor.block_url_pattern("*.tracker.com")

# Modify request
interceptor.modify_request("req-123", {
    "headers": {"Authorization": "Bearer token"}
})
```

## Event Handlers

### RequestWillBeSent
Called before a request is sent to the network.

```python
def on_request_will_be_sent(self, request_params):
    request_id = request_params.get("requestId")
    request_data = request_params.get("request")
    method = request_data.get("method")
    url = request_data.get("url")
    # Process request
```

### ResponseReceived
Called when a response is received.

```python
def on_response_received(self, response_params):
    request_id = response_params.get("requestId")
    response_data = response_params.get("response")
    status = response_data.get("status")
    headers = response_data.get("headers")
    # Process response
```

### LoadingFinished
Called when resource loading completes successfully.

```python
def on_loading_finished(self, finished_params):
    request_id = finished_params.get("requestId")
    encoded_data_length = finished_params.get("encodedDataLength")
    # Track completion
```

### LoadingFailed
Called when resource loading fails.

```python
def on_loading_failed(self, failed_params):
    request_id = failed_params.get("requestId")
    error_text = failed_params.get("errorText")
    # Track failure
```

## Metrics Collection

The `get_metrics()` method returns comprehensive performance data:

```python
metrics = monitor.get_metrics()

# Available metrics:
{
    "total_requests": 45,                    # Total number of requests
    "total_responses": 44,                   # Total number of responses
    "total_bytes": 2048576,                  # Total bytes transferred
    "average_response_time": 0.245,          # Average response time in seconds
    "failed_requests": [...],                # List of failed requests
    "by_resource_type": {...},               # Requests grouped by type
    "by_status_code": {...},                 # Requests grouped by status
    "by_domain": {...},                      # Requests grouped by domain
    "slowest_requests": [...],               # Top 5 slowest requests
    "fastest_requests": [...],               # Top 5 fastest requests
}
```

## Request Filtering

Filter recorded requests by various criteria:

```python
# By HTTP method
post_requests = monitor.filter_requests(method="POST")

# By URL pattern (regex)
api_requests = monitor.filter_requests(url_pattern=r"api\..*")

# By resource type
xhr_requests = monitor.filter_requests(resource_type="xhr")

# By status code
failed = monitor.filter_requests(status=404)

# By status code range
errors = monitor.filter_requests(status=500)

# Multiple filters (AND logic)
api_errors = monitor.filter_requests(
    method="POST",
    url_pattern=r"api\..*",
    status=500
)
```

## Interception Examples

### Adding Authentication Headers

```python
async def add_auth_headers(request):
    if "api.example.com" in request.get("url", ""):
        # Headers will be modified before request is sent
        request["headers"]["Authorization"] = "Bearer token123"

monitor.interceptor.add_request_handler(add_auth_headers)
```

### Logging API Calls

```python
async def log_api_calls(request):
    url = request.get("url", "")
    method = request.get("method", "GET")
    if "api" in url:
        print(f"API Call: {method} {url}")

monitor.interceptor.add_request_handler(log_api_calls)
```

### Detecting Slow Requests

```python
async def detect_slow_responses(response):
    status = response.get("status", 0)
    if status >= 500:
        print(f"Server error detected: {status}")

monitor.interceptor.add_response_handler(detect_slow_responses)
```

### Blocking Tracking Domains

```python
monitor.interceptor.block_url_pattern("*.google-analytics.com")
monitor.interceptor.block_url_pattern("*.facebook.com/tr*")
monitor.interceptor.block_url_pattern("*.doubleclick.net")
```

## Pre-built Monitoring Patterns

### API Monitoring

```python
from network_monitor import MonitoringPatterns

api_monitor = MonitoringPatterns.create_api_monitor()
api_monitor.enable()

# Automatically logs API requests
# Get API-specific metrics
metrics = api_monitor.get_metrics()
api_calls = api_monitor.filter_requests(method="POST")
```

### Performance Monitoring

```python
perf_monitor = MonitoringPatterns.create_performance_monitor()
perf_monitor.enable()

metrics = perf_monitor.get_metrics()
print(f"Average response time: {metrics['average_response_time']:.2f}s")
for req in metrics['slowest_requests']:
    print(f"  Slow: {req['url']} - {req['time']:.2f}s")
```

### Security Monitoring

```python
sec_monitor = MonitoringPatterns.create_security_monitor()
sec_monitor.enable()

# Automatically blocks tracking domains
# Logs insecure requests
metrics = sec_monitor.get_metrics()
```

### Bandwidth Monitoring

```python
bw_monitor = MonitoringPatterns.create_bandwidth_monitor()
bw_monitor.enable()

metrics = bw_monitor.get_metrics()
print(f"Total bandwidth: {metrics['total_bytes']} bytes")
```

## Response Body Extraction

Extract response bodies with memory management:

```python
# Store response body
await monitor.set_response_body(
    request_id="req-123",
    body='{"data": "response content"}',
    is_encoded=False
)

# Retrieve response
response = monitor.get_response("req-123")
if response and response.body:
    print(f"Body: {response.body}")
```

## Complete Example: Monitoring E-commerce Transaction

```python
import asyncio
from network_monitor import NetworkMonitor

async def monitor_checkout():
    monitor = NetworkMonitor()
    monitor.enable()

    # Add handlers for specific endpoints
    async def track_payment(request):
        if "/payment" in request.get("url", ""):
            print(f"Payment request: {request.get('method')}")

    async def track_order_confirmation(response):
        if response.get("status") == 201:
            print("Order created successfully")

    monitor.interceptor.add_request_handler(track_payment)
    monitor.interceptor.add_response_handler(track_order_confirmation)

    # Your browser automation code here
    # Navigate to checkout, fill forms, submit payment, etc.

    # Get final metrics
    metrics = monitor.get_metrics()

    print(f"\nCheckout Summary:")
    print(f"Total requests: {metrics['total_requests']}")
    print(f"Total data: {metrics['total_bytes']} bytes")
    print(f"Average response time: {metrics['average_response_time']:.2f}s")

    if metrics['failed_requests']:
        print(f"Failed requests: {len(metrics['failed_requests'])}")
        for failed in metrics['failed_requests']:
            print(f"  {failed['url']} - {failed['status']}")
```

## Best Practices

1. **Enable/Disable Carefully**: Always disable monitoring when done to free resources
2. **Limit Response Bodies**: Use `max_response_bodies` parameter to control memory usage
3. **Use Patterns**: Leverage pre-built patterns for common use cases
4. **Filter Appropriately**: Use filtering to analyze specific request subsets
5. **Clear Data**: Call `monitor.clear()` between test runs if reusing monitor
6. **Async Handlers**: Ensure handlers are proper async functions
7. **Error Handling**: Wrap handler code in try-except for robustness

## Memory Considerations

- Response bodies are only stored up to `max_response_bodies` limit
- Use `filter_requests()` to work with subsets of data
- Call `clear()` to reset between monitoring sessions
- Consider the resource type and size of responses being stored

## Integration with Browser Automation

### Example with Playwright-like Driver

```python
import asyncio
from network_monitor import NetworkMonitor

async def monitor_page_load(driver):
    monitor = NetworkMonitor()
    monitor.enable()

    # Set up CDP event listeners (pseudo-code)
    driver.on("Network.requestWillBeSent",
              monitor.on_request_will_be_sent)
    driver.on("Network.responseReceived",
              monitor.on_response_received)
    driver.on("Network.loadingFinished",
              monitor.on_loading_finished)
    driver.on("Network.loadingFailed",
              monitor.on_loading_failed)

    # Navigate and interact
    await driver.goto("https://example.com")
    await driver.click("button.submit")

    # Analyze
    metrics = monitor.get_metrics()
    return metrics
```

## Troubleshooting

### No requests recorded
- Ensure `monitor.enable()` is called before browser navigation
- Verify CDP event handlers are properly connected to browser events

### Memory issues with response bodies
- Reduce `max_response_bodies` parameter
- Set it to 0 to disable body storage

### Slow performance
- Disable response body capture if not needed
- Use filtering to reduce in-memory data
- Clear data between test runs

## File Location

Main module: `/home/jamesprial/code/skills/.claude/skills/nodriver/scripts/network_monitor.py`
Examples: `/home/jamesprial/code/skills/.claude/skills/nodriver/scripts/network_monitor_examples.py`

## API Reference

See inline documentation in the module for detailed API reference. All classes and methods include comprehensive docstrings with examples.

## License

This module is provided as-is for network monitoring and analysis purposes.
