# CTFd Whale Plugin - TODO List

## Core Issues
- [ ] Fix container renewal race condition in control.py
  - Currently, multiple users can trigger container renewal simultaneously, causing conflicts
  - Need to add proper locking mechanism in try_renew_container

- [ ] Add proper Docker daemon restart handling
  - When Docker daemon restarts, containers become inaccessible
  - Need to implement reconnection and container state recovery

- [ ] Fix network cleanup in grouped containers
  - Network resources aren't properly cleaned up when containers are removed
  - Need to ensure network cleanup in remove_container function

- [ ] Add transaction handling for container operations
  - Database operations in DBContainer lack proper transaction management
  - Need to wrap critical operations in transactions

## New Features
- [ ] Add container health checks
  - Currently no way to monitor container health
  - Need to implement periodic checks and auto-recovery

- [ ] Implement container usage statistics
  - No tracking of container usage patterns
  - Need to add metrics for container uptime, resource usage, and user activity