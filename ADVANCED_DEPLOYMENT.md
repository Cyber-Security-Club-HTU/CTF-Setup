# Advanced Deployment Guide

This guide will help you deploy CTFd and CTFd-Whale in a multi-server configuration, with CTFd running on one server and challenge containers on another.

## Prerequisites

Before proceeding with this advanced deployment, make sure you have:
- Successfully deployed CTFd with CTFd-Whale on a single server
- Basic understanding of Docker and frp
- Two servers with network connectivity between them

## Architecture Overview

In this advanced deployment, we'll use two separate machines:
- **Web Server**: Hosts CTFd and frps
- **Target Server**: Hosts challenge containers and frpc

![Architecture](CTFd/plugins/ctfd-whale/docs/imgs/arch.png)

## Target Server Setup

### 1. Initialize Docker Swarm

```bash
docker swarm init
docker node update --label-add "name=linux-1" $(docker node ls -q)
```

### 2. Secure Docker with TLS

Follow the [Docker documentation](https://docs.docker.com/engine/security/protect-access/#use-tls-https-to-protect-the-docker-daemon-socket) to set up TLS certificates for secure communication.

> **IMPORTANT**: Protect your certificates carefully. Anyone with access to these certificates can take over the user running `dockerd` (often root).

### 3. Configure Docker Service

Copy the systemd service file to prevent it from being overwritten:

```bash
cp /lib/systemd/system/docker.service /etc/systemd/system/docker.service
```

Edit the file to add TLS configuration:

```systemd
ExecStart=/usr/bin/dockerd \
    --tlsverify \
    --tlscacert=/etc/docker/certs/ca.pem \
    --tlscert=/etc/docker/certs/server-cert.pem \
    --tlskey=/etc/docker/certs/server-key.pem \
    -H tcp://0.0.0.0:2376 \
    -H unix:///var/run/docker.sock
```

Reload and restart Docker:

```bash
systemctl daemon-reload
systemctl restart docker
```

### 4. Create Challenge Network

```bash
docker network create --driver overlay --attachable challenges
```

### 5. Install and Configure frps

Download and install frp:

```bash
wget https://github.com/fatedier/frp/releases/download/v0.37.0/frp_0.37.0_linux_amd64.tar.gz
tar xzvf frp_0.37.0_linux_amd64.tar.gz
cd frp_0.37.0_linux_amd64
mkdir /etc/frp
```

Create `frps.ini` with the following content:

```ini
[common]
bind_port = 7987
vhost_http_port = 8001
token = your_token
subdomain_host = your-domain.com
```

Set up frps as a systemd service:

```bash
cp systemd/frps.service /etc/systemd/system
systemctl daemon-reload
systemctl enable frps
systemctl start frps
```

### 6. Configure frpc

Run frpc in a Docker container connected to the challenge network:

```bash
docker run -it --restart=always -d --network challenges -p 7400:7400 frankli0324/frp:frpc \
    --server_addr=web_server_ip:web_server_port \
    --server_port=7987 \
    --admin_addr=0.0.0.0 \
    --admin_port=7400 \
    --admin_user=username \
    --admin_pwd=password \
    --token=your_token
```

Alternatively, you can use docker-compose for better management:

```yaml
version: '3'
services:
  frpc:
    image: frankli0324/frp:frpc
    restart: always
    networks:
      - challenges
    ports:
      - 7400:7400
    command:
      - --server_addr=web_server_ip:web_server_port
      - --server_port=7987
      - --admin_addr=0.0.0.0
      - --admin_port=7400
      - --admin_user=username
      - --admin_pwd=password
      - --token=your_token

networks:
  challenges:
    external: true
```

## Web Server Setup

### 1. Clone CTFd 3.5.3

```bash
git clone -b 3.5.3 https://github.com/CTFd/CTFd.git
cd CTFd
```

> **Note**: CTFd-Whale is already included in this repository as a plugin. There's no need to clone it separately.

### 2. Configure Docker with TLS Certificates

Copy your client certificates to the CTFd directory and update the docker-compose.yml file to mount them:

```yaml
services:
  ctfd:
    # ... existing configuration ...
    volumes:
      - ./certs:/certs:ro
    environment:
      - DOCKER_TLS_CERTDIR=/certs
      - DOCKER_HOST=tcp://target_server_ip:2376
      - DOCKER_TLS_VERIFY=1
      - DOCKER_CERT_PATH=/certs
```

### 3. Configure frps

Create `conf/frp/frps.ini` with the following content:

```ini
[common]
bind_port = 7987
vhost_http_port = 8001
token = your_token
subdomain_host = your-domain.com
```

### 4. Update docker-compose.yml

Add the frps service to your docker-compose.yml:

```yaml
services:
  # ... existing services ...

  frps:
    image: glzjin/frp
    restart: always
    volumes:
      - ./conf/frp:/conf
    entrypoint:
      - /usr/local/bin/frps
      - -c
      - /conf/frps.ini
    ports:
      - 10000-10100:10000-10100
      - 8001:8001
    networks:
        default:
        frp_connect:

networks:
    # ... existing networks ...
    frp_connect:
        driver: overlay
        internal: true
        ipam:
            config:
                - subnet: 172.1.0.0/16
```

### 5. Start Containers

```bash
docker-compose up -d
```

### 6. Configure CTFd-Whale Plugin

Access the Whale Configuration page at `/plugins/ctfd-whale/admin/settings` and configure the following settings:

#### Docker Settings
- **API URL**: `tcp://target_server_ip:2376`
- **Credentials**: Leave empty
- **Swarm Nodes**: `linux-1` or `windows-1`
- **Use SSL**: Checked

#### Standalone Containers
- **Auto Connect Network**: `challenges`
- **Dns Setting**: `1.1.1.1`

#### Grouped Containers
- **Auto Connect Containers**: Leave empty
- **Multi-Container Network Subnet**: `174.1.0.0/16`
- **Multi-Container Network Subnet New Prefix**: `24`

#### Router Settings
- **Router type**: `frp`
- **API URL**: `http://username:password@target_server_ip:7400`
- **Http Domain Suffix**: `your-domain.com`
- **External Http Port**: `8001`
- **Direct IP Address**: `your-domain.com`
- **Direct Minimum Port**: `10000`
- **Direct Maximum Port**: `10100`
- **Frpc config template**:
```ini
[common]
token = your_token
server_addr = web_server_ip
server_port = 7987
admin_addr = 0.0.0.0
admin_port = 7400
admin_user = username
admin_pwd = password
```

![Whale Configuration 1](CTFd/plugins/ctfd-whale/docs/imgs/whale-config1.png)
![Whale Configuration 2](CTFd/plugins/ctfd-whale/docs/imgs/whale-config2.png)
![Whale Configuration 3](CTFd/plugins/ctfd-whale/docs/imgs/whale-config3.png)