# ServiceHub Deployment Guide

This guide covers deploying ServiceHub in various environments.

## 🚀 Quick Start (Development)

### Prerequisites
- Docker & Docker Compose
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd servicehub-backend
cp .env.example .env
```

### 2. Start Services
```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f backend

# Run migrations and create sample data
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py create_sample_data --users 50 --services 100
```

### 3. Access the Application
- **API**: http://localhost:8002/api/
- **Admin**: http://localhost:8002/admin/
- **API Docs**: http://localhost:8002/api/docs/
- **Health Check**: http://localhost:8002/api/health/

## 🏭 Production Deployment

### Prerequisites
- Docker & Docker Compose
- Domain name with SSL certificate
- Email service (Gmail, SendGrid, etc.)
- Payment gateway account (Stripe)
- Cloud storage (AWS S3) - optional

### 1. Environment Configuration

Create `.env.prod`:
```bash
# Django Configuration
DEBUG=False
SECRET_KEY=your-super-secret-production-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_PASSWORD=your-secure-database-password

# Superuser
DJANGO_SUPERUSER_EMAIL=admin@yourdomain.com
DJANGO_SUPERUSER_PASSWORD=your-admin-password

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (optional)
USE_S3=True
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name

# Payment Gateway
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
```

### 2. SSL Certificate Setup

Place your SSL certificates in `nginx/ssl/`:
```bash
mkdir -p nginx/ssl
# Copy your certificate files
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

### 3. Deploy
```bash
# Build and start production services
docker-compose -f docker-compose.prod.yml up -d --build

# Check health
curl http://yourdomain.com/health
```

### 4. Post-Deployment Tasks
```bash
# Create superuser (if not created automatically)
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Create sample data (optional)
docker-compose -f docker-compose.prod.yml exec backend python manage.py create_sample_data
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Enable debug mode | `True` | No |
| `SECRET_KEY` | Django secret key | - | Yes |
| `ALLOWED_HOSTS` | Allowed hostnames | `localhost,127.0.0.1` | No |
| `DB_NAME` | Database name | `servicehub_dev` | No |
| `DB_USER` | Database user | `servicehub_user` | No |
| `DB_PASSWORD` | Database password | `secure_password` | No |
| `DB_HOST` | Database host | `localhost` | No |
| `DB_PORT` | Database port | `5433` | No |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6381/0` | No |
| `USE_S3` | Use AWS S3 for storage | `False` | No |
| `STRIPE_SECRET_KEY` | Stripe secret key | - | For payments |
| `EMAIL_HOST` | SMTP host | - | For emails |
| `EMAIL_HOST_USER` | SMTP username | - | For emails |
| `EMAIL_HOST_PASSWORD` | SMTP password | - | For emails |

### Service Configuration

#### Database
- **Engine**: PostgreSQL 15
- **Connection Pooling**: Enabled
- **Backup**: Automated daily backups recommended

#### Redis
- **Memory Policy**: `allkeys-lru`
- **Persistence**: AOF enabled
- **Max Memory**: 256MB (configurable)

#### Celery
- **Worker Concurrency**: 2 (production)
- **Task Routing**: Automatic
- **Beat Scheduler**: Database-backed

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Application health
curl http://yourdomain.com/api/health/

# Service status
docker-compose -f docker-compose.prod.yml ps

# Logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Database Maintenance
```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U servicehub_user servicehub_prod > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U servicehub_user servicehub_prod < backup.sql
```

### Performance Monitoring
- **Database**: Monitor query performance and connection counts
- **Redis**: Monitor memory usage and hit rates
- **Application**: Monitor response times and error rates
- **System**: Monitor CPU, memory, and disk usage

## 🔒 Security Considerations

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Use strong `SECRET_KEY`
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure proper firewall rules
- [ ] Set up database backups
- [ ] Enable security headers
- [ ] Configure rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates

### Security Headers
The Nginx configuration includes:
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `X-Frame-Options`
- `X-XSS-Protection`
- `Referrer-Policy`

### Rate Limiting
- **API endpoints**: 10 requests/second
- **Authentication**: 5 requests/second
- **Burst capacity**: Configurable

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Error
```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec db pg_isready

# Check connection from backend
docker-compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

#### Redis Connection Error
```bash
# Check Redis status
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping

# Check connection from backend
docker-compose -f docker-compose.prod.yml exec backend python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

#### Static Files Not Loading
```bash
# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Check Nginx configuration
docker-compose -f docker-compose.prod.yml exec nginx nginx -t
```

#### SSL Certificate Issues
```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL configuration
curl -I https://yourdomain.com
```

### Log Analysis
```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs backend

# Database logs
docker-compose -f docker-compose.prod.yml logs db

# Nginx logs
docker-compose -f docker-compose.prod.yml logs nginx

# Celery logs
docker-compose -f docker-compose.prod.yml logs celery_worker
```

## 📈 Scaling

### Horizontal Scaling
- **Backend**: Add more backend containers behind load balancer
- **Celery**: Add more worker containers
- **Database**: Consider read replicas
- **Redis**: Consider Redis Cluster

### Vertical Scaling
- **CPU**: Increase container CPU limits
- **Memory**: Increase container memory limits
- **Storage**: Use faster storage (SSD)

### Load Balancing
```yaml
# Example load balancer configuration
backend:
  deploy:
    replicas: 3
  depends_on:
    - db
    - redis
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
```

### Database Migrations
```bash
# Check migration status
docker-compose -f docker-compose.prod.yml exec backend python manage.py showmigrations

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create new migration
docker-compose -f docker-compose.prod.yml exec backend python manage.py makemigrations
```

### Backup Strategy
1. **Database**: Daily automated backups
2. **Media Files**: Sync to cloud storage
3. **Configuration**: Version control
4. **SSL Certificates**: Backup and renewal alerts

## 📞 Support

For deployment support:
1. Check the troubleshooting section
2. Review application logs
3. Consult the main README.md
4. Open an issue in the repository

---

**Happy Deploying! 🚀**