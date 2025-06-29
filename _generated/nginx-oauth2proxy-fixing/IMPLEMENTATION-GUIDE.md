# OAuth2 Proxy Fix - Implementation Guide

**Generated:** 2025-01-27  
**Priority:** 🚨 **CRITICAL**  
**Estimated Time:** 3.5 hours  

## 🎯 **Objective**

Transform the broken oauth2proxy branch into a clean, working OAuth2 authentication solution by:
1. Removing all breaking changes
2. Implementing standalone OAuth2 proxy architecture
3. Preserving full functionality

## 📋 **Pre-Implementation Checklist**

- [ ] Backup current branch: `git checkout -b oauth2proxy-backup`
- [ ] Confirm main branch baseline: Test `kagent-main` functionality
- [ ] Prepare test environment: Kubernetes cluster ready
- [ ] OAuth credentials ready: For testing OAuth2 functionality

## 🚀 **Implementation Steps**

### **Step 1: Remove Breaking Changes (30 minutes)**

#### **1.1 Delete Nginx ConfigMap**
**File to DELETE:** `helm/kagent/templates/nginx-configmap.yaml`

```bash
# Complete removal - this file is the root cause of all issues
rm helm/kagent/templates/nginx-configmap.yaml
```

**Rationale:** This ConfigMap overrides the working built-in nginx configuration and removes 80% of functionality.

#### **1.2 Revert Deployment Template**
**File:** `helm/kagent/templates/deployment.yaml`

**REMOVE Lines 27-29:**
```yaml
      volumes:
        - name: nginx-config
          configMap:
            name: {{ include "kagent.fullname" . }}-nginx-config
```

**REMOVE Lines 112-115:**
```yaml
          volumeMounts:
            - name: nginx-config
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
```

### **Step 2: Implement Standalone OAuth2 Proxy (2 hours)**

#### **2.1 Update OAuth2 Proxy Container**
**File:** `helm/kagent/templates/deployment.yaml`

**CHANGE OAuth2 Proxy Container (starting around line 190):**

**FROM:**
```yaml
        - name: oauth2-proxy
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.oauth2Proxy.image.registry }}/{{ .Values.oauth2Proxy.image.repository }}:{{ .Values.oauth2Proxy.image.tag }}"
          imagePullPolicy: {{ .Values.oauth2Proxy.image.pullPolicy }}
          args:
            - --http-address=0.0.0.0:4180
            - --metrics-address=0.0.0.0:44180
            {{- range .Values.oauth2Proxy.config.upstreams }}
            - --upstream={{ . }}
            {{- end }}
```

**TO:**
```yaml
        - name: oauth2-proxy
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.oauth2Proxy.image.registry }}/{{ .Values.oauth2Proxy.image.repository }}:{{ .Values.oauth2Proxy.image.tag }}"
          imagePullPolicy: {{ .Values.oauth2Proxy.image.pullPolicy }}
          args:
            - --http-address=0.0.0.0:8090
            - --metrics-address=0.0.0.0:44180
            - --upstream=http://127.0.0.1:8080
```

**CHANGE Ports Section:**

**FROM:**
```yaml
          ports:
            - name: http
              containerPort: 4180
              protocol: TCP
```

**TO:**
```yaml
          ports:
            - name: http
              containerPort: 8090
              protocol: TCP
```

#### **2.2 Update Service Configuration**
**File:** `helm/kagent/templates/service.yaml`

**REPLACE the entire ports section:**

**FROM:**
```yaml
  ports:
    - port: {{ .Values.service.ports.ui.port }}
      targetPort: {{ .Values.service.ports.ui.targetPort }}
      protocol: TCP
      name: ui
```

**TO:**
```yaml
  ports:
    {{- if .Values.oauth2Proxy.enabled }}
    - port: {{ .Values.service.ports.ui.port }}
      targetPort: 8090
      protocol: TCP
      name: ui
    {{- else }}
    - port: {{ .Values.service.ports.ui.port }}
      targetPort: {{ .Values.service.ports.ui.targetPort }}
      protocol: TCP
      name: ui
    {{- end }}
```

#### **2.3 Update Values Configuration**
**File:** `helm/kagent/values.yaml`

**CHANGE the oauth2Proxy.config.upstreams:**

**FROM:**
```yaml
    # Upstream configuration - will be set automatically to point to nginx
    upstreams: ["http://127.0.0.1:8080"]
```

**TO:**
```yaml
    # Standalone configuration - points to nginx only
    upstreams: ["http://127.0.0.1:8080"]
```

**ADD service port configuration:**
```yaml
service:
  type: ClusterIP
  ports:
    ui:
      port: 80
      targetPort: 8080
    # ... existing ports ...
    oauth2Proxy:
      port: 8090
      targetPort: 8090
```

### **Step 3: Testing and Validation (1 hour)**

#### **3.1 Template Validation**
```bash
# Test template rendering without OAuth2
helm template test-release ./helm/kagent

# Test template rendering with OAuth2 enabled
helm template test-release ./helm/kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.clientId=test-client-id \
  --set oauth2Proxy.clientSecret=test-client-secret \
  --set oauth2Proxy.cookieSecret=test-cookie-secret
```

#### **3.2 Functional Testing**

**Test Scenario 1: OAuth2 Disabled (Default)**
```bash
# Deploy without OAuth2
helm install kagent ./helm/kagent

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/kagent

# Test functionality
kubectl port-forward svc/kagent 8080:80 &
curl -s http://localhost:8080 | head -5  # Should return HTML
curl -s http://localhost:8080/api/version  # Should return API response

# Clean up
pkill -f "port-forward"
helm uninstall kagent
```

**Test Scenario 2: OAuth2 Enabled**
```bash
# Deploy with OAuth2 (use real credentials for full testing)
helm install kagent ./helm/kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.clientId=your-github-client-id \
  --set oauth2Proxy.clientSecret=your-github-client-secret \
  --set oauth2Proxy.cookieSecret=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment/kagent

# Test OAuth2 flow
kubectl port-forward svc/kagent 8090:80 &
curl -v http://localhost:8090  # Should redirect to GitHub OAuth

# Clean up
pkill -f "port-forward"
helm uninstall kagent
```

#### **3.3 Validation Checklist**

**✅ OAuth2 Disabled Tests:**
- [ ] Helm template renders without errors
- [ ] Deployment starts successfully
- [ ] UI loads on port 8080
- [ ] API endpoints respond (`/api/version`)
- [ ] WebSocket connections work
- [ ] Logs show nginx access/error logs

**✅ OAuth2 Enabled Tests:**
- [ ] Helm template renders with OAuth2 container
- [ ] Deployment starts with 6 containers (including oauth2-proxy)
- [ ] Service exposes port 80 → 8090
- [ ] OAuth2 proxy redirects to provider
- [ ] After authentication, full functionality available
- [ ] API endpoints work through OAuth2 proxy

## 🔧 **Troubleshooting Guide**

### **Common Issues and Solutions**

#### **Issue 1: Template Rendering Fails**
```bash
# Check for YAML syntax errors
helm template test ./helm/kagent --debug

# Check specific template
helm template test ./helm/kagent --show-only templates/deployment.yaml
```

#### **Issue 2: OAuth2 Container Won't Start**
```bash
# Check container logs
kubectl logs deployment/kagent -c oauth2-proxy

# Check OAuth2 proxy configuration
kubectl exec deployment/kagent -c oauth2-proxy -- cat /proc/1/cmdline
```

#### **Issue 3: Service Routing Issues**
```bash
# Check service configuration
kubectl get svc kagent -o yaml

# Check endpoint mapping
kubectl get endpoints kagent
```

#### **Issue 4: Nginx Configuration**
```bash
# Verify nginx is using built-in config (not ConfigMap)
kubectl exec deployment/kagent -c ui -- cat /etc/nginx/nginx.conf

# Should match kagent-main/ui/conf/nginx.conf exactly
```

## 📊 **Verification Commands**

### **Configuration Verification**
```bash
# Verify no nginx ConfigMap exists
kubectl get configmap | grep nginx  # Should return nothing

# Verify built-in nginx config is used
kubectl exec deployment/kagent -c ui -- wc -l /etc/nginx/nginx.conf
# Should return 77 lines (same as main branch)

# Verify OAuth2 proxy upstream
kubectl exec deployment/kagent -c oauth2-proxy -- ps aux | grep upstream
# Should show --upstream=http://127.0.0.1:8080
```

### **Functionality Verification**
```bash
# Test API endpoints
kubectl port-forward svc/kagent 8080:80 &
curl http://localhost:8080/api/version
curl http://localhost:8080/api/health

# Test WebSocket (if available)
# Use browser developer tools to test WebSocket connections

# Test OAuth2 flow (if enabled)
kubectl port-forward svc/kagent 8090:80 &
curl -v http://localhost:8090  # Should show OAuth redirect
```

## 🎯 **Success Criteria**

### **Phase 1 Success (Breaking Changes Removed)**
- [ ] `nginx-configmap.yaml` file deleted
- [ ] Volume mounts removed from deployment
- [ ] Helm templates render without errors
- [ ] System works like main branch (OAuth2 disabled)

### **Phase 2 Success (OAuth2 Implementation)**
- [ ] OAuth2 proxy runs on port 8090
- [ ] Service routes correctly based on OAuth2 enabled/disabled
- [ ] OAuth2 proxy points to nginx (port 8080)
- [ ] All original functionality preserved

### **Phase 3 Success (Testing Complete)**
- [ ] OAuth2 disabled: Works identically to main branch
- [ ] OAuth2 enabled: Authentication works with full functionality
- [ ] No regression in API or WebSocket functionality
- [ ] Clean, maintainable configuration

## 🚨 **Critical Reminders**

1. **DO NOT modify the built-in nginx configuration** (`ui/conf/nginx.conf`)
2. **COMPLETELY remove** the nginx ConfigMap - don't modify it
3. **Test both scenarios**: OAuth2 enabled and disabled
4. **Verify port configuration**: 8090 for OAuth2, 8080 for nginx
5. **Confirm upstream configuration**: OAuth2 proxy → nginx → services

## 🔄 **Rollback Plan**

If implementation fails:

1. **Immediate Rollback**: `git checkout oauth2proxy-backup`
2. **Quick Fix**: Set `oauth2Proxy.enabled: false` in values
3. **Full Revert**: Restore from main branch baseline

## 📝 **Post-Implementation**

After successful implementation:

1. **Update Documentation**: Record OAuth2 configuration steps
2. **Create Examples**: Sample values files for different providers
3. **Test Suite**: Add automated tests for OAuth2 scenarios
4. **Monitoring**: Set up alerts for OAuth2 proxy health

---

## ✅ **Final Validation**

The implementation is successful when:

- **OAuth2 Disabled**: `curl http://localhost:8080/api/version` returns API response
- **OAuth2 Enabled**: `curl http://localhost:8090` redirects to OAuth provider
- **Full Functionality**: All features work through both access methods
- **Clean Architecture**: Clear separation between auth and application logic 
