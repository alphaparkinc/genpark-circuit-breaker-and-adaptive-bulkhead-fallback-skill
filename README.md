# genpark-circuit-breaker-and-adaptive-bulkhead-fallback-skill

Resilience circuit breaker state machine, adaptive concurrency bulkhead, and graceful degradation fallback arbiter.

100% Python Standard Library implementation with zero external dependencies.

## Key Capabilities

- **3-State Circuit Breaker Finite State Machine**: Manages transitions across `CLOSED`, `OPEN`, and `HALF_OPEN` states.
- **Rolling Error Rate Window**: Tracks failures over a bounded rolling deque to detect cascading outages before exhausting backend thread pools.
- **Adaptive Bulkhead Concurrency Isolation**: Enforces maximum inflight concurrent executions to isolate failures to failing sub-services.
- **Fast-Fail & Graceful Fallback**: Instantly redirects downstream callers to cached or degraded fallbacks without blocking on remote timeouts.

## Architecture

```
[Downstream Service Call Request]
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│             CircuitBreakerBulkhead                  │
│  - State Machine Arbiter (CLOSED / OPEN / HALF_OPEN)│
│  - Concurrency Bulkhead Inflight Counter            │
│  - Rolling Sliding Window Error Rate Calculator     │
│  - Fast-Fail Fallback Router                        │
└─────────────────────────────────────────────────────┘
         │                               │
  (Healthy / In-Quota)          (Tripped / Bulkhead Full)
         ▼                               ▼
[Execute Downstream Call]       [Fast-Fail Graceful Fallback]
```

## MCP Server Integration

Run standard MCP stdio server:
```bash
python mcp_server.py
```

Exposed Tools:
- `circuit_can_execute`: Checks if an execution is permitted under current circuit state and bulkhead concurrency limits.
- `circuit_record_result`: Records execution outcome (success or failure) to update rolling metrics and state transitions.
- `circuit_get_status`: Retrieves current diagnostic state of circuit breaker and bulkhead usage.

## Quickstart (Python API)

```python
from client import CircuitBreakerBulkhead

circuit = CircuitBreakerBulkhead()
check = circuit.can_execute()
if check["allowed"]:
    # Call remote API
    circuit.record_success()
else:
    # Execute fallback
    print("Fallback activated:", check["reason"])
```

---

## GenPark Ecosystem

- **Official Website**: [https://www.genpark.ai](https://www.genpark.ai)
- **LinkedIn Page**: [https://www.linkedin.com/company/92955550](https://www.linkedin.com/company/92955550)
