# Systemd Service Setup

This guide shows how to configure frederick-matrix to run automatically on system startup using systemd.

## Overview

The systemd service will:
- Start the Matrix mesh (Synapse, Element, Cloudflare tunnel) on boot
- Monitor the services and restart them if they crash
- Manage logs through journalctl
- Run under your user account (no root needed for the service itself)

## Prerequisites

- Docker Engine installed and running
- Your user added to the `docker` group: `sudo usermod -aG docker $USER`
- Frederick-matrix already set up and working (run `make setup` first)
- GitHub CLI authenticated (`gh auth login`)

## Installation Steps

### 1. Create the Systemd Service File

Create a user-level systemd service file at `~/.config/systemd/user/frederick-matrix.service`:

```bash
mkdir -p ~/.config/systemd/user
```

Copy this template and adjust the paths:

```ini
[Unit]
Description=Frederick Matrix Mesh Chat
After=docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/home/YOUR_USERNAME/workshed/managed_repos/frederick-matrix
ExecStart=/home/YOUR_USERNAME/workshed/managed_repos/frederick-matrix/start.sh
Restart=always
RestartSec=10

# Environment variables (if needed)
# Environment="PATH=/usr/local/bin:/usr/bin:/bin"

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=frederick-matrix

[Install]
WantedBy=default.target
```

**Important:** Replace `YOUR_USERNAME` with your actual username.

For this machine, the exact path would be:
```
WorkingDirectory=/home/david/workshed/managed_repos/frederick-matrix
ExecStart=/home/david/workshed/managed_repos/frederick-matrix/start.sh
```

### 2. Make start.sh Executable

Ensure the start script has execute permissions:

```bash
chmod +x /home/david/workshed/managed_repos/frederick-matrix/start.sh
```

### 3. Enable Lingering (Important!)

User services only run when you're logged in by default. To make them run on boot:

```bash
sudo loginctl enable-linger $USER
```

This allows your user services to start at boot without you being logged in.

### 4. Reload Systemd Configuration

Tell systemd about the new service:

```bash
systemctl --user daemon-reload
```

### 5. Enable the Service

Enable the service to start on boot:

```bash
systemctl --user enable frederick-matrix.service
```

### 6. Start the Service

Start it now (without rebooting):

```bash
systemctl --user start frederick-matrix.service
```

## Verification

### Check Service Status

```bash
systemctl --user status frederick-matrix.service
```

You should see:
- `Active: active (running)` in green
- Recent log entries showing the tunnel URL being published

### View Logs

```bash
# View recent logs
journalctl --user -u frederick-matrix.service

# Follow logs in real-time
journalctl --user -u frederick-matrix.service -f

# Last 50 lines
journalctl --user -u frederick-matrix.service -n 50
```

### Check Docker Containers

```bash
docker ps
```

You should see three containers running:
- `synapse`
- `element`
- `cloudflared`

### Test the Services

- Element: http://localhost:8080
- Synapse: http://localhost:8008
- Check `server.json` for the published tunnel URL

## Management Commands

### Stop the Service

```bash
systemctl --user stop frederick-matrix.service
```

### Restart the Service

```bash
systemctl --user restart frederick-matrix.service
```

### Disable Autostart (but keep it installed)

```bash
systemctl --user disable frederick-matrix.service
```

### Re-enable Autostart

```bash
systemctl --user enable frederick-matrix.service
```

### Reload Configuration After Editing

If you edit the service file:

```bash
systemctl --user daemon-reload
systemctl --user restart frederick-matrix.service
```

## Troubleshooting

### Service Won't Start

1. **Check the service status for errors:**
   ```bash
   systemctl --user status frederick-matrix.service
   ```

2. **Check logs:**
   ```bash
   journalctl --user -u frederick-matrix.service -n 100
   ```

3. **Verify paths in the service file are correct**

4. **Test start.sh manually:**
   ```bash
   cd /home/david/workshed/managed_repos/frederick-matrix
   ./start.sh
   ```
   Press Ctrl+C to stop, then try the systemd service again.

### Docker Permission Errors

If you see "permission denied" errors for Docker:

```bash
# Verify you're in the docker group
groups | grep docker

# If not, add yourself (then log out/in)
sudo usermod -aG docker $USER

# Restart docker
sudo systemctl restart docker
```

### Service Doesn't Start on Boot

1. **Verify lingering is enabled:**
   ```bash
   loginctl show-user $USER | grep Linger
   ```
   Should show `Linger=yes`

2. **Re-enable if needed:**
   ```bash
   sudo loginctl enable-linger $USER
   ```

3. **Check service is enabled:**
   ```bash
   systemctl --user is-enabled frederick-matrix.service
   ```
   Should output `enabled`

### GitHub API Authentication Fails

The service needs access to your GitHub credentials. If `gh auth login` was done in your interactive shell, you may need to ensure the credentials are accessible to the service.

Check:
```bash
gh auth status
```

If issues persist, you might need to set up a GitHub token in the service file:
```ini
[Service]
Environment="GH_TOKEN=your_github_personal_access_token"
```

### Tunnel URL Not Publishing

1. **Check cloudflared logs:**
   ```bash
   docker logs cloudflared
   ```

2. **Verify start.sh can detect the URL:**
   ```bash
   docker compose logs cloudflared 2>&1 | grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' | tail -1
   ```

3. **Check GitHub API access:**
   ```bash
   gh api repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/contents/server.json
   ```

## Advanced Configuration

### Custom Environment Variables

If you need to set environment variables (PATH, tokens, etc.):

```ini
[Service]
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
Environment="GH_TOKEN=ghp_xxxxxxxxxxxxx"
Environment="POLL_INTERVAL=120"
```

### Resource Limits

Limit CPU or memory usage:

```ini
[Service]
CPUQuota=50%
MemoryMax=2G
```

### Email Notifications on Failure

Set up email alerts when the service fails (requires configured mail system):

```ini
[Service]
OnFailure=status-email@%n.service
```

### Running Multiple Instances

If you want to run multiple frederick-matrix instances, create separate service files:
- `frederick-matrix-1.service`
- `frederick-matrix-2.service`

Each should have different:
- WorkingDirectory
- Port mappings in docker-compose.yml

## Uninstalling the Service

To completely remove the systemd service:

```bash
# Stop and disable
systemctl --user stop frederick-matrix.service
systemctl --user disable frederick-matrix.service

# Remove the service file
rm ~/.config/systemd/user/frederick-matrix.service

# Reload systemd
systemctl --user daemon-reload

# Optionally disable lingering if you don't need it for other services
sudo loginctl disable-linger $USER
```

## Integration with Makefile

You can add these targets to the Makefile for convenience:

```makefile
.PHONY: service-install service-start service-stop service-status service-logs

service-install:
	@echo "Installing systemd service..."
	@mkdir -p ~/.config/systemd/user
	@echo "Please manually create ~/.config/systemd/user/frederick-matrix.service"
	@echo "See docs/systemd-service.md for the template"

service-enable:
	sudo loginctl enable-linger $(USER)
	systemctl --user daemon-reload
	systemctl --user enable frederick-matrix.service
	@echo "Service enabled! Start with: make service-start"

service-start:
	systemctl --user start frederick-matrix.service

service-stop:
	systemctl --user stop frederick-matrix.service

service-restart:
	systemctl --user restart frederick-matrix.service

service-status:
	systemctl --user status frederick-matrix.service

service-logs:
	journalctl --user -u frederick-matrix.service -f
```

Then use:
```bash
make service-enable    # One-time setup
make service-start     # Start the service
make service-status    # Check if it's running
make service-logs      # Watch logs
```

## See Also

- [Operations Guide](operations.md) - Day-to-day management commands
- [Architecture](architecture.md) - How the system works
- [Troubleshooting](operations.md#troubleshooting) - Common issues

## Quick Reference

```bash
# Enable on boot (one-time setup)
sudo loginctl enable-linger $USER
systemctl --user enable frederick-matrix.service

# Start/stop/restart
systemctl --user start frederick-matrix.service
systemctl --user stop frederick-matrix.service
systemctl --user restart frederick-matrix.service

# Status and logs
systemctl --user status frederick-matrix.service
journalctl --user -u frederick-matrix.service -f

# Disable autostart
systemctl --user disable frederick-matrix.service
```
