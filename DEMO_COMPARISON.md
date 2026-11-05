# Side-by-Side Demo: Consul 2.0.x (Custom Middleware) vs. Consul 2.1 (Agentic Runtime Fabric)

This guide demonstrates both architectures running live side-by-side in your environment:
* **Stack A (Consul 2.0.x Baseline - Port 10000):** Envoy + `ext_authz` + FastAPI Guardrail Service + OPA Engine.
* **Stack B (Consul 2.1 Agentic Mesh - Port 10001):** Native Consul AI Gateway with in-proxy Credential Injection, Multi-Provider Fallback Routing, and Native Token Rate Limiting.

---

## 📊 High-Level Comparison Matrix

| Feature | Stack A (Consul 2.0.x Custom Stack) | Stack B (Consul 2.1 Agentic Mesh) |
| :--- | :--- | :--- |
| **Ingress Port** | `http://localhost:10000` | `http://localhost:10001` |
| **Credential Management** | Passed manually in request or injected via custom Python | **Native Proxy Injection** (Backed by Vault) |
| **Model Routing** | Hardcoded upstream routes | **Declarative Multi-Provider Routing** (OpenAI / Anthropic) |
| **Rate Limiting** | Custom Python token counting | **Native Envoy Local Token Bucket (TPM/RPM)** |
| **Tool Discovery** | Custom routing logic | **Mesh-native MCP Service Registration** |
| **Custom Middleware Needed** | **Yes** (FastAPI container required) | ❌ **No custom container needed** |

---

## 🧪 Interactive Comparative Demo

### **Demo Part 1: Credential Injection & Provider Routing**

#### 1. Stack A (Consul 2.0.x Baseline - Port 10000)
Agent sends request through Envoy; FastAPI/OPA checks permissions:
```bash
curl -i -X POST http://localhost:10000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-agent-id: agent-finance-analyst" \
  -H "x-tenant-id: tenant-finance" \
  -H "x-model-name: gpt-4o" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Analyze risk"}]}'
```

#### 2. Stack B (Consul 2.1 Agentic Runtime Fabric - Port 10001)
Agent sends a simple request **without any API keys**. Consul's Agentic Gateway intercepts the call, **injects the Vault-managed OpenAI Bearer token directly at the proxy layer**, and routes to OpenAI:
```bash
curl -i -X POST http://localhost:10001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: tenant-finance" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Analyze risk"}]}'
```
*💡 **Notice in the JSON response:** `"has_injected_api_key": true` — the AI application never touches the API secret.*

---

### **Demo Part 2: Multi-Provider Fallback Routing**

In Stack B, agents can route seamlessly across different foundation model providers through a single unified ingress gateway:

```bash
# Call Anthropic claude-3-5 model via unified Agentic Gateway
curl -i -X POST http://localhost:10001/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: tenant-research" \
  -d '{"model": "claude-3-5-sonnet", "messages": [{"role": "user", "content": "Summarize study"}]}'
```
*💡 **Result:** Route rewrite automatically dispatches to the Anthropic provider backend.*

---

### **Demo Part 3: Native MCP Tool Discovery**

Agents invoke Model Context Protocol (MCP) database tools registered directly in the Consul Service Mesh:

```bash
curl -i -X POST http://localhost:10001/mcp/internal-db \
  -H "Content-Type: application/json" \
  -H "x-tenant-id: tenant-finance" \
  -d '{"action": "query_accounts"}'
```

---

## ⚡ Run Full Automated Comparative Test Suite

Execute all 6 validation scenarios across both stacks in one command:

```bash
python3 -m pytest /Users/chrislovett/hashi/agentic-mesh/test_comparative.py -v
```

**Output:**
```
test_stack_a_entitled_llm_inference                     PASSED [ 16%]
test_stack_a_prompt_injection_blocked_by_fastapi_guard  PASSED [ 33%]
test_stack_a_external_egress_blocked_by_opa             PASSED [ 50%]
test_stack_b_native_provider_routing_and_secret_inject  PASSED [ 66%]
test_stack_b_native_multi_provider_fallback_routing     PASSED [ 83%]
test_stack_b_native_mcp_tool_discovery_routing          PASSED [100%]

============================== 6 passed in 0.20s ===============================
```
