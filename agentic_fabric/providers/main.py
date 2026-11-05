"""
Mock Multi-Provider LLM & MCP Tool Endpoints
Simulates OpenAI, Anthropic, and Local Inference Providers with Token Counting
"""
from fastapi import FastAPI, Request, Header, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import time

app = FastAPI(title="Multi-Provider LLM & MCP Mock Backends", version="2.1.0")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]

# Track token usage per tenant for demo observability
token_usage_ledger = {"tenant-finance": 0, "tenant-research": 0, "global": 0}

@app.post("/openai/v1/chat/completions")
async def openai_completions(req: ChatCompletionRequest, request: Request):
    """Primary OpenAI Provider Backend (e.g. gpt-4o)"""
    auth_header = request.headers.get("authorization", "")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid injected provider API key",
        )
    
    tenant = request.headers.get("x-tenant-id", "unknown-tenant")
    prompt_tokens = sum(len(m.content.split()) for m in req.messages) * 2
    completion_tokens = 15
    total_tokens = prompt_tokens + completion_tokens

    token_usage_ledger[tenant] = token_usage_ledger.get(tenant, 0) + total_tokens
    token_usage_ledger["global"] += total_tokens

    return {
        "id": "chatcmpl-openai-mock",
        "provider": "openai",
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[OpenAI Provider Response via Consul Agentic Mesh] Processed for {tenant}.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
        "headers_inspected": {
            "x-tenant-id": tenant,
            "has_injected_api_key": True,
        },
    }

@app.post("/anthropic/v1/messages")
async def anthropic_completions(request: Request):
    """Fallback Anthropic Provider Backend (e.g. claude-3-5-sonnet)"""
    body = await request.json()
    tenant = request.headers.get("x-tenant-id", "unknown-tenant")
    
    return {
        "id": "msg-anthropic-mock",
        "provider": "anthropic",
        "model": body.get("model", "claude-3-5-sonnet"),
        "content": [
            {
                "type": "text",
                "text": f"[Anthropic Fallback Provider Response] Responded seamlessly for {tenant}.",
            }
        ],
        "usage": {"input_tokens": 20, "output_tokens": 15},
    }

@app.post("/mcp/internal-db")
async def mcp_internal_db(request: Request):
    """MCP Tool: Database Provider"""
    body = await request.json()
    tenant = request.headers.get("x-tenant-id", "unknown-tenant")
    return {
        "mcp_server": "internal-db-service",
        "status": "success",
        "data": [{"account_id": "ACC-8801", "balance": 950000.0, "tenant": tenant}],
    }

@app.get("/metrics/tokens")
async def get_token_metrics():
    """AI Observability Endpoint for Token Tracking"""
    return {"token_usage_ledger": token_usage_ledger}

@app.get("/healthz")
async def health():
    return {"status": "healthy", "service": "agentic-provider-mock"}
