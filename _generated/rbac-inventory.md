# Kagent Component RBAC Permissions List

**Date:** June 30, 2025  
**Purpose:** Complete inventory of RBAC permissions by component  
**Scope:** All kagent components and agents

## Core Kagent Service Account

**ServiceAccount:** `kagent` (in release namespace)  
**Used by:** Main kagent deployment (controller, app, ui, tools containers)

### Getter Role (`kagent-getter-role`)

```yaml
rules:
- apiGroups: ["kagent.dev"]
  resources: ["agents", "modelconfigs", "teams", "toolservers", "memories"]
  verbs: ["get", "list", "watch"]

- apiGroups: ["kagent.dev"]
  resources: ["agents/status", "modelconfigs/status", "teams/status", "toolservers/status", "memories/status"]
  verbs: ["get", "patch", "update"]

- apiGroups: [""]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

- apiGroups: ["batch"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

- apiGroups: ["apiextensions.k8s.io"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]

- apiGroups: ["gateway.networking.k8s.io/v1"]
  resources: ["*"]
  verbs: ["get", "list", "watch"]
```

### Writer Role (`kagent-writer-role`)

```yaml
rules:
- apiGroups: ["kagent.dev"]
  resources: ["agents", "modelconfigs", "teams", "toolservers", "memories"]
  verbs: ["create", "update", "patch", "delete"]

- apiGroups: [""]
  resources: ["*"]
  verbs: ["create", "update", "patch", "delete"]

- apiGroups: ["apps"]
  resources: ["*"]
  verbs: ["create", "update", "patch", "delete"]

- apiGroups: ["batch"]
  resources: ["*"]
  verbs: ["create", "update", "patch", "delete"]

- apiGroups: ["apiextensions.k8s.io"]
  resources: ["*"]
  verbs: ["create", "update", "patch", "delete"]

- apiGroups: ["gateway.networking.k8s.io/v1"]
  resources: ["*"]
  verbs: ["create", "update", "patch", "delete"]
```

## Controller Manager Role

**ServiceAccount:** Used by Go controller  
**ClusterRole:** `manager-role`

```yaml
rules:
- apiGroups: ["agent.kagent.dev"]
  resources: ["toolservers"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]

- apiGroups: ["agent.kagent.dev"]
  resources: ["toolservers/finalizers"]
  verbs: ["update"]

- apiGroups: ["agent.kagent.dev"]
  resources: ["toolservers/status"]
  verbs: ["get", "patch", "update"]

- apiGroups: ["kagent.dev"]
  resources: ["agents", "memories", "modelconfigs", "teams"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]

- apiGroups: ["kagent.dev"]
  resources: ["agents/finalizers", "memories/finalizers", "modelconfigs/finalizers", "teams/finalizers"]
  verbs: ["update"]

- apiGroups: ["kagent.dev"]
  resources: ["agents/status", "memories/status", "modelconfigs/status", "teams/status"]
  verbs: ["get", "patch", "update"]
```

## Agent RBAC Permissions

### Argo Rollouts Agent

**ServiceAccount:** `kagent` (shared)  
**ClusterRole:** `kagent-argo-role`

```yaml
rules:
- apiGroups: [""]
  resources: ["namespaces", "services", "endpoints", "pods", "persistentvolumeclaims"]
  verbs: ["*"]

- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets", "statefulsets"]
  verbs: ["*"]

- apiGroups: ["policy"]
  resources: ["poddisruptionbudgets"]
  verbs: ["*"]

- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["*"]

- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies", "ingresses"]
  verbs: ["*"]

- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  verbs: ["*"]

- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["*"]

- apiGroups: ["authentication.k8s.io"]
  resources: ["tokenreviews", "subjectaccessreviews"]
  verbs: ["*"]

- apiGroups: ["authorization.k8s.io"]
  resources: ["selfsubjectaccessreviews", "selfsubjectrulesreviews", "subjectaccessreviews"]
  verbs: ["*"]

- apiGroups: ["policy"]
  resources: ["podsecuritypolicies"]
  verbs: ["use"]
  resourceNames: ["example"]

- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["validatingwebhookconfigurations", "mutatingwebhookconfigurations"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["secrets", "configmaps", "serviceaccounts"]
  verbs: ["*"]

- apiGroups: ["argoproj.io", "gateway.networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods/portforward"]
  verbs: ["create"]
```

### Istio Agent

**ServiceAccount:** `kagent` (shared)  
**ClusterRole:** `kagent-istio-role`

```yaml
rules:
- apiGroups: [""]
  resources: ["namespaces", "services", "endpoints", "pods", "persistentvolumeclaims"]
  verbs: ["*"]

- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets", "statefulsets"]
  verbs: ["*"]

- apiGroups: ["policy"]
  resources: ["poddisruptionbudgets"]
  verbs: ["*"]

- apiGroups: ["autoscaling"]
  resources: ["horizontalpodautoscalers"]
  verbs: ["*"]

- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies", "ingresses"]
  verbs: ["*"]

- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  verbs: ["*"]

- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["*"]

- apiGroups: ["authentication.k8s.io"]
  resources: ["tokenreviews", "subjectaccessreviews"]
  verbs: ["*"]

- apiGroups: ["authorization.k8s.io"]
  resources: ["selfsubjectaccessreviews", "selfsubjectrulesreviews", "subjectaccessreviews"]
  verbs: ["*"]

- apiGroups: ["policy"]
  resources: ["podsecuritypolicies"]
  verbs: ["use"]
  resourceNames: ["example"]

- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["validatingwebhookconfigurations", "mutatingwebhookconfigurations"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["secrets", "configmaps", "serviceaccounts"]
  verbs: ["*"]

- apiGroups: ["networking.istio.io", "security.istio.io", "telemetry.istio.io", "extensions.istio.io", "install.istio.io", "gateway.networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods/portforward"]
  verbs: ["create"]
```

### Cilium Manager Agent

**ServiceAccount:** `kagent` (shared)  
**ClusterRole:** `kagent-cilium-manager-role`

```yaml
rules:
- apiGroups: ["cilium.io"]
  resources: ["*"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces", "services", "endpoints", "componentstatuses"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["*"]

- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "statefulsets", "replicasets"]
  verbs: ["*"]

- apiGroups: ["networking.k8s.io"]
  resources: ["networkpolicies", "ingresses"]
  verbs: ["*"]

- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["*"]

- apiGroups: ["helm.toolkit.fluxcd.io"]
  resources: ["helmreleases"]
  verbs: ["*"]
```

### Cilium Debug Agent

**ServiceAccount:** `kagent` (shared)  
**ClusterRole:** `kagent-cilium-debug-role`

```yaml
rules:
- apiGroups: ["cilium.io"]
  resources: ["*"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces", "services", "endpoints", "componentstatuses", "events"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["*"]

- apiGroups: ["networking.k8s.io"]
  resources: ["*"]
  verbs: ["*"]

- apiGroups: ["apiextensions.k8s.io"]
  resources: ["customresourcedefinitions"]
  verbs: ["*"]
```

### Cilium Policy Agent

**ServiceAccount:** `kagent` (shared)  
**ClusterRole:** `kagent-cilium-policy-role`

```yaml
rules:
- apiGroups: ["cilium.io"]
  resources: ["*"]
  verbs: ["*"]
```

## Additional Components

### K8s Agent
**Note:** No separate RBAC file found - uses main kagent ServiceAccount permissions

### KGateway Agent
**Note:** No separate RBAC file found - uses main kagent ServiceAccount permissions

### PromQL Agent
**Note:** No separate RBAC file found - uses main kagent ServiceAccount permissions

### Observability Agent
**Note:** No separate RBAC file found - uses main kagent ServiceAccount permissions

### Helm Agent
**Note:** No separate RBAC file found - uses main kagent ServiceAccount permissions

## Summary by Permission Type

### Cluster-Wide Admin Permissions
- **Argo Rollouts Agent:** Full RBAC modification (`rbac.authorization.k8s.io/*`)
- **Istio Agent:** Full RBAC modification (`rbac.authorization.k8s.io/*`)
- **Core Kagent:** Read access to RBAC resources

### Pod Execution Permissions
- **Cilium Manager Agent:** `pods/exec`, `pods/log`
- **Cilium Debug Agent:** `pods/exec`, `pods/log`

### Wildcard Resource Access
- **Core Kagent Getter:** `*` resources in core, apps, batch, rbac, apiextensions API groups (read-only)
- **Core Kagent Writer:** `*` resources in core, apps, batch, apiextensions API groups (write)
- **All Cilium Agents:** `*` resources in `cilium.io` API group
- **Argo/Istio Agents:** `*` resources in multiple API groups

### Admission Controller Access
- **Argo Rollouts Agent:** `validatingwebhookconfigurations`, `mutatingwebhookconfigurations`
- **Istio Agent:** `validatingwebhookconfigurations`, `mutatingwebhookconfigurations`

### Custom Resource Definitions
- **All Agents:** Full access to CRDs (`apiextensions.k8s.io/customresourcedefinitions`)

---

**Total ClusterRoles:** 7  
**Total ClusterRoleBindings:** 7  
**ServiceAccounts:** 1 (shared by all components)  
**Components with RBAC modification:** 2 (Argo, Istio)  
**Components with pod exec:** 2 (Cilium Manager, Cilium Debug) 
