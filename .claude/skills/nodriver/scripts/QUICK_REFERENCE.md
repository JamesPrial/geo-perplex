# Network Monitor - Quick Reference

Fast lookup guide for common tasks and API usage.

## Installation & Import

```python
from network_monitor import NetworkMonitor, MonitoringPatterns
from network_monitor_integration import (
    NetworkMonitorSession,
    PerformanceAnalyzer,
    SecurityAnalyzer,
)
```

## Basic Setup

```python
# Create monitor
monitor = NetworkMonitor()

# Enable
monitor.enable()

# Get metrics
metrics = monitor.get_metrics()

# Disable
monitor.disable()
```

## Context Manager

```python
async with NetworkMonitor() as monitor:
    monitor.enable()
    # Your code here
    metrics = monitor.get_metrics()
```

## Using Sessions

```python
session = NetworkMonitorSession("my_test")
async with session as monitor:
    # Your code here
    pass
summary = session.get_summary()
```

## Event Handlers

```python
# Request will be sent
monitor.on_request_will_be_sent({
    "requestId": "123",
    "request": {
        "url": "https://api.example.com",
        "method": "GET",
        "headers": {},
    },
    "type": "xhr",
})

# Response received
monitor.on_response_received({
    "requestId": "123",
    "response": {
        "status": 200,
        "statusText": "OK",
        "headers": {},
    },
})

# Loading finished
monitor.on_loading_finished({
    "requestId": "123",
    "encodedDataLength": 1024,
})

# Loading failed
monitor.on_loading_failed({
    "requestId": "123",
    "errorText": "Network error",
})
```

## Request/Response Access

```python
# Get request
req = monitor.get_request("request-id-123")
print(req.url, req.method, req.headers)

# Get response
resp = monitor.get_response("request-id-123")
print(resp.status, resp.body)

# Get all
all_requests = monitor._requests  # Dict[str, NetworkRequest]
all_responses = monitor._responses  # Dict[str, NetworkResponse]
```

## Metrics

```python
metrics = monitor.get_metrics()

# Summary
metrics["total_requests"]        # int
metrics["total_responses"]       # int
metrics["total_bytes"]           # int
metrics["average_response_time"] # float (seconds)

# Lists
metrics["failed_requests"]       # List[Dict]
metrics["slowest_requests"]      # List[Dict]
metrics["fastest_requests"]      # List[Dict]

# Grouping
metrics["by_resource_type"]      # Dict[str, int]
metrics["by_status_code"]        # Dict[int, int]
metrics["by_domain"]             # Dict[str, int]
```

## Filtering Requests

```python
# By method
get_requests = monitor.filter_requests(method="GET")
post_requests = monitor.filter_requests(method="POST")

# By URL pattern (regex)
api_requests = monitor.filter_requests(url_pattern=r"api\..*")

# By resource type
xhr_requests = monitor.filter_requests(resource_type="xhr")
images = monitor.filter_requests(resource_type="image")

# By status code
failed = monitor.filter_requests(status=404)
errors = monitor.filter_requests(status=500)

# Multiple filters (AND)
api_errors = monitor.filter_requests(
    method="POST",
    url_pattern=r"api\..*",
    status=500
)
```

## Interceptor - Request Handlers

```python
# Add handler
async def my_handler(request):
    print(f"Request: {request['url']}")

monitor.interceptor.add_request_handler(my_handler)

# Add auth header
async def add_auth(request):
    request.setdefault("headers", {})["Authorization"] = "Bearer token"

monitor.interceptor.add_request_handler(add_auth)

# Conditional header
async def conditional(request):
    if "api" in request.get("url", ""):
        request["headers"]["X-API-Version"] = "2"

monitor.interceptor.add_request_handler(conditional)
```

## Interceptor - Response Handlers

```python
# Add handler
async def my_response_handler(response):
    print(f"Status: {response['status']}")

monitor.interceptor.add_response_handler(my_response_handler)

# Log errors
async def log_errors(response):
    if response.get("status", 0) >= 400:
        print(f"Error: {response['status']}")

monitor.interceptor.add_response_handler(log_errors)
```

## Interceptor - Blocking

```python
# Block pattern
monitor.interceptor.block_url_pattern("*.analytics.js")
monitor.interceptor.block_url_pattern("*.tracker.com")

# Check if blocked
is_blocked = monitor.interceptor.should_block(url)
```

## Interceptor - Modify Requests

```python
monitor.interceptor.modify_request("request-id", {
    "headers": {"X-Custom": "value"},
    "url": "https://new-url.com",
})
```

## Pre-built Patterns

```python
# API monitoring
api_monitor = MonitoringPatterns.create_api_monitor()

# Performance monitoring
perf_monitor = MonitoringPatterns.create_performance_monitor()

# Security monitoring
sec_monitor = MonitoringPatterns.create_security_monitor()

# Bandwidth monitoring
bw_monitor = MonitoringPatterns.create_bandwidth_monitor()
```

## Data Management

```python
# Store response body
await monitor.set_response_body("request-id", "response body")

# Clear all data
monitor.clear()
```

## Response Body Extraction

```python
# Set body
await monitor.set_response_body(
    request_id="req-123",
    body='{"data": "json"}',
    is_encoded=False
)

# Get body
resp = monitor.get_response("req-123")
if resp:
    print(resp.body)
```

## Performance Analysis

```python
from network_monitor_integration import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(monitor)

# Get report
report = analyzer.get_performance_report()

# Print formatted
analyzer.print_report()

# Access specific metrics
fastest = report['analysis']['fastest_request']
slowest = report['analysis']['slowest_request']
high_latency = report['issues']['high_latency_requests']
```

## Security Analysis

```python
from network_monitor_integration import SecurityAnalyzer

analyzer = SecurityAnalyzer(monitor)

# Find issues
insecure = analyzer.find_insecure_requests()
sensitive = analyzer.find_sensitive_data_patterns()
origins = analyzer.analyze_cross_origin_requests()

# Get full report
report = analyzer.get_security_report()
```

## Event Capture

```python
from network_monitor_integration import NetworkEventCapture

capture = NetworkEventCapture()

# Capture events
capture.capture_request(request_event)
capture.capture_response(response_event)
capture.capture_finished(finished_event)
capture.capture_failed(failed_event)

# Get events
events = capture.get_events()
exchange = capture.get_exchange("request-id")

# Export
json_str = capture.export_json()

# Clear
capture.clear()
```

## Request Modification Chain

```python
from network_monitor_integration import RequestModificationChain

chain = RequestModificationChain()

# Add header
chain.add_header("User-Agent", "MyBot/1.0")

# Add auth
chain.add_auth_token("secret-token", scheme="Bearer")

# Conditional header
chain.add_custom_header_condition(
    lambda url: "api" in url,
    "X-API-Version",
    "2"
)

# Apply
modified_request = chain.apply(request)
```

## Common Patterns

### Monitor API Calls
```python
api_monitor = MonitoringPatterns.create_api_monitor()
api_monitor.enable()
# ... navigate and interact ...
api_calls = api_monitor.filter_requests(method="POST")
```

### Find Slow Pages
```python
monitor = NetworkMonitor()
# ... navigate ...
metrics = monitor.get_metrics()
for req in metrics["slowest_requests"]:
    print(f"Slow: {req['url']} - {req['time']:.2f}s")
```

### Block Tracking
```python
monitor = MonitoringPatterns.create_security_monitor()
monitor.enable()
# Tracking domains already blocked
```

### Analyze Performance
```python
analyzer = PerformanceAnalyzer(monitor)
analyzer.print_report()
```

### Check Security
```python
analyzer = SecurityAnalyzer(monitor)
report = analyzer.get_security_report()
for insecure in report["insecure_requests"]:
    print(f"Insecure: {insecure['url']}")
```

## Dataclass Access

### NetworkRequest
```python
request.request_id    # str
request.url           # str
request.method        # str
request.timestamp     # float
request.headers       # Dict[str, str]
request.post_data     # Optional[str]
request.initiator     # Optional[str]
request.resource_type # str
```

### NetworkResponse
```python
response.request_id   # str
response.status       # int
response.status_text  # str
response.headers      # Dict[str, str]
response.body         # Optional[str]
response.body_size    # int
response.mime_type    # str
response.timestamp    # float
```

## Metrics Dictionary Keys

```python
metrics = monitor.get_metrics()

metrics["total_requests"]        # Total count
metrics["total_responses"]       # Total count
metrics["total_bytes"]           # Total size
metrics["average_response_time"] # Float seconds
metrics["failed_requests"]       # List of failures
metrics["by_resource_type"]      # Dict counts
metrics["by_status_code"]        # Dict counts
metrics["by_domain"]             # Dict counts
metrics["slowest_requests"]      # Top 5 list
metrics["fastest_requests"]      # Top 5 list
```

## Filter Request Return Format

```python
filtered = monitor.filter_requests(...)
# Returns: List[Dict]
#   [
#     {
#       "request": {
#         "id": str,
#         "url": str,
#         "method": str,
#         "headers": Dict,
#         "post_data": Optional[str],
#       },
#       "response": {
#         "status": int,
#         "headers": Dict,
#         "body": Optional[str],
#       }
#     },
#     ...
#   ]
```

## Testing

```bash
# Run all tests
python network_monitor_tests.py

# Run examples
python network_monitor_examples.py
```

## File Locations

```
/home/jamesprial/code/skills/.claude/skills/nodriver/scripts/

network_monitor.py                # Core module
network_monitor_examples.py        # 10 examples
network_monitor_integration.py     # Integration utilities
network_monitor_tests.py           # Test suite
NETWORK_MONITOR_README.md          # Full API docs
INDEX.md                           # Detailed index
QUICK_REFERENCE.md                 # This file
```

## Common Errors & Solutions

### "No requests recorded"
- Check `monitor.enable()` called first
- Verify CDP events connected to browser

### "MemoryError"
- Reduce `max_response_bodies` parameter
- Call `monitor.clear()` between runs

### "Async handler not called"
- Ensure handler is `async def`
- Check event names match CDP spec

### "Filter returns empty"
- Verify regex pattern matches URLs
- Check filter criteria match actual data

## Tips & Tricks

1. Use patterns for common cases (API, security, performance)
2. Use filtering to work with subsets of requests
3. Use session for lifecycle management
4. Use analyzers for insights
5. Clear between test runs
6. Log async handlers for debugging
7. Start simple, add complexity as needed
