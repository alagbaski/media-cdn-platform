# Media CDN Platform

A production-grade Media Content Delivery Network (CDN) platform designed for high-performance file uploads and edge-optimized delivery. This solution leverages **NGINX** as a high-speed static file server and **FastAPI** as a robust application backend.

## 🏗 Architecture

The platform follows a classic **Edge/Origin** architecture where NGINX acts as the intelligent edge layer, serving cached/static media directly from disk while proxying dynamic API requests to the origin backend.

```mermaid
graph TD
    subgraph "Client Layer"
        C1[Browser / API Client]
    end

    subgraph "Edge Layer (NGINX:8080)"
        N1[CDN Router]
        N2[Static Media Handler]
        N3[API Proxy Handler]
    end

    subgraph "Application Layer (FastAPI:8000)"
        F1[FastAPI Backend]
        F2[Upload Service]
        F3[Health/Metrics]
    end

    subgraph "Storage Layer"
        S1[(Local Filesystem /storage/uploads)]
    end

    %% Flow: Media Retrieval
    C1 -- GET /media/{file} --> N2
    N2 -- Direct Disk Read --> S1

    %% Flow: API Request
    C1 -- API Requests --> N3
    N3 -- Proxy Pass --> F1

    %% Flow: Upload
    F1 -- "save_file()" --> F2
    F2 -- Write to Disk --> S1

    style Edge Layer fill:#f9f,stroke:#333,stroke-width:2px
    style Application Layer fill:#bbf,stroke:#333,stroke-width:2px
    style Storage Layer fill:#dfd,stroke:#333,stroke-width:2px
```

### Key Design Decisions
- **Static CDN Mode**: NGINX serves media directly from the filesystem. This bypasses the Python interpreter entirely for binary delivery, ensuring ultra-low latency and maximum concurrency.
- **Unified Storage Volume**: A shared Docker volume between NGINX and the Backend ensures that uploaded files are immediately available for serving at the edge.
- **Edge Caching Headers**: NGINX is configured to inject immutable cache headers for media assets, allowing browsers and downstream CDNs to cache content for up to 1 year.

---

## 🚀 Features

- ✅ **High-Performance Delivery**: Minimal overhead via NGINX `alias` serving.
- ✅ **Edge Caching**: Pre-configured `Cache-Control` headers for optimal browser behavior.
- ✅ **Deterministic 404s**: No phantom caching of failed requests.
- ✅ **DevOps Friendly**: Fully containerized with Docker Compose.
- ✅ **API First**: Clean FastAPI backend with automatic Swagger/ReDoc documentation.

---

## 🛠 Tech Stack

- **Edge Proxy**: NGINX (latest)
- **Backend**: FastAPI (Python 3.12)
- **Process Manager**: Gunicorn (Uvicorn Workers)
- **Containerization**: Docker & Docker Compose
- **Storage**: Local Filesystem (POSIX-compliant)

---

## 📡 API Endpoints

### Media Operations
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **POST** | `/api/v1/media/upload` | Upload a new media file (Multipart Form) |
| **GET** | `/api/v1/media/` | List all available media files |
| **GET** | `/media/{filename}` | Retrieve a specific media file (Served by NGINX) |

### System Health
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/v1/health` | Basic liveness check |
| **GET** | `/api/v1/health/ready`| Readiness check (verifies storage connectivity) |

---

## 📦 Setup & Deployment

1. **Clone and Initialize**:
   ```bash
   git clone <repository-url>
   cd media-cdn-platform
   ```

2.  **Environment Setup**:
    ```bash
    cp .env.example .env
    ```

3. **Start the Platform**:
   ```bash
   docker-compose up --build -d
   ```

---

## 🧪 Usage Examples

### 1. Upload a File
```bash
curl -F "file=@my_image.jpg" http://localhost:8080/api/v1/media/upload
```

### 2. Retrieve Media (Edge)
```bash
curl -I http://localhost:8080/media/my_image.jpg
```
*Observe the `Cache-Control: public, max-age=31536000, immutable` header.*

### 3. Check Health
```bash
curl http://localhost:8080/api/v1/health/ready
```
