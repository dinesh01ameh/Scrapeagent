# SwissKnife AI Scraper - API Reference

## 🌐 **API Overview**

The SwissKnife AI Scraper provides a comprehensive RESTful API built with FastAPI. All endpoints are documented with OpenAPI/Swagger and can be accessed at `http://localhost:8601/docs` when the server is running.

**Base URL**: `http://localhost:8601`  
**API Version**: v1  
**Documentation**: `http://localhost:8601/docs`  
**OpenAPI Schema**: `http://localhost:8601/openapi.json`

---

## 🔐 **Authentication Endpoints**

### **POST /auth/login**
Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_123",
    "email": "user@example.com",
    "full_name": "John Doe",
    "username": "johndoe"
  }
}
```

### **POST /auth/register**
Register new user account.

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "securepassword",
  "full_name": "Jane Smith",
  "username": "janesmith"
}
```

**Response (201):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user_124",
    "email": "newuser@example.com",
    "full_name": "Jane Smith",
    "username": "janesmith"
  }
}
```

---

## 🕷️ **Scraping Endpoints**

### **POST /scrape**
Basic scraping endpoint with adaptive extraction.

**Request Body:**
```json
{
  "url": "https://example.com",
  "query": "Extract all product information",
  "extraction_config": {
    "format": "json",
    "include_metadata": true
  },
  "session_id": "session_123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "content": {
      "title": "Example Page",
      "text": "Extracted content...",
      "metadata": {
        "url": "https://example.com",
        "timestamp": "2025-08-06T12:00:00Z",
        "word_count": 1250
      }
    },
    "extraction_type": "adaptive",
    "processing_time": 2.34
  },
  "execution_time": 2.5,
  "message": "Content extracted successfully"
}
```

### **POST /natural-language-scrape**
Natural language query-based scraping.

**Request Body:**
```json
{
  "url": "https://shop.example.com",
  "query": "Find all products with their prices and descriptions",
  "session_id": "session_123"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "name": "Product A",
        "price": "$29.99",
        "description": "High-quality product..."
      }
    ],
    "total_found": 2,
    "query_interpretation": "Product information extraction",
    "confidence_score": 0.95
  },
  "execution_time": 3.2
}
```

### **POST /multimodal-scrape**
Multi-modal content extraction (text, images, documents).

**Request Body:**
```json
{
  "url": "https://example.com/article",
  "content_types": ["text", "images", "links"],
  "query": "Extract article content and related images"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "text_content": {
      "title": "Article Title",
      "body": "Article content...",
      "word_count": 850
    },
    "images": [
      {
        "url": "https://example.com/image1.jpg",
        "alt_text": "Description",
        "dimensions": "800x600"
      }
    ],
    "links": [
      {
        "url": "https://related-site.com",
        "text": "Related Article",
        "type": "external"
      }
    ]
  },
  "execution_time": 4.1
}
```

---

## 📊 **System Endpoints**

### **GET /health**
Basic health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-06T12:00:00Z",
  "version": "2.2.0"
}
```

### **GET /health/detailed**
Comprehensive system health check.

**Response (200):**
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy", "response_time": 12},
    "redis": {"status": "healthy", "response_time": 3},
    "crawl4ai": {"status": "healthy", "response_time": 45},
    "jina_ai": {"status": "healthy", "response_time": 120}
  },
  "performance": {
    "active_sessions": 5,
    "total_requests": 1250,
    "success_rate": 98.5
  }
}
```

---

## 🚨 **Error Handling**

### **HTTP Status Codes**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `422` - Validation Error
- `500` - Internal Server Error

### **Error Response Format**
```json
{
  "detail": "Error description",
  "error_code": "SCRAPING_ERROR",
  "timestamp": "2025-08-06T12:00:00Z"
}
```

---

**For complete API documentation, visit: http://localhost:8601/docs**

**Last Updated**: August 6, 2025