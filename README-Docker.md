# Directory Server Docker Setup

This directory contains Docker configuration files to run the directory browser server in a containerized environment.

## 🐳 **Quick Start**

### **Basic Setup (Development)**
```bash
# Build and run the directory server
docker-compose up --build

# Access the application
# Open http://localhost:5000 in your browser (or http://localhost:<OUTGOING_PORT> if you set OUTGOING_PORT)
```

### **Production Setup**
```bash
# Run with nginx reverse proxy
docker-compose --profile production up --build

# Access via nginx
# Open http://localhost:80 in your browser
```

## 📁 **File Structure**

```
webscraping/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Multi-service orchestration
├── requirements.txt        # Python dependencies
├── nginx.conf             # Reverse proxy configuration
├── .dockerignore          # Build context exclusions
├── directory_server.py    # Flask application
├── directory_client.html  # Frontend interface
└── README-Docker.md       # This file
```

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTGOING_PORT` | `5000` | Host port mapped to the app (compose: `${OUTGOING_PORT:-5000}:5000`; container still listens on 5000) |
| `MEDIA_DIR` | `/share/data` | Host directory bind-mounted into the container as **`/mnt/data`** (fixed path in `directory_server.py`) |
| `DIR_BROWSER_LOG_LEVEL` | `CRITICAL` | Python logging level. `CRITICAL` hides almost all log lines (only fatal startup/errors use `critical`). Use `INFO` or `DEBUG` when troubleshooting. |
| `DIR_BROWSER_FLASK_DEBUG` | `False` | Flask debug mode (true/false). The app runs with **reloader disabled** so Docker does not exit with code 0 when debug is on. |

### **Volume Mounts**

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `${MEDIA_DIR:-/share/data}` | `/mnt/data` | Directory to browse (read-write in compose) |

## 🚀 **Usage Commands**

### **Development Mode**
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs (app writes to stdout; Docker captures this)
docker-compose logs -f directory-server

# Stop services
docker-compose down
```

### **Production Mode**
```bash
# Start with nginx reverse proxy
docker-compose --profile production up -d

# Check service status
docker-compose ps

# View all logs
docker-compose logs -f
```

### **Individual Container Management**
```bash
# Build image only
docker-compose build

# Rebuild without cache
docker-compose build --no-cache

# Execute commands in container
docker-compose exec directory-server python -c "print('Hello from container')"

# Access container shell
docker-compose exec directory-server bash
```

## 🔍 **Health Monitoring**

### **Health Check Endpoint**
```bash
# Check server health
curl http://localhost:5000/api/health   # use your OUTGOING_PORT if not 5000

# Check via nginx (production)
curl http://localhost/health
```

### **Debug Endpoints**
```bash
# View active requests
curl http://localhost:5000/api/debug/requests   # use your OUTGOING_PORT if not 5000

# Server statistics
docker stats directory-browser
```

## 🔒 **Security Considerations**

### **Container Security**
- ✅ Non-root user (`appuser`)
- ✅ Read-only volume mounts where possible
- ✅ Health checks enabled
- ✅ Resource limits (configurable)

### **Network Security**
- ✅ Internal network isolation
- ✅ Reverse proxy with security headers
- ✅ HTTPS ready (nginx configuration included)

## 📊 **Performance Tuning**

### **Resource Limits**
Add to `docker-compose.yml`:
```yaml
services:
  directory-server:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### **Nginx Optimization**
- Buffer settings configured for large files
- Timeout settings for slow connections
- Security headers enabled

## 🛠️ **Troubleshooting**

### **Common Issues**

**1. Permission Denied (media mount)**
```bash
# Check volume permissions
ls -la /mnt/data

# Fix permissions if needed
sudo chmod 755 /mnt/data
```

**2. Port Already in Use**
```bash
# Check what's using your outgoing port (default 5000)
sudo netstat -tlnp | grep :5000

# Change the published port via environment (default 5000)
# OUTGOING_PORT=5001 docker-compose up
```

**3. Container Won't Start**
```bash
# Check container logs
docker-compose logs directory-server

# Check health status
docker-compose ps
```

**4. Exit code 1 and little or nothing in Logs**

- In Portainer, clear any **log filter** (empty filter can hide lines).
- Ensure you **rebuilt the image** after code changes (`docker compose build --no-cache`).
- On the host: `docker logs --tail 200 <container_name>` — startup messages go to **stdout**; fatals print `FATAL:` to stdout and stderr.
- Set `DIR_BROWSER_LOG_LEVEL=INFO` temporarily so normal `logger` lines appear (default `CRITICAL` hides most of them).

### **Debug Commands**
```bash
# Inspect container
docker inspect directory-browser

# Check container resources
docker stats directory-browser

# View container processes
docker-compose exec directory-server ps aux
```

## 🔄 **Updates and Maintenance**

### **Updating the Application**
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### **Log rotation**
The app logs to **stdout**; Docker stores that stream (default `json-file` driver). Use `docker logs` / Portainer logs, or configure a **logging driver** / **log opts** on the service (e.g. `json-file` with `max-size` and `max-file` in `docker-compose.yml`) to cap disk use.

## 📝 **Customization**

### **Custom Configuration**
Set **`MEDIA_DIR`** in the stack environment to the host folder you want to expose; inside the container it is always mounted at **`/mnt/data`**. The app does not use a `config.ini` file.

### **Custom Nginx Configuration**
Modify `nginx.conf` for your specific needs:
- SSL certificates
- Custom domains
- Rate limiting
- Caching rules

## 🆘 **Support**

For issues or questions:
1. Check container logs: `docker-compose logs`
2. Verify health endpoint: `curl http://localhost:5000/api/health` (replace `5000` with `OUTGOING_PORT` if set)
3. Check volume mounts: `docker inspect directory-browser`
4. Review this README for common solutions 