# Networking Guide

The Cloudflare tunnel is the recommended approach — it bypasses all port forwarding. This doc covers alternatives and fallbacks for when tunnels aren't available.

## Android Hotspot Port Forwarding

**With root:**
```bash
# Find your hotspot subnet (usually 192.168.43.0/24)
ip addr show wlan0

# Forward port 443 to your laptop on the hotspot
iptables -t nat -A PREROUTING -i rndis0 -p tcp --dport 443 -j DNAT --to-destination 192.168.43.x:443
iptables -t nat -A POSTROUTING -j MASQUERADE
```

**Without root:** Use "Port Forwarder" app from Play Store — set external port 443 to internal 192.168.43.x:443.

**Remember:** This only helps if your carrier isn't behind CGNAT. Check with `curl ifconfig.me` from your phone vs what your carrier shows — if they differ, you're behind CGNAT and need the tunnel approach regardless.

## WSL (Windows + Ubuntu)

Two hops: internet → Windows → WSL.

**Hop 1 — Windows to WSL:**
```powershell
# Run in PowerShell as Admin
# Find WSL IP first:
wsl hostname -I    # e.g. 172.22.x.x

netsh interface portproxy add v4tov4 listenport=8008 listenaddress=0.0.0.0 connectport=8008 connectaddress=172.22.x.x

# Allow through Windows Firewall
netsh advfirewall firewall add rule name="Matrix 8008" dir=in action=allow protocol=tcp localport=8008
```

**Hop 2 — Router to Windows:**
- Log into your router (usually 192.168.1.1 or 192.168.0.1)
- Find port forwarding settings (varies by router)
- Forward external port 443 → your Windows machine's LAN IP:8008

**Gotcha:** WSL IP changes on reboot. Fix with a script in your `.bashrc` or a scheduled task that re-runs the `netsh` command.

## Linux (Native)

Single hop: internet → your machine.

**Port forwarding on router:**
- Router admin → forward 443 → your machine's LAN IP:8008

**If you also need to redirect ports locally** (e.g. 443 → 8008 on the same box):
```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8008

# Make it persistent
sudo apt install iptables-persistent
sudo netfilter-persistent save
```

**Firewall (if ufw is active):**
```bash
sudo ufw allow 8008/tcp
sudo ufw allow 443/tcp
```

## Comparison

| Setup | Hops to configure | CGNAT problem? |
|-------|-------------------|----------------|
| Cloudflare tunnel | 0 (punches out) | No |
| Android hotspot | 1 (phone iptables) | Almost certainly yes |
| WSL | 2 (Windows portproxy + router) | No if home network |
| Native Linux | 1 (router only) | No if home network |

In all cases, the Cloudflare named tunnel bypasses every one of these hops. Port forwarding is the fallback for when you have a cooperative network but tunnels are unavailable.

## Network Gotchas We Hit

- **Coffee shop WiFi**: Client isolation blocks LAN access between devices. Cloudflare quick tunnels also failed because QUIC (UDP) was blocked. Named tunnels would work here via HTTP/2 fallback.
- **WSL2 NAT**: Docker ports bind inside WSL but aren't accessible from the Windows host without `netsh interface portproxy`.
- **Phone hotspot**: Quick tunnels worked here — carrier allowed QUIC outbound.
