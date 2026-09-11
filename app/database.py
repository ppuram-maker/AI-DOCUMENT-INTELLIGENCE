import sqlite3
from pathlib import Path

# Path to the SQLite database file in the project root directory
DB_PATH = Path(__file__).resolve().parent.parent / "document_intelligence.db"


def get_db_connection() -> sqlite3.Connection:
    """
    Establish and return a connection to the SQLite database.
    Using sqlite3.Row allows accessing columns by name like a Python dictionary.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """
    Create the database tables if they do not already exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
            """
        )

        # Create documents table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                extracted_text TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER
            )
            """
        )

        # Add user_id to older databases if it doesn't exist
        cursor.execute("PRAGMA table_info(documents)")
        columns = [row[1] for row in cursor.fetchall()]

        if "user_id" not in columns:
            cursor.execute(
                "ALTER TABLE documents ADD COLUMN user_id INTEGER"
            )

        conn.commit()


# ==============================================================================
# Document Database Operations
# ==============================================================================

def save_document(
    filename: str,
    extracted_text: str,
    summary: str,
    user_id: int
) -> int:
    """
    Save a processed document and associate it with the logged-in user.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (
                filename,
                extracted_text,
                summary,
                user_id
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                filename,
                extracted_text,
                summary,
                user_id
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_documents(user_id: int) -> list[dict]:
    """
    Retrieve documents belonging only to the specified user.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, filename, summary, created_at
            FROM documents
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_document_by_id(document_id: int, user_id: int) -> dict | None:
    """
    Retrieve a document only if it belongs to the specified user.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, filename, extracted_text, summary, created_at
            FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (document_id, user_id),
        )
        row = cursor.fetchone()

        if row:
            return dict(row)

        return None


def delete_document(document_id: int, user_id: int) -> bool:
    """
    Delete a document record from the database by its ID.

    Args:
        document_id: The integer ID of the document to delete.
        user_id: The integer ID of the user who owns the document.

    Returns:
        bool: True if a document was deleted, False if no document with that ID exists.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM documents
            WHERE id = ? AND user_id = ?
            """,
            (document_id, user_id),
        )
        conn.commit()
        # cursor.rowcount returns the number of deleted rows
        return cursor.rowcount > 0


# ==============================================================================
# User Authentication Database Operations
# ==============================================================================

def create_user(username: str, email: str, password_hash: str) -> int | None:
    """
    Insert a new user record into the database.
    
    Uses parameterized SQL queries to prevent SQL injection.
    Gracefully handles duplicate username or email by returning None if an IntegrityError occurs.

    Args:
        username: Unique username for the user.
        email: Unique email address for the user.
        password_hash: Securely hashed password string (never plain text).

    Returns:
        int | None: The new user's ID on success, or None if username/email already exists.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (username.strip(), email.strip().lower(), password_hash),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # Username or email already exists in the database
        return None


def get_user_by_id(user_id: int) -> dict | None:
    """
    Retrieve a user record by ID.
    Used for testing/verification.

    Args:
        user_id: The integer ID of the user.

    Returns:
        dict | None: The user record as a dictionary, or None if not found.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
def get_user_by_username(username: str) -> dict | None:
    """
    Retrieve a user by username.

    Returns:
        dict | None: User details if found, otherwise None.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE username = ?
            """,
            (username,),
        )
        row = cursor.fetchone()

        if row:
            return dict(row)

        return None