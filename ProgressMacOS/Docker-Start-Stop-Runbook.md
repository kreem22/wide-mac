# Docker Start/Stop Runbook

## Stop Docker Desktop

### Method 1: Force quit (fastest)
```bash
killall "Docker Desktop"
```

### Method 2: Graceful quit (cleaner)
```bash
osascript -e 'quit app "Docker"'
```

### Verify Docker is stopped
```bash
docker ps 2>&1
```
**Expected output:** `Cannot connect to Docker daemon` or `permission denied`

---

## Verify Llama Still Running (Independent)

After stopping Docker, verify Llama is unaffected:
```bash
lsof -i :8081
```

**Expected output:** Process `llama-server` should still be listening on port 8081

---

## Start Docker Desktop

### Method 1: Open app directly
```bash
open -a Docker
```

### Method 2: Open via Finder
- Go to Applications folder
- Double-click `Docker.app`

### Wait for Docker to start (takes ~10-30 seconds)
```bash
sleep 15 && docker ps
```
**Expected output:** List of containers (confirmation Docker is running)

---

## Check Docker Status

```bash
docker ps
```

- **Success:** Shows container list (computer-use-server should be there)
- **Failure:** `Cannot connect to Docker daemon` (Docker not running yet)

---

## Important Notes

✅ **Stopping Docker does NOT affect:**
- Llama server (runs locally on Mac)
- NemoClaw (already stopped, will be deleted)
- Your Mac's other processes

✅ **Starting Docker does NOT restart containers automatically**
- Containers stopped with `docker stop` remain stopped
- Use `docker start <container-name>` to restart them
- Or use `docker compose up` if using docker-compose

---

## Common Scenarios

### Scenario 1: Stop everything, keep Llama running
```bash
# Stop Docker (Llama unaffected)
killall "Docker Desktop"

# Verify Llama still running
lsof -i :8081

# Result: Llama works, Docker/containers are off
```

### Scenario 2: Restart Docker and containers
```bash
# Start Docker
open -a Docker

# Wait for startup
sleep 20

# Check Docker status
docker ps

# Restart specific container if needed
docker start computer-use-server
```

### Scenario 3: Free up memory (kill non-essential apps)
```bash
# Kill WhatsApp, VSCode, Chrome
pkill -9 WhatsApp
pkill -9 "Code"
pkill -9 "Chrome"

# Stop Docker (optional)
killall "Docker Desktop"

# Verify Llama still works
lsof -i :8081
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| Stop Docker (force) | `killall "Docker Desktop"` |
| Stop Docker (graceful) | `osascript -e 'quit app "Docker"'` |
| Start Docker | `open -a Docker` |
| Check Docker status | `docker ps` |
| Check Llama status | `lsof -i :8081` |
| Wait for Docker startup | `sleep 20 && docker ps` |

---

**Last Updated:** 2026-09-10 22:30 UTC
