# CropMD – API Documentation

Base URL: `https://your-api.onrender.com/api`

All protected endpoints require: `Authorization: Bearer <access_token>`

---

## Authentication

### POST /auth/register

**Request:**
```json
{
  "name": "John Farmer",
  "email": "john@farm.com",
  "password": "SecurePass123",
  "phone": "+1234567890",
  "role": "farmer"
}
```

**Response 201:**
```json
{
  "message": "Registration successful",
  "user": { "id": "...", "name": "John Farmer", "email": "john@farm.com", "role": "farmer" },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

**Errors:** `400` missing fields | `409` email exists | `400` validation

---

### POST /auth/login

**Request:** `{ "email": "...", "password": "..." }`

**Response 200:** Same as register response

---

### POST /auth/refresh

**Header:** `Authorization: Bearer <refresh_token>`

**Response:** `{ "access_token": "eyJ..." }`

---

## Predictions

### POST /predictions/analyze

**Content-Type:** `multipart/form-data`

**Fields:**
- `image` (file, required) — JPEG/PNG/WEBP, max 10MB
- `farm_id` (string, optional)
- `notes` (string, optional)
- `lat`, `lng` (float, optional) — GPS coordinates

**Response 201:**
```json
{
  "scan_id": "668abc...",
  "image_url": "https://res.cloudinary.com/...",
  "prediction": {
    "class_name": "Tomato___Early_blight",
    "crop_name": "Tomato",
    "disease_name": "Early blight",
    "confidence": 0.912,
    "confidence_pct": 91.2,
    "severity": "High",
    "is_healthy": false,
    "top_predictions": [
      { "class_name": "Tomato___Early_blight", "confidence": 0.912 },
      { "class_name": "Tomato___Late_blight", "confidence": 0.054 }
    ]
  },
  "advisory": {
    "description": "Early blight (Alternaria solani)...",
    "symptoms": ["Dark brown spots with concentric rings", "..."],
    "treatments": [{ "name": "Chlorothalonil", "dosage": "2 g/L", "frequency": "Every 7-10 days" }],
    "pesticides": [{ "name": "Daconil 2787", "active_ingredient": "Chlorothalonil" }],
    "prevention": ["Use certified disease-free seeds", "..."],
    "fertilizer_tips": ["Ensure balanced NPK", "..."],
    "irrigation_tips": "Use drip or furrow irrigation..."
  }
}
```

**Errors:** `400` no image | `413` too large | `415` unsupported type

---

### GET /predictions/history

**Query params:** `page`, `limit`, `crop`, `status`, `from`, `to`

**Response:**
```json
{
  "scans": [{ "id": "...", "prediction": {...}, "image_url": "...", "created_at": "..." }],
  "total": 42,
  "page": 1,
  "pages": 3
}
```

---

### GET /predictions/stats/summary

**Response:**
```json
{
  "total_scans": 42,
  "healthy_count": 28,
  "disease_count": 14,
  "health_rate": 66.7,
  "top_diseases": [{ "disease": "Early blight", "count": 6 }],
  "recent_activity": [{ "date": "2024-06-01", "count": 3 }]
}
```

---

## Analytics

### GET /analytics/dashboard?days=30

**Response:**
```json
{
  "period_days": 30,
  "total_scans": 42,
  "healthy": 28,
  "diseased": 14,
  "health_rate": 66.7,
  "severity_breakdown": { "High": 5, "Medium": 6, "Low": 3 },
  "top_crops": [{ "crop": "Tomato", "count": 18 }],
  "top_diseases": [{ "disease": "Early blight", "crop": "Tomato", "count": 8 }]
}
```

---

## Chatbot

### POST /chatbot/chat

**Request:**
```json
{
  "message": "How do I treat tomato early blight?",
  "conversation_id": "optional-existing-id",
  "scan_context": { "crop_name": "Tomato", "disease_name": "Early blight", "confidence_pct": 91.2 }
}
```

**Response:**
```json
{
  "reply": "For tomato early blight, apply Chlorothalonil 2g/L every 7–10 days...",
  "conversation_id": "668xyz..."
}
```

---

## Error Format

All errors follow:
```json
{ "error": "Human-readable message", "code": "OPTIONAL_ERROR_CODE" }
```

HTTP Status Codes:
- `400` Bad Request
- `401` Unauthorized / Token expired
- `403` Forbidden (insufficient role)
- `404` Not Found
- `409` Conflict (duplicate email)
- `413` Payload too large
- `415` Unsupported media type
- `429` Rate limited
- `500` Internal server error
