# FinLedger

> **A production-inspired fintech backend built with FastAPI and PostgreSQL.**

FinLedger is a backend project that simulates how modern fintech companies process payments securely using digital wallets, double-entry ledgers, fraud detection, and transaction reconciliation.

---

## 🚀 Features

- User Authentication (JWT)
- Digital Wallets
- Payment Processing
- Double-Entry Ledger
- Transaction History
- Fraud Detection
- Reconciliation Engine
- REST APIs
- Docker Support

---

## 🛠 Tech Stack

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL
- **Authentication:** JWT
- **Cache:** Redis (Planned)
- **Messaging:** RabbitMQ / Kafka (Planned)
- **DevOps:** Docker, GitHub Actions
- **Cloud:** AWS / Railway

---

## 📂 Project Structure

```text
finledger/
├── app/
├── tests/
├── docs/
├── docker/
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## ▶️ Getting Started

Clone the repository:

```bash
git clone https://github.com/<your-username>/finledger.git
cd finledger
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
uvicorn app.main:app --reload
```

API Documentation:

```
http://localhost:8000/docs
```

---

## 🎯 Project Goals

- Learn fintech system architecture
- Build secure payment APIs
- Implement wallet and ledger systems
- Understand reconciliation and fraud detection
- Apply backend engineering best practices

---

## 📌 Roadmap

- [ ] Authentication
- [ ] Wallet Service
- [ ] Payment Service
- [ ] Ledger System
- [ ] Fraud Detection
- [ ] Reconciliation
- [ ] Event-Driven Architecture
- [ ] Cloud Deployment

---

