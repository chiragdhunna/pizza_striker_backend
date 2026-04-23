# 🍕 Pizza Striker Backend

Welcome to the **Pizza Striker Backend** repository — the backend service for a fun, strike-based gamified application built for office teams! In this app, employees who goof up get a _strike_, and once they collect 3 strikes, they owe everyone a **pizza party**! 🎉

---

## 🚀 Project Overview

This backend powers the **Pizza Striker** app which keeps track of employees, their strikes, and the rules of engagement. It ensures everyone follows the fun, and nobody escapes their cheesy fate. 😄

---

## 🛠️ Tech Stack

- **Language**: Python 🐍
- **Framework**: FastAPI
- **Database**: PostgreSQL 16 (Docker container)
- **ORM**: SQLAlchemy 2.0 (async with `asyncpg`)
- **Migrations**: Alembic
- **Authentication**: JWT-based login with RBAC (admin / employee)
- **Containerization**: Docker Compose (separate containers for backend + database)

---

## 🔐 Features

- ✅ User authentication (JWT access + refresh tokens)
- 🛂 Role-based access control (admin, employee)
- 📌 Admin can add/revoke strikes for employees
- 📜 Strike history tracking for every user
- 🍕 Auto-trigger pizza party event after 3 strikes (strikes reset to 0)
- 🔔 In-app notifications for strikes, revocations, and pizza events
- 📊 Admin dashboard with stats, leaderboard, activity feed, and strike trends

---

## 📦 Setup Instructions

### Option 1: Docker (Recommended)

1. **Clone the repository**

```bash
git clone https://github.com/chiragdhunna/pizza-striker-backend.git
cd pizza-striker-backend
```

2. **Create a `.env` file**

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=pizza_admin
POSTGRES_PASSWORD=pizza_secret_123
POSTGRES_DB=pizza_striker
DATABASE_URL=postgresql+asyncpg://pizza_admin:pizza_secret_123@db:5432/pizza_striker

JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

APP_ENV=development
APP_DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

3. **Start both containers**

```bash
docker-compose up --build
```

The backend will be available at `http://localhost:8080` and PostgreSQL at `localhost:5432`.

### Option 2: Local Development

1. **Clone and set up virtual environment**

```bash
git clone https://github.com/chiragdhunna/pizza-striker-backend.git
cd pizza-striker-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start PostgreSQL** (via Docker or local install)

```bash
docker run -d --name pizza_db -e POSTGRES_USER=pizza_admin -e POSTGRES_PASSWORD=pizza_secret_123 -e POSTGRES_DB=pizza_striker -p 5432:5432 postgres:16-alpine
```

3. **Create `.env`** with `DATABASE_URL=postgresql+asyncpg://pizza_admin:pizza_secret_123@localhost:5432/pizza_striker` (and other vars from above)

4. **Run migrations and start the server**

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

---

## 🐳 Docker Setup

Two separate containers managed by Docker Compose:

| Container           | Image              | Port | Purpose             |
| ------------------- | ------------------ | ---- | ------------------- |
| `pizza_striker_db`  | postgres:16-alpine | 5432 | PostgreSQL database |
| `pizza_striker_app` | Custom (Python)    | 8080 | FastAPI backend     |

```bash
# Start
docker-compose up --build -d

# View logs
docker-compose logs -f app
docker-compose logs -f db

# Stop
docker-compose down

# Fresh start (delete data)
docker-compose down -v
```

### Connecting to the Database

```bash
# From host
psql -h localhost -p 5432 -U pizza_admin -d pizza_striker

# Via Docker
docker exec -it pizza_striker_db psql -U pizza_admin -d pizza_striker
```

---

## 🧪 Running Tests

```bash
pytest
```

---

## 🔗 Frontend Repository

Flutter app: [pizza_striker](https://github.com/chiragdhunna/pizza_striker)

---

## 📂 Folder Structure

```
pizza_striker_backend/
├── app/
│   ├── main.py                  # FastAPI app initialization, CORS, lifespan
│   ├── config.py                # Settings from .env
│   ├── database.py              # SQLAlchemy async engine, sessionmaker
│   ├── models.py                # SQLAlchemy ORM models
│   ├── auth/                    # Login, register, JWT, RBAC
│   ├── users/                   # User profile endpoints
│   ├── strikes/                 # Strike endpoints (employee view)
│   ├── pizza_events/            # Pizza event endpoints
│   ├── notifications/           # Notification endpoints
│   ├── admin/                   # Admin panel (users, strikes, events, dashboard)
│   └── utils/                   # Pagination, response helpers
├── alembic/                     # Database migrations
├── tests/                       # Pytest test suite
├── Dockerfile                   # Backend container
├── docker-compose.yml           # Backend + PostgreSQL
├── requirements.txt
└── PLAN.md                      # Detailed development plan
```

---

---

---

## 👨‍💻 Author

Built with ❤️ by [Chirag Dhunna](https://github.com/chiragdhunna)

---

Happy Striking and don't forget to bring the pizza! 🍕
