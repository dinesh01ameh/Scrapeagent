# Port Management Rules - SwissKnife AI Scraper

## 🔌 Port Configuration Rule

**PERMANENT PORT: 8601**

SwissKnife AI Scraper is permanently configured to use port **8601** for all operations. This port is hardcoded in the configuration and cannot be changed without modifying the source code.

## 🛡️ Port Conflict Resolution

### Automatic Port Management

When starting the server, the system automatically:

1. **Checks port 8601 availability**
2. **Identifies conflicting processes**
3. **Terminates conflicting processes** (with user confirmation for non-SwissKnife processes)
4. **Ensures port is available** before starting the server

### Startup Sequence

```
🚀 Starting SwissKnife AI Scraper...
🔍 Checking port 8601 availability...
⚠️ Port 8601 is busy
🔄 Attempting to free port 8601...
✅ Port 8601 is now available
🌐 Starting web server on port 8601...
```

## 🔧 Manual Port Management

### Using Make Commands

```bash
# Check port status
make check-port

# Kill processes on port 8601
make kill-port

# Clean restart (recommended)
make restart-clean

# Check system and port status
make check
```

### Using Python Scripts

```bash
# Check port status
python scripts/port_check.py status

# Kill processes on port 8601
python scripts/port_check.py kill

# Clean up old SwissKnife processes
python scripts/port_check.py cleanup

# Prepare port for use (recommended)
python scripts/port_check.py prepare

# Get detailed port information
python scripts/port_check.py info
```

### Using API Endpoints

Once the server is running:

```bash
# Check port status via API
curl http://localhost:8601/api/v1/admin/port/status

# Clean up port conflicts via API
curl -X POST http://localhost:8601/api/v1/admin/port/cleanup
```

## 🔄 Restart Procedures

### Standard Restart
```bash
# Method 1: Using make
make restart-clean

# Method 2: Using startup script
python scripts/start.py

# Method 3: Manual steps
python scripts/port_check.py prepare
python main.py
```

### Emergency Restart
If the server is unresponsive:

```bash
# Kill all processes on port 8601
make kill-port
# or
python scripts/port_check.py kill

# Clean up old processes
python scripts/port_check.py cleanup

# Start fresh
make start
```

## 🚨 Conflict Resolution Strategies

### 1. SwissKnife Process Detection
- Automatically detects existing SwissKnife processes
- Gracefully terminates old instances
- No user confirmation required

### 2. External Process Handling
- Identifies non-SwissKnife processes using port 8601
- Requests user confirmation before termination
- Provides process information (PID, name, command)

### 3. Graceful Shutdown
- Attempts SIGTERM first (graceful shutdown)
- Waits up to 10 seconds for process termination
- Falls back to SIGKILL if necessary
- Verifies port availability after termination

## 📊 Port Status Information

The system provides detailed port status including:

```json
{
  "port": 8601,
  "available": false,
  "process": {
    "pid": 12345,
    "name": "python",
    "cmdline": ["python", "main.py"],
    "status": "LISTEN"
  },
  "timestamp": 1703123456.789
}
```

## 🔒 Security Considerations

### Process Identification
- Only terminates processes that are clearly identified
- Provides detailed process information before termination
- Requires confirmation for non-SwissKnife processes

### Safe Termination
- Uses proper signal handling (SIGTERM → SIGKILL)
- Waits for graceful shutdown before force killing
- Verifies port release after termination

## 🐳 Docker Configuration

Port 8601 is also configured in Docker:

```yaml
# docker-compose.yml
ports:
  - "8601:8601"
```

```dockerfile
# Dockerfile
EXPOSE 8601
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8601"]
```

## 🔧 Configuration Files

Port 8601 is hardcoded in:

- `config/settings.py` - Default port setting
- `.env.example` - Environment template
- `docker-compose.yml` - Docker port mapping
- `Dockerfile` - Container port exposure
- `Makefile` - Development commands

## 🚀 Quick Reference

| Action | Command |
|--------|---------|
| Start server | `make start` |
| Clean restart | `make restart-clean` |
| Check port | `make check-port` |
| Kill port processes | `make kill-port` |
| Port status API | `GET /api/v1/admin/port/status` |
| Port cleanup API | `POST /api/v1/admin/port/cleanup` |

## 🆘 Troubleshooting

### Port Still Busy After Cleanup
```bash
# Check what's using the port
python scripts/port_check.py info

# Force kill all processes
sudo lsof -ti:8601 | xargs kill -9

# Verify port is free
python scripts/port_check.py status
```

### Permission Denied Errors
```bash
# Run with elevated privileges if needed
sudo python scripts/port_check.py kill

# Or identify the process owner
ps aux | grep 8601
```

### Multiple SwissKnife Instances
```bash
# Clean up all old instances
python scripts/port_check.py cleanup

# Verify cleanup
ps aux | grep -i swissknife
```

## 📝 Notes

- Port 8601 is chosen to avoid conflicts with common services
- The port management system is designed to be robust and safe
- All port operations are logged for debugging
- The system prioritizes graceful shutdowns over force kills
- Docker containers automatically use the correct port configuration
