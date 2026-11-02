{{/*
Expand the name of the chart.
*/}}
{{- define "agent-mesh-authz.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agent-mesh-authz.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "agent-mesh-authz.labels" -}}
helm.sh/chart: {{ include "agent-mesh-authz.name" . }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "agent-mesh-authz.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agent-mesh-authz.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agent-mesh-authz.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
