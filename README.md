# AI Document Intelligence Platform

An AI-powered document management and summarization platform that allows users to securely upload PDF documents, extract their text, generate intelligent summaries using Google Gemini, and manage their document history through a web interface.

🚀 **Live Demo:** https://ai-document-intelligence-e3x1.onrender.com

## Features

* 🔐 User registration and login
* 🔑 JWT-based authentication
* 🔒 Secure password hashing using bcrypt
* 📄 PDF document upload
* 📝 Automatic text extraction from PDF documents
* 🤖 AI-powered document summarization using Google Gemini
* 🧩 Chunking and Map-Reduce summarization for large documents
* 🗃️ SQLite database for storing users and document information
* 👤 User-level document authorization
* 📚 Document history
* 👀 View saved document summaries
* 🗑️ Delete documents
* 📏 50 MB file-size validation
* 🎨 Responsive web-based frontend

## Tech Stack

### Backend

* Python
* FastAPI
* SQLite
* PyMuPDF
* JWT
* bcrypt

### Frontend

* HTML
* CSS
* JavaScript

### AI

* Google Gemini API

## How It Works

```text
User
  │
  ▼
Frontend
  │
  ▼
FastAPI Backend
  │
  ├── Authentication
  │     └── JWT + bcrypt
  │
  ├── PDF Upload
  │
  ├── Text Extraction
  │     └── PyMuPDF
  │
  ├── Text Chunking
  │
  ├── AI Summarization
  │     └── Google Gemini
  │
  └── Document Storage
        └── SQLite
```

## Project Structure

```text
AI-DOCUMENT-INTELLIGENCE/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── extractor.py
│   ├── summarizer.py
│   ├── chunker.py
│   └── database.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── uploads/
├── tests/
├── requirements.txt
├── README.md
├── document_intelligence.db
└── .gitignore
```

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI-DOCUMENT-INTELLIGENCE
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment

macOS/Linux:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
```

Do not commit the `.env` file to GitHub.

## Running the Backend

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

FastAPI API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Running the Frontend

Open another terminal and run:

```bash
python3 -m http.server 5500 --directory frontend
```

Then open:

```text
http://127.0.0.1:5500
```

## API Endpoints

| Method | Endpoint          | Description                      |
| ------ | ----------------- | -------------------------------- |
| GET    | `/`               | Check API status                 |
| POST   | `/register`       | Register a new user              |
| POST   | `/login`          | Authenticate a user              |
| POST   | `/upload`         | Upload a document                |
| POST   | `/extract-text`   | Extract text from a PDF          |
| POST   | `/summarize`      | Generate an AI summary           |
| GET    | `/documents`      | Retrieve user's document history |
| GET    | `/documents/{id}` | View a specific document         |
| DELETE | `/documents/{id}` | Delete a document                |

## Authentication

The application uses JWT-based authentication.

After successful login, the backend generates an access token. Protected endpoints require the token to be sent using the Bearer authentication scheme.

```text
Authorization: Bearer <access_token>
```

Passwords are never stored as plain text. They are securely hashed using bcrypt before being stored in the database.

## AI Summarization

The application uses the Google Gemini API to generate document summaries.

For large documents, the extracted text is divided into smaller chunks. Each chunk is summarized separately, and the individual summaries are then combined into a final unified summary.

This Map-Reduce approach helps the application process documents that are too large to summarize in a single AI request.

## Database

SQLite is used for persistent storage.

The database stores information such as:

* User accounts
* Document filenames
* Extracted document text
* Generated summaries
* User-document relationships

User-level authorization ensures that users can access only their own stored documents.

## File Validation

The application validates uploaded files before processing them.

Current restrictions include:

* PDF files for text extraction and summarization
* Maximum upload size of 50 MB

Invalid file types and oversized files are rejected by the application.

## Security

The project includes several security measures:

* JWT authentication
* bcrypt password hashing
* Protected document endpoints
* User-level document authorization
* Environment variables for secrets
* File-size validation
* File-type validation
* Session expiration handling

## Future Improvements

Possible future enhancements include:

* DOCX and TXT text extraction
* Production deployment
* Cloud database integration
* Improved document search
* AI-generated document question answering
* Document tagging and categorization
* Automated backend testing
* Production-ready CORS configuration

## Author

**Pavan Adithya**

B.Tech Computer Science and Engineering
GITAM University

---

⭐ Built as a full-stack AI application combining Python, FastAPI, JavaScript, SQLite, and Google Gemini.
