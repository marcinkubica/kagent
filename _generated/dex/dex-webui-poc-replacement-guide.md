# Dex WebUI POC: In-Place OAuth2-Proxy Replacement Guide

## Overview

This document provides a step-by-step guide to replace oauth2-proxy with Dex for WebUI authentication in POC stage. The approach maintains Dex as a **separate container service** without any code integration, similar to how oauth2-proxy currently works.

**Architecture**: `User → Dex (Auth Proxy) → WebUI`

### Key Principles
- ✅ **No Code Changes**: WebUI remains unchanged
- ✅ **Separate Container**: Dex runs as independent service
- ✅ **Drop-in Replacement**: Same flow as oauth2-proxy
- ✅ **POC Ready**: Simple configuration for testing
- ✅ **Multi-Provider**: GitHub + Google support

---

## Current vs New Architecture

### Current (OAuth2-Proxy)
```
┌─────────┐    ┌──────────────┐    ┌─────────────┐
│  User   │───▶│ OAuth2-Proxy │───▶│  WebUI      │
│         │    │   :8090      │    │   :8080     │
└─────────┘    └──────────────┘    └─────────────┘
```

### New (Dex + oauth2-proxy compatibility)
```
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│  User   │───▶│ Dex + Proxy │───▶│  WebUI      │
│         │    │   :8090     │    │   :8080     │
└─────────┘    └─────────────┘    └─────────────┘
```

**Note**: We'll use oauth2-proxy as a thin client to Dex, maintaining the same interface for WebUI.

---

## Step-by-Step Implementation

### Step 1: Update Helm Values

Replace the existing oauth2-proxy configuration with Dex + oauth2-proxy setup:

```yaml
# helm/kagent/values.yaml

# Remove existing oauth2Proxy section, replace with:
auth:
  enabled: true
  
  # Dex Identity Provider
  dex:
    enabled: true
    image:
      registry: ghcr.io
      repository: dexidp/dex
      tag: "v2.38.0"
      pullPolicy: IfNotPresent
    
    issuer: "http://dex.kagent.svc.cluster.local:5556"
    
    storage:
      type: memory  # For POC, use memory storage
    
    web:
      http: "0.0.0.0:5556"
    
    connectors:
      github:
        enabled: true
        clientId: ""  # Set via secret
        clientSecret: ""  # Set via secret
        org: "your-github-org"  # Replace with your org
      
      google:
        enabled: true
        clientId: ""  # Set via secret
        clientSecret: ""  # Set via secret
        hostedDomain: "your-domain.com"  # Replace with your domain
    
    staticClients:
    - id: kagent-oauth2-proxy
      name: "Kagent OAuth2-Proxy Client"
      secret: "kagent-oauth2-proxy-secret"
      redirectURIs:
      - "http://localhost:8090/oauth2/callback"
      - "http://kagent.local:8090/oauth2/callback"
    
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 200m
        memory: 128Mi
  
  # OAuth2-Proxy as Dex Client
  oauth2Proxy:
    enabled: true
    image:
      registry: quay.io
      repository: oauth2-proxy/oauth2-proxy
      tag: "v7.9.0"
      pullPolicy: IfNotPresent
    
    # Configure as OIDC client to Dex
    provider: "oidc"
    
    oidc:
      issuerUrl: "http://dex.kagent.svc.cluster.local:5556"
    
    clientId: "kagent-oauth2-proxy"
    clientSecret: "kagent-oauth2-proxy-secret"
    cookieSecret: ""  # Generate: python -c 'import secrets; print(secrets.token_urlsafe(32))'
    
    config:
      emailDomains: ["*"]  # Allow any email for POC
      upstreams: ["http://kagent-ui.kagent.svc.cluster.local:8080"]
      
      # Cookie settings
      cookieSecure: false  # Set to true for HTTPS
      cookieHttpOnly: true
      cookieSameSite: "lax"
      cookieExpire: "1h"
      
      # Session settings
      sessionStoreType: "cookie"
      
      # Skip auth for health checks
      skipAuthPaths:
        - "^/ping"
        - "^/health"
        - "^/ready"
      
      extraArgs:
        - "--provider-display-name=Kagent Login"
        - "--skip-provider-button=false"
        - "--pass-basic-auth=false"
        - "--pass-access-token=true"
        - "--pass-user-headers=true"
        - "--set-xauthrequest=true"
        - "--cookie-name=_kagent_oauth"
    
    resources:
      requests:
        cpu: 50m
        memory: 64Mi
      limits:
        cpu: 200m
        memory: 128Mi
    
    secrets:
      external: false  # Use inline secrets for POC
      secretName: "kagent-auth-secrets"
```

### Step 2: Create Helm Templates

#### 2.1 Dex Deployment Template

Create `helm/kagent/templates/auth-dex-deployment.yaml`:

```yaml
{{- if and .Values.auth.enabled .Values.auth.dex.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "kagent.fullname" . }}-dex
  labels:
    {{- include "kagent.labels" . | nindent 4 }}
    app.kubernetes.io/component: dex
spec:
  replicas: 1
  selector:
    matchLabels:
      {{- include "kagent.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: dex
  template:
    metadata:
      labels:
        {{- include "kagent.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: dex
    spec:
      containers:
      - name: dex
        image: "{{ .Values.auth.dex.image.registry }}/{{ .Values.auth.dex.image.repository }}:{{ .Values.auth.dex.image.tag }}"
        imagePullPolicy: {{ .Values.auth.dex.image.pullPolicy }}
        command: ["/usr/local/bin/dex", "serve", "/etc/dex/cfg/config.yaml"]
        ports:
        - name: http
          containerPort: 5556
          protocol: TCP
        volumeMounts:
        - name: config
          mountPath: /etc/dex/cfg
        env:
        {{- if .Values.auth.dex.connectors.github.enabled }}
        - name: GITHUB_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: {{ .Values.auth.oauth2Proxy.secrets.secretName }}
              key: github-client-id
        - name: GITHUB_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: {{ .Values.auth.oauth2Proxy.secrets.secretName }}
              key: github-client-secret
        {{- end }}
        {{- if .Values.auth.dex.connectors.google.enabled }}
        - name: GOOGLE_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: {{ .Values.auth.oauth2Proxy.secrets.secretName }}
              key: google-client-id
        - name: GOOGLE_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: {{ .Values.auth.oauth2Proxy.secrets.secretName }}
              key: google-client-secret
        {{- end }}
        resources:
          {{- toYaml .Values.auth.dex.resources | nindent 10 }}
        livenessProbe:
          httpGet:
            path: /healthz
            port: 5556
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /healthz
            port: 5556
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: {{ include "kagent.fullname" . }}-dex-config
{{- end }}
```

#### 2.2 Dex Service Template

Create `helm/kagent/templates/auth-dex-service.yaml`:

```yaml
{{- if and .Values.auth.enabled .Values.auth.dex.enabled }}
apiVersion: v1
kind: Service
metadata:
  name: {{ include "kagent.fullname" . }}-dex
  labels:
    {{- include "kagent.labels" . | nindent 4 }}
    app.kubernetes.io/component: dex
spec:
  type: ClusterIP
  ports:
  - port: 5556
    targetPort: http
    protocol: TCP
    name: http
  selector:
    {{- include "kagent.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/component: dex
{{- end }}
```

#### 2.3 Dex ConfigMap Template

Create `helm/kagent/templates/auth-dex-configmap.yaml`:

```yaml
{{- if and .Values.auth.enabled .Values.auth.dex.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "kagent.fullname" . }}-dex-config
  labels:
    {{- include "kagent.labels" . | nindent 4 }}
    app.kubernetes.io/component: dex
data:
  config.yaml: |
    issuer: {{ .Values.auth.dex.issuer }}
    
    storage:
      type: {{ .Values.auth.dex.storage.type }}
    
    web:
      http: {{ .Values.auth.dex.web.http }}
    
    connectors:
    {{- if .Values.auth.dex.connectors.github.enabled }}
    - type: github
      id: github
      name: GitHub
      config:
        clientID: $GITHUB_CLIENT_ID
        clientSecret: $GITHUB_CLIENT_SECRET
        redirectURI: {{ .Values.auth.dex.issuer }}/callback
        {{- if .Values.auth.dex.connectors.github.org }}
        org: {{ .Values.auth.dex.connectors.github.org }}
        {{- end }}
    {{- end }}
    
    {{- if .Values.auth.dex.connectors.google.enabled }}
    - type: google
      id: google
      name: Google
      config:
        clientID: $GOOGLE_CLIENT_ID
        clientSecret: $GOOGLE_CLIENT_SECRET
        redirectURI: {{ .Values.auth.dex.issuer }}/callback
        {{- if .Values.auth.dex.connectors.google.hostedDomain }}
        hostedDomains:
        - {{ .Values.auth.dex.connectors.google.hostedDomain }}
        {{- end }}
    {{- end }}
    
    oauth2:
      skipApprovalScreen: true
    
    staticClients:
    {{- range .Values.auth.dex.staticClients }}
    - id: {{ .id }}
      redirectURIs:
      {{- range .redirectURIs }}
      - {{ . | quote }}
      {{- end }}
      name: {{ .name }}
      secret: {{ .secret }}
    {{- end }}
    
    enablePasswordDB: false
{{- end }}
```

#### 2.4 Update OAuth2-Proxy Deployment

Modify `helm/kagent/templates/deployment.yaml` to update the oauth2-proxy section:

```yaml
# In the existing deployment.yaml, update the oauth2-proxy container section:
{{- if and .Values.auth.enabled .Values.auth.oauth2Proxy.enabled }}
- name: oauth2-proxy
  image: "{{ .Values.auth.oauth2Proxy.image.registry }}/{{ .Values.auth.oauth2Proxy.image.repository }}:{{ .Values.auth.oauth2Proxy.image.tag }}"
  imagePullPolicy: {{ .Values.auth.oauth2Proxy.image.pullPolicy }}
  ports:
  - name: http
    containerPort: 8090
    protocol: TCP
  args:
  - --http-address=0.0.0.0:8090
  - --provider={{ .Values.auth.oauth2Proxy.provider }}
  {{- if .Values.auth.oauth2Proxy.oidc.issuerUrl }}
  - --oidc-issuer-url={{ .Values.auth.oauth2Proxy.oidc.issuerUrl }}
  {{- end }}
  - --upstream={{ index .Values.auth.oauth2Proxy.config.upstreams 0 }}
  {{- range .Values.auth.oauth2Proxy.config.emailDomains }}
  - --email-domain={{ . }}
  {{- end }}
  - --cookie-secure={{ .Values.auth.oauth2Proxy.config.cookieSecure }}
  - --cookie-httponly={{ .Values.auth.oauth2Proxy.config.cookieHttpOnly }}
  - --cookie-samesite={{ .Values.auth.oauth2Proxy.config.cookieSameSite }}
  - --cookie-expire={{ .Values.auth.oauth2Proxy.config.cookieExpire }}
  - --cookie-name={{ .Values.auth.oauth2Proxy.config.extraArgs | join "=" | regexFind "_kagent_oauth" | default "_oauth2_proxy" }}
  - --session-store-type={{ .Values.auth.oauth2Proxy.config.sessionStoreType }}
  {{- range .Values.auth.oauth2Proxy.config.skipAuthPaths }}
  - --skip-auth-regex={{ . }}
  {{- end }}
  {{- range .Values.auth.oauth2Proxy.config.extraArgs }}
  - {{ . }}
  {{- end }}
  env:
  - name: OAUTH2_PROXY_CLIENT_ID
    value: {{ .Values.auth.oauth2Proxy.clientId | quote }}
  - name: OAUTH2_PROXY_CLIENT_SECRET
    value: {{ .Values.auth.oauth2Proxy.clientSecret | quote }}
  - name: OAUTH2_PROXY_COOKIE_SECRET
    value: {{ .Values.auth.oauth2Proxy.cookieSecret | quote }}
  resources:
    {{- toYaml .Values.auth.oauth2Proxy.resources | nindent 12 }}
  livenessProbe:
    httpGet:
      path: /ping
      port: 8090
    initialDelaySeconds: 30
    periodSeconds: 30
  readinessProbe:
    httpGet:
      path: /ping
      port: 8090
    initialDelaySeconds: 10
    periodSeconds: 10
{{- end }}
```

#### 2.5 Create Secrets Template

Create `helm/kagent/templates/auth-secrets.yaml`:

```yaml
{{- if and .Values.auth.enabled (not .Values.auth.oauth2Proxy.secrets.external) }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ .Values.auth.oauth2Proxy.secrets.secretName }}
  labels:
    {{- include "kagent.labels" . | nindent 4 }}
type: Opaque
data:
  {{- if .Values.auth.dex.connectors.github.enabled }}
  github-client-id: {{ .Values.auth.dex.connectors.github.clientId | b64enc }}
  github-client-secret: {{ .Values.auth.dex.connectors.github.clientSecret | b64enc }}
  {{- end }}
  {{- if .Values.auth.dex.connectors.google.enabled }}
  google-client-id: {{ .Values.auth.dex.connectors.google.clientId | b64enc }}
  google-client-secret: {{ .Values.auth.dex.connectors.google.clientSecret | b64enc }}
  {{- end }}
{{- end }}
```

### Step 3: Create POC Values File

Create `helm/kagent/examples/dex-webui-poc-values.yaml`:

```yaml
# POC Configuration for Dex + WebUI
# Copy this file and customize for your environment

auth:
  enabled: true
  
  dex:
    enabled: true
    issuer: "http://dex.kagent.svc.cluster.local:5556"  # Internal cluster URL
    
    connectors:
      github:
        enabled: true
        clientId: "your-github-oauth-app-client-id"
        clientSecret: "your-github-oauth-app-client-secret"
        org: "your-github-org"  # Replace with your GitHub org
      
      google:
        enabled: false  # Enable if you want Google auth
        clientId: "your-google-oauth-client-id"
        clientSecret: "your-google-oauth-client-secret"
        hostedDomain: "your-company.com"
  
  oauth2Proxy:
    enabled: true
    clientId: "kagent-oauth2-proxy"
    clientSecret: "kagent-oauth2-proxy-secret"
    cookieSecret: "REPLACE-WITH-GENERATED-SECRET"  # Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
    
    config:
      upstreams: ["http://kagent-ui.kagent.svc.cluster.local:8080"]

# Disable existing oauth2Proxy if it exists
oauth2Proxy:
  enabled: false

# UI Configuration (unchanged)
ui:
  enabled: true
  image:
    registry: cr.kagent.dev
    repository: kagent-dev/kagent/ui
    tag: ""
    pullPolicy: IfNotPresent
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 1000m
      memory: 1Gi

# Service configuration
service:
  type: ClusterIP
  ports:
    ui:
      port: 80
      targetPort: 8080
    oauth2Proxy:  # This will now serve Dex + OAuth2-Proxy
      port: 8090
      targetPort: 8090
```

### Step 4: Setup Instructions

#### 4.1 Prerequisites

1. **GitHub OAuth App** (if using GitHub):
   ```bash
   # Go to: https://github.com/settings/applications/new
   # Application name: Kagent POC
   # Homepage URL: http://localhost:8090
   # Authorization callback URL: http://dex.kagent.svc.cluster.local:5556/callback
   ```

2. **Google OAuth Client** (if using Google):
   ```bash
   # Go to: https://console.developers.google.com/
   # Create OAuth 2.0 Client ID
   # Authorized redirect URIs: http://dex.kagent.svc.cluster.local:5556/callback
   ```

3. **Generate Cookie Secret**:
   ```bash
   python -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

#### 4.2 Deployment Steps

1. **Update Values File**:
   ```bash
   # Copy the POC values file
   cp helm/kagent/examples/dex-webui-poc-values.yaml my-poc-values.yaml
   
   # Edit with your OAuth credentials
   vim my-poc-values.yaml
   ```

2. **Deploy to Kubernetes**:
   ```bash
   # Deploy with Dex authentication
   helm upgrade --install kagent ./helm/kagent -f my-poc-values.yaml
   
   # Check deployment status
   kubectl get pods -l app.kubernetes.io/name=kagent
   ```

3. **Verify Services**:
   ```bash
   # Check Dex is running
   kubectl get pod -l app.kubernetes.io/component=dex
   kubectl logs -l app.kubernetes.io/component=dex
   
   # Check OAuth2-Proxy is running
   kubectl get pod -l app.kubernetes.io/component=oauth2-proxy
   kubectl logs -l app.kubernetes.io/component=oauth2-proxy
   ```

4. **Port Forward for Testing**:
   ```bash
   # Forward the OAuth2-Proxy port (this is your entry point)
   kubectl port-forward service/kagent-oauth2-proxy 8090:8090
   
   # Forward Dex port (for debugging)
   kubectl port-forward service/kagent-dex 5556:5556
   ```

5. **Test Authentication**:
   ```bash
   # Open browser to:
   open http://localhost:8090
   
   # You should see Dex login page with provider options
   # After login, you'll be redirected to the WebUI
   ```

### Step 5: Troubleshooting

#### 5.1 Common Issues

**Issue**: Dex not starting
```bash
# Check logs
kubectl logs -l app.kubernetes.io/component=dex

# Common fixes:
# 1. Check OAuth client credentials in secrets
# 2. Verify redirect URIs match
# 3. Check issuer URL is accessible
```

**Issue**: OAuth2-Proxy connection error
```bash
# Check logs
kubectl logs -l app.kubernetes.io/component=oauth2-proxy

# Common fixes:
# 1. Verify Dex service is accessible: http://dex.kagent.svc.cluster.local:5556
# 2. Check OIDC discovery: curl http://dex.kagent.svc.cluster.local:5556/.well-known/openid_configuration
# 3. Verify client ID/secret match Dex static client
```

**Issue**: WebUI not accessible
```bash
# Check upstream configuration
kubectl describe configmap kagent-dex-config

# Verify UI service is running
kubectl get service kagent-ui
kubectl get pod -l app.kubernetes.io/component=ui
```

#### 5.2 Debug Commands

```bash
# Test Dex health
kubectl exec -it deployment/kagent-dex -- curl http://localhost:5556/healthz

# Test OIDC discovery
kubectl exec -it deployment/kagent-dex -- curl http://localhost:5556/.well-known/openid_configuration

# Test OAuth2-Proxy health
kubectl exec -it deployment/kagent -- curl http://localhost:8090/ping

# Check service connectivity
kubectl exec -it deployment/kagent -- curl http://dex.kagent.svc.cluster.local:5556/healthz
kubectl exec -it deployment/kagent -- curl http://kagent-ui.kagent.svc.cluster.local:8080
```

### Step 6: Production Considerations

#### 6.1 Security Hardening

```yaml
# For production, update values:
auth:
  dex:
    issuer: "https://dex.yourdomain.com"  # Use HTTPS
    storage:
      type: kubernetes  # Use persistent storage
  
  oauth2Proxy:
    config:
      cookieSecure: true  # Require HTTPS
      cookieSameSite: "strict"  # Stricter cookie policy
    
    secrets:
      external: true  # Use external secret management
```

#### 6.2 Monitoring Setup

```yaml
# Add monitoring annotations
auth:
  dex:
    podAnnotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "5558"
      prometheus.io/path: "/metrics"
  
  oauth2Proxy:
    podAnnotations:
      prometheus.io/scrape: "true"
      prometheus.io/port: "8090"
      prometheus.io/path: "/metrics"
```

---

## Testing Checklist

- [ ] Dex pod starts successfully
- [ ] OAuth2-Proxy pod starts successfully
- [ ] Can access http://localhost:8090
- [ ] Dex login page appears with provider options
- [ ] GitHub authentication works (if enabled)
- [ ] Google authentication works (if enabled)
- [ ] After login, redirected to WebUI
- [ ] WebUI loads correctly
- [ ] Logout works properly
- [ ] Session persists across browser refresh

---

## Rollback Plan

If issues occur, rollback to oauth2-proxy:

```bash
# Quick rollback
helm upgrade kagent ./helm/kagent --set auth.enabled=false --set oauth2Proxy.enabled=true

# Or restore from backup
helm rollback kagent [REVISION]
```

---

## Next Steps

Once POC is successful:

1. **Add HTTPS/TLS** for production security
2. **Configure persistent storage** for Dex (PostgreSQL/Kubernetes CRDs)
3. **Add monitoring and alerting**
4. **Implement proper secret management**
5. **Add additional identity providers** (LDAP, SAML)
6. **Scale to other services** (API, A2A)

This setup provides a clean separation of concerns while maintaining the same user experience as oauth2-proxy, making it a perfect POC for evaluating Dex's capabilities. 
