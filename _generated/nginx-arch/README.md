# Nginx Architecture Documentation

**Generated:** 2025-01-27  
**Branch:** oauth2proxy  
**Purpose:** Comprehensive analysis of nginx's role in Kagent architecture

## Overview

This directory contains detailed documentation and diagrams explaining nginx's critical role as the reverse proxy and authentication gateway in the Kagent system architecture.

## Contents

- `architecture-overview.md` - Complete system architecture with nginx as central routing hub
- `authentication-flow.md` - OAuth2-Proxy integration and authentication sequence
- `configuration-details.md` - Nginx configuration management and routing logic
- `user-journey-analysis.md` - Detailed analysis of user interactions through nginx
- `mermaid-diagrams/` - All mermaid diagram source files
- `nginx-configs/` - Configuration examples and comparisons

## Key Findings

### Nginx's Primary Roles
1. **Reverse Proxy & Request Router** - Single entry point routing to microservices
2. **Authentication Gateway** - OAuth2-Proxy integration for secure access
3. **WebSocket Handler** - Real-time communication support
4. **Load Balancer** - Internal service distribution
5. **Header Manager** - Proxy header forwarding and user context

### Architecture Impact
- **Critical Path**: Every user request flows through nginx
- **Service Integration**: Enables microservices communication
- **Security Layer**: Optional authentication enforcement
- **Performance**: Single-point optimization for all traffic

### Configuration Management
- **Main Branch**: Static built-in configuration
- **OAuth2-Proxy Branch**: Dynamic ConfigMap with authentication
- **Helm Integration**: Template-based deployment configuration

## Quick Start

1. Review `architecture-overview.md` for system understanding
2. Check `authentication-flow.md` for OAuth2-Proxy integration
3. Examine `configuration-details.md` for implementation specifics
4. View mermaid diagrams for visual representation

## Technical Details

- **Container**: UI container (port 8080)
- **Process Manager**: Supervisor manages nginx + Next.js
- **Upstream Services**: UI (8001), API (8083), WebSocket (8081)
- **Authentication**: Optional OAuth2-Proxy (4180)
- **Logging**: stdout/stderr for container visibility 
