# CropMD – Deployment Guide

## Production Architecture

```
Browser → Vercel CDN (React) → Render (Flask API) → MongoDB Atlas
                                      ↓
                              Cloudinary (Images)
                              Gemini API (Chat)
```

---

## Step 1 – MongoDB Atlas

1. Go to [cloud.mongodb.com](https://cloud.mongodb.com) → Create free M0 cluster
2. Create DB user with password
3. Network Access → Add IP → `0.0.0.0/0` (allow all for Render)
4. Connect → Drivers → Copy connection string
5. Replace `<password>` in the URI

---

## Step 2 – Cloudinary

1. Sign up at [cloudinary.com](https://cloudinary.com) (free tier: 25GB storage)
2. Dashboard → Copy Cloud Name, API Key, API Secret

---

## Step 3 – Train ML Model (or use pretrained)

```bash
cd ml
pip install -r requirements_ml.txt

# Download PlantVillage from Kaggle
kaggle datasets download abdallahalidev/plantvillage-dataset
unzip plantvillage-dataset.zip -d ./data

python train.py \
  --data_dir ./data/PlantVillage \
  --output_dir ./outputs \
  --epochs_phase1 20 \
  --epochs_phase2 15 \
  --mixed_precision \
  --export_tflite
```

Copy outputs to backend:
```bash
mkdir -p backend/ml_models
cp outputs/<run_id>/cropmd_model.keras backend/ml_models/
cp outputs/<run_id>/class_names.json backend/ml_models/
```

---

## Step 4 – Deploy Backend to Render

1. Push code to GitHub
2. New Web Service at [render.com](https://render.com)
3. Settings:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn "app:create_app()" --workers 2 --bind 0.0.0.0:$PORT --timeout 120`
4. Environment Variables (add all from `.env.example`):

```
MONGO_URI=mongodb+srv://...
SECRET_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
FLASK_ENV=production
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
GEMINI_API_KEY=...
CORS_ORIGINS=https://cropmd.vercel.app
MODEL_PATH=ml_models/cropmd_model.keras
CLASS_NAMES_PATH=ml_models/class_names.json
```

Note: Upload your trained model file via Render Disk or host it in S3/Cloudinary and download on startup.

---

## Step 5 – Deploy Frontend to Vercel

```bash
cd frontend
npm run build
```

1. Import GitHub repo at [vercel.com](https://vercel.com)
2. Framework: Vite
3. Root Directory: `frontend`
4. Environment Variables:
   ```
   VITE_API_URL=https://your-render-service.onrender.com/api
   ```
5. Deploy

---

## Step 6 – Seed Database

After deployment, hit:
```
POST /api/admin/seed-diseases
Authorization: Bearer <admin-token>
```

---

## Docker Compose (Local Development)

```yaml
# docker-compose.yml (included in project root)
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["5000:5000"]
    env_file: ./backend/.env
    volumes: ["./backend/ml_models:/app/ml_models"]

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      - VITE_API_URL=http://localhost:5000/api

  mongo:
    image: mongo:7
    ports: ["27017:27017"]
    volumes: ["mongo_data:/data/db"]

volumes:
  mongo_data:
```

Run: `docker-compose up --build`

---

## Performance Targets

| Metric | Target |
|---|---|
| Model inference latency | < 2s |
| API response time (P95) | < 500ms |
| Image upload + prediction | < 5s end-to-end |
| Model accuracy (validation) | > 94% |
| Frontend Lighthouse score | > 85 |
