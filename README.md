# Consul Agentic Mesh & AI Workload Security

Enterprise proof-of-concept, architecture patterns, and deployment manifests for securing **AI Agent Workloads** with **Consul Service Mesh**, **Envoy `ext_authz`**, **FastAPI Guardrails**, **Open Policy Agent (OPA)**, and the **Consul 2.1 Agentic Runtime Fabric**.

---

## 🎯 Repository Structure

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
├── consul_install/openshift/   # Enterprise Consul 2.1 Helm & OpenShift SCC Manifests
├── helm/
│   ├── agentic-fabric/         # Stack B: Consul 2.1 Agentic Runtime Fabric Chart
│   └── agent-mesh-authz/       # Stack A: Envoy ext_authz + FastAPI + OPA Chart
│
├── DEMO_AGENTIC_FABRIC.md      # Live OpenShift Demo Guide for Consul 2.1 Agentic Fabric
├── DEMO_COMPARISON.md          # Side-by-side architecture comparison guide
├── DEMO_GUIDE.md               # Step-by-step interactive demo guide
├── test_comparative.py         # Automated comparative test suite (Stack A vs Stack B)
└── test_integration.py         # Automated pytest regression suite (Stack A)
```

---

## 🏗️ Architectural Models

### **Stack A: Consul 2.0.x Custom Stack (Port 10000)**
* **Mechanism:** In-pod Envoy sidecar intercepts traffic and delegates to a shared **FastAPI + OPA** service via `ext_authz`.
* **Strengths:** Python flexibility for custom regex, PII redaction, and prompt injection filters.

### **Stack B: Consul 2.1 Agentic Runtime Fabric (Port 10001)**
* **Mechanism:** Native **Consul AI Gateway** configuring in-proxy **Vault Credential Injection**, **Multi-Provider Failover Routing** (OpenAI $\leftrightarrow$ Anthropic), **Native Token Bucket Limiting (TPM/RPM)**, and **MCP Tool Discovery**.
* **Strengths:** Zero custom middleware; high-performance C++ Envoy execution on the service mesh data plane.

---

## 🚀 Live Demos

* **[Consul 2.1 Agentic Fabric OpenShift Walkthrough](DEMO_AGENTIC_FABRIC.md)** — Step-by-step commands and live curl/Python snippets for credential injection, rate limiting, and MCP discovery.
* **[Stack Comparison Guide](DEMO_COMPARISON.md)** — Deep dive into Stack A vs Stack B latency and operational complexity.
* **[Stack A Guardrail Guide](DEMO_GUIDE.md)** — Test cases for prompt injection and PII interception.

---

## ☸️ OpenShift Deployment Commands

```bash
# 1. Install Consul Enterprise on OpenShift (ROSA 4.22)
cd consul_install/openshift
./install-consul.sh

# 2. Deploy Stack B (Consul 2.1 Agentic Runtime Fabric)
helm upgrade --install agentic-fabric ./helm/agentic-fabric --namespace agentic-workloads

# 3. Expose Consul UI Route
oc create route passthrough consul-ui --service=consul-ui --port=https -n consul
```
