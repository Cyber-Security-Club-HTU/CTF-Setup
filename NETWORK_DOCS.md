# CTFd-Whale Network Documentation

## Overview

This document explains the network architecture and configuration of CTFd-Whale deployment, including how challenges are accessed, how the networking components interact, and the security considerations.

## Network Architecture

### Docker Networks

1. **Internal Container Network** (`ctfd_frp_containers`)
   - Subnet: `172.2.0.0/16`
   - Purpose: Internal communication between challenge containers and frpc
   - Managed by: Docker Swarm
   - Connected Containers:
     - Challenge containers (e.g., `5c606317-8aaf-40c2-8d47-9ef0f3937b1e`)
     - frpc container (`ctfd_frpc_1`)

2. **Swarm Node Network**
   - IP: `10.0.0.125`
   - Purpose: External communication for the cloud instance
   - Used by: Docker Swarm for node communication
   - Get IP from `docker node inspect self --format '{{ .Status.Addr }}'`

3. **FRP Connect Network** (`ctfd_frp_connect`)
   - Subnet: `172.1.0.0/16`
   - Purpose: Communication between FRPS and FRPC
   - Connected Services: CTFd, FRPS, FRPC
   - Access: Internal only

4. **Internal Network**
   - Purpose: Isolated network for sensitive services
   - Connected Services: CTFd, DB, Redis, Nginx
   - Access: No external access, internal only

### Port Mappings

1. **CTFd Main Application**
   - Port: `8000` (internal)
   - Access: Through Nginx (80, 8000)
   - Purpose: Main CTFd interface

2. **Challenge Access**
   - Default: Port 80 (through nginx)
   - Alternative: Port 8001 (direct to frps)
   - Access Pattern: `http://[container-uuid].ctfhtu.duckdns.org`
   - Purpose: Challenge container access through frp proxy

## Component Configuration

### 1. CTFd-Whale Web Settings

The CTFd-whale plugin requires specific web settings to function correctly. These settings are configured in the CTFd admin panel under the "Whale" section.

#### Docker Configuration
```
Auto Connect Network: ctfd_frp_containers
Dns Setting: 1.1.1.1
Swarm Nodes: linux-1
```

**Explanation:**
- **Auto Connect Network**: Specifies which Docker network challenge containers should be connected to. Must match the network name in docker-compose.yml (`ctfd_frp_containers`).
- **Dns Setting**: DNS server to use for challenge containers. Using Cloudflare's 1.1.1.1 for better performance.
- **Swarm Nodes**: Comma-separated list of Docker Swarm node names where challenges can be deployed.

#### Router Configuration
```
Router type: frp
API URL: http://frpc:7400
Http Domain Suffix: ctfhtu.duckdns.org
External Http Port: 8001
Direct IP Address: ctfhtu.duckdns.org
Direct Minimum Port: 10000
Direct Maximum Port: 10500
```

**Explanation:**
- **Router type**: Set to `frp` to use FRP for challenge access.
- **API URL**: URL to access the FRPC admin API. Must be accessible from the CTFd container.
- **Http Domain Suffix**: Domain suffix for challenge subdomains (e.g., `[container-uuid].ctfhtu.duckdns.org`).
- **External Http Port**: Port on FRPS that handles HTTP traffic (must match `vhost_http_port` in frps.ini).
- **Direct IP Address**: IP or domain for direct challenge access.
- **Direct Minimum/Maximum Port**: Port range for direct TCP/UDP access to challenges.

### 2. FRP Configuration

#### frps.ini
```ini
[common]
bind_port = 7987
vhost_http_port = 8001
token = 5e9bf974fe0a8792904ca35da2cded6b
subdomain_host = ctfhtu.duckdns.org
```

**Explanation:**
- **bind_port**: Port used for FRP control protocol between FRPS and FRPC.
- **vhost_http_port**: Port on FRPS that handles HTTP traffic for challenges. Must match "External Http Port" in CTFd-whale settings.
- **token**: Authentication token for FRPS and FRPC communication.
- **subdomain_host**: Domain suffix for challenge subdomains. Must match "Http Domain Suffix" in CTFd-whale settings.

#### frpc.ini
```ini
[common]
token = 5e9bf974fe0a8792904ca35da2cded6b
server_addr = frps
server_port = 7987
admin_addr = 0.0.0.0
admin_port = 7400
```

**Explanation:**
- **token**: Must match the token in frps.ini.
- **server_addr**: Hostname of the FRPS server.
- **server_port**: Must match bind_port in frps.ini.
- **admin_addr**: Address to bind the admin API (0.0.0.0 for all interfaces).
- **admin_port**: Port for the admin API (must match "API URL" port in CTFd-whale settings).

### 3. Nginx Configuration

The nginx configuration (`http.conf`) handles two types of traffic:

1. **Main CTFd Server**
```nginx
server {
    listen 80;
    listen 8000;
    server_name 84.8.108.50;
    # Proxies to CTFd main application
}
```

2. **Challenge Subdomain Server**
```nginx
server {
    listen 80;
    server_name *.ctfhtu.duckdns.org;
    # Proxies to frps for challenge access
}
```

## Challenge Access Flow

1. **Default Access (Port 80)**
```
User Request -> Nginx (*.ctfhtu.duckdns.org) -> frps:8001 -> frpc -> Challenge Container
```

2. **Direct Access (Port 8001)**
```
User Request -> frps:8001 -> frpc -> Challenge Container
```

3. **Main CTFd Access (Port 8000)**
```
User Request -> CTFd Main Application (8000)
```

## Nginx Routing and Headers

### Proxy Chain and Headers

The routing of challenge requests through nginx to frp requires specific headers to be set correctly. Here's how it works:

1. **Header Importance**:
```conf
location / {
  proxy_pass http://frps:8001;
  proxy_redirect off;
  proxy_set_header Host $host;           # Crucial for frp routing
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Host $server_name;
  proxy_set_header X-Forwarded-Proto $scheme;
  ...
}
```

2. **Why Headers Matter**:
- `Host` header: Tells frp which subdomain is being requested
- `X-Real-IP`: Preserves the original client IP
- `X-Forwarded-For`: Maintains the request chain
- `X-Forwarded-Host`: Preserves the original host
- `X-Forwarded-Proto`: Maintains the protocol information

3. **Routing Flow**:
```
User Request (*.ctfhtu.duckdns.org:80)
-> Nginx (port 80)
-> frps (port 8001)
-> frpc
-> Challenge Container
```

4. **Common Issues**:
- Moving headers to http block can break routing
- Missing Host header prevents frp from identifying the correct challenge
- Incorrect header order can affect proxy chain

5. **Port 8001 Direct Access**:
When accessing port 8001 directly:
```
User Request (*.ctfhtu.duckdns.org:8001) -> frps -> frpc -> Challenge Container
```
- Bypasses nginx completely
- Goes straight to frps
- Works even if nginx configuration has issues

## Troubleshooting

### Useful Commands

1. **Check Network Connectivity**
```bash
docker network inspect ctfd_frp_containers
docker network inspect ctfd_frp_connect
```

2. **Check FRP Status**
```bash
docker-compose logs frpc
docker-compose logs frps
```

3. **Check Nginx Configuration**
```bash
docker-compose exec nginx nginx -t
```