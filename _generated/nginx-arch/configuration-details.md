# Nginx Configuration Details

## Container Installation Process

### How Nginx Gets Installed in the UI Container

The nginx installation in Kagent's UI container follows a systematic multi-stage Docker build process using **Chainguard's Wolfi-based images** for security and minimal footprint.

#### Base Image and Package Installation

The UI container uses **Chainguard's `wolfi-base`** image as its foundation:

```dockerfile
FROM --platform=linux/$BUILDARCH $BASE_IMAGE_REGISTRY/chainguard/wolfi-base:latest AS base-os
```

**Key Installation Steps:**

1. **APK Package Installation**: Nginx is installed via the Alpine Package Keeper (APK) package manager:
   ```dockerfile
   RUN apk update \
       && apk add curl bash openssl unzip ca-certificates nginx supervisor \
       && update-ca-certificates \
       && rm -rf /var/cache/apk/*
   ```

2. **Multi-Stage Build Process**: The Dockerfile uses a two-stage approach:
   - **Stage 1 (base-os)**: Build and compile the Next.js application
   - **Stage 2 (final)**: Create the production runtime environment

#### Chainguard Wolfi Base Image Details

**What is Wolfi?**
- **Linux "undistro"**: Designed specifically for containers and cloud-native environments
- **Security-focused**: Built with comprehensive SBOMs (Software Bill of Materials)
- **APK package format**: Uses the proven Alpine package management system
- **Minimal footprint**: No kernel, relies on container runtime
- **glibc support**: Unlike Alpine's musl, provides full glibc compatibility

**Why Chainguard Images?**
- **Zero-known vulnerabilities**: Daily builds with latest security patches
- **Supply chain security**: Cryptographic signatures and provenance tracking
- **Distroless philosophy**: Minimal attack surface with only essential components
- **Enterprise-grade**: Used in production environments requiring high security

#### Container User and Permission Setup

The installation process includes careful user and permission management:

```dockerfile
RUN mkdir -p /app/ui/public /run/nginx/ /var/lib/nginx/tmp/ /var/lib/nginx/logs/  \
    && addgroup -g 1001    nginx                        \
    && adduser  -u 1001 -G nginx -s /bin/bash -D nextjs \
    && adduser  -u 1002 -G nginx -s /bin/bash -D nginx  \
    && chown    -vR nextjs:nginx /app/ui                \
    && chown    -vR nextjs:nginx /run/nginx             \
    && chown    -vR nextjs:nginx /var/lib/nginx/
```

**Security Features:**
- **Non-root execution**: Container runs as `nextjs` user (UID 1001)
- **Shared group**: Both `nextjs` and `nginx` users belong to `nginx` group
- **Proper permissions**: All nginx directories owned by appropriate users
- **Minimal privileges**: Following principle of least privilege

#### Configuration File Deployment

Configuration files are copied during the build process:

```dockerfile
WORKDIR /app
COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
```

**File Locations:**
- **Nginx config**: `/etc/nginx/nginx.conf` (standard nginx location)
- **Supervisor config**: `/etc/supervisor/conf.d/supervisord.conf`
- **Application files**: `/app/ui/` (Next.js application and static assets)

#### Process Management with Supervisor

The container uses **Supervisor** to manage both nginx and Next.js processes:

```ini
[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
autostart=true
autorestart=true
priority=20

[program:nextjs]
command=bun /app/ui/server.js
directory=/app/ui
environment=PORT=8001,HOSTNAME="0.0.0.0"
autostart=true
autorestart=true
priority=10
```

**Process Management Benefits:**
- **Automatic restart**: Both services restart on failure
- **Proper logging**: stdout/stderr captured and forwarded
- **Process coordination**: nginx starts after Next.js (priority ordering)
- **Single container**: Multiple services in one container with proper lifecycle management

#### Container Startup Sequence

1. **Container starts**: Supervisor daemon launches as PID 1
2. **Next.js starts**: Bun runtime starts Next.js server on port 8001 (priority 10)
3. **Nginx starts**: Nginx starts and proxies to Next.js (priority 20)
4. **Health monitoring**: Supervisor monitors both processes and restarts on failure

#### Build Optimization Features

**Multi-stage efficiency:**
- **Build artifacts**: Only production-ready files copied to final image
- **Layer optimization**: Separate layers for dependencies and application code
- **Cache utilization**: Docker layer caching for faster rebuilds

**Security hardening:**
- **Minimal packages**: Only essential packages installed
- **Regular updates**: Base image updated daily with security patches
- **Signed images**: Cryptographically signed with Sigstore/Cosign
- **SBOM included**: Complete software bill of materials for transparency

This installation approach ensures nginx is deployed securely, efficiently, and with proper process management while maintaining the minimal attack surface philosophy of distroless containers.

## Configuration Management Strategy

Kagent uses different nginx configuration approaches depending on the deployment branch and authentication requirements.

## Configuration Sources

### 1. Main Branch: Built-in Configuration
- **Location**: `ui/conf/nginx.conf`
- **Type**: Static configuration built into container image
- **Management**: Version controlled with application code
- **Deployment**: Copied during Docker build process

### 2. OAuth2-Proxy Branch: ConfigMap Override
- **Location**: Kubernetes ConfigMap `kagent-nginx-config`
- **Type**: Dynamic configuration managed by Helm
- **Management**: Template-based with Helm values
- **Deployment**: Mounted as volume in container

## Complete Configuration Analysis

### Main Branch Configuration

#### File Structure
```
ui/
├── conf/
│   ├── nginx.conf          # Main nginx configuration
│   └── supervisord.conf    # Process manager configuration
└── Dockerfile              # Container build instructions
```

#### Full nginx.conf (Main Branch)
```nginx
events {
    worker_connections 1024;
}

http {
    # Logging configuration
    access_log /dev/stdout;
    error_log /dev/stderr;

    # Log formats for debugging and monitoring
    log_format main '$time_local $remote_addr - $remote_user - $request $status $body_bytes_sent $http_referer $http_user_agent $http_x_forwarded_for';
    log_format upstreamlog '$time_local $remote_addr - $remote_user - $server_name $host to: $upstream_addr: $request $status upstream_response_time $upstream_response_time msec $msec request_time $request_time';

    # Upstream service definitions
    upstream kagent_ui {
        server 127.0.0.1:8001;
    }

    upstream kagent_ws_backend {
        server 127.0.0.1:8081;
    }

    upstream kagent_backend {
        server 127.0.0.1:8083;
    }

    # WebSocket connection upgrade mapping
    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    server {
        listen 8080;
        server_name localhost;

        # Frontend routes - serve Next.js application
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

        # Backend API routes
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

        # WebSocket routes for real-time communication
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

### OAuth2-Proxy Branch Configuration

#### Helm Template Structure
```yaml
# ConfigMap with templated nginx configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: kagent-nginx-config
data:
  nginx.conf: |-
    {{- if .Values.oauth2Proxy.enabled }}
    # OAuth2-Proxy enabled configuration
    {{- else }}
    # Standard configuration without authentication
    {{- end }}
```

#### OAuth2-Proxy Enhanced Configuration
```nginx
events {
    worker_connections 1024;
}

http {
    # Enhanced logging for authentication debugging
    access_log /dev/stdout;
    error_log /dev/stderr;

    log_format main '$time_local $remote_addr - $remote_user - $request $status $body_bytes_sent $http_referer $http_user_agent $http_x_forwarded_for';
    log_format upstreamlog '$time_local $remote_addr - $remote_user - $server_name $host to: $upstream_addr: $request $status upstream_response_time $upstream_response_time msec $msec request_time $request_time';

    # Standard upstream definitions
    upstream kagent_ui {
        server 127.0.0.1:8001;
    }
    upstream kagent_ws_backend {
        server 127.0.0.1:8081;
    }
    upstream kagent_backend {
        server 127.0.0.1:8083;
    }

    # OAuth2-Proxy upstream (when enabled)
    {{- if .Values.oauth2Proxy.enabled }}
    upstream oauth2_proxy {
        server 127.0.0.1:4180;
    }
    {{- end }}

    # WebSocket upgrade mapping
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }

    server {
        listen 8080;
        server_name localhost;

        {{- if .Values.oauth2Proxy.enabled }}
        # OAuth2-Proxy endpoints
        location /oauth2/ {
            proxy_pass http://oauth2_proxy;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $server_name;
        }

        # Internal authentication endpoint
        location = /oauth2/auth {
            internal;
            proxy_pass http://oauth2_proxy;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-Uri $request_uri;
            proxy_set_header Content-Length "";
            proxy_pass_request_body off;
        }

        # Protected frontend routes
        location / {
            auth_request /oauth2/auth;
            
            # Extract user information from auth response
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

        # Protected backend routes
        location /api/ {
            auth_request /oauth2/auth;
            
            # Extract user information
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

        # Protected WebSocket routes
        location /api/ws/ {
            auth_request /oauth2/auth;
            
            # Extract user information
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
        # Non-authenticated configuration (same as main branch)
        {{- end }}
    }
}
```

## Container Integration

### Dockerfile Integration
```dockerfile
# Copy nginx configuration
COPY conf/nginx.conf /etc/nginx/nginx.conf
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Set up nginx directories and permissions
RUN mkdir -p /run/nginx/ /var/lib/nginx/tmp/ /var/lib/nginx/logs/ \
    && chown -vR nextjs:nginx /run/nginx \
    && chown -vR nextjs:nginx /var/lib/nginx/

# Expose port 80 (mapped to nginx port 8080)
EXPOSE 80
```

### Supervisor Configuration
```ini
[supervisord]
nodaemon=true
user=nextjs
logfile=/dev/stdout
logfile_maxbytes=0
loglevel=debug

[program:nginx]
command=/usr/sbin/nginx -g "daemon off;"
autostart=true
autorestart=true
startretries=5
numprocs=1
startsecs=0
priority=20
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:nextjs]
command=bun /app/ui/server.js
directory=/app/ui
environment=PORT=8001,HOSTNAME="0.0.0.0",NODE_ENV=production
autostart=true
autorestart=true
startretries=5
numprocs=1
startsecs=0
priority=10
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
```

## Kubernetes Deployment Integration

### ConfigMap Mount (OAuth2-Proxy Branch)
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: ui
        volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/nginx.conf
          subPath: nginx.conf
      volumes:
      - name: nginx-config
        configMap:
          name: kagent-nginx-config
```

### Service Configuration
```yaml
apiVersion: v1
kind: Service
spec:
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

## Advanced Configuration Features

### WebSocket Optimization
```nginx
# WebSocket-specific optimizations
location /api/ws/ {
    proxy_pass http://kagent_ws_backend/api/ws/;
    
    # WebSocket protocol handling
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    
    # Timeout configuration for long-lived connections
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;
    
    # Disable buffering for real-time communication
    proxy_buffering off;
    proxy_cache off;
    
    # Connection handling
    proxy_connect_timeout 5s;
    proxy_socket_keepalive on;
}
```

### Load Balancing Configuration
```nginx
# Multiple upstream servers (for scaling)
upstream kagent_backend {
    server 127.0.0.1:8083 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8084 weight=1 max_fails=3 fail_timeout=30s backup;
    
    # Load balancing method
    least_conn;
    
    # Health checks
    keepalive 32;
    keepalive_requests 100;
    keepalive_timeout 60s;
}
```

### Security Headers
```nginx
# Security headers for all responses
add_header X-Frame-Options DENY;
add_header X-Content-Type-Options nosniff;
add_header X-XSS-Protection "1; mode=block";
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
add_header Referrer-Policy "strict-origin-when-cross-origin";
```

### Rate Limiting
```nginx
# Rate limiting configuration
http {
    # Define rate limiting zones
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;
    
    server {
        # Apply rate limiting to API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            # ... rest of configuration
        }
        
        # Apply stricter rate limiting to auth endpoints
        location /oauth2/ {
            limit_req zone=auth burst=10 nodelay;
            # ... rest of configuration
        }
    }
}
```

### Caching Configuration
```nginx
# Caching for static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary Accept-Encoding;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

### Monitoring and Health Checks
```nginx
# Health check endpoint
location /nginx-health {
    access_log off;
    return 200 "healthy\n";
    add_header Content-Type text/plain;
}

# Metrics endpoint (if using nginx-prometheus-exporter)
location /nginx-metrics {
    access_log off;
    allow 127.0.0.1;
    deny all;
    # Metrics collection configuration
}
```

## Configuration Validation

### Testing Configuration
```bash
# Test nginx configuration syntax
nginx -t -c /etc/nginx/nginx.conf

# Reload configuration without restart
nginx -s reload

# Check nginx status
nginx -s status
```

### Debug Configuration
```nginx
# Enable debug logging
error_log /dev/stderr debug;

# Debug specific modules
error_log /dev/stderr debug;
debug_connection 127.0.0.1;
```

## Performance Tuning

### Worker Process Optimization
```nginx
# Optimize for container environment
worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}
```

### Buffer Optimization
```nginx
# Optimize buffer sizes
client_body_buffer_size 128k;
client_max_body_size 10m;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;
output_buffers 1 32k;
postpone_output 1460;
```

### Connection Optimization
```nginx
# Connection handling optimization
sendfile on;
tcp_nopush on;
tcp_nodelay on;
keepalive_timeout 65;
keepalive_requests 100;
```

## Troubleshooting

### Common Configuration Issues
1. **Permission Denied**: Check file permissions and user context
2. **Port Conflicts**: Verify upstream port configurations
3. **Header Size Limits**: Increase buffer sizes for large headers
4. **WebSocket Failures**: Check connection upgrade handling

### Debug Commands
```bash
# Check nginx configuration
docker exec -it <container> nginx -t

# View nginx logs
docker logs <container> | grep nginx

# Test upstream connectivity
docker exec -it <container> curl -I http://127.0.0.1:8001

# Monitor nginx status
docker exec -it <container> ps aux | grep nginx
```

### Configuration Best Practices
1. **Use Templates**: Leverage Helm templates for dynamic configuration
2. **Environment Variables**: Use environment-specific values
3. **Version Control**: Track configuration changes
4. **Testing**: Validate configuration in staging environments
5. **Monitoring**: Implement comprehensive logging and metrics
6. **Security**: Regular security header and TLS configuration updates

## Conclusion

The nginx configuration in Kagent is sophisticated and purpose-built for:
- **Microservices Routing**: Efficient traffic distribution
- **Authentication Integration**: Seamless OAuth2-Proxy integration
- **WebSocket Support**: Real-time communication capabilities
- **Performance Optimization**: Tuned for container environments
- **Observability**: Comprehensive logging and monitoring
- **Security**: Multiple layers of protection and validation

The dual-configuration approach (main branch vs OAuth2-Proxy branch) provides flexibility for different deployment scenarios while maintaining consistent core functionality. 
