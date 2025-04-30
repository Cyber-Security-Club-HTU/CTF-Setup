## Troubleshooting

### Issue 1: Docker API Connection Error
**Problem**: "Unable to connect to Docker API" error in CTFd-whale plugin settings.

**Root Cause**: The Docker Python package version (4.1.0) had compatibility issues with the Docker socket connection.

**Solution**:
1. Upgrade the Docker Python package in the CTFd container:
```bash
docker-compose exec ctfd pip install 'docker>=6.1.0'
```

2. Restart the CTFd container:
```bash
docker-compose restart ctfd
```

3. Verify the connection:
```bash
docker-compose exec ctfd python3 -c "import docker; client = docker.from_env(); print(client.ping())"
```

### Issue 2: Network Configuration
**Problem**: Network configuration issues with overlay networks.

**Solution**:
1. Ensure Docker Swarm is properly initialized
2. Use the correct network configuration in docker-compose.yml
3. Set proper subnet ranges for frp_connect and frp_containers networks

### Issue 3: frpc Configuration
**Problem**: frpc unable to bind to specific IP addresses.

**Solution**:
1. Use 0.0.0.0 as admin_addr in frpc.ini to allow binding to all interfaces
2. Ensure that `server_port` in frpc.ini and `bind_port` in frps.ini are the same.

### Issue 4: Network Attachment Failure
**Problem**: ERROR: for ctfd_frpc_1 Cannot start service frpc: attaching to network failed, make sure your network options are correct and check manager logs: context deadline exceeded

**Solution**:
1. Remove fixed IP from frp_connect network:

```yaml
# Incorrect configuration:
networks:
    frp_containers:
    frp_connect: 172.1.0.3 # Remove fixed IP

# Correct configuration:
networks:
    frp_containers:
    frp_connect:
```

### Verification Steps

1. Check Docker socket mount:
```bash
docker-compose exec ctfd ls -l /var/run/docker.sock
```

2. Verify Docker API connection:
```bash
docker-compose exec ctfd python3 -c "import docker; client = docker.from_env(); print(client.ping())"
```

3. Check frpc logs:
```bash
docker-compose logs frpc
```

### Issue 5: Failed to load resource: the server responded with a status of 403 (FORBIDDEN)

This happens when you try to start a challenge, it will give you:
```
Failed to load resource: the server responded with a status of 403 (FORBIDDEN)
http://ctf.htu.edu.jo/api/v1/plugins/ctfd-whale/container?challenge_id=#
```

**Solution**:

To fix it, make sure to check your ctfd_frp_containers network using `docker networks ls` if its available, and also check on CTFd-whale web settings if its the same name.

### Additional Troubleshooting Tips

#### Network Connectivity Issues
- Verify that the target server can reach the web server on the required ports
- Check firewall rules on both servers
- Ensure Docker overlay networks are properly configured

#### Certificate Issues
- Verify that certificates are correctly mounted in the CTFd container
- Check that certificate paths in environment variables match the actual paths
- Ensure certificates have the correct permissions

#### frp Connection Issues
- Verify that frps is running on the web server
- Check that frpc can reach frps on the specified port
- Ensure the token matches between frps and frpc configurations

#### Challenge Container Issues
- Check Docker logs on the target server for container startup errors
- Verify that the challenge network is properly created and accessible
- Ensure the CTFd-Whale plugin is correctly configured to use the target server
