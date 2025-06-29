# User Journey Analysis: Nginx's Role

## Overview
This document analyzes how users interact with the Kagent system through nginx as the primary gateway.

## User Journey Types

### 1. Web UI Access
**Path**: User → Load Balancer → Service → Nginx → Next.js
- Nginx routes `/` to Next.js on port 8001
- Handles static assets and dynamic content
- Optional authentication via OAuth2-Proxy

### 2. API Interactions
**Path**: User → Load Balancer → Service → Nginx → App Server
- Nginx routes `/api/*` to App Server on port 8083
- Forwards user context headers
- Handles authentication and authorization

### 3. Real-time Communication
**Path**: User → Load Balancer → Service → Nginx → WebSocket Server
- Nginx routes `/api/ws/*` to WebSocket Server on port 8081
- Manages WebSocket connection upgrades
- Maintains long-lived connections

## Authentication Flow Impact

### Without OAuth2-Proxy (Main Branch)
```
User Request → Nginx → Direct Service Access
```

### With OAuth2-Proxy (OAuth2-Proxy Branch)
```
User Request → Nginx → auth_request → OAuth2-Proxy → Service Access
                ↓
        Authentication Required → OAuth Provider → User Login
```

## Performance Characteristics

### Response Times
- **Static Content**: <50ms (cached)
- **API Calls**: 100-500ms (depending on backend)
- **WebSocket**: <10ms connection establishment
- **Authentication**: +50-100ms overhead

### Scalability
- Single nginx handles thousands of concurrent connections
- Efficient upstream load balancing
- Connection pooling for backend services

## User Experience Impact

### Positive Aspects
- **Single Entry Point**: Consistent access pattern
- **Transparent Proxy**: Users unaware of backend complexity
- **Real-time Features**: WebSocket support enables live updates
- **Security**: Optional authentication without user friction

### Potential Issues
- **Single Point of Failure**: Nginx outage affects all access
- **Latency**: Additional proxy hop adds minimal latency
- **Authentication Redirects**: OAuth flow requires user interaction

## Monitoring User Experience

### Key Metrics
- Request response times
- Error rates by endpoint
- WebSocket connection success rates
- Authentication success rates

### User-Facing Endpoints
- `/` - Main application interface
- `/api/version` - Health check
- `/api/agents` - Agent management
- `/api/ws/agents` - Real-time agent communication
- `/oauth2/sign_in` - Authentication entry point

## Conclusion

Nginx serves as the critical user experience gateway, providing:
- Unified access to all Kagent services
- Optional authentication integration
- Real-time communication support
- Performance optimization through caching and connection pooling 
