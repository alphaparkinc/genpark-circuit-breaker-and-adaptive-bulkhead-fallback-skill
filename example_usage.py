"""Example usage for Circuit Breaker and Adaptive Bulkhead Fallback."""
from client import CircuitBreakerBulkhead


def mock_service_call(circuit: CircuitBreakerBulkhead, fail: bool = False):
    check = circuit.can_execute()
    if not check["allowed"]:
        print(f"[FAST-FAIL FALLBACK] Reason: {check['reason']} (State: {check['state']})")
        return "FALLBACK_CACHED_RESPONSE"

    try:
        if fail:
            raise ConnectionResetError("Remote downstream timeout 504")
        circuit.record_success()
        return "SUCCESS_REMOTE_RESPONSE"
    except Exception as e:
        circuit.record_failure()
        return f"ERROR: {str(e)}"


def main():
    print("=== 1. Normal Operations (State: CLOSED) ===")
    cb = CircuitBreakerBulkhead(
        failure_rate_threshold=0.50,
        sliding_window_size=4,
        recovery_timeout_seconds=5.0,
        max_concurrent_calls=2,
    )
    for _ in range(3):
        res = mock_service_call(cb, fail=False)
        print("Result:", res)

    print("\n=== 2. Inducing Consecutive Failures to Trip Circuit ===")
    for i in range(4):
        res = mock_service_call(cb, fail=True)
        print(f"Call #{i+1} -> {res}")

    print("Current State:", cb.get_status()["state"])

    print("\n=== 3. Immediate Subsequent Call (Short-Circuited) ===")
    fallback_res = mock_service_call(cb, fail=False)
    print("Output:", fallback_res)

    print("\n=== 4. Testing Bulkhead Concurrency Limit ===")
    cb_bulkhead = CircuitBreakerBulkhead(max_concurrent_calls=1)
    res_allowed = cb_bulkhead.can_execute()
    print("Call 1 Allowed:", res_allowed["allowed"])
    res_blocked = cb_bulkhead.can_execute()
    print("Call 2 Allowed:", res_blocked["allowed"], "(Reason:", res_blocked["reason"], ")")


if __name__ == "__main__":
    main()
