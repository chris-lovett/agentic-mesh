# Consul Envoy & OPA Guardrails for AI Workloads

This repository provides an enterprise proof-of-concept and deployment template for securing **AI Agent Workloads** using **Consul Service Mesh**, **Envoy `ext_authz`**, **FastAPI Content Guardrails**, and **Open Policy Agent (OPA)**.

---

## 🎯 Architecture Overview

```
   Tenant Agent Request
            │
            ▼
┌──────────────────────────────┐
│     Envoy Proxy Sidecar      │ (Port 10000)
└──────────────┬───────────────┘
               │ 1. Intercept & ext_authz check
               ▼
┌──────────────────────────────┐
│  FastAPI Guardrail Service   │ (Port 8000)
│   • Regex PII Scanner        │
│   • Prompt Injection Filter  │
└──────────────┬───────────────┘
               │ 2. Evaluate Rego Entitlements
               ▼
┌──────────────────────────────┐
│          OPA Engine          │ (Port 8181)
│   • Allowed Tools & Models   │
│   • Egress Boundaries        │
└──────────────┬───────────────┘
               │
       ┌───────┴───────┐
  200 OK          403 Forbidden
 (Approved)          (Blocked)
       │                 │
       ▼                 ▼
 Upstream Services    Drop Connection
 (LLM / MCP Tools)   (Return Error to Pod)
```

---

## 📁 Repository Structure

```
.
├── auth_service/               # FastAPI Guardrail service & OPA Rego policies
│   ├── main.py
│   ├── Dockerfile
│   └── policies/
│       └── policy.rego         # OPA Rego entitlement rules
├── upstream_service/           # Mock Platform LLM Inference & MCP Tools
│   ├── main.py
│   └── Dockerfile
├── envoy/                      # Envoy configuration with ext_authz filter
│   └── envoy.yaml
├── docker-compose.yml          # Local live testing stack
├── test_integration.py         # Automated pytest regression suite (7 scenarios)
├── DEMO_GUIDE.md               # Step-by-step interactive demo guide
├── helm/agent-mesh-authz/      # Production Kubernetes / OpenShift Helm Chart
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/              # Consul CRDs, Deployments, and ConfigMaps
└── requirements.txt
```

---

## 🚀 Quickstart (Local Docker)

### 1. Start the Stack
```bash
docker compose up -d --build
```

### 2. Run Automated Verification Tests
```bash
python3 -m pytest test_integration.py -v
```

### 3. Interactive Testing
Check out [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for step-by-step `curl` commands testing:
* **Allowed Path:** Entitled Finance Agent calling approved LLM (`gpt-4o`) $\rightarrow$ `200 OK`
* **Blocked by OPA:** Finance Agent attempting unentitled external search tool $\rightarrow$ `403 Forbidden`
* **Blocked by Guardrails:** Prompt injection or PII in payload $\rightarrow$ `403 Forbidden`

---

## ☸️ Kubernetes & OpenShift Deployment (Helm)

A complete Helm chart configured for Consul Connect sidecar injection and `ServiceDefaults` / `ServiceIntentions` is located under `helm/agent-mesh-authz/`.

```bash
helm install agent-mesh-authz ./helm/agent-mesh-authz \
  --namespace tenant-finance \
  --create-namespace
```
