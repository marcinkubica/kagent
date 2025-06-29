# Multi-Provider OAuth2 Setup (Advanced)

## Architecture Overview

Since oauth2-proxy doesn't support multiple providers natively, you need multiple instances:

```
User Request → Load Balancer/Ingress
                    ↓
            ┌─────────────────┐
            │  Auth Gateway   │
            └─────────────────┘
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
┌─────────────┐         ┌─────────────┐
│OAuth2-Proxy │         │OAuth2-Proxy │
│  (GitHub)   │         │  (Google)   │
│   :8090     │         │   :8091     │
└─────────────┘         └─────────────┘
        ↓                       ↓
        └───────────┬───────────┘
                    ↓
            ┌─────────────────┐
            │   Kagent App    │
            │     :8080       │
            └─────────────────┘
```

## Implementation Options

### Option A: Ingress-Based Routing

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kagent-auth
spec:
  rules:
  - host: kagent.local
    http:
      paths:
      - path: /auth/github
        pathType: Prefix
        backend:
          service:
            name: kagent-github-oauth
            port:
              number: 8090
      - path: /auth/google  
        pathType: Prefix
        backend:
          service:
            name: kagent-google-oauth
            port:
              number: 8091
      - path: /
        pathType: Prefix
        backend:
          service:
            name: kagent
            port:
              number: 80
```

### Option B: Custom Auth Gateway

Deploy a simple auth gateway that presents both options:

```html
<!-- auth-gateway.html -->
<h1>Choose Login Method</h1>
<a href="/auth/github">Login with GitHub</a>
<a href="/auth/google">Login with Google</a>
```

### Option C: Use External Auth Service

Use something like **Dex** or **Keycloak** that supports multiple providers:

```bash
# Deploy Dex with multiple connectors
helm install dex dex/dex \
  --set config.connectors[0].type=github \
  --set config.connectors[1].type=google
```

## Recommended Approach for Your Use Case

Given you want:
- GitHub for org members
- Google for user.name@gmail.com

**Simplest solution**: Use **Google OAuth with email restriction**:

```bash
# Switch to Google OAuth
helm upgrade kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.provider=google \
  --set oauth2Proxy.config.emailDomains=["gmail.com"] \
  --set oauth2Proxy.clientId=your-google-client-id \
  --set oauth2Proxy.clientSecret=your-google-client-secret
```

This allows any Gmail user, but you can further restrict with additional configuration.

## Future Enhancement

We could extend the Helm chart to support multiple oauth2-proxy instances:

```yaml
oauth2Proxy:
  instances:
    github:
      enabled: true
      provider: github
      port: 8090
    google:
      enabled: true  
      provider: google
      port: 8091
```

This would deploy multiple oauth2-proxy containers in the same pod, each handling different providers. 
