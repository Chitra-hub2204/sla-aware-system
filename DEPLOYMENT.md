# SLA Monitoring System - Deployment Guide

## Overview
This guide covers deploying the SLA-aware monitoring system to Railway (backend) and Netlify (frontend).

---

## 1. Backend Deployment (Railway)

### Prerequisites
- Railway account (https://railway.app)
- Git repository with your code

### Steps

1. **Create a new Railway project**
   - Go to Railway dashboard
   - Click "New Project"
   - Select "Deploy from GitHub repo" (or use Railway CLI)

2. **Configure Railway service**
   - Railway will auto-detect the Dockerfile in the `backend/` directory
   - Set the root directory to `backend/` if needed
   - Railway will automatically:
     - Build the Docker image
     - Expose port 8080
     - Set PORT environment variable

3. **Environment Variables (if needed)**
   - `PORT`: Automatically set by Railway (usually 8080)
   - `NETCONF_MODE`: Set to `mock` (default)
   - No additional variables required for basic operation

4. **Get your Railway backend URL**
   - After deployment, Railway provides a public URL
   - Example: `https://sla-aware-system-production.up.railway.app`
   - Copy this URL for frontend configuration

5. **Verify deployment**
   - Visit: `https://your-railway-url.railway.app/health`
   - Should return: `{"status": "ok", "time": "..."}`
   - Visit: `https://your-railway-url.railway.app/metrics`
   - Should return Prometheus metrics

---

## 2. Frontend Deployment (Netlify)

### Prerequisites
- Netlify account (https://netlify.com)
- Git repository

### Steps

1. **Update API configuration**
   - Edit `src/api.js`
   - Set `VITE_API_BASE_URL` environment variable in Netlify:
     - Go to Site settings → Environment variables
     - Add: `VITE_API_BASE_URL` = `https://your-railway-url.railway.app`

2. **Deploy to Netlify**
   - Option A: Connect GitHub repo
     - Go to Netlify dashboard
     - Click "Add new site" → "Import an existing project"
     - Select your GitHub repository
     - Build command: `npm run build`
     - Publish directory: `dist`
   
   - Option B: Netlify CLI
     ```bash
     npm install -g netlify-cli
     netlify login
     netlify deploy --prod
     ```

3. **Verify CORS**
   - Backend CORS is configured to allow all origins (`*`)
   - If issues occur, update `backend/app.py` CORS config with your Netlify domain

4. **Test the frontend**
   - Visit your Netlify URL
   - Create a test order
   - Verify it appears in the orders list

---

## 3. Prometheus Configuration (for monitoring)

### For Local Development
- Use `docker-compose.yml`
- Prometheus will scrape `backend:8080`

### For Production (Railway)
- Update `prometheus.yml`:
  ```yaml
  scrape_configs:
    - job_name: "sla_backend"
      static_configs:
        - targets:
            - "https://your-railway-url.railway.app"
  ```
- Note: Prometheus must be able to reach the Railway URL
- If running Prometheus locally, ensure it can access the public Railway URL

---

## 4. Grafana Dashboard Setup

1. **Import Dashboard**
   - Open Grafana (http://localhost:3000 for local)
   - Go to Dashboards → Import
   - Upload `grafana_dashboard.json`
   - Configure Prometheus datasource:
     - URL: `http://prometheus:9090` (for docker-compose)
     - Or your Prometheus URL

2. **Configure Datasource**
   - Settings → Data sources → Add data source
   - Select Prometheus
   - URL: `http://prometheus:9090` (local) or your Prometheus URL
   - Save & Test

3. **Verify Panels**
   - All 5 panels should display data:
     - App Status
     - Latency Trend
     - Request Rate
     - CPU Usage
     - Memory Usage

---

## 5. Email Alerts Configuration

### Gmail SMTP (Already Configured)
- Email: `ugcet22055@gmail.com`
- Password: `rxbfnuvywknvxxoc` (App Password)
- SMTP: `smtp.gmail.com:587`

### Email Alerts Trigger
- **SLA Breach**: Sent when `latency > 500` OR `uptime < 99`
- **SLA Restored**: Sent when service returns to healthy state

### Testing Email Alerts
1. Create an order with latency > 500 or uptime < 99
2. Check email inbox for breach alert
3. Update order to healthy values
4. Check for restoration alert

---

## 6. Testing the Complete System

### Test Flow

1. **Create Order (Frontend)**
   - Visit Netlify frontend
   - Fill form:
     - Name: "Test User"
     - Service Type: "Compute VM"
     - SLA Uptime: 99 (locked)
     - SLA Latency: 500 (locked)
   - Click "Create"

2. **Verify Backend**
   - Check Railway logs for:
     - `[NETCONF] Service order-X activated`
     - Order creation success

3. **Verify Metrics**
   - Visit: `https://your-railway-url.railway.app/metrics`
   - Search for:
     - `sla_latency{service_id="order-1"}`
     - `sla_uptime{service_id="order-1"}`
     - `service_activation_status{service_id="order-1"}`

4. **Verify Grafana**
   - Open Grafana dashboard
   - Check "Latency Trend" panel
   - Should show data for `order-1`

5. **Test SLA Breach**
   - Create order with latency > 500 (modify backend temporarily or use API)
   - Verify email alert received
   - Check Grafana for breach status

---

## 7. Troubleshooting

### Backend Issues

**Problem**: Backend not accessible
- **Solution**: Check Railway deployment logs
- Verify PORT environment variable is set
- Check Railway public URL is correct

**Problem**: Metrics not appearing
- **Solution**: 
  - Verify `/metrics` endpoint returns data
  - Check Prometheus can reach Railway URL
  - Verify CORS allows Prometheus requests

**Problem**: Email alerts not sending
- **Solution**:
  - Check Gmail App Password is correct
  - Verify SMTP settings in `backend/email_service.py`
  - Check Railway logs for email errors

### Frontend Issues

**Problem**: CORS errors
- **Solution**: Backend CORS is set to `*`, should work. If not, add Netlify domain explicitly

**Problem**: API calls failing
- **Solution**:
  - Verify `VITE_API_BASE_URL` is set in Netlify
  - Check Railway backend URL is correct
  - Verify backend `/health` endpoint responds

### Prometheus Issues

**Problem**: No metrics scraped
- **Solution**:
  - Verify Railway URL is accessible from Prometheus
  - Check `prometheus.yml` target URL
  - Verify `/metrics` endpoint is public

---

## 8. Production Checklist

- [ ] Railway backend deployed and accessible
- [ ] Netlify frontend deployed with correct API URL
- [ ] Prometheus configured to scrape Railway backend
- [ ] Grafana dashboard imported and showing data
- [ ] Email alerts tested (breach and restoration)
- [ ] CORS configured correctly
- [ ] All metrics exposed on `/metrics` endpoint
- [ ] NETCONF mock mode working
- [ ] SLA breach detection working
- [ ] Order creation flow end-to-end tested

---

## 9. Environment Variables Summary

### Railway (Backend)
- `PORT`: Auto-set by Railway
- `NETCONF_MODE`: `mock` (default)

### Netlify (Frontend)
- `VITE_API_BASE_URL`: Your Railway backend URL

### Prometheus (Local)
- `RAILWAY_BACKEND_URL`: Your Railway backend URL (optional, update prometheus.yml directly)

---

## Support

For issues or questions:
1. Check Railway deployment logs
2. Check Netlify build logs
3. Verify all URLs are correct
4. Test endpoints individually (health, metrics)

---

**Last Updated**: 2025-01-17

