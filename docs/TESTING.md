# MoveCRM Testing Guide

This guide covers testing procedures for the MoveCRM MVP system.

## 🧪 Testing Overview

The MoveCRM system includes multiple components that need to be tested:

- **Backend API** - Flask application with multi-tenant support
- **YOLOE Service** - FastAPI service for AI item detection
- **Frontend Dashboard** - React application for CRM management
- **Embeddable Widget** - JavaScript widget for customer websites
- **Database** - PostgreSQL with proper schema and constraints
- **Authentication** - SuperTokens integration with multi-tenant support

## 🚀 Quick Start Testing

### 1. Start the Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd movecrm-mvp

# Start all services
docker-compose up -d

# Wait for services to be healthy
docker-compose ps
```

### 2. Import Postman Collection

1. Open Postman
2. Import `postman/MoveCRM_API.postman_collection.json`
3. Import `postman/MoveCRM_Environment.postman_environment.json`
4. Set the environment to "MoveCRM Local Development"

### 3. Run Basic Health Checks

Execute these requests in order:
1. **Backend Health** - Should return `{"status": "healthy"}`
2. **YOLOE Service Health** - Should return `{"status": "healthy"}`

## 🔐 Authentication Testing

### Register and Login Flow

1. **Register User**
   ```json
   POST /api/auth/register
   {
     "email": "admin@demo.com",
     "password": "password123",
     "name": "Demo Admin",
     "role": "admin"
   }
   ```

2. **Login User**
   ```json
   POST /api/auth/login
   {
     "email": "admin@demo.com",
     "password": "password123"
   }
   ```
   - Should return access token
   - Token is automatically saved to environment

3. **Get User Profile**
   ```
   GET /api/auth/profile
   Authorization: Bearer {token}
   ```

### Multi-tenant Testing

Test with different tenant slugs:
- `demo` - Default demo tenant
- `acme-moving` - Example moving company
- `premium-movers` - Another example company

Each tenant should have isolated data.

## 📝 Quote Management Testing

### Public Quote Submission (Widget)

Test the public endpoint that the widget uses:

```
POST /api/public/quote
X-Tenant-Slug: demo
Content-Type: multipart/form-data

Form data:
- name: John Smith
- email: john@example.com
- phone: (555) 123-4567
- pickup_address: 123 Main St, City, State
- delivery_address: 456 Oak Ave, City, State
- move_date: 2024-12-15
- notes: Need help with packing
- files: [image files]
```

### Authenticated Quote Management

1. **Get All Quotes**
   ```
   GET /api/quotes
   Authorization: Bearer {token}
   X-Tenant-Slug: demo
   ```

2. **Get Quote by ID**
   ```
   GET /api/quotes/{id}
   Authorization: Bearer {token}
   X-Tenant-Slug: demo
   ```

3. **Update Quote**
   ```json
   PUT /api/quotes/{id}
   {
     "status": "approved",
     "estimated_price": 1500.00,
     "notes": "Quote approved"
   }
   ```

## 🤖 YOLOE Detection Testing

### Auto Detection

Test automatic item detection:

```
POST /api/detect/auto
Authorization: Bearer {token}
X-Tenant-Slug: demo
Content-Type: multipart/form-data

files: [furniture images]
```

Expected response:
```json
{
  "detections": [
    {
      "class": "sofa",
      "confidence": 0.85,
      "bbox": [100, 200, 300, 400],
      "catalog_match": {
        "name": "Sofa",
        "cubic_feet": 40.0,
        "category": "furniture"
      }
    }
  ],
  "total_cubic_feet": 40.0,
  "estimated_price": 600.00
}
```

### Text-Prompted Detection

Test detection with text prompts:

```
POST /api/detect/text
Authorization: Bearer {token}
X-Tenant-Slug: demo
Content-Type: multipart/form-data

prompt: "furniture items"
files: [room images]
```

## 🎨 Frontend Testing

### Dashboard Access

1. Open http://localhost:3000
2. Login with demo credentials:
   - Company Slug: `demo`
   - Email: `admin@demo.com`
   - Password: `password123`

### Test Dashboard Features

1. **Quotes Page**
   - View quotes list
   - Click on quote details
   - Update quote status
   - Add notes

2. **Customers Page**
   - View customer list
   - Search customers
   - View customer details

3. **Pricing Rules**
   - View current pricing
   - Update rates
   - Save changes

4. **Brand Settings**
   - Update company info
   - Change colors
   - Upload logo

5. **Item Catalog**
   - View items
   - Add new items
   - Update aliases
   - Set cubic footage

## 🔗 Widget Testing

### Basic Widget Test

1. Open `widget/examples/demo.html` in browser
2. Click the floating "Get Moving Quote" button
3. Fill out the form:
   - Name: Test Customer
   - Email: test@example.com
   - Phone: (555) 123-4567
   - Pickup: 123 Test St
   - Delivery: 456 Test Ave
   - Date: Future date
   - Notes: Test submission

4. Upload test images (optional)
5. Submit the form

### Widget Integration Test

Create a test HTML page:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Widget Test</title>
</head>
<body>
    <h1>Test Website</h1>
    <p>This is a test page for the MoveCRM widget.</p>
    
    <script src="http://localhost:8080/movecrm-widget.js"></script>
    <script>
        MoveCRMWidget.init({
            tenantSlug: 'demo',
            apiUrl: 'http://localhost:5000/api',
            primaryColor: '#2563eb'
        });
    </script>
</body>
</html>
```

## 🔍 Error Testing

### Rate Limiting

Test rate limiting by making multiple rapid requests:

```bash
# Test public quote endpoint rate limiting
for i in {1..20}; do
  curl -X POST http://localhost:5000/api/public/quote \
    -H "X-Tenant-Slug: demo" \
    -F "name=Test$i" \
    -F "email=test$i@example.com"
done
```

Should return 429 status after hitting the limit.

### Invalid Data

Test with invalid data:

1. **Invalid Tenant**
   ```
   X-Tenant-Slug: nonexistent
   ```
   Should return 404 or 403

2. **Invalid Email Format**
   ```json
   {
     "email": "invalid-email",
     "password": "password123"
   }
   ```

3. **Missing Required Fields**
   ```json
   {
     "email": "test@example.com"
     // missing password
   }
   ```

### File Upload Limits

Test file upload restrictions:

1. **Large Files** - Upload files > 50MB
2. **Invalid Types** - Upload non-image files
3. **Too Many Files** - Upload > 5 files

## 📊 Performance Testing

### Load Testing

Use tools like Apache Bench or Artillery:

```bash
# Test quote submission endpoint
ab -n 100 -c 10 -p quote_data.json -T application/json \
  http://localhost:5000/api/public/quote
```

### Database Performance

Monitor database queries:

```sql
-- Enable query logging in PostgreSQL
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- Monitor slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

## 🐛 Debugging

### Backend Logs

```bash
# View backend logs
docker-compose logs -f backend

# View specific service logs
docker-compose logs -f yoloe-service
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U movecrm -d movecrm

# View tables
\dt

# Check data
SELECT * FROM quotes LIMIT 5;
SELECT * FROM tenants;
```

### Redis Cache

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# View keys
KEYS *

# Check rate limiting
GET rate_limit:demo:127.0.0.1
```

## ✅ Test Checklist

### Backend API
- [ ] Health check responds
- [ ] User registration works
- [ ] User login returns token
- [ ] Protected endpoints require auth
- [ ] Multi-tenant isolation works
- [ ] Rate limiting functions
- [ ] File uploads work
- [ ] CORS headers present

### YOLOE Service
- [ ] Health check responds
- [ ] Auto detection works
- [ ] Text detection works
- [ ] File validation works
- [ ] Error handling works

### Frontend
- [ ] Login page loads
- [ ] Authentication works
- [ ] Dashboard displays
- [ ] Quotes page functions
- [ ] Admin pages accessible
- [ ] Responsive design works

### Widget
- [ ] Widget loads on page
- [ ] Form validation works
- [ ] File upload functions
- [ ] Submission succeeds
- [ ] Error handling works
- [ ] Mobile responsive

### Integration
- [ ] Widget → Backend → Database
- [ ] Backend → YOLOE → Response
- [ ] Frontend → Backend → Display
- [ ] Multi-tenant data isolation
- [ ] File storage works
- [ ] Email notifications (if implemented)

## 🚨 Common Issues

### Service Won't Start
- Check Docker logs: `docker-compose logs service-name`
- Verify environment variables
- Check port conflicts
- Ensure dependencies are healthy

### Database Connection Failed
- Verify PostgreSQL is running
- Check connection string
- Ensure database exists
- Check user permissions

### CORS Errors
- Verify CORS configuration in backend
- Check request headers
- Ensure proper origins allowed

### Widget Not Loading
- Check CDN server is running
- Verify widget URL is correct
- Check browser console for errors
- Ensure CORS is configured

### Authentication Issues
- Verify SuperTokens is running
- Check API keys match
- Ensure tenant exists
- Check token expiration

## 📈 Monitoring

### Health Checks

Set up monitoring for:
- `/health` endpoints
- Database connectivity
- Redis connectivity
- File storage access

### Metrics

Monitor:
- Response times
- Error rates
- Quote submission rates
- File upload sizes
- Database query performance

### Alerts

Set up alerts for:
- Service downtime
- High error rates
- Database connection issues
- Disk space usage
- Memory usage

