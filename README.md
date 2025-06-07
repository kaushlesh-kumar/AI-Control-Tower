# AI Control Tower with MLflow AI Gateway and Admin Dashboard

This project provides an AI Gateway powered by MLflow, middleware for token-based authentication and policy enforcement, and an admin dashboard for managing users, tokens, and policies. It is designed to facilitate secure and scalable access to AI models deployed via MLflow.

---

## **Features**

1. **AI Gateway**:
   - Serves AI models via endpoints defined in `gateway_config.yml`.
   - Supports Azure OpenAI models with rate limits and quotas.

2. **Middleware**:
   - Enforces token-based authentication.
   - Validates token policies (allowed models, rate limits, quotas).
   - Logs access for auditing.

3. **Admin API**:
   - Provides endpoints for user registration, login, token creation, and policy assignment.
   - Built with FastAPI.

4. **Streamlit Admin Dashboard**:
   - Web interface for managing users, tokens, and policies.
   - Allows admins to assign policies to tokens and monitor usage.

---

## **Architecture**

The project consists of the following services:

1. **Database (`db`)**:
   - MySQL database for storing users, tokens, policies, and logs.

2. **AI Gateway (`ai_gateway`)**:
   - Serves AI models via endpoints defined in `gateway_config.yml`.

3. **Middleware (`middleware`)**:
   - Handles authentication and policy enforcement for requests to the AI Gateway.

4. **Admin API (`admin_api`)**:
   - Provides RESTful APIs for managing users, tokens, and policies.

5. **Streamlit Admin Dashboard (`streamlit_admin`)**:
   - Web-based admin interface for managing users and tokens.

6. **Nginx Proxy (`nginx`)**:
   - Acts as a reverse proxy for routing requests to the middleware.

---

## **Setup and Installation**

### **Prerequisites**
- Docker and Docker Compose installed on your system.

### **Environment Variables**
Create a `.env` file or use the provided `mlflow.env` file to configure environment variables (change the values, do not  use the default ones):
```env
DATABASE_URL=XXXXX
JWT_SECRET=XXXX
JWT_ALGORITHM=HS256
ADMIN_USERNAME=XXX
ADMIN_PASSWORD=XXXX
DEFAULT_QUOTA_LIMIT=10000
ACCESS_TOKEN_EXPIRE_MINUTES=30
