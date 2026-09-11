from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
import shutil

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.database import (
    create_user,
    delete_document,
    get_document_by_id,
    get_documents,
    get_user_by_username,
    init_db,
    save_document,
)
from app.extractor import extract_text_from_pdf
from app.summarizer import summarize_text

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )
        

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager that runs startup and shutdown events.
    Automatically initializes the SQLite database when the app starts.
    """
    init_db()
    yield


app = FastAPI(title="AI Document Intelligence", lifespan=lifespan)

# Allow local frontend development requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


# ==============================================================================
# Authentication Models & Endpoints
# ==============================================================================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str    


@app.post("/register")
def register_user(request: RegisterRequest):
    """
    Register a new user with a securely hashed password.
    
    Validates input fields, enforces minimum password length, hashes the password,
    and prevents duplicate username/email registrations.
    """
    # 1. Validate non-empty fields
    if not request.username or not request.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
    if not request.email or not request.email.strip():
        raise HTTPException(status_code=400, detail="Email cannot be empty.")
    if not request.password or not request.password.strip():
        raise HTTPException(status_code=400, detail="Password cannot be empty.")

    # 2. Enforce minimum password length (at least 8 characters)
    if len(request.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long.",
        )

    # 3. Securely hash the password (never store plain text)
    hashed_password = pwd_context.hash(request.password)

    # 4. Save the user record to the database
    user_id = create_user(
        username=request.username,
        email=request.email,
        password_hash=hashed_password,
    )

    # 5. Handle duplicate username or email
    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Username or email already exists.",
        )

    # 6. Return success response (never expose password or password hash)
    return {
        "message": "User registered successfully",
        "user_id": user_id,
    }


# ==============================================================================
# Document Processing Endpoints
# ==============================================================================

@app.get("/")
def read_root():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/style.css")
def serve_css():
    return FileResponse(FRONTEND_DIR / "style.css")


@app.get("/script.js")
def serve_js():
    return FileResponse(FRONTEND_DIR / "script.js")


@app.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 50MB."
    )

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Only {', '.join(sorted(ALLOWED_EXTENSIONS))} files are allowed.",
        )

    file_path = UPLOAD_DIR / f"{current_user['sub']}_{datetime.now().timestamp()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "message": "File uploaded successfully",
    }


@app.post("/extract-text")
def extract_text(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 50MB."
    )

    file_extension = Path(file.filename).suffix.lower()
    if file_extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only .pdf files are accepted for text extraction.",
        )

    file_path = UPLOAD_DIR / f"{current_user['sub']}_{datetime.now().timestamp()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        extracted_text = extract_text_from_pdf(str(file_path))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from the uploaded PDF. The file may be corrupted or invalid."
        )
    finally:
        file_path.unlink(missing_ok=True)

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF contains no readable text."
    )

    return {
        "filename": file.filename,
        "text": extracted_text,
        "character_count": len(extracted_text),
    }    


@app.post("/summarize")
def summarize_document(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 50MB."
    )

    file_extension = Path(file.filename).suffix.lower()
    if file_extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only .pdf files are accepted for summarization.",
        )

    # 1. Save uploaded PDF to the uploads directory
    file_path = UPLOAD_DIR / f"{current_user['sub']}_{datetime.now().timestamp()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Extract text from the PDF
    try:
        extracted_text = extract_text_from_pdf(str(file_path))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract text from the uploaded PDF. The file may be corrupted or invalid."
    )
    finally:
        file_path.unlink(missing_ok=True)
  
    # 3. Handle empty extracted text with a clear HTTP error
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF contains no readable text to summarize.",
        )

    # 4. Generate summary using the Gemini summarizer (with chunking support)
    try:
        summary = summarize_text(extracted_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate summary: {str(e)}",
        )

    # 5. Save document details and summary to SQLite database
    document_id = save_document(
        filename=file.filename,
        extracted_text=extracted_text,
        summary=summary,
        user_id=int(current_user["sub"])
    )

    return {
        "id": document_id,
        "filename": file.filename,
        "summary": summary,
    }


@app.get("/documents")
def list_documents(current_user: dict = Depends(get_current_user)):
    """
    Retrieve all previously processed and summarized documents from the database.
    """
    return get_documents(user_id=int(current_user["sub"]))


@app.get("/documents/{document_id}")
def get_document(document_id: int, current_user: dict = Depends(get_current_user)):
    """
    Retrieve a single document and its stored summary by document ID.
    Returns 404 if the document does not exist.
    """
    document = get_document_by_id(document_id, user_id=int(current_user["sub"]))
    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {document_id} not found.",
        )
    return document


@app.delete("/documents/{document_id}")
def delete_document_endpoint(document_id: int, current_user: dict = Depends(get_current_user)):
    """
    Delete a document and its stored summary from the database by ID.
    Returns 404 if the document does not exist.
    """
    deleted = delete_document(document_id, user_id=int(current_user["sub"]))
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {document_id} not found.",
        )
    return {
        "message": "Document deleted successfully",
        "id": document_id,
    }


@app.post("/login")
def login_user(request: LoginRequest):
    user = get_user_by_username(request.username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not pwd_context.verify(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    token_data = {
        "sub": str(user["id"]),
        "username": user["username"],
        "exp": datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    access_token = jwt.encode(
        token_data,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }
