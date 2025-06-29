# OAuth2 Proxy Setup Example

## Quick GitHub OAuth Setup

### 1. Create GitHub OAuth App

1. Go to [GitHub Developer Settings](https://github.com/settings/applications/new)
2. Fill in the form:
   - **Application name**: `Kagent Development`
   - **Homepage URL**: `http://localhost:8001`
   - **Authorization callback URL**: `http://localhost:8001/oauth2/callback`
3. Click "Register application"
4. Copy the **Client ID** and **Client Secret**

### 2. Deploy with OAuth2 Proxy

```bash
# Generate a secure cookie secret
COOKIE_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Deploy with OAuth2 proxy enabled
helm upgrade --install kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.clientId=your-github-client-id \
  --set oauth2Proxy.clientSecret=your-github-client-secret \
  --set oauth2Proxy.cookieSecret=$COOKIE_SECRET \
  --set oauth2Proxy.github.org=your-github-org \
  --set service.type=LoadBalancer
```

### 3. Access the Application

```bash
# Port forward to the service
kubectl port-forward -n kagent service/kagent 8001:80

# Open browser to http://localhost:8001
# You'll be redirected to GitHub for authentication
```

### 4. Production Setup

For production, use external secret management:

```bash
# Create secrets externally
kubectl create secret generic oauth2-proxy-secrets -n kagent \
  --from-literal=client-id=your-github-client-id \
  --from-literal=client-secret=your-github-client-secret \
  --from-literal=cookie-secret=$COOKIE_SECRET

# Deploy with external secrets
helm upgrade --install kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.secrets.external=true \
  --set oauth2Proxy.github.org=your-github-org
```

## Configuration Options

- **Provider**: GitHub (default), Google, Azure, OIDC
- **GitHub Org**: Restrict access to specific GitHub organization
- **GitHub Team**: Further restrict to specific team within org
- **Email Domains**: Restrict by email domain
- **Cookie Settings**: Secure defaults for financial compliance

## Validation

✅ **OAuth2 Disabled**: Direct access to UI on port 80  
✅ **OAuth2 Enabled**: Authentication required, redirects to GitHub  
✅ **Service Routing**: Automatic switching between direct and proxied access 
