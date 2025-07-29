# Podman Configuration Summary

This document summarizes the changes made to configure your container setup to use Podman instead of Docker.

## Files Modified

### 1. `docker-start.sh`
- Updated all `docker-compose` commands to `podman-compose`
- Updated script title and descriptions to reference Podman
- All functionality remains the same, just using Podman backend

### 2. `README.md`
- Updated installation instructions to reference Podman instead of Docker
- Updated example commands to use `podman` and `podman-compose`
- Updated "Quick Start Commands" section

### 3. VSCode Settings (`../../AppData/Roaming/Code/User/settings.json`)
- Added `"docker.dockerPath": "podman"` to use Podman as Docker backend
- Added `"docker.composeCommand": "podman-compose"` for compose operations
- Updated compose command template to use `podman-compose`

## Prerequisites

Before using this setup, ensure you have Podman installed:

### Windows
```bash
# Install Podman Desktop or use package manager
winget install RedHat.Podman-Desktop
```

### macOS
```bash
# Using Homebrew
brew install podman
```

### Linux (Ubuntu/Debian)
```bash
# Add repository and install
sudo apt-get update
sudo apt-get install podman podman-compose
```

## Podman-Compose Installation

If `podman-compose` is not available, you can install it separately:

```bash
# Using pip
pip install podman-compose

# Or using system package manager (Linux)
sudo apt-get install podman-compose  # Ubuntu/Debian
sudo dnf install podman-compose      # Fedora/RHEL
```

## Usage

All existing commands work the same way:

```bash
# Start infrastructure
./docker-start.sh infrastructure

# Start full service
./docker-start.sh full

# Interactive mode
./docker-start.sh
```

## Verification

To verify Podman is working correctly:

```bash
# Check Podman version
podman --version

# Check podman-compose version
podman-compose --version

# Test basic functionality
podman run hello-world
```

## Benefits of Podman

- **Rootless containers**: Run containers without root privileges
- **No daemon**: Podman doesn't require a background daemon
- **Docker compatibility**: Drop-in replacement for most Docker commands
- **Security**: Enhanced security with user namespaces
- **Systemd integration**: Better integration with systemd services

## Troubleshooting

### Common Issues

1. **Permission issues**: Podman runs rootless by default, which is more secure
2. **Port binding**: May need to adjust port ranges for rootless operation
3. **Volume mounts**: Path handling might differ slightly from Docker

### Solutions

```bash
# If you need to run as root (not recommended)
sudo podman-compose up -d

# Check Podman system info
podman system info

# Reset Podman if needed
podman system reset
```

## Rollback to Docker

If you need to rollback to Docker, simply:

1. Revert the VSCode settings changes
2. Replace `podman-compose` with `docker-compose` in `docker-start.sh`
3. Update README.md references back to Docker

The `docker-compose.yml` file doesn't need changes as it's compatible with both systems.
