"""MCP server for Circuit Breaker and Adaptive Bulkhead Fallback."""
import sys
import json
from client import CircuitBreakerBulkhead

_circuit = CircuitBreakerBulkhead()


def handle_request(req):
    method = req.get("method")
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": "circuit_can_execute",
                    "description": "Checks if an execution is permitted under current circuit state and bulkhead concurrency limits",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                },
                {
                    "name": "circuit_record_result",
                    "description": "Records execution outcome (success or failure) to update rolling metrics and state transitions",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "success": {"type": "boolean"},
                        },
                        "required": ["success"],
                    },
                },
                {
                    "name": "circuit_get_status",
                    "description": "Retrieves current diagnostic state of circuit breaker and bulkhead usage",
                    "inputSchema": {
                        "type": "object",
                        "properties": {},
                    },
                },
            ]
        }
    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        if tool_name == "circuit_can_execute":
            res = _circuit.can_execute()
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
        elif tool_name == "circuit_record_result":
            if args.get("success"):
                _circuit.record_success()
            else:
                _circuit.record_failure()
            return {"content": [{"type": "text", "text": json.dumps(_circuit.get_status(), indent=2)}]}
        elif tool_name == "circuit_get_status":
            res = _circuit.get_status()
            return {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
    return {"error": "Method not found"}


if __name__ == "__main__":
    for line in sys.stdin:
        if line.strip():
            print(json.dumps(handle_request(json.loads(line))))
            sys.stdout.flush()
