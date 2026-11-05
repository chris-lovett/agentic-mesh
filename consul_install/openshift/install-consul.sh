#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "Installing Consul Enterprise on OpenShift (ROSA 4.22)"
echo "=========================================================="

# 1. Create consul namespace
oc create namespace consul --dry-run=client -o yaml | oc apply -f -

# 2. Apply Consul SCC permissions for OpenShift
echo "Applying OpenShift SecurityContextConstraints (consul-scc)..."
oc apply -f consul-scc.yaml

# Grant anyuid and privileged permissions to consul service accounts
oc adm policy add-scc-to-user anyuid -z consul-server -n consul || true
oc adm policy add-scc-to-user anyuid -z consul-client -n consul || true
oc adm policy add-scc-to-user anyuid -z consul-connect-injector -n consul || true

# 3. Create Enterprise License Secret (if license file exists)
if [ -f "/Users/chrislovett/hashi/consul_license" ]; then
  echo "Creating Consul Enterprise License secret..."
  oc create secret generic consul-ent-license \
    --from-file=key=/Users/chrislovett/hashi/consul_license \
    -n consul --dry-run=client -o yaml | oc apply -f -
else
  echo "⚠️ Warning: /Users/chrislovett/hashi/consul_license not found. Creating placeholder secret."
  oc create secret generic consul-ent-license \
    --from-literal=key="placeholder" \
    -n consul --dry-run=client -o yaml | oc apply -f -
fi

# 4. Add HashiCorp Helm Repository
echo "Adding HashiCorp Helm repository..."
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# 5. Install Consul via Helm
echo "Installing Consul control plane via Helm..."
helm upgrade --install consul hashicorp/consul \
  --namespace consul \
  --values values.yaml \
  --skip-crds

echo "=========================================================="
echo "Consul installation initiated! Track rollout with:"
echo "oc get pods -n consul -w"
echo "=========================================================="
