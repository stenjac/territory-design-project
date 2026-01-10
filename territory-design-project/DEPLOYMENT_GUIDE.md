# Internal Deployment Guide

This guide covers multiple options for deploying the Territory Dashboard internally within your organization.

---

## 🎯 Deployment Options Overview

| Option | Best For | Cost | Difficulty | Access Control |
|--------|----------|------|------------|----------------|
| **Streamlit Cloud** | Quick demos, small teams | Free/Paid | Easy ⭐ | Basic SSO |
| **Docker + Internal Server** | Full control, IT managed | Infrastructure only | Medium ⭐⭐ | VPN/Firewall |
| **AWS/Azure/GCP** | Enterprise, scalable | Pay-as-you-go | Medium ⭐⭐ | IAM/AD integration |
| **Kubernetes** | Large orgs, microservices | Infrastructure + ops | Hard ⭐⭐⭐ | Full enterprise auth |
| **Local Network Share** | Very small teams | Free | Easy ⭐ | Network only |

---

## 🚀 Option 1: Streamlit Community Cloud (Quickest)

**Best for:** Quick prototypes, demos, small teams (< 20 users)

### Pros:
- ✅ Fastest deployment (5 minutes)
- ✅ No infrastructure needed
- ✅ Auto-updates from GitHub
- ✅ Free tier available
- ✅ Basic password protection

### Cons:
- ❌ Public unless on paid plan
- ❌ Limited customization
- ❌ Resource limits on free tier

### Steps:

1. **Push code to GitHub** (already done!)

2. **Go to Streamlit Cloud**:
   - Visit: https://streamlit.io/cloud
   - Sign in with GitHub

3. **Deploy**:
   - Click "New app"
   - Select your repository: `territory-design-project`
   - Main file: `territory_dashboard.py`
   - Click "Deploy"

4. **Add Password Protection** (Community Cloud Teams):
   - Requires paid plan ($250/month for team)
   - Settings → Secrets → Add viewer authentication

5. **Share with team**:
   - Get URL: `https://YOUR-APP-NAME.streamlit.app`
   - Share link with team members

### Making it "Internal Only":

**Option A - Password Protection:**
Add this to the top of `territory_dashboard.py`:

```python
import streamlit as st
import hmac

def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], "YOUR_ORG_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

if not check_password():
    st.stop()

# Rest of your app code...
```

**Option B - IP Allowlist** (Enterprise plan only):
- Configure IP allowlist in Streamlit Cloud settings
- Only allow your corporate IPs

---

## 🐳 Option 2: Docker + Internal Server (Recommended for IT)

**Best for:** Organizations with IT infrastructure, 20-500 users

### Pros:
- ✅ Full control over infrastructure
- ✅ Deploy on internal network
- ✅ Integrate with corporate auth (LDAP/AD)
- ✅ No external dependencies
- ✅ Customizable resources

### Cons:
- ❌ Requires server maintenance
- ❌ Need IT/DevOps involvement

### Step 1: Create Dockerfile

```bash
# Create Dockerfile in project root
cat > Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY *.csv .
COPY *.png .
COPY *.md .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the app
ENTRYPOINT ["streamlit", "run", "territory_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
EOF
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  territory-dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ENABLE_CORS=false
      - STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
    volumes:
      - ./data:/app/data  # Optional: for dynamic data updates
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

### Step 3: Deploy on Internal Server

```bash
# On your internal server (Linux/Windows Server)

# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 2. Clone your repository
git clone https://github.com/YOUR_USERNAME/territory-design-project.git
cd territory-design-project

# 3. Build and run
docker-compose up -d

# 4. Check status
docker-compose ps
docker-compose logs -f

# Access at: http://YOUR_SERVER_IP:8501
```

### Step 4: Add Authentication (Nginx Reverse Proxy)

```nginx
# /etc/nginx/sites-available/territory-dashboard

server {
    listen 80;
    server_name territory-dashboard.yourcompany.internal;

    # Basic Auth
    auth_basic "Territory Dashboard - Company Access Only";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_read_timeout 86400;
    }
}
```

Create password file:
```bash
sudo htpasswd -c /etc/nginx/.htpasswd username
```

### Step 5: SSL/HTTPS (Optional but Recommended)

```bash
# Using Let's Encrypt (if externally accessible)
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d territory-dashboard.yourcompany.com

# Or use your corporate SSL certificate
# Place cert files and configure nginx
```

---

## ☁️ Option 3: Cloud Deployment (AWS/Azure/GCP)

**Best for:** Enterprise organizations, 100+ users, high availability

### AWS Deployment (Using ECS Fargate)

**Step 1: Push Docker Image to ECR**

```bash
# Login to AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create repository
aws ecr create-repository --repository-name territory-dashboard

# Build and push
docker build -t territory-dashboard .
docker tag territory-dashboard:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/territory-dashboard:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/territory-dashboard:latest
```

**Step 2: Create ECS Task Definition**

```json
{
  "family": "territory-dashboard",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "territory-dashboard",
      "image": "YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/territory-dashboard:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/territory-dashboard",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Step 3: Deploy with Application Load Balancer**

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name territory-dashboard-cluster

# Create ECS service with ALB
aws ecs create-service \
  --cluster territory-dashboard-cluster \
  --service-name territory-dashboard-service \
  --task-definition territory-dashboard \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=territory-dashboard,containerPort=8501"
```

**Step 4: Configure AWS Cognito for SSO**

```python
# Add to territory_dashboard.py for AWS Cognito auth
import streamlit as st
from aws_cognito_auth import authenticate

user = authenticate()
if not user:
    st.stop()

st.write(f"Welcome, {user['name']} ({user['email']})")
# Rest of app...
```

### Azure Deployment (Using App Service)

```bash
# Login to Azure
az login

# Create resource group
az group create --name territory-dashboard-rg --location eastus

# Create App Service plan
az appservice plan create \
  --name territory-dashboard-plan \
  --resource-group territory-dashboard-rg \
  --sku B1 \
  --is-linux

# Create web app from container
az webapp create \
  --resource-group territory-dashboard-rg \
  --plan territory-dashboard-plan \
  --name territory-dashboard-app \
  --deployment-container-image-name YOUR_DOCKERHUB/territory-dashboard:latest

# Configure app settings
az webapp config appsettings set \
  --resource-group territory-dashboard-rg \
  --name territory-dashboard-app \
  --settings WEBSITES_PORT=8501

# Enable Azure AD authentication
az webapp auth update \
  --resource-group territory-dashboard-rg \
  --name territory-dashboard-app \
  --enabled true \
  --action LoginWithAzureActiveDirectory
```

### GCP Deployment (Using Cloud Run)

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/territory-dashboard

# Deploy to Cloud Run
gcloud run deploy territory-dashboard \
  --image gcr.io/YOUR_PROJECT_ID/territory-dashboard \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --max-instances 10 \
  --memory 2Gi \
  --cpu 2

# Add IAM authentication (requires Google Workspace)
gcloud run services add-iam-policy-binding territory-dashboard \
  --member='domain:yourcompany.com' \
  --role='roles/run.invoker'
```

---

## 🏢 Option 4: Enterprise Kubernetes Deployment

**Best for:** Large organizations with existing K8s infrastructure

### Kubernetes Manifests

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: territory-dashboard
  namespace: sales-ops
spec:
  replicas: 3
  selector:
    matchLabels:
      app: territory-dashboard
  template:
    metadata:
      labels:
        app: territory-dashboard
    spec:
      containers:
      - name: territory-dashboard
        image: your-registry/territory-dashboard:latest
        ports:
        - containerPort: 8501
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /_stcore/health
            port: 8501
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: territory-dashboard
  namespace: sales-ops
spec:
  selector:
    app: territory-dashboard
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8501
  type: LoadBalancer
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: territory-dashboard
  namespace: sales-ops
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: basic-auth
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - territory.yourcompany.com
    secretName: territory-dashboard-tls
  rules:
  - host: territory.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: territory-dashboard
            port:
              number: 80
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml
```

---

## 🔐 Authentication & Access Control

### Option A: Basic Authentication (Simple)

```python
# Add to territory_dashboard.py
import streamlit as st
import hmac

def check_auth():
    def password_entered():
        if hmac.compare_digest(
            st.session_state["username"],
            st.secrets["auth"]["username"]
        ) and hmac.compare_digest(
            st.session_state["password"],
            st.secrets["auth"]["password"]
        ):
            st.session_state["authenticated"] = True
            del st.session_state["username"]
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    if st.session_state.get("authenticated", False):
        return True

    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=password_entered)

    if "authenticated" in st.session_state and not st.session_state["authenticated"]:
        st.error("Invalid credentials")
    return False

if not check_auth():
    st.stop()
```

Create `.streamlit/secrets.toml`:
```toml
[auth]
username = "sales_ops"
password = "your_secure_password_here"
```

### Option B: LDAP/Active Directory Integration

```python
# Install: pip install python-ldap3
from ldap3 import Server, Connection, ALL

def authenticate_ldap(username, password):
    server = Server('ldap.yourcompany.com', get_info=ALL)
    try:
        conn = Connection(
            server,
            user=f'DOMAIN\\{username}',
            password=password,
            auto_bind=True
        )
        return True
    except:
        return False

# In your app
if not st.session_state.get("authenticated"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_ldap(username, password):
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()
```

### Option C: OAuth2/SAML (Enterprise SSO)

```python
# Install: pip install streamlit-oauth
from streamlit_oauth import OAuth2Component

# Configure OAuth
oauth2 = OAuth2Component(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    authorize_endpoint="https://login.microsoftonline.com/YOUR_TENANT/oauth2/v2.0/authorize",
    token_endpoint="https://login.microsoftonline.com/YOUR_TENANT/oauth2/v2.0/token",
    refresh_token_endpoint="https://login.microsoftonline.com/YOUR_TENANT/oauth2/v2.0/token",
)

# Authenticate
result = oauth2.authorize_button(
    name="Login with Microsoft",
    redirect_uri="https://territory.yourcompany.com",
    scope="openid email profile",
)

if result and 'token' in result:
    st.session_state['user'] = result
else:
    st.stop()
```

---

## 📊 Data Source Integration

### Option 1: Connect to Internal Database

```python
# Install: pip install sqlalchemy psycopg2-binary
import pandas as pd
from sqlalchemy import create_engine

# Connect to corporate database
@st.cache_resource
def get_database_connection():
    engine = create_engine(
        'postgresql://user:password@internal-db.yourcompany.com:5432/sales'
    )
    return engine

# Load live data instead of CSV
def load_accounts():
    engine = get_database_connection()
    query = """
        SELECT
            account_name,
            account_size,
            current_owner,
            estimated_annual_value,
            customer_status
        FROM accounts
        WHERE active = true
    """
    df = pd.read_sql(query, engine)
    return df

# Replace CSV loading with database
accounts = load_accounts()
```

### Option 2: Salesforce Integration

```python
# Install: pip install simple-salesforce
from simple_salesforce import Salesforce

@st.cache_resource
def get_sf_connection():
    sf = Salesforce(
        username='user@yourcompany.com',
        password='password',
        security_token='token'
    )
    return sf

def load_sf_accounts():
    sf = get_sf_connection()
    query = """
        SELECT Name, AnnualRevenue, OwnerId, Type
        FROM Account
        WHERE IsDeleted = false
    """
    data = sf.query_all(query)
    df = pd.DataFrame(data['records'])
    return df
```

### Option 3: File Share / Network Drive

```python
# Mount corporate file share
import os

# Windows network share
NETWORK_PATH = r'\\fileserver\sales_ops\data\accounts.csv'

# Or NFS mount (Linux)
NFS_PATH = '/mnt/sales_ops/data/accounts.csv'

df = pd.read_csv(NETWORK_PATH)
```

---

## 📈 Scaling & Performance

### Add Caching for Large Datasets

```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_accounts():
    return pd.read_csv('accounts.csv')

@st.cache_data(ttl=600)  # Cache for 10 minutes
def run_analysis(df):
    # Heavy computation
    return results
```

### Load Balancing (Multiple Instances)

```bash
# Docker Compose with multiple replicas
docker-compose up --scale territory-dashboard=3
```

### Resource Limits

```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

---

## 🔒 Security Best Practices

1. **Never commit credentials**
   - Use `.streamlit/secrets.toml` (in .gitignore)
   - Or environment variables

2. **Enable HTTPS**
   - Use SSL/TLS certificates
   - Enforce HTTPS redirects

3. **Input validation**
   - Sanitize file uploads
   - Validate user inputs

4. **Network security**
   - Deploy behind firewall
   - Use VPN for access
   - Restrict to corporate IPs

5. **Audit logging**
   ```python
   import logging
   logging.info(f"User {username} accessed dashboard at {datetime.now()}")
   ```

---

## 📋 Deployment Checklist

- [ ] Choose deployment method
- [ ] Set up infrastructure (server/cloud)
- [ ] Configure authentication
- [ ] Set up SSL/HTTPS
- [ ] Test with pilot users
- [ ] Configure data sources
- [ ] Set up monitoring/logging
- [ ] Create backup strategy
- [ ] Document access procedures
- [ ] Train users
- [ ] Plan maintenance windows

---

## 🆘 Troubleshooting

### App won't start
```bash
# Check logs
docker logs territory-dashboard
# Or
docker-compose logs -f
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8502:8501"  # Use 8502 instead
```

### Memory issues
```bash
# Increase memory limit
docker update --memory 4g territory-dashboard
```

### Connection refused
- Check firewall rules
- Verify VPN connection
- Check server IP/port

---

## 📞 Getting Help

- **IT/DevOps Team**: For infrastructure setup
- **Security Team**: For authentication/authorization
- **Streamlit Docs**: https://docs.streamlit.io/deploy
- **Docker Docs**: https://docs.docker.com
- **Cloud Provider Docs**: AWS/Azure/GCP documentation

---

**Recommended: Start with Option 2 (Docker + Internal Server) for most organizations**
