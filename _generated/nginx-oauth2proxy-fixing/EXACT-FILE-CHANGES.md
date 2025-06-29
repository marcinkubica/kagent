# Exact File Changes Required

**Generated:** 2025-01-27  
**Priority:** 🚨 **CRITICAL**  

## 📋 **File Changes Summary**

| Action | File | Description |
|--------|------|-------------|
| DELETE | `helm/kagent/templates/nginx-configmap.yaml` | Remove broken nginx ConfigMap |
| MODIFY | `helm/kagent/templates/deployment.yaml` | Remove volume mounts, update OAuth2 proxy |
| MODIFY | `helm/kagent/templates/service.yaml` | Add conditional port routing |
| MODIFY | `helm/kagent/values.yaml` | Update OAuth2 proxy configuration |

---

## 🗑️ **File Deletion**

### **DELETE: `helm/kagent/templates/nginx-configmap.yaml`**

**Action:** Complete file removal

```bash
rm helm/kagent/templates/nginx-configmap.yaml
```

**Rationale:** This file overrides the working built-in nginx configuration and breaks 80% of functionality.

---

## ✏️ **File Modifications**

### **1. MODIFY: `helm/kagent/templates/deployment.yaml`**

#### **Change 1.1: Remove Volume Definition**

**Location:** Lines 27-29  
**Action:** DELETE these lines

```yaml
# DELETE THESE LINES:
      volumes:
        - name: nginx-config
          configMap:
            name: {{ include "kagent.fullname" . }}-nginx-config
```

#### **Change 1.2: Remove Volume Mount from UI Container**

**Location:** Lines 112-115  
**Action:** DELETE these lines

```yaml
# DELETE THESE LINES:
          volumeMounts:
            - name: nginx-config
              mountPath: /etc/nginx/nginx.conf
              subPath: nginx.conf
```

#### **Change 1.3: Update OAuth2 Proxy Container**

**Location:** Around line 200-220  
**Action:** REPLACE oauth2-proxy args section

**BEFORE:**
```yaml
          args:
            - --http-address=0.0.0.0:4180
            - --metrics-address=0.0.0.0:44180
            {{- range .Values.oauth2Proxy.config.upstreams }}
            - --upstream={{ . }}
            {{- end }}
            - --provider={{ .Values.oauth2Proxy.provider }}
```

**AFTER:**
```yaml
          args:
            - --http-address=0.0.0.0:8090
            - --metrics-address=0.0.0.0:44180
            - --upstream=http://127.0.0.1:8080
            - --provider={{ .Values.oauth2Proxy.provider }}
```

#### **Change 1.4: Update OAuth2 Proxy Ports**

**Location:** Around line 280  
**Action:** REPLACE containerPort

**BEFORE:**
```yaml
          ports:
            - name: http
              containerPort: 4180
              protocol: TCP
```

**AFTER:**
```yaml
          ports:
            - name: http
              containerPort: 8090
              protocol: TCP
```

### **2. MODIFY: `helm/kagent/templates/service.yaml`**

#### **Change 2.1: Add Conditional Port Routing**

**Location:** Lines 10-14  
**Action:** REPLACE the UI port configuration

**BEFORE:**
```yaml
  ports:
    - port: {{ .Values.service.ports.ui.port }}
      targetPort: {{ .Values.service.ports.ui.targetPort }}
      protocol: TCP
      name: ui
```

**AFTER:**
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

### **3. MODIFY: `helm/kagent/values.yaml`**

#### **Change 3.1: Update OAuth2 Proxy Service Port**

**Location:** Around line 140  
**Action:** ADD oauth2Proxy port configuration

**BEFORE:**
```yaml
service:
  type: ClusterIP
  ports:
    ui:
      port: 80
      targetPort: 8080
    app:
      port: 8081
      targetPort: 8081
    controller:
      port: 8083
      targetPort: 8083
    tools:
      port: 8084
      targetPort: 8084
    querydoc:
      port: 8085
      targetPort: 8085
    oauth2Proxy:
      port: 4180
      targetPort: 4180
```

**AFTER:**
```yaml
service:
  type: ClusterIP
  ports:
    ui:
      port: 80
      targetPort: 8080
    app:
      port: 8081
      targetPort: 8081
    controller:
      port: 8083
      targetPort: 8083
    tools:
      port: 8084
      targetPort: 8084
    querydoc:
      port: 8085
      targetPort: 8085
    oauth2Proxy:
      port: 8090
      targetPort: 8090
```

#### **Change 3.2: Simplify OAuth2 Proxy Configuration**

**Location:** Around line 240  
**Action:** REPLACE upstreams configuration

**BEFORE:**
```yaml
  config:
    # Email domains that are allowed (empty means any)
    emailDomains: []
    # Example: ["example.com", "company.org"]
    
    # Upstream configuration - will be set automatically to point to nginx
    upstreams: ["http://127.0.0.1:8080"]
```

**AFTER:**
```yaml
  config:
    # Email domains that are allowed (empty means any)
    emailDomains: []
    # Example: ["example.com", "company.org"]
    
    # Standalone configuration - points to nginx only
    upstreams: ["http://127.0.0.1:8080"]
```

---

## 🔍 **Verification After Changes**

### **Expected File Structure After Changes:**

```bash
# These files should exist and be modified:
helm/kagent/templates/deployment.yaml    # Modified
helm/kagent/templates/service.yaml       # Modified  
helm/kagent/values.yaml                  # Modified

# This file should be DELETED:
helm/kagent/templates/nginx-configmap.yaml  # REMOVED

# This file should be UNCHANGED:
ui/conf/nginx.conf                       # Preserved (built-in config)
```

### **Template Rendering Test:**

```bash
# Should render without errors
helm template test ./helm/kagent

# Should include OAuth2 proxy when enabled
helm template test ./helm/kagent --set oauth2Proxy.enabled=true
```

### **Container Count Verification:**

```bash
# OAuth2 disabled: 5 containers (controller, app, ui, tools, querydoc)
helm template test ./helm/kagent | grep "name:" | grep -E "(controller|app|ui|tools|querydoc)" | wc -l
# Expected: 5

# OAuth2 enabled: 6 containers (+ oauth2-proxy)
helm template test ./helm/kagent --set oauth2Proxy.enabled=true | grep "name:" | grep -E "(controller|app|ui|tools|querydoc|oauth2-proxy)" | wc -l
# Expected: 6
```

### **Port Configuration Verification:**

```bash
# OAuth2 disabled: Service targets port 8080
helm template test ./helm/kagent | grep -A2 "name: ui" | grep targetPort
# Expected: targetPort: 8080

# OAuth2 enabled: Service targets port 8090
helm template test ./helm/kagent --set oauth2Proxy.enabled=true | grep -A2 "name: ui" | grep targetPort
# Expected: targetPort: 8090
```

---

## 🎯 **Critical Success Indicators**

After implementing these changes:

1. **✅ No nginx ConfigMap**: `kubectl get configmap | grep nginx` returns nothing
2. **✅ Built-in nginx config**: Container uses `/ui/conf/nginx.conf` (77 lines)
3. **✅ OAuth2 proxy on 8090**: Container listens on port 8090, not 4180
4. **✅ Service routing**: Conditionally routes to 8090 (OAuth2) or 8080 (direct)
5. **✅ Upstream configuration**: OAuth2 proxy points to `http://127.0.0.1:8080`

## ⚠️ **Common Mistakes to Avoid**

1. **Don't modify `ui/conf/nginx.conf`** - This is the working baseline
2. **Don't keep nginx-configmap.yaml** - It must be completely deleted
3. **Don't use port 4180** - OAuth2 proxy should use 8090
4. **Don't point to individual services** - OAuth2 proxy should point to nginx only
5. **Don't forget service conditional** - Service must route based on OAuth2 enabled/disabled

---

## 🔧 **Implementation Commands**

```bash
# Step 1: Remove breaking ConfigMap
rm helm/kagent/templates/nginx-configmap.yaml

# Step 2: Apply file modifications
# (Use the exact changes documented above)

# Step 3: Verify changes
helm template test ./helm/kagent --debug
helm template test ./helm/kagent --set oauth2Proxy.enabled=true --debug

# Step 4: Test deployment
helm install kagent ./helm/kagent
kubectl wait --for=condition=available --timeout=300s deployment/kagent

# Step 5: Functional verification
kubectl port-forward svc/kagent 8080:80 &
curl http://localhost:8080/api/version
```

This completes all the exact file changes needed to fix the oauth2proxy branch and implement a clean, working OAuth2 authentication solution. 
