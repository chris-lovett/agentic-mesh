# Consul Agentic Mesh & AI Workload Security

Enterprise proof-of-concept, architecture patterns, and deployment manifests for securing **AI Agent Workloads** with **Consul Service Mesh**, **Envoy `ext_authz`**, **FastAPI Guardrails**, **Open Policy Agent (OPA)**, and the **Consul 2.1 Agentic Runtime Fabric**.

---

## 🎯 What This Repository Contains

```
.
├── agentic_fabric/             # Consul 2.1 Agentic Runtime Fabric (Native AI Gateway)
│   ├── envoy/                  # Native Token Limiting (TPM/RPM) & Vault Secret Injection
│   ├── helm/                   # Consul 2.1 CRDs (ServiceDefaults, ServiceRoute)
│   └── providers/              # Multi-Provider Foundation Model Mocks (OpenAI, Anthropic, MCP)
│
├── auth_service/               # FastAPI Guardrail Orchestrator & OPA Rego Policies
│   ├── main.py                 # PII Regex Scans & Prompt Injection Filters
│   └── policies/policy.rego    # Declarative Tool & Egress Entitlement Matrix
│
├── upstream_service/           # Mock Platform LLM Inference & Internal/External Tools
├── envoy/                      # Envoy Proxy Sidecar with ext_authz Filter
├── consul_install/openshift/   # Enterprise Consul 2.1 Helm & OpenShift SCC Manifests
├── helm/agent-mesh-authz/      # Kubernetes / OpenShift Helm Chart for Agent Pods
├── test_integration.py         # Automated pytest regression suite (Stack A)
├── test_comparative.py         # Automated comparative test suite (Stack A vs Stack B)
├── DEMO_GUIDE.md               # Step-by-step interactive demo guide
└── DEMO_COMPARISON.md          # Side-by-side architecture comparison guide
```

---

## 🏗️ Two Architecture Horizons Side-by-Side

### **Stack A: Consul 2.0.x Custom Stack (Port 10000)**
* **Mechanism:** In-pod Envoy sidecar intercepts traffic and delegates to a shared **FastAPI + OPA** service via `ext_authz`.
* **Strengths:** Full Python flexibility for PII redaction, prompt injection filtering, and complex dynamic business logic.

### **Stack B: Consul 2.1 Agentic Runtime Fabric (Port 10001)**
* **Mechanism:** Native **Consul AI Gateway** configuring in-proxy **Vault Credential Injection**, **Multi-Provider Failover Routing** (OpenAI $\rightarrow$ Anthropic), and **Native Token Bucket Limiting (TPM/RPM)**.
* **Strengths:** Eliminates custom middleware containers and handles AI traffic controls directly in the mesh data plane.

---

## 🚀 Quickstart (Local Docker)

### 1. Launch Both Stacks
```bash
docker compose up -d --build
```

### 2. Run Automated Comparative Tests
```bash
python3 -m pytest test_comparative.py -v
```

### 3. Interactive Demos
* See [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for individual policy and guardrail test scenarios.
* See [`DEMO_COMPARISON.md`](DEMO_COMPARISON.md) for side-by-side credential injection and multi-provider failover.

---

## ☸️ OpenShift & Kubernetes Deployment

### 1. Install Enterprise Consul on OpenShift (ROSA)
```bash
cd consul_install/openshift
./install-consul.sh
```

### 2. Deploy the AI Agent Workload Helm Chart
```bash
helm install agent-mesh-authz ./helm/agent-mesh-authz \
  --namespace tenant-finance \
  --create-namespace
```
