# Network Monitoring via CDP - Complete Module Index

Comprehensive Chrome DevTools Protocol network monitoring library with request/response interception, performance metrics, and failure tracking.

## File Structure

```
.claude/skills/nodriver/scripts/
├── network_monitor.py                 # Core monitoring module
├── network_monitor_examples.py         # 10 comprehensive usage examples
├── network_monitor_integration.py      # Integration utilities and patterns
├── network_monitor_tests.py            # Test suite and test patterns
├── NETWORK_MONITOR_README.md           # Complete API documentation
└── INDEX.md                            # This file
```

## Quick Start

### 1. Basic Network Monitoring

```python
from network_monitor import NetworkMonitor

monitor = NetworkMonitor()
monitor.enable()

# Your browser automation code here
# monitor.on_request_will_be_sent(request_params)
# monitor.on_response_received(response_params)

metrics = monitor.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Failed requests: {len(metrics['failed_requests'])}")
```

### 2. Using Pre-built Patterns

```python
from network_monitor import MonitoringPatterns

# For API monitoring
api_monitor = MonitoringPatterns.create_api_monitor()

# For performance analysis
perf_monitor = MonitoringPatterns.create_performance_monitor()

# For security monitoring
sec_monitor = MonitoringPatterns.create_security_monitor()
```

### 3. Request Interception

```python
monitor = NetworkMonitor()

# Add request handler
async def add_auth(request):
    request["headers"]["Authorization"] = "Bearer token"

monitor.interceptor.add_request_handler(add_auth)

# Block tracking domains
monitor.interceptor.block_url_pattern("*.analytics.com")
```

## Module Components

### core/network_monitor.py

**Main Classes:**
- `NetworkRequest` - Dataclass representing a network request
- `NetworkResponse` - Dataclass representing a response
- `NetworkInterceptor` - Manages request/response interception
- `NetworkMonitor` - Main monitoring coordinator
- `MonitoringPatterns` - Pre-built monitoring patterns

**Key Methods:**
- `enable()` - Start monitoring
- `disable()` - Stop monitoring
- `on_request_will_be_sent(params)` - Handle RequestWillBeSent event
- `on_response_received(params)` - Handle ResponseReceived event
- `on_loading_finished(params)` - Handle LoadingFinished event
- `on_loading_failed(params)` - Handle LoadingFailed event
- `get_metrics()` - Get aggregated metrics
- `filter_requests()` - Filter by URL, method, status, etc.
- `interceptor` - Access the request/response interceptor

**Interceptor Methods:**
- `add_request_handler(handler)` - Add custom request handler
- `add_response_handler(handler)` - Add custom response handler
- `block_url_pattern(pattern)` - Block URLs matching pattern
- `modify_request(request_id, modifications)` - Modify request before sending

**Patterns:**
- `create_api_monitor()` - Monitor API calls
- `create_performance_monitor()` - Monitor performance
- `create_security_monitor()` - Monitor security
- `create_bandwidth_monitor()` - Monitor bandwidth usage

### network_monitor_examples.py

**10 Complete Examples:**

1. **Basic Network Monitoring** - Track all requests and collect metrics
2. **Request Interception** - Intercept and modify requests
3. **Response Body Extraction** - Extract and store response bodies
4. **Performance Analysis** - Analyze response times and identify slow requests
5. **Failed Request Tracking** - Monitor and analyze failed requests
6. **Security Monitoring** - Block unwanted requests and monitor security
7. **API Monitoring** - Monitor API calls specifically
8. **Request Filtering** - Filter by URL, method, status, resource type
9. **Custom Pattern** - Create custom monitoring patterns
10. **Comprehensive Session** - Monitor complete browsing session

Each example includes:
- Clear use case description
- Step-by-step implementation
- Output and verification
- Comments explaining key concepts

### network_monitor_integration.py

**Integration Classes:**

- `CDPBridgeAdapter` - Abstract base for CDP implementation adapters
- `NetworkMonitorSession` - Session lifecycle management with context manager
- `NetworkEventCapture` - Capture events for replaying and testing
- `RequestModificationChain` - Chain multiple request modifications
- `PerformanceAnalyzer` - Analyze performance metrics
- `SecurityAnalyzer` - Analyze security aspects

**Utility Functions:**
- `create_standard_interceptor()` - Create configured interceptor
- `create_logging_interceptor()` - Create logging-focused interceptor

**Key Features:**
- Session lifecycle management
- Event replay and export
- Fluent modification API
- Comprehensive analysis tools
- Ready-to-use utilities

### network_monitor_tests.py

**Test Classes:**

- `TestNetworkMonitorBasics` - Core functionality tests
- `TestNetworkInterception` - Interception feature tests
- `TestMonitoringPatterns` - Pattern tests
- `TestIntegrationUtilities` - Integration utility tests

**Test Methods:**
- `test_request_tracking()` - Verify request recording
- `test_response_tracking()` - Verify response recording
- `test_failed_request_tracking()` - Verify failure tracking
- `test_metrics_collection()` - Verify metrics aggregation
- `test_request_filtering()` - Verify filtering functionality
- `test_request_modification()` - Verify request interception
- `test_url_blocking()` - Verify URL pattern blocking
- `test_api_monitor_pattern()` - Verify API pattern
- `test_security_monitor_pattern()` - Verify security pattern
- `test_performance_monitor_pattern()` - Verify performance pattern
- `test_monitoring_session()` - Verify session management
- `test_event_capture()` - Verify event capture
- `test_performance_analyzer()` - Verify performance analysis
- `test_security_analyzer()` - Verify security analysis

Run all tests:
```bash
python network_monitor_tests.py
```

## Data Structures

### NetworkRequest
```python
@dataclass
class NetworkRequest:
    request_id: str
    url: str
    method: str
    timestamp: float
    headers: Dict[str, str]
    post_data: Optional[str]
    initiator: Optional[str]
    resource_type: str
```

### NetworkResponse
```python
@dataclass
class NetworkResponse:
    request_id: str
    status: int
    status_text: str
    headers: Dict[str, str]
    body: Optional[str]
    body_size: int
    mime_type: str
    timestamp: float
```

### Metrics Dictionary
```python
{
    "total_requests": int,
    "total_responses": int,
    "total_bytes": int,
    "average_response_time": float,
    "failed_requests": [
        {
            "url": str,
            "status": int,
            "status_text": str,
            "method": str,
            "timestamp": str,
        }
    ],
    "by_resource_type": {str: int},
    "by_status_code": {int: int},
    "by_domain": {str: int},
    "slowest_requests": [
        {
            "url": str,
            "time": float,
            "status": int,
        }
    ],
    "fastest_requests": [...]
}
```

## Common Usage Patterns

### 1. Monitor E-commerce Checkout

```python
async def monitor_checkout(driver):
    monitor = NetworkMonitor()
    monitor.enable()

    async def track_payment(request):
        if "/payment" in request.get("url", ""):
            print(f"Payment: {request['method']}")

    monitor.interceptor.add_request_handler(track_payment)

    # Navigate and checkout...
    metrics = monitor.get_metrics()
    return metrics
```

### 2. Find Performance Bottlenecks

```python
monitor = NetworkMonitor()
metrics = monitor.get_metrics()

print("Slowest requests:")
for req in metrics['slowest_requests']:
    print(f"  {req['url']}: {req['time']:.2f}s")

print("Failed requests:")
for failed in metrics['failed_requests']:
    print(f"  {failed['url']} - {failed['status']}")
```

### 3. Security Audit

```python
from network_monitor_integration import SecurityAnalyzer

analyzer = SecurityAnalyzer(monitor)
report = analyzer.get_security_report()

for insecure in report['insecure_requests']:
    print(f"Insecure: {insecure['url']}")
```

### 4. API Integration Testing

```python
api_monitor = MonitoringPatterns.create_api_monitor()
api_monitor.enable()

# Navigate and interact...

api_requests = api_monitor.filter_requests(method="POST")
for req in api_requests:
    print(f"API Call: {req['request']['url']}")
```

## Event Handling

### CDP Events

The module handles four main CDP Network events:

1. **Network.requestWillBeSent**
   - Fires before request is sent
   - Handler: `on_request_will_be_sent(params)`
   - Access: request URL, method, headers, body

2. **Network.responseReceived**
   - Fires when response is received
   - Handler: `on_response_received(params)`
   - Access: status code, headers, MIME type

3. **Network.loadingFinished**
   - Fires when resource loading completes
   - Handler: `on_loading_finished(params)`
   - Access: encoded data length, timing

4. **Network.loadingFailed**
   - Fires when resource loading fails
   - Handler: `on_loading_failed(params)`
   - Access: error text, reason

## Advanced Features

### Request Modification Chain

```python
from network_monitor_integration import RequestModificationChain

chain = RequestModificationChain()
chain.add_header("User-Agent", "CustomBot/1.0")
chain.add_auth_token("secret-token")
chain.add_custom_header_condition(
    lambda url: "api" in url,
    "X-API-Version",
    "2"
)

modified = chain.apply(request)
```

### Performance Analysis

```python
from network_monitor_integration import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(monitor)
report = analyzer.get_performance_report()

# Access detailed metrics
print(f"Slowest: {report['analysis']['slowest_request']['url']}")
print(f"Avg time: {report['summary']['average_response_time']:.2f}s")
```

### Security Analysis

```python
from network_monitor_integration import SecurityAnalyzer

analyzer = SecurityAnalyzer(monitor)

insecure = analyzer.find_insecure_requests()
sensitive = analyzer.find_sensitive_data_patterns()
origins = analyzer.analyze_cross_origin_requests()
```

## Performance Considerations

1. **Memory Usage**
   - Response bodies limited to `max_response_bodies` (default: 100)
   - Reduce limit for large-scale monitoring
   - Use filtering to work with subsets

2. **Event Processing**
   - Async handlers recommended
   - Avoid blocking operations in handlers
   - Use interceptor for efficient filtering

3. **Data Retention**
   - Call `clear()` between sessions
   - Implement periodic cleanup for long-running monitors
   - Consider exporting data before clearing

## Integration with Browser Automation

### Pseudo-code Integration

```python
# With browser driver
driver = await launch_browser()
monitor = NetworkMonitor()
monitor.enable()

# Connect CDP events (framework-specific)
driver.on("Network.requestWillBeSent",
          monitor.on_request_will_be_sent)
driver.on("Network.responseReceived",
          monitor.on_response_received)

# Automate
await driver.navigate("https://example.com")
await driver.click("button.submit")

# Analyze
metrics = monitor.get_metrics()
```

## Troubleshooting

### No requests recorded
- Verify `enable()` called before navigation
- Check event handler connections
- Ensure CDP events are being fired

### Memory issues
- Reduce `max_response_bodies`
- Call `clear()` regularly
- Use filtering to reduce data

### Slow performance
- Disable response body capture
- Reduce event handler complexity
- Use patterns instead of custom handlers

## File Locations

```
/home/jamesprial/code/skills/.claude/skills/nodriver/scripts/
├── network_monitor.py
├── network_monitor_examples.py
├── network_monitor_integration.py
├── network_monitor_tests.py
├── NETWORK_MONITOR_README.md
└── INDEX.md
```

## Testing

Run the test suite:

```bash
cd /home/jamesprial/code/skills/.claude/skills/nodriver/scripts
python network_monitor_tests.py
```

Expected output:
```
============================================================
NETWORK MONITOR TEST SUITE
============================================================

Running basic functionality tests...
✓ Request tracking test passed
✓ Response tracking test passed
✓ Failed request tracking test passed
✓ Metrics collection test passed
✓ Request filtering test passed

[... more tests ...]

============================================================
ALL TESTS PASSED!
============================================================
```

## Examples

See `network_monitor_examples.py` for 10 complete, runnable examples:

```bash
python network_monitor_examples.py
```

Examples include:
1. Basic network monitoring
2. Request interception and modification
3. Response body extraction
4. Performance analysis
5. Failed request tracking
6. Security monitoring
7. API call monitoring
8. Request filtering
9. Custom monitoring patterns
10. Comprehensive session monitoring

## Best Practices

1. **Always clean up** - Use context managers or call `disable()`
2. **Be specific** - Use filters and patterns for focused monitoring
3. **Handle errors** - Wrap handler code in try-except
4. **Limit scope** - Use appropriate `max_response_bodies` setting
5. **Clear regularly** - Call `clear()` between test runs
6. **Log appropriately** - Use async handlers for logging
7. **Test thoroughly** - Run test suite before production use

## Next Steps

1. Review the examples in `network_monitor_examples.py`
2. Check integration utilities in `network_monitor_integration.py`
3. Run the test suite in `network_monitor_tests.py`
4. Read detailed API docs in `NETWORK_MONITOR_README.md`
5. Integrate with your browser automation framework
6. Customize patterns and handlers for your use case

## Support Files

- **API Documentation**: `NETWORK_MONITOR_README.md`
- **Examples**: `network_monitor_examples.py`
- **Integration**: `network_monitor_integration.py`
- **Tests**: `network_monitor_tests.py`

All files are in `/home/jamesprial/code/skills/.claude/skills/nodriver/scripts/`
