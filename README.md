# CoolCTFd: Run CTFd-Whale Smoothly with CTFd

CoolCTFd is a combination of CTFd and CTFd-Whale plugin that is meant to address the issue of the old CTFd-whale plugin version and make it compatible with CTFd.

This project was created for the sole purpose of helping the CTFd community to have a better experience with CTFd-Whale plugin as it was a tedious process to get it working.

## What is CTFd-Whale?

CTFd-Whale is a plugin for CTFd that allows you to run challenges as standalone containers. It provides a way to deploy challenges in Docker containers, making it easier to manage and isolate challenges. For more information, please refer to the [CTFd-Whale GitHub Repository](https://github.com/glzjin/CTFd-Whale).

## Features

- Run challenges in isolated Docker containers
- Support for both standalone and multi-container challenges
- Automatic container lifecycle management
- Integration with frp for challenge access
- Support for both single-server and multi-server deployments

## Quick Start

This repository contains everything you need to run CTFd with CTFd-Whale. Simply clone this repository and follow the deployment guides:

```bash
git clone https://github.com/yourusername/CoolCTFd.git
cd CoolCTFd
```

Then follow either the basic or advanced deployment guide.

## Deployment Options

### Basic Deployment (Single Server)

The basic deployment runs CTFd and all challenges on a single server. This is suitable for smaller CTFs or testing environments.

See [BASIC_DEPLOYMENT.md](BASIC_DEPLOYMENT.md) for detailed instructions.

### Advanced Deployment (Multi-Server)

The advanced deployment separates CTFd and challenges across multiple servers. This is suitable for production environments or larger CTFs.

See [ADVANCED_DEPLOYMENT.md](ADVANCED_DEPLOYMENT.md) for detailed instructions.

### Network Documentation

See [NETWORK_DOCS.md](NETWORK_DOCS.md) for detailed instructions.

## Important Note

CTFd and CTFd-Whale are already included in this repository. There's no need to clone them separately when following the deployment guides.

## CTFd-Whale Plugin Configuration

### Docker Settings

- **API URL**: `unix:///var/run/docker.sock` (single server) or `https://target_server_ip:2376` (multi-server)
- **Credentials**: Leave empty for local Docker or path to client certificates for remote Docker
- **Swarm Nodes**: `linux-1` (or your node label)
- **Use SSL**: Unchecked for local Docker, checked for remote Docker

### Standalone Containers

- **Auto Connect Network**: `ctfd_frp_containers` (single server) or `challenges` (multi-server)
- **Dns Setting**: `1.1.1.1`

### Grouped Containers

- **Auto Connect Containers**: Leave empty
- **Multi-Container Network Subnet**: `174.1.0.0/16`
- **Multi-Container Network Subnet New Prefix**: `24`

### Router Settings

- **Router type**: `frp`
- **API URL**: `http://frpc:7400`
- **Http Domain Suffix**: `your-domain.com`
- **External Http Port**: `8001`
- **Direct IP Address**: `your-domain.com`
- **Direct Minimum Port**: `10000`
- **Direct Maximum Port**: `10100`
- **Frpc config template**:
```
[common]
token = your_token
server_addr = frps
server_port = 7987
admin_addr = 0.0.0.0
admin_port = 7400
```

## Troubleshooting

Check [TROUBLESHOOT.md](TROUBLESHOOT.md) for more information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under Apache License 2.0. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [CTFd](https://github.com/CTFd/CTFd)
- [CTFd-Whale](https://github.com/glzjin/CTFd-Whale)
- [frp](https://github.com/fatedier/frp)