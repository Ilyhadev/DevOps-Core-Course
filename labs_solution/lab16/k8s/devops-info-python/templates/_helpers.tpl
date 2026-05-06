{{/* Expand the chart name. */}}
{{- define "devops-info-python.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Build a full resource name. */}}
{{- define "devops-info-python.fullname" -}}
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

{{/* Chart label value. */}}
{{- define "devops-info-python.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels for all resources. */}}
{{- define "devops-info-python.labels" -}}
helm.sh/chart: {{ include "devops-info-python.chart" . }}
{{ include "devops-info-python.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Labels used by selectors. */}}
{{- define "devops-info-python.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-python.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
