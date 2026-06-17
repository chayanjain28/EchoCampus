# EchoCampus AI - AI-Powered Student Welfare & Campus Intelligence Platform

> **Every Student Voice, Intelligently Heard.**

EchoCampus AI is an advanced, production-ready Campus Intelligence and Student Welfare Monitoring Platform. Rather than a simple, traditional complaint management portal, EchoCampus AI translates the collective voice of students into structured category routing, sentiment tracking, severity scoring, duplicate detection, and automated administrative insights.

---

## 🚀 Core Platform Highlights & AI Features

1. **AI Complaint Categorization & Routing**: Automatically parses student reports using the Google Gemini API to assign concerns into one of 8 services (Hostel, Mess, WiFi, Transport, Academic, Infrastructure, Security, or Other) and routes them to the correct department (IT Department, Hostel Warden, Mess Committee, etc.).
2. **AI Severity Scoring (0–100)**: Evaluates the safety risk, infrastructure damage, and urgency of student reports, displaying a clear urgency index.
3. **Sentiment Analysis**: Tags incoming concerns as Positive, Neutral, or Negative to monitor student distress levels.
4. **Simplified Gemini Duplicate Detection**: Compares submitted reports against recent active issues. If the similarity score exceeds `0.85`, complaints are grouped under a single parent issue with a reporter count to prevent admin overload.
5. **Campus Service Satisfaction Index (CSSI)**: Calculates a dynamic welfare health indicator out of 100 for each service department:
   $$CSSI = (0.4 \times Feedback Ratings) + (0.4 \times Resolution Ratings) + (0.2 \times Sentiment Score)$$
6. **Auto-Escalation Engine**: Automatically flags pending issues over 7 days as `Escalated`, and pending issues over 14 days as `Critical Escalation` for student welfare accountability.
7. **AI Weekly Summarizer & Trend Forecaster**: Synthesizes active reports into concise administrative bullet points and predicts spikes in service complaints based on historical context.
8. **AI Monthly Welfare Report Downloader**: Generates a detailed, executive-ready monthly report downloadable in Markdown (`.md`) or ready to print as a PDF.
9. **Voice-to-Text Dictation**: Uses the HTML5 Web Speech API to transcribe student speech in real time into report descriptions.
10. **Anonymous Reporting**: Students can mask their identity; EchoCampus AI hides user details from administrators while still allowing students to track progress inside their history.

---

## 🛠 Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy ORM
- **Database**: SQLite (No-dependency, lightweight SQL)
- **Frontend**: React.js, Vite, Tailwind CSS, Chart.js, React Router, Axios
- **AI Engine**: Google Gemini API (`gemini-1.5-flash` for classification, analysis, and reports)

---

## 📂 Project Structure

```text
echo-campus-ai/
│
├── backend/
│   ├── auth/
│   │   └── auth_handler.py       # JWT verify and role dependencies
│   ├── database/
│   │   └── connection.py         # SQLAlchemy engine & session setup
│   ├── models/
│   │   └── models.py             # User, Complaint, Feedback, Notification tables
│   ├── routes/
│   │   ├── auth.py               # User login/register
│   │   ├── complaints.py         # Submission, evidence upload, duplicate grouping
│   │   ├── feedback.py           # Ratings & messages
│   │   ├── notifications.py      # Student notifications read/unread
│   │   └── analytics.py          # CSSI charts, summarizer, welfare report
│   ├── services/
│   │   └── gemini_service.py     # Google Gemini API wrapper (with rule-based fallbacks)
│   ├── utils/
│   │   └── security.py           # PBKDF2 password hashing & pure JWT helper
│   ├── main.py                   # FastAPI initialization & static file mount
│   ├── seed.py                   # Initial database seeder
│   └── test_backend.py           # API integration verification script
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx# Auth routing lock
│   │   │   └── Toast.jsx         # Custom slide-in notifications
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Auth registration state & tokens
│   │   ├── pages/
│   │   │   ├── LandingPage.jsx   # Public dashboard with transparency stats
│   │   │   ├── LoginPage.jsx     # Glassmorphic user login
│   │   │   ├── RegisterPage.jsx  # Glassmorphic user signup
│   │   │   ├── StudentDashboard.jsx # Dictation form, history, notifications, satisfaction rating
│   │   │   └── AdminDashboard.jsx # Executive KPIs, CSSI bar charts, AI summary, welfare downloader
│   │   ├── services/
│   │   │   └── api.js            # Axios client with interceptors
│   │   ├── App.jsx               # Route mapping
│   │   ├── index.css             # Tailwind directives & Outfit font setup
│   │   └── main.jsx              # React initialization
│   ├── tailwind.config.js        # Color palette and font configuration
│   ├── postcss.config.js         # CSS compiler config
│   ├── index.html                # Entry HTML title
│   └── package.json              # npm package list
└── README.md
```

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key (Optional; fallbacks to rule-based parser if empty)

### 1. Backend Setup
Navigate to the `backend` folder, install requirements, set up your environment variables, and run the database seeder:

```bash
# Go to project directory
cd echo-campus-ai

# Install Python requirements
pip install sqlalchemy fastapi uvicorn pydantic[email] python-multipart google-generativeai python-dotenv httpx

# Set environment variables (Optional but recommended)
# Windows CMD:
set GEMINI_API_KEY=your_actual_gemini_api_key
# Windows PowerShell:
$env:GEMINI_API_KEY="your_actual_gemini_api_key"

# Initialize and Seed Database
python backend/seed.py

# Start Backend Server
python backend/main.py
```
The backend API server will start at `http://localhost:8000`. You can inspect the Swagger interactive API docs at `http://localhost:8000/docs`.

### 2. Frontend Setup
Open a new terminal session, navigate to the `frontend` folder, install node packages, and launch Vite dev server:

```bash
# Go to frontend folder
cd echo-campus-ai/frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev
```
The React frontend application will launch at `http://localhost:5173`.

---

## 🔑 Demo Credentials

| Role | Username / Email | Password |
|---|---|---|
| **Student** | `student@echocampus.edu` | `password123` |
| **Administrator** | `admin@echocampus.edu` | `admin123` |

You can also create a new student or admin account instantly using the **Create Account** button on the sign-up view.

---

## 🧪 Running Automated Tests
We have built an integration test suite validating authorization, AI routing, duplicate checks, feedback loops, and report compilation:

```bash
# From echo-campus-ai root folder
python backend/test_backend.py
```
All endpoints will run in-memory using `TestClient` and output a validation summary.

---

## 📡 API Documentation Overview

### Authentication
- `POST /api/auth/register`: Create user, return access token and user information.
- `POST /api/auth/login`: Validate password, return JWT token.
- `GET /api/auth/me`: Get profile details (Protected).

### Complaints
- `POST /api/complaints`: File a new concern (runs Gemini categorization, sentiment, severity score, routes department, checks duplicates).
- `GET /api/complaints`: Lists complaints (Filtered to own if student, lists all if admin).
- `GET /api/complaints/{id}`: Detailed view of issue, lists duplicate child links & AI recommendations.
- `PUT /api/complaints/{id}/status`: Admin updates status (Pending, In Progress, Resolved, Rejected, Escalated) and routes.
- `POST /api/complaints/{id}/rate-resolution`: Student rates the resolution quality (1–5 stars).
- `POST /api/complaints/upload-evidence`: Upload proof image.

### Feedback
- `POST /api/feedback`: Submit category-specific ratings (1–5 stars).
- `GET /api/feedback`: Admin retrieves all campus feedbacks.

### Analytics & Reporting
- `GET /api/analytics/dashboard`: Computes Campus Health Score, student satisfaction, efficiency rates, and department CSSI scores.
- `GET /api/analytics/summary`: Synthesizes active concerns into Live AI summaries.
- `GET /api/analytics/welfare-report`: Dynamically compiles monthly Markdown executive report.
- `GET /api/analytics/predictions`: Predicts upcoming complaint spikes based on current loads.
