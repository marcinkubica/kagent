# OAuth2Proxy Branch - Nginx Configuration Fix Proposal

**Generated:** 2025-06-29 01:15 UTC  
**Priority:** 🚨 **CRITICAL**  
**Status:** **READY FOR IMPLEMENTATION**  

## Executive Summary

This proposal outlines the necessary changes to fix the **critical nginx configuration deficiencies** in the OAuth2Proxy branch that are preventing proper API functionality, WebSocket support, and logging capabilities.

## Problem Statement

### Current Issues
1. **API Endpoints Broken**: All `/api/*` requests return 404
2. **WebSocket Communication Failed**: Real-time features non-functional
3. **No Request Logging**: Zero observability into traffic
4. **Missing Proxy Headers**: Limited functionality and debugging capability
5. **Incomplete Configuration**: Helm template missing 80% of required nginx config

### Root Cause
The `helm/kagent/templates/nginx-configmap.yaml` template contains a **severely simplified nginx configuration** that lacks:
- API proxy routes (`/api/`)
- WebSocket proxy routes (`/api/ws/`)
- Logging configuration
- Proper proxy headers
- Connection upgrade handling

## Proposed Solution

### Phase 1: Fix Core Nginx Configuration

#### 1.1 Update Helm Template
**File:** `helm/kagent/templates/nginx-configmap.yaml`

**Current (Broken)**:
```yaml
data:
  nginx.conf: |-
    events {
        worker_connections 1024;
    }
    http {
        upstream kagent_ui {
            server 127.0.0.1:8001;
        }
        upstream kagent_ws_backend {
            server 127.0.0.1:8081;
        }
        upstream kagent_backend {
            server 127.0.0.1:8083;
        }
        map $http_upgrade $connection_upgrade {
            default upgrade;
            "" close;
        }
        server {
            listen 8080;
            server_name localhost;
            location / {
                proxy_pass http://kagent_ui;
            }
        }
    }
```

**Proposed (Complete)**:
```yaml
data:
  nginx.conf: |-
    events {
        worker_connections 1024;
    }
    http {
        # Log to stdout for container visibility
        access_log /dev/stdout;
        error_log /dev/stderr;

        log_format main        '[$time_local] $remote_addr - $remote_user - $request $status $body_bytes_sent $http_referer $http_user_agent $http_x_forwarded_for';
        log_format upstreamlog '[$time_local] $remote_addr - $remote_user - $server_name $host to: $upstream_addr: $request $status upstream_response_time $upstream_response_time msec $msec request_time $request_time';

        upstream kagent_ui {
            server 127.0.0.1:8001;
        }
        upstream kagent_ws_backend {
            server 127.0.0.1:8081;
        }
        upstream kagent_backend {
            server 127.0.0.1:8083;
        }
{{- if .Values.oauth2Proxy.enabled }}
        upstream oauth2_proxy {
            server 127.0.0.1:4180;
        }
{{- end }}
        map $http_upgrade $connection_upgrade {
            default upgrade;
            '' close;
        }
        server {
            listen 8080;
            server_name localhost;
{{- if .Values.oauth2Proxy.enabled }}
            # Health check endpoints (bypass oauth2-proxy)
            location ~ ^/(ping|health|ready)$ {
                return 200 "OK";
                add_header Content-Type text/plain;
            }

            # OAuth2 Proxy callback (bypass auth)
            location /oauth2/ {
                proxy_pass http://oauth2_proxy;
                proxy_http_version 1.1;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $server_name;
            }

            # Auth endpoint
            location = /oauth2/auth {
                proxy_pass http://oauth2_proxy;
                proxy_pass_request_body off;
                proxy_set_header Content-Length "";
                proxy_set_header X-Original-URI $request_uri;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $server_name;
            }

            # Frontend routes (protected)
            location / {
                auth_request /oauth2/auth;
                
                # Pass auth headers to upstream
                auth_request_set $user $upstream_http_x_auth_request_user;
                auth_request_set $email $upstream_http_x_auth_request_email;
                auth_request_set $preferred_username $upstream_http_x_auth_request_preferred_username;
                
                proxy_pass http://kagent_ui;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Origin $scheme://$host;
                proxy_set_header X-Auth-Request-User $user;
                proxy_set_header X-Auth-Request-Email $email;
                proxy_set_header X-Auth-Request-Preferred-Username $preferred_username;
                proxy_cache_bypass $http_upgrade;
                
                # Redirect to oauth2-proxy on auth failure
                error_page 401 = @error401;
            }

            # Backend routes (protected)
            location /api/ {
                auth_request /oauth2/auth;
                
                # Pass auth headers to upstream
                auth_request_set $user $upstream_http_x_auth_request_user;
                auth_request_set $email $upstream_http_x_auth_request_email;
                auth_request_set $preferred_username $upstream_http_x_auth_request_preferred_username;
                
                proxy_pass http://kagent_backend/api/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $server_name;
                proxy_set_header X-Auth-Request-User $user;
                proxy_set_header X-Auth-Request-Email $email;
                proxy_set_header X-Auth-Request-Preferred-Username $preferred_username;
                proxy_cache_bypass $http_upgrade;
                
                # Redirect to oauth2-proxy on auth failure
                error_page 401 = @error401;
            }

            # WebSocket routes (protected)
            location /api/ws/ {
                auth_request /oauth2/auth;
                
                # Pass auth headers to upstream
                auth_request_set $user $upstream_http_x_auth_request_user;
                auth_request_set $email $upstream_http_x_auth_request_email;
                auth_request_set $preferred_username $upstream_http_x_auth_request_preferred_username;
                
                proxy_pass http://kagent_ws_backend/api/ws/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $server_name;
                proxy_set_header X-Auth-Request-User $user;
                proxy_set_header X-Auth-Request-Email $email;
                proxy_set_header X-Auth-Request-Preferred-Username $preferred_username;
                proxy_read_timeout 300s;
                proxy_send_timeout 300s;
                proxy_buffering off;
                
                # Redirect to oauth2-proxy on auth failure
                error_page 401 = @error401;
            }

            # Error handling for authentication failures
            location @error401 {
                return 302 /oauth2/start?rd=$scheme://$host$request_uri;
            }
{{- else }}
            # Frontend routes (no auth)
            location / {
                proxy_pass http://kagent_ui;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $host;
                proxy_set_header X-Forwarded-Host $host;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Origin $scheme://$host;
                proxy_cache_bypass $http_upgrade;
            }

            # Backend routes (no auth)
            location /api/ {
                proxy_pass http://kagent_backend/api/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection 'upgrade';
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $server_name;
                proxy_cache_bypass $http_upgrade;
            }

            # WebSocket routes (no auth)
            location /api/ws/ {
                proxy_pass http://kagent_ws_backend/api/ws/;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection $connection_upgrade;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_set_header X-Forwarded-Host $server_name;
                proxy_read_timeout 300s;
                proxy_send_timeout 300s;
                proxy_buffering off;
            }
{{- end }}
        }
    }
```

### Phase 2: Implementation Steps

#### 2.1 Backup Current Configuration
```bash
# Backup current broken config
kubectl get configmap kagent-nginx-config -n kagent -o yaml > backup-nginx-configmap.yaml
```

#### 2.2 Apply the Fix
```bash
# Update the Helm template file
# Then upgrade the deployment
OPENAI_API_KEY="foobar" helm upgrade kagent helm/kagent \
  --namespace kagent \
  --set service.type=ClusterIP \
  --set controller.image.registry=cr.kagent.dev \
  --set ui.image.registry=cr.kagent.dev \
  --set app.image.registry=cr.kagent.dev \
  --set providers.openAI.apiKey="foobar" \
  --set providers.default=openAI \
  --set oauth2Proxy.enabled=false
```

#### 2.3 Verification Tests
```bash
# Test UI access
curl --max-time 5 localhost:8082

# Test API access (CRITICAL - currently broken)
curl --max-time 5 localhost:8082/api/version

# Test API endpoints
curl --max-time 5 localhost:8082/api/teams
curl --max-time 5 localhost:8082/api/tools
curl --max-time 5 localhost:8082/api/modelconfigs

# Check nginx logs
kubectl logs -n kagent deployment/kagent -c ui --tail=50
```

### Phase 3: OAuth2-Proxy Integration Testing

#### 3.1 Enable OAuth2-Proxy
```bash
# Test with oauth2-proxy enabled
helm upgrade kagent helm/kagent \
  --namespace kagent \
  --set oauth2Proxy.enabled=true \
  --set oauth2Proxy.provider=github \
  --set oauth2Proxy.clientId="test-client-id" \
  --set oauth2Proxy.clientSecret="test-client-secret" \
  --set oauth2Proxy.cookieSecret="test-cookie-secret"
```

#### 3.2 Verify OAuth2-Proxy Integration
```bash
# Check oauth2-proxy container is running
kubectl get pods -n kagent -o wide

# Test auth redirect
curl -I localhost:8082

# Test oauth2 endpoints
curl localhost:8082/oauth2/ping
```

## Benefits of This Fix

### ✅ **Immediate Improvements**
1. **API Functionality Restored**: All `/api/*` endpoints will work
2. **WebSocket Support**: Real-time features will function
3. **Proper Logging**: Full observability into nginx traffic
4. **Production Headers**: Correct proxy header forwarding
5. **OAuth2-Proxy Ready**: Complete integration when enabled

### ✅ **Long-term Benefits**
1. **Feature Parity**: OAuth2Proxy branch matches main branch functionality
2. **Maintainability**: Single source of truth for nginx configuration
3. **Flexibility**: Easy to enable/disable oauth2-proxy
4. **Production Ready**: Complete configuration for enterprise use

## Risk Assessment

### 🟢 **Low Risk**
- Configuration is based on working main branch
- Includes proper fallback for oauth2-proxy disabled state
- Maintains backward compatibility

### ⚠️ **Mitigation Strategies**
- Backup current configuration before applying changes
- Test in development environment first
- Gradual rollout with verification at each step

## Testing Checklist

### Pre-Fix (Current State)
- [ ] ❌ API endpoints return 404
- [ ] ❌ WebSocket connections fail
- [ ] ❌ No nginx access logs
- [ ] ✅ UI frontend loads (basic functionality only)

### Post-Fix (Expected State)
- [ ] ✅ API endpoints return valid responses
- [ ] ✅ WebSocket connections establish successfully
- [ ] ✅ Nginx access logs visible in container logs
- [ ] ✅ UI frontend loads with full functionality
- [ ] ✅ OAuth2-proxy integration ready (when enabled)

## Implementation Timeline

### Immediate (Today)
1. **Update Helm template** - 30 minutes
2. **Test with oauth2-proxy disabled** - 15 minutes
3. **Verify API functionality** - 15 minutes

### Short-term (This Week)
1. **Test OAuth2-proxy integration** - 1 hour
2. **Documentation update** - 30 minutes
3. **Create deployment guide** - 30 minutes

## Success Criteria

### ✅ **Definition of Done**
1. All API endpoints (`/api/*`) return proper responses
2. WebSocket connections (`/api/ws/*`) function correctly
3. Nginx access logs appear in container logs
4. OAuth2-proxy can be enabled/disabled via Helm values
5. Feature parity with main branch achieved

## Files to Modify

1. **`helm/kagent/templates/nginx-configmap.yaml`** - Primary fix
2. **`_generated/oauth2proxy-nginx-fix-proposal.md`** - This document
3. **Documentation updates** - Deployment guides

## Conclusion

This fix is **critical for the OAuth2Proxy branch to be functional**. The current state renders the branch unusable for any API-dependent features. Implementation should be prioritized immediately.

The proposed solution provides:
- ✅ **Complete nginx configuration** matching main branch
- ✅ **OAuth2-proxy integration** when enabled
- ✅ **Backward compatibility** when oauth2-proxy is disabled
- ✅ **Production readiness** with proper logging and headers

---
**Proposal Status:** 📋 **READY FOR IMPLEMENTATION**  
**Priority:** 🚨 **CRITICAL**  
**Estimated Effort:** 2-3 hours total  
**Risk Level:** 🟢 **LOW** (with proper testing) 
