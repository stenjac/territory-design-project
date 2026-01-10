# 🚀 Deployment Quick Start

Choose your deployment method based on your organization's needs:

---

## 📋 Decision Tree

**Do you have IT/DevOps support?**
- ✅ YES → Option 2 (Docker) or Option 3 (Cloud)
- ❌ NO → Option 1 (Streamlit Cloud)

**How many users?**
- 1-20 users → Option 1 (Streamlit Cloud)
- 20-100 users → Option 2 (Docker)
- 100+ users → Option 3 (Cloud/Kubernetes)

**Need corporate authentication (AD/LDAP)?**
- ✅ YES → Option 2 or 3
- ❌ NO → Option 1

---

## 🎯 Option 1: Streamlit Cloud (5 Minutes)

**Best for:** Quick demos, small teams, no IT support needed

### Steps:
```bash
# 1. Push code to GitHub (already done!)
git push

# 2. Go to https://streamlit.io/cloud
# 3. Click "New app"
# 4. Select: territory-design-project / territory_dashboard.py
# 5. Click "Deploy"

# Done! Share URL: https://your-app.streamlit.app
```

### Add Password Protection:
```python
# Add to top of territory_dashboard.py
import streamlit as st
import hmac

def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], "YourPassword123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("Incorrect password")
    return False

if not check_password():
    st.stop()
```

---

## 🐳 Option 2: Docker on Internal Server (15 Minutes)

**Best for:** 20-500 users, full control, internal network

### Prerequisites:
- Linux/Windows server on internal network
- Docker installed
- Port 8501 accessible

### Quick Deploy:
```bash
# 1. SSH into your server
ssh user@your-server.company.com

# 2. Clone repository
git clone https://github.com/YOUR_USERNAME/territory-design-project.git
cd territory-design-project

# 3. Run deployment script
chmod +x deploy.sh
./deploy.sh

# 4. Select option 2 (background)

# Done! Access at: http://your-server.company.com:8501
```

### Manual Deploy:
```bash
# Build and run
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f

# Stop
docker-compose down
```

### Add Authentication:
```bash
# Install nginx
sudo apt-get install nginx apache2-utils

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Configure nginx (see DEPLOYMENT_GUIDE.md for full config)
sudo nano /etc/nginx/sites-available/territory-dashboard

# Enable and restart
sudo ln -s /etc/nginx/sites-available/territory-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## ☁️ Option 3: Cloud Deployment (30 Minutes)

**Best for:** 100+ users, high availability, enterprise scale

### AWS (ECS Fargate):
```bash
# 1. Build and push to ECR
aws ecr create-repository --repository-name territory-dashboard
docker build -t territory-dashboard .
docker tag territory-dashboard:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/territory-dashboard:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/territory-dashboard:latest

# 2. Create ECS cluster
aws ecs create-cluster --cluster-name territory-dashboard

# 3. Deploy (see DEPLOYMENT_GUIDE.md for full commands)
```

### Azure (App Service):
```bash
# 1. Login and create resource group
az login
az group create --name territory-dashboard-rg --location eastus

# 2. Deploy container
az webapp create \
  --resource-group territory-dashboard-rg \
  --plan territory-plan \
  --name territory-dashboard \
  --deployment-container-image-name YOUR_REGISTRY/territory-dashboard:latest

# Done! Access at: https://territory-dashboard.azurewebsites.net
```

### GCP (Cloud Run):
```bash
# 1. Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/territory-dashboard

# 2. Deploy
gcloud run deploy territory-dashboard \
  --image gcr.io/YOUR_PROJECT/territory-dashboard \
  --platform managed \
  --region us-central1

# Done! Access at the provided URL
```

---

## 🔐 Quick Authentication Setup

### Option A: Simple Password
Add to top of `territory_dashboard.py`:
```python
import streamlit as st
import hmac

def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], "SecurePass123"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input("Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("Incorrect password")
    return False

if not check_password():
    st.stop()
```

### Option B: Use Streamlit Secrets
1. Create `.streamlit/secrets.toml`:
```toml
[auth]
password = "your_secure_password_here"
```

2. Add to `.gitignore`:
```
.streamlit/secrets.toml
```

3. Use in app:
```python
if not hmac.compare_digest(password, st.secrets["auth"]["password"]):
    st.error("Access denied")
    st.stop()
```

---

## 🔧 Common Tasks

### View Logs:
```bash
# Docker
docker-compose logs -f

# Cloud
aws logs tail /ecs/territory-dashboard --follow  # AWS
az webapp log tail --name territory-dashboard    # Azure
gcloud run logs tail territory-dashboard         # GCP
```

### Update App:
```bash
# Docker
git pull
docker-compose down
docker-compose build
docker-compose up -d

# Cloud
# Push new image and deploy (see DEPLOYMENT_GUIDE.md)
```

### Scale Up:
```bash
# Docker (multiple instances)
docker-compose up --scale territory-dashboard=3

# Cloud
# Adjust replica count in console or CLI
```

### Backup Data:
```bash
# Export current data
docker exec territory-dashboard python3 -c "
import pandas as pd
df = pd.read_csv('accounts.csv')
df.to_csv('/app/output/backup.csv', index=False)
"

# Copy backup out
docker cp territory-dashboard:/app/output/backup.csv ./backup.csv
```

---

## 📊 Monitoring

### Health Check:
```bash
# Check if app is running
curl http://localhost:8501/_stcore/health

# Or visit in browser
http://your-server:8501/_stcore/health
```

### Resource Usage:
```bash
# Docker
docker stats territory-dashboard

# Cloud
# Use cloud provider's monitoring (CloudWatch, Azure Monitor, etc.)
```

---

## 🆘 Troubleshooting

### App won't start:
```bash
# Check logs
docker-compose logs -f

# Common issues:
# - Port 8501 already in use → Change port in docker-compose.yml
# - Out of memory → Increase memory limit
# - Missing dependencies → Rebuild: docker-compose build --no-cache
```

### Can't access from network:
```bash
# Check firewall
sudo ufw status
sudo ufw allow 8501

# Check Docker network
docker network inspect territory-network
```

### Performance issues:
```bash
# Increase resources in docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '4'
      memory: 4G
```

---

## 📞 Next Steps

1. **Test locally first:**
   ```bash
   streamlit run territory_dashboard.py
   ```

2. **Choose deployment method** (see decision tree above)

3. **Add authentication** (see auth examples)

4. **Deploy to test environment**

5. **Test with pilot users**

6. **Deploy to production**

7. **Monitor and maintain**

---

## 📚 Full Documentation

- **DEPLOYMENT_GUIDE.md** - Complete deployment guide with all options
- **auth_example.py** - Authentication code examples
- **Dockerfile** - Docker configuration
- **docker-compose.yml** - Docker Compose configuration
- **deploy.sh** - Automated deployment script

---

**Recommended: Start with Option 2 (Docker) for most organizations**

It provides the best balance of control, security, and ease of use.
