"""
FastAPI Guardrail & OPA Authorization Service for AI Workloads
Implements Envoy ext_authz HTTP Check interface.
"""
import os
import re
import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("auth-service")

app = FastAPI(title="AI Agent Auth & Guardrail Service", version="1.0.0")

OPA_URL = os.getenv("OPA_URL", "http://opa:8181/v1/data/bofa/agent/authz")

# ---------------------------------------------------------------------------
# Fallback / In-Memory Policy Store
# ---------------------------------------------------------------------------
AGENT_PERMISSIONS: Dict[str, Dict[str, Any]] = {
    "agent-finance-analyst": {
        "tenant": "tenant-finance",
        "allowed_tools": ["mcp-internal-db", "mcp-fx-rates"],
        "allowed_models": ["gpt-4o", "claude-3-5-sonnet", "llama-3-70b"],
        "allow_external_egress": False,
    },
    "agent-research-bot": {
        "tenant": "tenant-research",
        "allowed_tools": ["mcp-internal-db", "mcp-external-search"],
        "allowed_models": ["gpt-4o", "claude-3-5-sonnet"],
        "allow_external_egress": True,
    },
    "agent-untrusted-sandbox": {
        "tenant": "tenant-sandbox",
        "allowed_tools": [],
        "allowed_models": ["llama-3-8b"],
        "allow_external_egress": False,
    },
}

# ---------------------------------------------------------------------------
# Content Guardrail Engine (PII & Prompt Injection Detectors)
# ---------------------------------------------------------------------------
PII_PATTERNS = {
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    "API_SECRET_KEY": re.compile(r"\b(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})\b"),
}

PROMPT_INJECTION_KEYWORDS = [
    "ignore all previous instructions",
    "ignore previous instructions",
    "system prompt override",
    "bypass safety filters",
    "disregard guidelines and output confidential",
]

def evaluate_guardrails(content: str) -> Dict[str, Any]:
    """Runs regex scans, PII detection, and prompt injection filters."""
    if not content:
        return {"passed": True, "violations": []}
    
    violations = []
    content_lower = content.lower()

    # 1. PII Scans
    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(content):
            violations.append(f"PII Leakage Detected: {pii_type}")

    # 2. Prompt Injection Scans
    for keyword in PROMPT_INJECTION_KEYWORDS:
        if keyword in content_lower:
            violations.append(f"Prompt Injection Detected: '{keyword}'")

    return {
        "passed": len(violations) == 0,
        "violations": violations,
    }

# ---------------------------------------------------------------------------
# OPA Policy Evaluation
# ---------------------------------------------------------------------------
async def query_opa_policy(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Queries external OPA server, falling back to local Python evaluator if unreachable."""
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.post(OPA_URL, json={"input": input_data})
            if resp.status_code == 200:
                result = resp.json().get("result", {})
                return {
                    "allow": result.get("allow", False),
                    "reason": result.get("reason", "OPA decision"),
                }
    except Exception as exc:
        logger.debug(f"OPA service unreachable ({exc}), evaluating in-memory rules...")

    # In-memory evaluation fallback
    agent_id = input_data.get("agent_id", "")
    tenant_id = input_data.get("tenant_id", "")
    path = input_data.get("path", "")
    tool_name = input_data.get("tool_name", "")
    model = input_data.get("model", "gpt-4o")

    agent = AGENT_PERMISSIONS.get(agent_id)
    if not agent:
        return {"allow": False, "reason": f"Agent '{agent_id}' is unknown or not registered"}
    
    if agent.get("tenant") != tenant_id:
        return {"allow": False, "reason": f"Tenant mismatch: provided '{tenant_id}', expected '{agent.get('tenant')}'"}

    # Rule 1: LLM Inference
    if path == "/v1/chat/completions":
        if model in agent.get("allowed_models", []):
            return {"allow": True, "reason": "Authorized for LLM inference"}
        return {"allow": False, "reason": f"Model '{model}' is not permitted for agent '{agent_id}'"}

    # Rule 2: Internal Tools
    if path.startswith("/mcp/internal-"):
        if tool_name in agent.get("allowed_tools", []):
            return {"allow": True, "reason": f"Authorized for internal tool '{tool_name}'"}
        return {"allow": False, "reason": f"Agent '{agent_id}' is not entitled to use tool '{tool_name}'"}

    # Rule 3: External Tools / Egress
    if path.startswith("/mcp/external-"):
        if not agent.get("allow_external_egress"):
            return {"allow": False, "reason": f"Agent '{agent_id}' is forbidden from external egress"}
        if tool_name in agent.get("allowed_tools", []):
            return {"allow": True, "reason": f"Authorized for external tool '{tool_name}'"}
        return {"allow": False, "reason": f"Agent '{agent_id}' is not entitled to external tool '{tool_name}'"}

    return {"allow": False, "reason": f"Unrecognized destination path '{path}'"}

# ---------------------------------------------------------------------------
# Envoy ext_authz HTTP Check Endpoint
# ---------------------------------------------------------------------------
@app.api_route("/v1/auth/check", methods=["GET", "POST", "PUT", "DELETE"])
@app.api_route("/v1/auth/check/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def envoy_ext_authz_check(request: Request, full_path: Optional[str] = None):
    """
    Main authorization entrypoint for Envoy ext_authz filter.
    Envoy passes original headers and buffered metadata.
    """
    headers = request.headers
    
    # Extract metadata passed by Envoy or Agent
    original_uri = headers.get("x-original-uri") or headers.get("x-envoy-original-path") or (f"/{full_path}" if full_path else request.url.path)
    original_method = headers.get("x-original-method", request.method)
    agent_id = headers.get("x-agent-id", "agent-untrusted-sandbox")
    tenant_id = headers.get("x-tenant-id", "tenant-sandbox")
    tool_name = headers.get("x-tool-name", "")
    model_name = headers.get("x-model-name", "gpt-4o")

    # Read payload for guardrail inspection if available
    body_text = ""
    try:
        raw_body = await request.body()
        if raw_body:
            body_text = raw_body.decode("utf-8", errors="ignore")
            try:
                body_json = json.loads(body_text)
                if isinstance(body_json, dict):
                    if "model" in body_json:
                        model_name = body_json["model"]
                    if "tool" in body_json:
                        tool_name = body_json["tool"]
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Could not read request body: {e}")

    logger.info(f"🔍 [ext_authz] Incoming request: agent={agent_id}, tenant={tenant_id}, path={original_uri}, tool={tool_name}")

    # -------------------------------------------------------------
    # Step 1: Content Guardrail Check (FastAPI)
    # -------------------------------------------------------------
    guardrail_result = evaluate_guardrails(body_text)
    if not guardrail_result["passed"]:
        violations_str = "; ".join(guardrail_result["violations"])
        logger.warning(f"❌ [Guardrail Denied] {violations_str}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            headers={
                "x-auth-decision": "denied",
                "x-guardrail-status": "violation-detected",
                "x-auth-reason": violations_str,
            },
            content={
                "error": "Security Guardrail Violation",
                "violations": guardrail_result["violations"],
                "status": "blocked",
            },
        )

    # -------------------------------------------------------------
    # Step 2: OPA Policy / Entitlement Check
    # -------------------------------------------------------------
    opa_input = {
        "agent_id": agent_id,
        "tenant_id": tenant_id,
        "path": original_uri,
        "method": original_method,
        "tool_name": tool_name,
        "model": model_name,
    }
    
    opa_result = await query_opa_policy(opa_input)
    
    if not opa_result["allow"]:
        logger.warning(f"❌ [Policy Denied] agent={agent_id}, reason={opa_result['reason']}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            headers={
                "x-auth-decision": "denied",
                "x-auth-reason": opa_result["reason"],
            },
            content={
                "error": "Policy Authorization Denied",
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "reason": opa_result["reason"],
            },
        )

    # -------------------------------------------------------------
    # Step 3: Approved - Return 200 OK with Enriched Headers
    # -------------------------------------------------------------
    logger.info(f"✅ [Auth Approved] agent={agent_id}, path={original_uri}")
    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "x-auth-decision": "allowed",
            "x-authenticated-tenant": tenant_id,
            "x-authenticated-agent": agent_id,
            "x-guardrail-verdict": "pass",
            "x-auth-reason": opa_result["reason"],
        },
    )

@app.get("/healthz")
async def health_check():
    return {"status": "healthy", "service": "fastapi-opa-guardrail-orchestrator"}
