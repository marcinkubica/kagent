# Main Branch - Current Nginx Configuration

**Generated:** 2025-06-29 01:12 UTC  
**Branch:** main (deployed from oauth2proxy branch workspace)  
**Deployment:** kagent-66567f9498-2ghgs  
**Namespace:** kagent  

## Deployment Status

### OAuth2-Proxy Status
- **Enabled**: ❌ **DISABLED**
- **Containers**: 3/3 (controller, app, ui) - **No oauth2-proxy sidecar**
- **Service Type**: ClusterIP
- **Port Configuration**: Standard (80→8080, 8081→8081, 8083→8083)

### Pod Information
```
NAME                      READY   STATUS    RESTARTS   AGE
kagent-66567f9498-2ghgs   3/3     Running   0          2m5s
```

### Container Images (Main Branch)
```
controller: cr.kagent.dev/kagent-dev/kagent/controller:0.3.19
app:        cr.kagent.dev/kagent-dev/kagent/app:0.3.19
ui:         cr.kagent.dev/kagent-dev/kagent/ui:0.3.19
```

## Current Nginx Configuration

### Configuration Source
- **Source**: Built into UI container image (no external ConfigMap)
- **Location**: `/etc/nginx/nginx.conf` inside UI container
- **Type**: Static configuration from container build

### Active Nginx Configuration
```nginx
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

    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    server {
        listen 8080;
        server_name localhost;

        # Frontend routes
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

        # Backend routes
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
    }
}
```

## Configuration Analysis

### Key Characteristics

1. **OAuth2-Proxy Integration**: ❌ **NOT ACTIVE**
   - No oauth2-proxy upstream defined
   - No authentication routes (`/oauth2/`)
   - No auth_request directives

2. **Complete Proxy Configuration**: ✅ **FULL FEATURED**
   - Frontend routes properly configured
   - API routes with full proxy headers
   - WebSocket support for `/api/ws/`
   - Comprehensive logging setup

3. **Port Mapping**:
   - **Nginx listens on**: 8080
   - **UI upstream**: 127.0.0.1:8001
   - **WS backend**: 127.0.0.1:8081 (actively used)
   - **Backend**: 127.0.0.1:8083 (actively used)

4. **Advanced Features**:
   - ✅ **Logging**: Access and error logs to stdout/stderr
   - ✅ **WebSocket handling**: Full WebSocket proxy support
   - ✅ **API proxy routes**: Complete `/api/` routing
   - ✅ **Proxy headers**: Comprehensive header forwarding
   - ✅ **Connection upgrade**: Proper WebSocket upgrade handling

### Comparison with OAuth2Proxy Branch Config

**Main Branch (Complete)**:
```nginx
# Frontend routes
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

# Backend routes
location /api/ {
    proxy_pass http://kagent_backend/api/;
    # ... full proxy configuration
}

location /api/ws/ {
    proxy_pass http://kagent_ws_backend/api/ws/;
    # ... WebSocket configuration
}
```

**OAuth2Proxy Branch (Simplified)**:
```nginx
location / {
    proxy_pass http://kagent_ui;
}
```

## Service Configuration

### Current Service Ports
```yaml
ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: ui
  - port: 8081
    targetPort: 8081
    protocol: TCP
    name: app
  - port: 8083
    targetPort: 8083
    protocol: TCP
    name: controller
```

## Network Flow

### Current Flow (Main Branch)
```
User Request → Service:80 → UI Container:8080 → Nginx
                                                  ├─ / → UI App:8001
                                                  ├─ /api/ → Backend:8083
                                                  └─ /api/ws/ → WS Backend:8081
```

### OAuth2Proxy Branch Flow (Simplified)
```
User Request → Service:80 → UI Container:8080 → Nginx → UI App:8001
```

## Key Differences from OAuth2Proxy Branch

### 1. **Configuration Source**
- **Main Branch**: Built into container image
- **OAuth2Proxy Branch**: External ConfigMap (`kagent-nginx-config`)

### 2. **Configuration Complexity**
- **Main Branch**: ✅ **COMPLETE** - Full proxy configuration with API routes, WebSocket support, logging
- **OAuth2Proxy Branch**: ❌ **MINIMAL** - Basic proxy to UI only

### 3. **Functionality**
- **Main Branch**: 
  - ✅ Frontend serving
  - ✅ API proxy (`/api/`)
  - ✅ WebSocket support (`/api/ws/`)
  - ✅ Comprehensive logging
  - ✅ Proper header forwarding

- **OAuth2Proxy Branch**:
  - ✅ Frontend serving only
  - ❌ No API proxy routes
  - ❌ No WebSocket support
  - ❌ No logging configuration
  - ❌ Minimal header forwarding

### 4. **Headers and Proxy Configuration**
- **Main Branch**: Full proxy headers for production use
- **OAuth2Proxy Branch**: No proxy headers configured

## Root Cause Analysis

### Why OAuth2Proxy Branch Has Simplified Config

The OAuth2proxy branch is using a **Helm-generated ConfigMap** that appears to be using a **simplified template**, while the main branch uses the **full nginx configuration built into the container**.

This suggests:
1. **OAuth2Proxy branch ConfigMap template is incomplete**
2. **Missing API and WebSocket route definitions**
3. **Helm template may need updating** to include full nginx configuration

## Recommendations

### 1. Fix OAuth2Proxy Branch ConfigMap
The `helm/kagent/templates/nginx-configmap.yaml` should include:
- API proxy routes (`/api/`)
- WebSocket routes (`/api/ws/`)
- Proper proxy headers
- Logging configuration

### 2. Template Comparison
Compare the Helm nginx template with the built-in nginx configuration to ensure feature parity.

### 3. Testing Required
After fixing the ConfigMap, test:
- API functionality (`/api/` routes)
- WebSocket connections (`/api/ws/`)
- Proper header forwarding

## Conclusion

The **main branch has a complete, production-ready nginx configuration** with full API proxy support, WebSocket handling, and comprehensive logging, while the **oauth2proxy branch has a simplified configuration that's missing critical functionality**.

This explains potential functional differences between the branches beyond just the oauth2-proxy integration.

---
**Report Generated by:** SRE Analysis  
**Branch:** main (complete nginx configuration)  
**Status:** ✅ DOCUMENTED - Significant differences identified 
