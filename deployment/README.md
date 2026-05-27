# Deployment Configurations

This directory contains deployment configurations for Corpus Forge across different environments and platforms.

## Files Overview

### 1. **docker-compose.yml** (Root directory)
Quick local/development containerized deployment with Docker Compose.
- Runs the Flask app and Redis cache
- Suitable for development and testing

```bash
docker-compose up -d
```

### 2. **Dockerfile**
Production-ready Docker image definition.
- Based on Python 3.11 slim image
- Includes security best practices
- Health checks configured
- Non-root user execution

Build and run:
```bash
docker build -t corpus-forge:latest .
docker run -p 5000:5000 corpus-forge:latest
```

### 3. **kubernetes.yml**
Kubernetes deployment manifest for production clusters.
- 3 replica pods for high availability
- Service exposure via LoadBalancer
- Persistent volume for uploads
- Resource limits and health probes configured
- Secrets management integration

Deploy to Kubernetes:
```bash
kubectl apply -f kubernetes.yml
```

### 4. **nginx.conf**
Nginx reverse proxy configuration.
- SSL/TLS termination
- Security headers
- Gzip compression
- Static file caching
- Health check endpoint

Use with Docker:
```bash
docker run -v $(pwd)/nginx.conf:/etc/nginx/conf.d/default.conf \
           -p 443:443 \
           -p 80:80 \
           nginx:latest
```

### 5. **corpus-forge.service**
Systemd service file for Linux systemd deployments.
- Automatic restart on failure
- Security hardening
- Gunicorn worker configuration
- Proper user and permissions management

Install and run:
```bash
sudo cp corpus-forge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start corpus-forge
sudo systemctl enable corpus-forge
```

## Deployment Scenarios

### Local Development
Use `docker-compose.yml` in the root directory:
```bash
docker-compose up
```

### Docker Production
Use `Dockerfile`:
```bash
docker build -t corpus-forge:prod .
docker run -d \
  --name corpus-forge \
  -p 80:5000 \
  -e CORPUS_FORGE_SECRET=your-secret \
  -e FLASK_ENV=production \
  corpus-forge:prod
```

### Kubernetes Production
```bash
kubectl apply -f deployment/kubernetes.yml
kubectl get pods
kubectl logs -f <pod-name>
```

### Traditional Linux Server (systemd)
1. Install dependencies:
   ```bash
   sudo apt-get install python3.11 python3-pip
   ```

2. Copy service file:
   ```bash
   sudo cp corpus-forge.service /etc/systemd/system/
   ```

3. Start service:
   ```bash
   sudo systemctl start corpus-forge
   sudo systemctl status corpus-forge
   ```

### Behind Nginx Reverse Proxy
1. Start the Flask app (on localhost:5000)
2. Configure Nginx:
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/corpus-forge
   sudo ln -s /etc/nginx/sites-available/corpus-forge /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Environment Variables

See `.env.example` in the root directory for all available configuration options.

Key variables for deployment:
- `CORPUS_FORGE_SECRET` - Flask secret key (set to secure random value)
- `CORPUS_FORGE_UPLOADS` - Upload directory path
- `FLASK_ENV` - Set to `production` for production deployments
- `FLASK_DEBUG` - Set to `False` in production

## Security Considerations

- Always use HTTPS in production (Nginx handles SSL termination)
- Set strong `CORPUS_FORGE_SECRET` values
- Run containers as non-root user
- Use Kubernetes secrets for sensitive data
- Configure firewall rules appropriately
- Regular security updates for dependencies
- Enable health checks and monitoring

## Monitoring and Logging

### Docker
```bash
docker logs corpus-forge-app
```

### Kubernetes
```bash
kubectl logs -f deployment/corpus-forge-app
```

### Systemd
```bash
journalctl -u corpus-forge -f
tail -f /var/log/corpus-forge/access.log
```

### Nginx
```bash
tail -f /var/log/nginx/corpus-forge-access.log
tail -f /var/log/nginx/corpus-forge-error.log
```

## Troubleshooting

### Port already in use
- Docker: `docker ps` to find running containers
- Systemd: `sudo lsof -i :5000` to find process using port 5000

### Permission denied errors
- Ensure proper file permissions
- For systemd: Check user ownership of `/opt/corpus-forge`
- For Docker: Verify volume mount permissions

### Database connection issues
- Verify Redis is running and accessible
- Check environment variables are set correctly
- Review logs for specific error messages
