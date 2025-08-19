# Directory Server Docker Setup

This directory contains Docker configuration files to run the directory browser server in a containerized environment.

## 🐳 **Quick Start**

### **Basic Setup (Development)**
```bash
# Build and run the directory server
docker-compose up --build

# Access the application
# Open http://localhost:5000 in your browser
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
| `DEFAULT_ROOT_PATH` | `/mnt/nassys` | Root directory to browse |
| `FLASK_ENV` | `production` | Flask environment |
| `FLASK_DEBUG` | `0` | Debug mode (0=off, 1=on) |

### **Volume Mounts**

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `/mnt/nassys` | `/mnt/nassys` | Directory to browse (read-only) |
| `./logs` | `/app/logs` | Application logs |
| `./config.ini` | `/app/config.ini` | Configuration file (optional) |

## 🚀 **Usage Commands**

### **Development Mode**
```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs
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
curl http://localhost:5000/api/health

# Check via nginx (production)
curl http://localhost/health
```

### **Debug Endpoints**
```bash
# View active requests
curl http://localhost:5000/api/debug/requests

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

**1. Permission Denied**
```bash
# Check volume permissions
ls -la /mnt/nassys

# Fix permissions if needed
sudo chmod 755 /mnt/nassys
```

**2. Port Already in Use**
```bash
# Check what's using port 5000
sudo netstat -tlnp | grep :5000

# Change port in docker-compose.yml
ports:
  - "5001:5000"  # Use port 5001 instead
```

**3. Container Won't Start**
```bash
# Check container logs
docker-compose logs directory-server

# Check health status
docker-compose ps
```

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

### **Log Rotation**
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/directory-server

# Add configuration
/path/to/webscraping/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 appuser appuser
}
```

## 📝 **Customization**

### **Custom Configuration**
Create `config.ini`:
```ini
[Scrape]
media_dir = /path/to/your/media
```

### **Custom Nginx Configuration**
Modify `nginx.conf` for your specific needs:
- SSL certificates
- Custom domains
- Rate limiting
- Caching rules

## 🆘 **Support**

For issues or questions:
1. Check container logs: `docker-compose logs`
2. Verify health endpoint: `curl http://localhost:5000/api/health`
3. Check volume mounts: `docker inspect directory-browser`
4. Review this README for common solutions 