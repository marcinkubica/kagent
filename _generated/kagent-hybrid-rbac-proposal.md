# Kagent Hybrid RBAC Security Proposal

**Date:** June 30, 2025  
**Purpose:** Hybrid RBAC approach using both ClusterRole and namespace-scoped Roles  
**Current Risk Level:** 🔴 **CRITICAL**  
**Proposed Risk Level:** 🟡 **MEDIUM** (with option for 🟢 **LOW**)

## Executive Summary

Kagent supports **configurable namespace watching** via `controller.watchNamespaces` in values.yaml. This enables a **hybrid RBAC approach** that dramatically reduces security risk while maintaining flexibility:

- **ClusterRole**: Only for resources that truly need cluster-wide access
- **Role + RoleBinding**: For namespace-scoped operations
- **Configurable scope**: Based on deployment requirements

## Current Problem

**All permissions are cluster-wide** via ClusterRole + ClusterRoleBinding, meaning kagent can access resources in **every namespace** across the cluster.

## Hybrid RBAC Solution

### 🎯 **Approach 1: Namespace-Scoped Deployment (Recommended)**

For most deployments, kagent only needs access to specific namespaces.

#### Configuration
```yaml
# values.yaml
controller:
  watchNamespaces: 
    - kagent-system    # Where kagent is deployed
    - production       # Application namespaces to manage
    - staging
```

#### RBAC Structure
```yaml
# 1. ClusterRole - ONLY for truly cluster-wide resources
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kagent-cluster-reader
rules:
# ONLY cluster-scoped resources that cannot be namespace-scoped
- apiGroups: [""]
  resources: ["namespaces", "nodes"]
  verbs: ["get", "list", "watch"]

---
# 2. Role - For namespace-scoped operations (per watched namespace)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: kagent-namespace-role
  namespace: "{{ .namespace }}"  # Applied to each watched namespace
rules:
# Kagent custom resources
- apiGroups: ["kagent.dev"]
  resources: ["agents", "modelconfigs", "teams", "toolservers", "memories"]
  verbs: ["*"]

# Core resources - SPECIFIC, not wildcard
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets", "events"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

# Pod logs for troubleshooting
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]

# Apps resources - SPECIFIC
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

---
# 3. RoleBinding - Binds Role to ServiceAccount in each namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kagent-namespace-binding
  namespace: "{{ .namespace }}"
subjects:
- kind: ServiceAccount
  name: kagent
  namespace: kagent-system  # Where kagent is deployed
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kagent-namespace-role

---
# 4. ClusterRoleBinding - ONLY for cluster-scoped resources
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: kagent-cluster-binding
subjects:
- kind: ServiceAccount
  name: kagent
  namespace: kagent-system
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kagent-cluster-reader
```

### 🎯 **Approach 2: Tools-Specific ClusterRole (For Cross-Namespace Troubleshooting)**

If the tools container needs cluster-wide troubleshooting capabilities:

#### Separate ServiceAccounts
```yaml
# 1. Core kagent ServiceAccount - namespace-scoped
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kagent-core
  namespace: kagent-system

# 2. Tools ServiceAccount - cluster-scoped read-only
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kagent-tools
  namespace: kagent-system
```

#### Separate RBAC
```yaml
# Core kagent - namespace-scoped (same as Approach 1)
# ...

# Tools ClusterRole - READ-ONLY cluster-wide
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: kagent-tools-reader
rules:
# ONLY read access for troubleshooting
- apiGroups: [""]
  resources: ["pods", "services", "events", "namespaces", "nodes"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]
```

## Implementation Options

### Option A: Single Namespace (Highest Security)
```yaml
# values.yaml
controller:
  watchNamespaces: []  # Empty = only release namespace
```
**Security**: 🟢 **LOW RISK** - kagent limited to its own namespace

### Option B: Multi-Namespace (Balanced Security)
```yaml
# values.yaml
controller:
  watchNamespaces: 
    - production
    - staging
    - development
```
**Security**: 🟡 **MEDIUM RISK** - kagent limited to specified namespaces

### Option C: Cluster-Wide with Minimal Permissions (Current Proposal)
```yaml
# values.yaml
controller:
  watchNamespaces: []  # Empty = all namespaces
# Use minimal ClusterRole permissions
```
**Security**: 🟡 **MEDIUM RISK** - cluster-wide but minimal permissions

## Helm Template Implementation

### Dynamic Role Creation
```yaml
{{/* templates/namespace-roles.yaml */}}
{{- range $ns := .Values.controller.watchNamespaces }}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "kagent.fullname" $ }}-role
  namespace: {{ $ns }}
  labels:
    {{- include "kagent.labels" $ | nindent 4 }}
rules:
# ... role rules here ...

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "kagent.fullname" $ }}-binding
  namespace: {{ $ns }}
  labels:
    {{- include "kagent.labels" $ | nindent 4 }}
subjects:
- kind: ServiceAccount
  name: {{ include "kagent.fullname" $ }}
  namespace: {{ include "kagent.namespace" $ }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ include "kagent.fullname" $ }}-role
{{- end }}
```

## Security Comparison

| Approach | Scope | Risk Level | Blast Radius | Troubleshooting |
|----------|-------|------------|--------------|-----------------|
| **Current** | Cluster-wide wildcard | 🔴 CRITICAL | Entire cluster | Full |
| **Option A** | Single namespace | 🟢 LOW | One namespace | Limited |
| **Option B** | Multi-namespace | 🟡 MEDIUM | Selected namespaces | Scoped |
| **Option C** | Cluster minimal | 🟡 MEDIUM | Entire cluster | Full |

## Migration Strategy

### Phase 1: Add Namespace Configuration
```bash
# Enable namespace-scoped deployment
helm upgrade kagent ./helm/kagent/ \
  --set controller.watchNamespaces="{kagent-system,production}"
```

### Phase 2: Implement Hybrid RBAC
1. Create namespace-scoped Roles and RoleBindings
2. Reduce ClusterRole to minimal cluster-scoped resources
3. Test functionality in each watched namespace

### Phase 3: Validate and Monitor
1. Verify kagent operations in watched namespaces
2. Confirm no access to unwatched namespaces
3. Monitor for permission denied errors

## Recommendations by Environment

### 🏢 **Production/Enterprise**
- **Use Option A or B** (namespace-scoped)
- Explicitly define `watchNamespaces`
- Separate ServiceAccounts for different components
- Regular RBAC audits

### 🧪 **Development/Testing**
- **Use Option B** (multi-namespace)
- Include development namespaces in `watchNamespaces`
- Cluster-wide tools access for debugging

### 🏗️ **Platform Teams**
- **Use Option C** with enhanced monitoring
- Implement additional security controls (NetworkPolicies, etc.)
- Consider OPA/Gatekeeper policies for additional restrictions

## Benefits of Hybrid Approach

1. **Dramatically reduced blast radius** - limited to specified namespaces
2. **Maintained functionality** - full capabilities within scope
3. **Flexible configuration** - adapt to deployment requirements
4. **Principle of least privilege** - only necessary permissions
5. **Better compliance** - meets enterprise security requirements

## Conclusion

The hybrid RBAC approach leverages kagent's existing namespace watching capabilities to provide **significantly better security** while maintaining operational flexibility. 

**Immediate Action**: Implement namespace-scoped deployment for most use cases, reserving cluster-wide access only when truly necessary.

---

**Implementation Status:** ✅ Ready for design and implementation  
**Complexity:** Medium - requires Helm template updates  
**Security Impact:** Dramatic improvement from CRITICAL to LOW/MEDIUM risk 
