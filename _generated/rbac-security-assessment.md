# Kagent RBAC Security Assessment Report

**Date:** June 2025  
**Assessment Scope:** kagent/ folder RBAC permissions analysis  
**Risk Level:** 🔴 CRITICAL

## Executive Summary

The kagent system grants **extremely broad, near-cluster-admin level permissions** across multiple components. This represents a significant security concern as it provides extensive administrative capabilities that could be exploited if compromised. The current RBAC configuration essentially grants **cluster-admin equivalent privileges** to the kagent system.

## Detailed Findings

### Main Kagent Service Account Permissions

The core kagent service uses **two separate ClusterRoles** bound to the same ServiceAccount:

#### 1. Getter Role (Read Access)
**File:** `kagent/helm/kagent/templates/clusterrole.yaml` (lines 33-60)

```yaml
- apiGroups: [""]
  resources: ["*"]  # ALL core resources
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps", "batch", "rbac.authorization.k8s.io", "apiextensions.k8s.io"]
  resources: ["*"]  # ALL resources in these API groups
  verbs: ["get", "list", "watch"]
```

**Security Impact:** Full read access to all cluster resources including secrets, RBAC configurations, and system components.

#### 2. Writer Role (Full Write Access)
**File:** `kagent/helm/kagent/templates/clusterrole.yaml` (lines 85-110)

```yaml
- apiGroups: [""]
  resources: ["*"]  # ALL core resources
  verbs: ["create", "update", "patch", "delete"]
- apiGroups: ["apps", "batch", "apiextensions.k8s.io"]
  resources: ["*"]  # ALL resources in these API groups
  verbs: ["create", "update", "patch", "delete"]
```

**⚠️ Critical Security Issue:** These permissions grant **full administrative control** over:
- All pods, services, secrets, configmaps, namespaces
- All deployments, daemonsets, statefulsets, jobs
- All custom resource definitions (CRDs)
- All RBAC resources (can modify cluster permissions)

### Agent-Specific Excessive Permissions

#### Argo Rollouts Agent
**File:** `kagent/helm/agents/argo-rollouts/templates/rbac.yaml`

```yaml
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  verbs: ["*"]  # Full RBAC modification capabilities

- apiGroups: [""]
  resources: ["namespaces", "services", "endpoints", "pods", "persistentvolumeclaims"]
  verbs: ["*"]

- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "replicasets", "statefulsets"]
  verbs: ["*"]

- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["validatingwebhookconfigurations", "mutatingwebhookconfigurations"]
  verbs: ["*"]
```

**⚠️ Admin Privilege Escalation Risk:** Can create/modify/delete any RBAC configuration cluster-wide and control admission controllers.

#### Istio Agent
**File:** `kagent/helm/agents/istio/templates/rbac.yaml`

```yaml
- apiGroups: ["rbac.authorization.k8s.io"]
  resources: ["clusterroles", "clusterrolebindings", "roles", "rolebindings"]
  verbs: ["*"]  # Full RBAC modification capabilities

- apiGroups: ["admissionregistration.k8s.io"]
  resources: ["validatingwebhookconfigurations", "mutatingwebhookconfigurations"]
  verbs: ["*"]

- apiGroups: ["networking.istio.io", "security.istio.io", "telemetry.istio.io", "extensions.istio.io", "install.istio.io"]
  resources: ["*"]
  verbs: ["*"]
```

**⚠️ Same escalation risk** as Argo agent with additional service mesh control.

#### Cilium Manager Agent
**File:** `kagent/helm/agents/cilium-manager/templates/rbac.yaml`

```yaml
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
```

**Security Impact:** Full control over networking infrastructure and pod execution capabilities.

#### Cilium Debug Agent
**File:** `kagent/helm/agents/cilium-debug/templates/rbac.yaml`

```yaml
- apiGroups: ["cilium.io"]
  resources: ["*"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces", "services", "endpoints", "componentstatuses", "events"]
  verbs: ["*"]

- apiGroups: [""]
  resources: ["pods/log", "pods/exec"]
  verbs: ["*"]
```

**Security Impact:** Debugging capabilities with full pod execution access.

#### Cilium Policy Agent
**File:** `kagent/helm/agents/cilium-policy/templates/rbac.yaml`

```yaml
- apiGroups: ["cilium.io"]
  resources: ["*"]
  verbs: ["*"]
```

**Security Impact:** Full control over Cilium network policies.

### Controller Manager Role
**File:** `kagent/go/config/rbac/role.yaml`

```yaml
- apiGroups: ["kagent.dev", "agent.kagent.dev"]
  resources: ["agents", "memories", "modelconfigs", "teams", "toolservers"]
  verbs: ["create", "delete", "get", "list", "patch", "update", "watch"]
```

**Note:** This is appropriately scoped to kagent-specific resources only.

## Dangerous Permission Patterns Identified

### 1. Wildcard Resource Access
- **Pattern:** `resources: ["*"]`
- **Impact:** Grants access to ALL resources in an API group
- **Found in:** Main kagent roles, all agent roles
- **Risk Level:** 🔴 CRITICAL

### 2. Wildcard Verb Access
- **Pattern:** `verbs: ["*"]`
- **Impact:** Grants ALL possible actions (create, read, update, delete, etc.)
- **Found in:** All agent roles
- **Risk Level:** 🔴 CRITICAL

### 3. RBAC Manipulation Capabilities
- **Pattern:** Full access to `rbac.authorization.k8s.io` resources
- **Impact:** Allows privilege escalation to cluster-admin level
- **Found in:** Argo and Istio agents
- **Risk Level:** 🔴 CRITICAL

### 4. Pod Execution Access
- **Pattern:** `resources: ["pods/exec", "pods/log"]` with `verbs: ["*"]`
- **Impact:** Can execute commands in any pod and access logs
- **Found in:** Cilium agents
- **Risk Level:** 🟠 HIGH

### 5. Admission Controller Access
- **Pattern:** Full access to `admissionregistration.k8s.io` resources
- **Impact:** Can modify cluster-wide admission controllers
- **Found in:** Argo and Istio agents
- **Risk Level:** 🔴 CRITICAL

### 6. Secret Access
- **Pattern:** Core API group wildcard access includes secrets
- **Impact:** Can read/modify all secrets cluster-wide
- **Found in:** Main kagent roles, agent roles
- **Risk Level:** 🔴 CRITICAL

## Security Risk Assessment

### 🔴 CRITICAL RISKS

1. **Privilege Escalation**
   - RBAC modification capabilities allow escalation to cluster-admin
   - Agents can grant themselves additional permissions
   - No restrictions on what RBAC changes can be made

2. **Cluster Compromise**
   - Wildcard permissions provide near-complete cluster control
   - Can modify any resource in most API groups
   - Equivalent to cluster-admin access

3. **Security Control Bypass**
   - Admission controller modification capabilities
   - Can disable security policies and validations
   - Can bypass pod security standards

4. **Lateral Movement**
   - Pod exec access enables container compromise
   - Can execute commands in any pod cluster-wide
   - Access to all pod logs for reconnaissance

### 🟠 HIGH RISKS

1. **Secret Exposure**
   - Full access to all secrets cluster-wide
   - Can read API keys, certificates, passwords
   - No namespace restrictions

2. **Network Policy Bypass**
   - Can modify/delete network security policies
   - Full control over Cilium networking
   - Can disable network segmentation

3. **Audit Trail Manipulation**
   - Can potentially modify logging and monitoring configurations
   - Access to system component configurations
   - Can cover tracks of malicious activity

### 🟡 MEDIUM RISKS

1. **Resource Exhaustion**
   - Can create unlimited resources
   - No resource quotas or limits enforced via RBAC
   - Potential for denial of service

2. **Configuration Drift**
   - Broad permissions may lead to unintended changes
   - Difficult to track what changes are legitimate
   - Compliance and governance challenges

## Recommendations

### Immediate Actions (Priority 1)

1. **Remove Wildcard Permissions**
   - Replace `resources: ["*"]` with specific resource lists
   - Replace `verbs: ["*"]` with specific required actions
   - Audit each agent's actual requirements

2. **Remove RBAC Modification Capabilities**
   - Remove access to `rbac.authorization.k8s.io` resources from agents
   - Implement separate, restricted service accounts for RBAC changes if needed
   - Require manual approval for RBAC modifications

3. **Scope Permissions to Specific Namespaces**
   - Use Roles instead of ClusterRoles where possible
   - Implement namespace-specific service accounts
   - Restrict cross-namespace access

4. **Remove Pod Exec Permissions**
   - Remove `pods/exec` permissions unless absolutely required
   - Implement separate debug service accounts with time-limited access
   - Use admission controllers to restrict exec access

### Short-term Actions (Priority 2)

1. **Implement Resource Name Restrictions**
   - Use `resourceNames` to limit access to specific resources
   - Restrict secret access to only required secrets
   - Limit CRD access to kagent-specific resources

2. **Separate Service Accounts by Function**
   - Create dedicated service accounts for each agent
   - Implement role separation between read and write operations
   - Use different service accounts for different environments

3. **Add Admission Controller Restrictions**
   - Implement OPA Gatekeeper policies to restrict RBAC changes
   - Add validation for service account permissions
   - Prevent privilege escalation attempts

### Long-term Actions (Priority 3)

1. **Regular Permission Audits**
   - Implement automated RBAC scanning
   - Regular review of permission usage
   - Remove unused permissions

2. **Implement Monitoring and Alerting**
   - Monitor for RBAC changes
   - Alert on privilege escalation attempts
   - Log all administrative actions

3. **Security Hardening**
   - Implement pod security standards
   - Use network policies to restrict communication
   - Regular security assessments

## Principle of Least Privilege Implementation

### Recommended Permission Structure

```yaml
# Example: Scoped Argo Rollouts Agent
apiVersion: rbac.authorization.k8s.io/v1
kind: Role  # Use Role instead of ClusterRole
metadata:
  namespace: kagent  # Scope to specific namespace
  name: kagent-argo-role
rules:
- apiGroups: ["argoproj.io"]
  resources: ["rollouts", "analysistemplates", "analysisruns"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: ["apps"]
  resources: ["replicasets"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["create", "patch"]
```

### Service Account Separation Strategy

1. **Read-only Service Account**
   - Only `get`, `list`, `watch` permissions
   - Used for monitoring and status reporting

2. **Application Management Service Account**
   - Limited to specific namespaces
   - Only resources required for application lifecycle

3. **Debug Service Account**
   - Time-limited access
   - Requires approval for activation
   - Logged and monitored

## Conclusion

The current RBAC configuration in kagent represents a **critical security vulnerability** that essentially grants cluster-admin equivalent privileges to the kagent system. This violates the principle of least privilege and creates significant attack surface for potential compromise.

**Immediate action is required** to:
1. Remove wildcard permissions
2. Eliminate RBAC modification capabilities
3. Scope permissions to specific namespaces and resources
4. Implement proper service account separation

The security risk is compounded by the fact that multiple agents have overlapping excessive permissions, creating multiple attack vectors for privilege escalation and cluster compromise.

## Appendix: File Locations

### Main RBAC Files
- `kagent/helm/kagent/templates/clusterrole.yaml` - Main kagent permissions
- `kagent/helm/kagent/templates/clusterrolebinding.yaml` - Main role bindings
- `kagent/helm/kagent/templates/serviceaccount.yaml` - Service account definition

### Agent RBAC Files
- `kagent/helm/agents/argo-rollouts/templates/rbac.yaml`
- `kagent/helm/agents/istio/templates/rbac.yaml`
- `kagent/helm/agents/cilium-manager/templates/rbac.yaml`
- `kagent/helm/agents/cilium-debug/templates/rbac.yaml`
- `kagent/helm/agents/cilium-policy/templates/rbac.yaml`

### Controller RBAC Files
- `kagent/go/config/rbac/role.yaml` - Controller manager role

### Deployment Files
- `kagent/helm/kagent/templates/deployment.yaml` - Main deployment using service account

---

**Report Generated:** January 2025  
**Assessment Type:** Static Code Analysis  
**Scope:** kagent/ folder RBAC configurations  
**Methodology:** Manual review of YAML manifests and Helm templates 
