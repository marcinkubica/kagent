# Kagent Helm Chart RBAC Customization Analysis

**Date:** June 2025  
**Analysis Scope:** kagent Helm chart RBAC configuration options  
**Finding:** 🔴 CRITICAL - No RBAC customization available

## Executive Summary

The kagent Helm chart provides **NO options for users to customize or restrict RBAC permissions** during installation. Users are forced to accept extremely broad, near-cluster-admin level permissions with no ability to apply the principle of least privilege or meet enterprise security requirements.

## Detailed Analysis

### ❌ Current State: NO RBAC Customization Available

#### 1. No Values.yaml RBAC Configuration

**File Analyzed:** `kagent/helm/kagent/values.yaml`

The `values.yaml` file contains **zero RBAC-related configuration options**:

```yaml
# MISSING: No RBAC configuration options found
# Expected but absent:
# rbac:
#   create: true
#   enabled: true
# serviceAccount:
#   create: true
#   name: ""
```

**What's Missing:**
- No `rbac.create` or `rbac.enabled` flags
- No `serviceAccount.create` options  
- No permission customization settings
- No agent-specific RBAC toggles

#### 2. Hard-coded RBAC Templates

All RBAC resources are **completely hard-coded** with no conditional logic:

**File:** `kagent/helm/kagent/templates/serviceaccount.yaml`
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "kagent.fullname" . }}
  namespace: {{ include "kagent.namespace" . }}
  labels:
    {{- include "kagent.labels" . | nindent 4 }}
# NO conditional creation logic
```

**File:** `kagent/helm/kagent/templates/clusterrole.yaml`
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ include "kagent.fullname" . }}-getter-role
rules:
- apiGroups: [""]
  resources: ["*"]  # FIXED - No customization possible
  verbs: ["get", "list", "watch"]
```

**File:** `kagent/helm/kagent/templates/clusterrolebinding.yaml`
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
# NO conditional logic - always created and bound
```

#### 3. Agent RBAC is Non-configurable

Each agent's RBAC permissions are **fixed and non-negotiable**:

| Agent | RBAC File | Critical Permissions | Customizable |
|-------|-----------|---------------------|--------------|
| Argo Rollouts | `helm/agents/argo-rollouts/templates/rbac.yaml` | Full RBAC modification (`rbac.authorization.k8s.io/*`) | ❌ No |
| Istio | `helm/agents/istio/templates/rbac.yaml` | Cluster-wide admin + admission controllers | ❌ No |
| Cilium Manager | `helm/agents/cilium-manager/templates/rbac.yaml` | Pod exec + wildcard permissions | ❌ No |
| Cilium Debug | `helm/agents/cilium-debug/templates/rbac.yaml` | Pod exec + wildcard permissions | ❌ No |
| Cilium Policy | `helm/agents/cilium-policy/templates/rbac.yaml` | Wildcard Cilium permissions | ❌ No |

## Limited Options Available to Users

### 1. Agent Disabling (Partial Solution)

**Available Configuration:**
```yaml
# values.yaml - Only way to reduce permissions
k8s-agent:
  enabled: true
kgateway-agent:
  enabled: true
istio-agent:
  enabled: false          # Can disable entire agent
promql-agent:
  enabled: true
observability-agent:
  enabled: true
argo-rollouts-agent:
  enabled: false          # Can disable entire agent
helm-agent:
  enabled: true
cilium-policy-agent:
  enabled: false          # Can disable entire agent
cilium-manager-agent:
  enabled: false          # Can disable entire agent
cilium-debug-agent:
  enabled: false          # Can disable entire agent
```

**⚠️ Limitation**: This is all-or-nothing - you can't keep the agent but reduce its permissions.

**Usage Example:**
```bash
# Disable high-risk agents during installation
helm install kagent ./helm/kagent/ \
  --set istio-agent.enabled=false \
  --set argo-rollouts-agent.enabled=false \
  --set cilium-debug-agent.enabled=false \
  --set providers.openAI.apiKey=your-api-key
```

### 2. Manual Post-Installation Modification (Unsupported)

Users could manually edit RBAC after installation:

```bash
# Example: Remove wildcard permissions (NOT RECOMMENDED)
kubectl patch clusterrole kagent-writer-role --type='json' \
  -p='[{"op": "remove", "path": "/rules/1"}]'

# Example: Remove RBAC modification permissions from Argo agent
kubectl patch clusterrole kagent-argo-role --type='json' \
  -p='[{"op": "remove", "path": "/rules/5"}]'
```

**⚠️ Critical Problems:**
- Helm upgrades will overwrite manual changes
- No supported/documented approach
- High risk of breaking functionality
- No way to persist changes

### 3. Fork and Customize (Not Recommended)

Users could fork the Helm chart and modify templates:

**Pros:**
- Full control over RBAC permissions
- Can implement proper least privilege

**Cons:**
- Requires maintaining a separate fork
- Loses official updates and support
- Significant maintenance overhead
- No community support for custom versions

## What's Missing (Industry Standard Features)

Most production-ready Helm charts provide extensive RBAC customization:

### Expected Configuration Options

```yaml
# What kagent SHOULD have but doesn't:
rbac:
  create: true                    # Allow disabling RBAC creation
  restrictToNamespace: false      # Option for namespace-scoped permissions
  customRules: []                 # Allow custom permission rules
  annotations: {}                 # RBAC resource annotations
  
serviceAccount:
  create: true                    # Allow using existing SA
  name: ""                        # Specify existing SA name
  annotations: {}                 # SA annotations
  automountServiceAccountToken: true

# Per-agent RBAC customization
agents:
  argo-rollouts:
    rbac:
      enabled: true
      customRules: []             # Override default rules
      clusterWide: true           # Option for namespace-scoped
  istio:
    rbac:
      enabled: true
      allowRBACModification: false # Disable dangerous permissions
      clusterWide: true
  cilium-manager:
    rbac:
      enabled: true
      allowPodExec: false         # Disable pod execution
      customRules: []
```

### Comparison with Industry Standards

| Feature | Kagent | Nginx Ingress | Cert-Manager | ArgoCD | Istio |
|---------|--------|---------------|--------------|--------|-------|
| `rbac.create` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `serviceAccount.create` | ❌ | ✅ | ✅ | ✅ | ✅ |
| Custom RBAC rules | ❌ | ✅ | ✅ | ✅ | ✅ |
| Namespace-scoped option | ❌ | ✅ | ✅ | ✅ | ✅ |
| Per-component RBAC | ❌ | ✅ | ✅ | ✅ | ✅ |

## Security Implications

This lack of RBAC customization creates several critical security issues:

### 🔴 Critical Security Risks

1. **Forced Cluster-Admin Acceptance**
   - Users MUST accept cluster-admin level permissions
   - No option to apply principle of least privilege
   - Violates security best practices

2. **Compliance Violations**
   - Many organizations cannot approve such broad permissions
   - Fails SOC 2, PCI DSS, and other compliance frameworks
   - Audit findings for excessive permissions

3. **No Gradual Rollout Capability**
   - Cannot test with restricted permissions first
   - No way to validate functionality with minimal permissions
   - All-or-nothing deployment approach

4. **Attack Surface Maximization**
   - Every installation grants maximum possible permissions
   - No way to reduce blast radius
   - Single point of compromise affects entire cluster

### 🟠 High-Risk Scenarios

1. **Enterprise Adoption Blockers**
   - Security teams will reject installation
   - Cannot meet internal security policies
   - Requires security exceptions and approvals

2. **Multi-Tenant Environments**
   - Cannot safely deploy in shared clusters
   - Risk of cross-tenant privilege escalation
   - Violates tenant isolation principles

3. **Regulatory Environments**
   - Healthcare (HIPAA) compliance issues
   - Financial services (PCI DSS) violations
   - Government (FedRAMP) security requirements

## Recommendations

### For Users (Immediate Actions)

#### 1. Pre-Installation Security Review
```bash
# Review security implications before installation
echo "WARNING: kagent requires cluster-admin level permissions"
echo "Review your organization's security policies before proceeding"
```

#### 2. Minimize Agent Deployment
```bash
# Install with minimal agents to reduce attack surface
helm install kagent ./helm/kagent/ \
  --namespace kagent \
  --set providers.openAI.apiKey=your-api-key \
  --set istio-agent.enabled=false \
  --set argo-rollouts-agent.enabled=false \
  --set cilium-debug-agent.enabled=false \
  --set cilium-manager-agent.enabled=false
```

#### 3. Dedicated Cluster Strategy
```bash
# Deploy kagent in dedicated, isolated cluster
kubectl config use-context kagent-dedicated-cluster
helm install kagent ./helm/kagent/
```

#### 4. Enhanced Monitoring
```yaml
# Implement additional monitoring for RBAC changes
apiVersion: v1
kind: ConfigMap
metadata:
  name: rbac-monitoring
data:
  alert-rules.yaml: |
    groups:
    - name: kagent-rbac
      rules:
      - alert: KagentRBACModification
        expr: increase(apiserver_audit_total{verb="create",objectRef_resource="clusterroles"}[5m]) > 0
        annotations:
          summary: "Kagent modified cluster RBAC"
```

### For Production Environments

#### 1. Network Segmentation
```yaml
# Implement network policies to limit blast radius
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kagent-isolation
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: kagent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: kagent
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
```

#### 2. Admission Controller Protection
```yaml
# Use OPA Gatekeeper to prevent privilege escalation
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: preventrbacescalation
spec:
  crd:
    spec:
      names:
        kind: PreventRBACEscalation
      validation:
        properties:
          exemptServiceAccounts:
            type: array
            items:
              type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package preventrbacescalation
        
        violation[{"msg": msg}] {
          input.review.kind.kind == "ClusterRoleBinding"
          input.review.object.roleRef.name == "cluster-admin"
          not exempt_service_account
          msg := "Cluster-admin binding not allowed"
        }
```

#### 3. Regular RBAC Audits
```bash
# Automated RBAC audit script
#!/bin/bash
echo "=== Kagent RBAC Audit ==="
echo "ClusterRoles with wildcard permissions:"
kubectl get clusterroles -o json | jq -r '.items[] | select(.metadata.name | startswith("kagent")) | select(.rules[].resources[] == "*") | .metadata.name'

echo "ServiceAccounts with cluster-admin:"
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.roleRef.name == "cluster-admin") | select(.subjects[]?.name | startswith("kagent")) | .metadata.name'
```

### For the Kagent Development Team

#### 1. Implement Standard RBAC Options
```yaml
# Recommended values.yaml additions
rbac:
  create: true
  restrictToNamespace: false
  customRules: []
  annotations: {}

serviceAccount:
  create: true
  name: ""
  annotations: {}
  automountServiceAccountToken: true

# Per-agent configuration
agents:
  argo-rollouts:
    enabled: true
    rbac:
      enabled: true
      allowRBACModification: false
      customRules: []
  istio:
    enabled: true
    rbac:
      enabled: true
      allowRBACModification: false
      allowAdmissionControllers: false
```

#### 2. Template Refactoring
```yaml
# Example conditional RBAC template
{{- if .Values.rbac.create }}
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: {{ include "kagent.fullname" . }}-role
rules:
{{- if .Values.rbac.customRules }}
{{- toYaml .Values.rbac.customRules | nindent 0 }}
{{- else }}
# Default rules here
{{- end }}
{{- end }}
```

#### 3. Documentation Updates
- Add security considerations section
- Document permission requirements
- Provide enterprise deployment guides
- Include RBAC customization examples

## Alternative Solutions

### 1. Use Existing ServiceAccount
```bash
# Create restricted service account manually
kubectl create serviceaccount kagent-restricted
kubectl create clusterrole kagent-restricted --verb=get,list,watch --resource=pods,services
kubectl create clusterrolebinding kagent-restricted --clusterrole=kagent-restricted --serviceaccount=default:kagent-restricted

# Modify deployment to use it (requires chart modification)
```

### 2. Namespace-Scoped Deployment
```bash
# Deploy with namespace-only permissions (requires chart fork)
# This would require significant template modifications
```

### 3. Proxy-Based Access Control
```yaml
# Use a proxy service to limit API access
apiVersion: v1
kind: Service
metadata:
  name: kubernetes-api-proxy
spec:
  type: ClusterIP
  ports:
  - port: 443
    targetPort: 8443
  selector:
    app: api-proxy
```

## Conclusion

**The kagent Helm chart currently provides NO options for RBAC customization**, forcing users to accept extremely broad, near-cluster-admin level permissions. This represents a significant security gap and barrier to enterprise adoption.

### Key Findings:

1. **❌ Zero RBAC configuration options** in values.yaml
2. **❌ Hard-coded permissions** with no conditional logic
3. **❌ No per-agent RBAC customization** available
4. **❌ No namespace-scoped deployment** option
5. **❌ No compliance-friendly** installation method

### Impact:

- **Blocks enterprise adoption** due to security policy violations
- **Creates compliance issues** for regulated industries
- **Maximizes attack surface** with unnecessary permissions
- **Violates security best practices** and principle of least privilege

### Immediate Actions Required:

1. **Users**: Carefully evaluate security implications before installation
2. **Organizations**: Consider dedicated clusters or alternative solutions
3. **Kagent Team**: Implement standard RBAC customization features
4. **Community**: Advocate for proper RBAC controls in future releases

This analysis demonstrates that kagent's current RBAC implementation is **not suitable for production environments** that require proper security controls and compliance adherence.

---

**Report Generated:** January 2025  
**Analysis Type:** Helm Chart Security Assessment  
**Scope:** kagent Helm chart RBAC configuration options  
**Methodology:** Static analysis of Helm templates and values files  
**Files Analyzed:** 15+ Helm templates and configuration files 
