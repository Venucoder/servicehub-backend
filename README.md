# ServiceHub - Multi-Service Digital Distribution Platform

A comprehensive Django REST API backend for a modern service marketplace platform, similar to Fiverr or Upwork. This project demonstrates enterprise-level Django development with advanced features including real-time notifications, payment processing, analytics, and microservices architecture.

## 🚀 Features

### Core Functionality
- **User Management**: Multi-role authentication (customers, providers, admins)
- **Service Marketplace**: Full-featured service listing and discovery
- **Order Management**: Complete order lifecycle with real-time updates
- **Payment Processing**: Integrated payment system with multiple gateways
- **Review System**: Comprehensive rating and review functionality
- **Real-time Messaging**: WebSocket-based communication between users
- **Analytics Dashboard**: Advanced analytics and reporting

### Technical Features
- **JWT Authentication**: Secure token-based authentication
- **Role-based Permissions**: Granular access control
- **API Documentation**: Auto-generated OpenAPI/Swagger docs
- **Background Tasks**: Celery for async processing
- **Caching**: Redis-based caching system
- **File Storage**: Support for local and cloud storage (AWS S3)
- **Email Notifications**: Automated email system
- **Search & Filtering**: Advanced search with multiple filters
- **Rate Limiting**: API rate limiting and throttling

## 🏗️ Architecture

### Backend Stack
- **Framework**: Django 5.0.8 + Django REST Framework
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Task Queue**: Celery
- **Authentication**: JWT (Simple JWT)
- **API Documentation**: drf-spectacular
- **File Storage**: Django Storages (S3 compatible)

### Project Structure
```
backend/
├── apps/
│   ├── authentication/     # JWT auth, user verification
│   ├── users/             # User profiles and management
│   ├── services/          # Service listings and categories
│   ├── orders/            # Order management and workflow
│   ├── payments/          # Payment processing and wallets
│   └── analytics/         # Analytics and reporting
├── core/                  # Shared utilities and helpers
├── servicehub/           # Main Django project settings
└── manage.py
```

## 📊 Data Models

### User System
- **User**: Extended Django user with roles (customer/provider/admin)
- **UserSession**: Session tracking for security
- **LoginAttempt**: Security monitoring
- **TwoFactorAuth**: 2FA support

### Service Management
- **Service**: Main service model with packages and reviews
- **ServiceCategory**: Hierarchical categorization
- **ServicePackage**: Tiered pricing (Basic/Standard/Premium)
- **ServiceReview**: Detailed review system with ratings

### Order Workflow
- **Order**: Complete order lifecycle management
- **OrderMessage**: Real-time messaging between parties
- **OrderDeliverable**: File delivery system
- **OrderTimeline**: Activity tracking

### Payment System
- **Transaction**: All financial transactions
- **Wallet**: Provider earnings management
- **PayoutRequest**: Automated payout system
- **Invoice**: Professional invoicing

### Analytics
- **UserAnalytics**: User behavior tracking
- **ServiceAnalytics**: Service performance metrics
- **PlatformAnalytics**: Platform-wide statistics
- **RevenueReport**: Financial reporting

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd servicehub-backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
# Start PostgreSQL and Redis (or use Docker Compose)
docker-compose up -d db redis

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create sample data (optional)
python manage.py create_sample_data --users 50 --services 100
```

6. **Start development server**
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A servicehub worker -l info

# Terminal 3: Celery beat (for scheduled tasks)
celery -A servicehub beat -l info
```

### Docker Setup

```bash
# Build and start all services
docker-compose up --build

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Create sample data
docker-compose exec backend python manage.py create_sample_data
```

## 📚 API Documentation

### Authentication Endpoints
```
POST /api/auth/register/           # User registration
POST /api/auth/login/              # User login
POST /api/auth/refresh/            # Token refresh
POST /api/auth/logout/             # User logout
POST /api/auth/verify-email/       # Email verification
POST /api/auth/password-reset/     # Password reset
```

### Service Endpoints
```
GET    /api/services/              # List services (with filters)
POST   /api/services/              # Create service
GET    /api/services/{slug}/       # Service details
PUT    /api/services/{slug}/       # Update service
DELETE /api/services/{slug}/       # Delete service
GET    /api/services/categories/   # Service categories
GET    /api/services/featured/     # Featured services
```

### Order Endpoints
```
GET    /api/orders/                # List orders
POST   /api/orders/                # Create order
GET    /api/orders/{id}/           # Order details
PUT    /api/orders/{id}/           # Update order
POST   /api/orders/{id}/messages/  # Send message
GET    /api/orders/{id}/timeline/  # Order timeline
```

### Payment Endpoints
```
GET    /api/payments/transactions/ # Transaction history
POST   /api/payments/process/      # Process payment
GET    /api/payments/wallet/       # Wallet details
POST   /api/payments/payout/       # Request payout
```

### Interactive API Documentation
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **Schema**: `http://localhost:8000/api/schema/`

## 🔧 Configuration

### Environment Variables
```bash
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=servicehub_dev
DB_USER=servicehub_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5433

# Redis
REDIS_URL=redis://localhost:6381/0

# Email (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for production)
USE_S3=False
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket

# Payment Gateway
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

## 🧪 Testing

```bash
# Run tests
python manage.py test

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
python manage.py test apps.services
```

## 📈 Performance & Monitoring

### Caching Strategy
- **Redis**: Session storage, API response caching
- **Database**: Query optimization with select_related/prefetch_related
- **Static Files**: CDN integration for production

### Background Tasks
- **Analytics**: Daily/monthly report generation
- **Notifications**: Email and push notifications
- **Payments**: Automated payout processing
- **Cleanup**: Expired token cleanup

### Monitoring
- **Logging**: Structured logging with different levels
- **Metrics**: Custom metrics for business KPIs
- **Health Checks**: API health monitoring endpoints

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up SSL/TLS certificates
- [ ] Configure production database
- [ ] Set up Redis cluster
- [ ] Configure email service
- [ ] Set up file storage (S3)
- [ ] Configure payment gateway
- [ ] Set up monitoring and logging
- [ ] Configure backup strategy

### Docker Production
```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Resume Highlights

This project demonstrates:

- **Full-Stack Development**: Complete backend API with modern architecture
- **Database Design**: Complex relational database with optimized queries
- **Authentication & Security**: JWT, role-based access, security monitoring
- **Payment Integration**: Real-world payment processing implementation
- **Real-time Features**: WebSocket integration for live updates
- **Background Processing**: Async task processing with Celery
- **API Design**: RESTful API with comprehensive documentation
- **Testing**: Unit and integration testing strategies
- **DevOps**: Docker containerization and deployment configuration
- **Performance**: Caching, optimization, and monitoring implementation

## 📞 Contact

For questions about this project or collaboration opportunities, please reach out through the repository's issue tracker or contact information in the profile.

---

**Built with ❤️ using Django REST Framework**
