# 🍕 Pizza Striker Backend

Welcome to the **Pizza Striker Backend** repository — the backend service for a fun, strike-based gamified application built for office teams! In this app, employees who goof up get a _strike_, and once they collect 3 strikes, they owe everyone a **pizza party**! 🎉

---

## 🚀 Project Overview

This backend powers the **Pizza Striker** app which keeps track of employees, their strikes, and the rules of engagement. It ensures everyone follows the fun, and nobody escapes their cheesy fate. 😄

---

## 🛠️ Tech Stack

- **Language**: Python 🐍
- **Framework**: TBD (FastAPI or Flask)
- **Database**: SQLite (for dev) / PostgreSQL (for production)
- **ORM**: SQLAlchemy (TBD)
- **Authentication**: JWT-based login
- **Deployment**: Docker + Render

---

## 🔐 Features

- ✅ User authentication (login required)
- 🛂 Role-based access (admin, employee)
- 📌 Admin can add strikes; future: allow self-reporting with approval
- 📜 Strike history tracking for every user
- 🍕 Auto-trigger event after 3 strikes — initiates a pizza party notification
- 🧾 API for user, strike, and summary management
- 📊 Admin dashboard endpoints for summary & monitoring

---

## 📦 Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/chiragdhunna/pizza-striker-backend.git
cd pizza-striker-backend
```

2. **Create virtual environment and install dependencies**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Environment Configuration**
   Create a `.env` file:

```env
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=supersecretkey
```

4. **Run the server**

```bash
uvicorn app.main:app --reload
```

---

## 🐳 Docker Setup

Coming soon. This project will support Docker-first deployments, ideal for cloud platforms like Render.

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
app/
├── main.py
├── models/
├── routes/
├── schemas/
├── services/
├── auth/
└── utils/
```

---

## 📌 To-Do

- [ ] Finalize choice of FastAPI or Flask
- [ ] Add Docker support
- [ ] Define database schema and create migrations
- [ ] Implement strike limit logic & pizza party trigger
- [ ] Integrate frontend with API
- [ ] Future: Add Slack/email notification on 3 strikes

---

## 👨‍💻 Author

Built with ❤️ by [Chirag Dhunna](https://github.com/chiragdhunna)

---

Happy Striking and don't forget to bring the pizza! 🍕
