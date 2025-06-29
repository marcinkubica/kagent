# Kagent Architecture Overview: Nginx's Central Role

## System Architecture

Nginx serves as the **critical reverse proxy and routing engine** in the Kagent architecture, acting as the single entry point for all user requests and routing them to appropriate microservices.

## Container Architecture

### UI Container (Port 8080)
```
┌─────────────────────────────────────┐
│           UI Container              │
│  ┌─────────────┐  ┌─────────────┐   │
│  │   Nginx     │  │   Next.js   │   │
│  │  Port 8080  │  │  Port 8001  │   │
│  └─────────────┘  └─────────────┘   │
│           │                         │
│  ┌─────────────────────────────────┐ │
│  │        Supervisor               │ │
│  │    Process Manager              │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Service Distribution
- **UI Container**: Nginx (8080) + Next.js (8001)
- **App Container**: WebSocket (8081) + API Server (8083)
- **Controller Container**: Kubernetes Controller (8083)
- **Tools Container**: MCP Tools Server (8084)

## Nginx Routing Logic

### Core Routing Rules
```nginx
# Frontend routes
location / {
    proxy_pass http://kagent_ui;  # → localhost:8001
}

# Backend API routes
location /api/ {
    proxy_pass http://kagent_backend/api/;  # → localhost:8083
}

# WebSocket routes
location /api/ws/ {
    proxy_pass http://kagent_ws_backend/api/ws/;  # → localhost:8081
}
```

### Upstream Definitions
```nginx
upstream kagent_ui {
    server 127.0.0.1:8001;
}

upstream kagent_ws_backend {
    server 127.0.0.1:8081;
}

upstream kagent_backend {
    server 127.0.0.1:8083;
}
```

## Network Flow

### External Access Path
```
User → Load Balancer/Ingress → Kubernetes Service (Port 80) → 
UI Container Nginx (Port 8080) → Internal Services
```

### Internal Routing
```
Nginx (8080) ┬─ / → Next.js UI (8001)
             ├─ /api/ → App API (8083)
             └─ /api/ws/ → App WebSocket (8081)
```

## Key Features

### 1. Reverse Proxy Capabilities
- **Single Entry Point**: All traffic flows through nginx
- **Service Abstraction**: Hides internal service topology
- **Load Balancing**: Distributes requests across services
- **Health Monitoring**: Tracks upstream service status

### 2. WebSocket Support
- **Connection Upgrade**: Proper WebSocket handshake handling
- **Buffering Control**: Optimized for real-time communication
- **Timeout Management**: Long-lived connection support
- **Header Forwarding**: Maintains connection context

### 3. Header Management
```nginx
proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $server_name;
```

### 4. Logging & Monitoring
- **Access Logs**: Request tracking and analysis
- **Error Logs**: Debugging and troubleshooting
- **Upstream Logs**: Service communication monitoring
- **Container Integration**: stdout/stderr for Kubernetes

## Configuration Management

### Main Branch Configuration
- **Source**: Built-in `nginx.conf` in container image
- **Type**: Static configuration
- **Features**: Complete proxy setup with all routes
- **Authentication**: None (direct access)

### OAuth2-Proxy Branch Configuration
- **Source**: ConfigMap override
- **Type**: Dynamic configuration
- **Features**: Authentication-protected routes
- **Authentication**: OAuth2-Proxy integration

## Service Integration

### Kubernetes Service Mapping
```yaml
ports:
  - port: 80          # External access
    targetPort: 8080  # Nginx port
    name: ui
  - port: 8081        # App WebSocket
    targetPort: 8081
    name: app
  - port: 8083        # Controller API
    targetPort: 8083
    name: controller
```

### Container Communication
- **Localhost**: All services communicate via 127.0.0.1
- **Port-based**: Each service has dedicated port
- **Proxy Headers**: Context forwarded via HTTP headers
- **Authentication**: Optional user context injection

## Performance Considerations

### Optimization Features
- **Connection Pooling**: Efficient upstream connections
- **Buffering Control**: Optimized for different content types
- **Compression**: Automatic content compression
- **Caching**: Strategic caching for static content

### Scalability
- **Horizontal Scaling**: Multiple nginx instances
- **Load Distribution**: Balanced upstream routing
- **Resource Management**: Efficient memory usage
- **Connection Limits**: Configurable connection pooling

## Security Features

### Network Security
- **Internal Communication**: Localhost-only upstream connections
- **Header Validation**: Secure header forwarding
- **Protocol Enforcement**: HTTPS/WSS support
- **Rate Limiting**: Configurable request throttling

### Authentication Integration
- **OAuth2-Proxy**: Seamless authentication integration
- **User Context**: Secure user information forwarding
- **Session Management**: Cookie-based session handling
- **Access Control**: Route-based access restrictions

## Monitoring & Observability

### Logging Strategy
```nginx
log_format main '$time_local $remote_addr - $remote_user - $request $status $body_bytes_sent $http_referer $http_user_agent $http_x_forwarded_for';
log_format upstreamlog '$time_local $remote_addr - $remote_user - $server_name $host to: $upstream_addr: $request $status upstream_response_time $upstream_response_time msec $msec request_time $request_time';
```

### Health Monitoring
- **Readiness Probes**: Container health checks
- **Upstream Status**: Backend service monitoring
- **Error Tracking**: Comprehensive error logging
- **Performance Metrics**: Request timing and throughput

## Conclusion

Nginx is absolutely essential to the Kagent architecture, serving as:
- **Traffic Gateway**: Single point of entry for all requests
- **Service Router**: Intelligent routing to microservices
- **Security Layer**: Authentication and access control
- **Performance Optimizer**: Efficient request handling and caching
- **Observability Hub**: Comprehensive logging and monitoring

Without nginx, the microservices architecture would lose its cohesion, security, and performance optimization capabilities. 
