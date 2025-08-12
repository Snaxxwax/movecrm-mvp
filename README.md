# MoveCRM MVP

A complete multi-tenant CRM system for moving companies with AI-powered item detection, automated pricing, and embeddable quote widgets.

## 🚀 Features

- **Multi-tenant Architecture** - Support multiple moving companies with isolated data
- **AI-Powered Item Detection** - YOLOE-based automatic item recognition from photos
- **Automated Pricing** - Calculate quotes based on cubic footage, labor, and tenant rates
- **Embeddable Widget** - JavaScript widget for customer websites
- **Role-based Access Control** - Admin, staff, and customer roles
- **Real-time Notifications** - Quote status updates and notifications
- **File Upload Support** - Secure image upload with validation
- **Rate Limiting** - Prevent abuse with per-tenant and IP-based limits

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │ YOLOE Service   │
│   (React)       │◄──►│   (Flask)       │◄──►│   (FastAPI)     │
│                 │    │                 │    │                 │
│ - Dashboard     │    │ - Multi-tenant  │    │ - Item Detection│
│ - Quote Mgmt    │    │ - SuperTokens   │    │ - RunPod GPU    │
│ - Customer Mgmt │    │ - Rate Limiting │    │ - Batch Process │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   PostgreSQL    │              │
         └──────────────┤   + Redis       │──────────────┘
                        │   + SuperTokens │
                        └─────────────────┘

┌─────────────────┐    ┌─────────────────┐
│ Embeddable      │    │   Widget CDN    │
│ Widget (JS)     │◄──►│   (Nginx)       │
│                 │    │                 │
│ - Quote Form    │    │ - CORS Enabled  │
│ - File Upload   │    │ - Cached Assets │
│ - Responsive    │    │ - Global CDN    │
└─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
movecrm-mvp/
├── backend/                 # Flask API server
│   ├── src/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API endpoints
│   │   ├── utils/          # Utilities
│   │   └── main.py         # Application entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── yoloe-service/          # AI detection service
│   ├── src/
│   │   ├── models.py       # Pydantic models
│   │   ├── yoloe_detector.py
│   │   └── runpod_client.py
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   └── App.jsx
│   ├── package.json
│   ├── Dockerfile
│   └── Dockerfile.dev
├── widget/                 # Embeddable widget
│   ├── src/
│   │   └── movecrm-widget.js
│   ├── examples/
│   │   └── demo.html
│   ├── dist/               # Built widget files
│   ├── build.sh
│   └── README.md
├── docs/                   # Documentation
│   └── database_schema.sql
├── docker-compose.yml      # Local development
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd movecrm-mvp
```

### 2. Environment Configuration

Copy environment files and configure:

```bash
# Backend
cp backend/.env.example backend/.env

# YOLOE Service
cp yoloe-service/.env.example yoloe-service/.env

# Frontend (if needed)
cp frontend/.env.example frontend/.env
```

### 3. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **YOLOE Service**: http://localhost:8001
- **Widget CDN**: http://localhost:8080
- **Database Admin**: http://localhost:8082 (Adminer)
- **File Storage**: http://localhost:9001 (MinIO Console)

## 🔧 Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5000
```

### Frontend Development

```bash
cd frontend
pnpm install
pnpm run dev
```

### YOLOE Service Development

```bash
cd yoloe-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Widget Development

```bash
cd widget
# Edit src/movecrm-widget.js
# Test with examples/demo.html
./build.sh  # Build for production
```

## 🧪 Testing

### API Testing

Use the provided Postman collection:

```bash
# Import postman/MoveCRM_API.postman_collection.json
# Set environment variables:
# - base_url: http://localhost:5000
# - tenant_slug: demo
```

### Widget Testing

Open `widget/examples/demo.html` in your browser to test the embeddable widget.

## 🚀 Deployment

### Production Deployment

1. **Build Images**:
```bash
docker-compose -f docker-compose.prod.yml build
```

2. **Deploy to Cloud**:
- Use Docker Swarm, Kubernetes, or cloud services
- Configure environment variables for production
- Set up SSL certificates
- Configure CDN for widget distribution

3. **Database Migration**:
```bash
# Run database migrations
docker-compose exec backend flask db upgrade
```

### Environment Variables

#### Backend (.env)
```env
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/movecrm
REDIS_URL=redis://host:6379/0
SUPERTOKENS_CONNECTION_URI=http://supertokens:3567
SECRET_KEY=your-secret-key
YOLOE_SERVICE_URL=http://yoloe-service:8001
```

#### YOLOE Service (.env)
```env
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8001
RUNPOD_API_KEY=your-runpod-key
YOLOE_MODEL_PATH=yolov8n.pt
```

## 📚 API Documentation

### Authentication

The API uses SuperTokens for authentication with multi-tenant support:

```bash
# Login
POST /api/auth/login
{
  "email": "user@company.com",
  "password": "password",
  "tenantSlug": "company-slug"
}
```

### Quote Management

```bash
# Create quote
POST /api/quotes
Headers: X-Tenant-Slug: company-slug

# Get quotes
GET /api/quotes
Headers: X-Tenant-Slug: company-slug

# Public quote submission (widget)
POST /api/public/quote
Headers: X-Tenant-Slug: company-slug
```

### YOLOE Detection

```bash
# Auto detection
POST /api/detect/auto
Content-Type: multipart/form-data

# Text-prompted detection
POST /api/detect/text
{
  "prompt": "furniture items",
  "files": [...]
}
```

## 🔒 Security

- **Multi-tenant Isolation**: All data is isolated by tenant_id
- **Rate Limiting**: Configurable limits per tenant and IP
- **File Upload Validation**: Type and size restrictions
- **CORS Configuration**: Proper cross-origin settings
- **SQL Injection Prevention**: Parameterized queries
- **XSS Protection**: Input sanitization

## 🎨 Widget Customization

The embeddable widget is highly customizable:

```javascript
MoveCRMWidget.init({
  tenantSlug: 'your-company',
  apiUrl: 'https://api.movecrm.com',
  primaryColor: '#2563eb',
  borderRadius: '8px',
  maxFiles: 5,
  maxFileSize: 50 * 1024 * 1024
});
```

## 📊 Monitoring

### Health Checks

All services include health check endpoints:

- Backend: `GET /health`
- YOLOE Service: `GET /health`
- Frontend: `GET /health`

### Logging

Structured logging is configured for all services:

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f yoloe-service
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` directory
- **Issues**: Create an issue on GitHub
- **Email**: support@movecrm.com

## 🗺️ Roadmap

- [ ] Advanced AI item recognition
- [ ] Mobile app for field staff
- [ ] Integration with moving truck GPS
- [ ] Customer portal
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] API rate limiting dashboard
- [ ] Automated testing suite

