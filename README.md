# 🚀 Real-Time Chat Application CI/CD Pipeline (Flask, MySQL, Jenkins)

This project demonstrates a complete DevOps pipeline for a two-tier, real-time web application.

## ⚙️ Architecture and Tools

| Component | Tool | Role |
| :--- | :--- | :--- |
| **Application** | Flask-SocketIO | Real-time messaging and web server. |
| **Database** | MySQL 8.0 | Stores chat history persistently. |
| **Containerization** | Docker & Docker Compose | Packages the app and database services. |
| **CI/CD** | Jenkins & GitHub | Automates build, test, and deployment upon code commit. |

## 📦 How to Run Locally (Phase 1)

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yourusername/pj1.git](https://github.com/yourusername/pj1.git)
    cd pj1
    ```
2.  **Start Services:** Ensure Docker Desktop is running.
    ```bash
    docker compose up --build -d
    ```
3.  **Access:** Open your browser to `http://localhost:5000`.

## 🤖 Deployment Pipeline (Phase 2: Jenkins)

The `Jenkinsfile` defines the following stages executed on the Jenkins server:
1.  **Checkout Code:** Pulls the latest code from this repository.
2.  **Build Image:** Creates a new Docker image (`chat-app:build-XXX`).
3.  **Push Image:** Pushes the new image to Docker Hub.
4.  **Deploy Containers:** Executes `docker compose down` (stops old) and `docker compose up -d` (starts new) on the target server.
