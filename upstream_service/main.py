"""
Mock Upstream Services:
1. Platform Namespace: /v1/chat/completions (LLM Inference), /mcp/internal-db, /mcp/internal-fx-rates
2. External Services: /mcp/external-search
"""
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Mock Platform & External Services", version="1.0.0")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    """Platform Namespace: LLM Inference API"""
    auth_tenant = request.headers.get("x-authenticated-tenant", "unknown")
    auth_agent = request.headers.get("x-authenticated-agent", "unknown")
    
    return {
        "id": "chatcmpl-mock-12345",
        "object": "chat.completion",
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[LLM Response] Processed prompt for {auth_agent} ({auth_tenant}).",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 15, "completion_tokens": 12, "total_tokens": 27},
    }

@app.post("/mcp/internal-db")
async def internal_db_tool(request: Request):
    """Platform Namespace: Internal MCP Tool (Database Query)"""
    body = await request.json()
    query = body.get("query", "SELECT 1")
    return {
        "tool": "mcp-internal-db",
        "status": "success",
        "result": [
            {"account_id": "ACC-9921", "balance_usd": 1450200.50, "status": "ACTIVE"},
            {"account_id": "ACC-9922", "balance_usd": 320100.00, "status": "ACTIVE"},
        ],
        "message": f"Successfully executed query: '{query}'",
    }

@app.post("/mcp/internal-fx-rates")
async def internal_fx_rates(request: Request):
    """Platform Namespace: Internal MCP Tool (FX Rates)"""
    return {
        "tool": "mcp-fx-rates",
        "rates": {"USD/EUR": 0.92, "USD/GBP": 0.79, "USD/JPY": 152.3},
    }

@app.post("/mcp/external-search")
async def external_search_tool(request: Request):
    """External Services: External Search Tool"""
    body = await request.json()
    query = body.get("query", "")
    return {
        "tool": "mcp-external-search",
        "status": "success",
        "results": [
            {"title": "Latest AI Governance Standards", "url": "https://example.com/ai-gov"},
            {"title": "Open Policy Agent in Financial Services", "url": "https://example.com/opa-fin"},
        ],
        "query": query,
    }

@app.get("/healthz")
async def health():
    return {"status": "healthy", "service": "upstream-mock"}
