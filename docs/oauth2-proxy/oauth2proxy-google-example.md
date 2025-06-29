# Google OAuth2 Setup for Specific User

## Quick Google OAuth Setup

### 1. Create Google OAuth App

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 Client ID:
   - **Application type**: Web application
   - **Name**: `Kagent Development`
   - **Authorized redirect URIs**: `http://localhost:8001/oauth2/callback`
5. Copy the **Client ID** and **Client Secret**

### 2. Deploy with Google OAuth

```bash
# Generate a secure cookie secret
COOKIE_SECRET=$(python -c 'import secrets; print(secrets.token_urlsafe(32))')

# Deploy with Google OAuth enabled for specific user
helm upgrade --install kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.provider=google \
  --set oauth2Proxy.clientId=your-google-client-id \
  --set oauth2Proxy.clientSecret=your-google-client-secret \
  --set oauth2Proxy.cookieSecret=$COOKIE_SECRET \
  --set oauth2Proxy.config.emailDomains=["*"] \
  --set oauth2Proxy.config.extraArgs=["--authenticated-emails-file=/tmp/emails.txt"] \
  --set service.type=LoadBalancer
```

### 3. Allow Specific Email

Create a config with allowed emails:

```bash
# Create ConfigMap with allowed emails
kubectl create configmap oauth2-emails -n kagent \
  --from-literal=emails.txt="user.name@gmail.com"

# Update deployment to mount the email list
# (This would require modifying the deployment template)
```

### 4. Alternative: Use Email Domain Restriction

```bash
# Allow only gmail.com domain
helm upgrade --install kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.provider=google \
  --set oauth2Proxy.clientId=your-google-client-id \
  --set oauth2Proxy.clientSecret=your-google-client-secret \
  --set oauth2Proxy.cookieSecret=$COOKIE_SECRET \
  --set oauth2Proxy.config.emailDomains=["gmail.com"]
```

## Simple Switch Between Providers

You can easily switch between GitHub and Google:

```bash
# GitHub OAuth
helm upgrade kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.provider=github \
  --set oauth2Proxy.github.org=your-org

# Google OAuth  
helm upgrade kagent ./helm/kagent -n kagent \
  --set oauth2Proxy.provider=google \
  --set oauth2Proxy.config.emailDomains=["gmail.com"]
``` 
