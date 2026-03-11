"""
Session-based PDF storage using temporary files
"""
import uuid
import os
import time
from pathlib import Path
from typing import Optional

UPLOAD_DIR = Path("/tmp/pdf_uploads")
SESSION_TIMEOUT = 1800  # 30 minutes

class SessionManager:
    def __init__(self):
        UPLOAD_DIR.mkdir(exist_ok=True)

    def create_session(self, pdf_contents: bytes) -> str:
        """Save PDF to temp file and return session ID"""
        session_id = str(uuid.uuid4())
        filepath = UPLOAD_DIR / f"{session_id}.pdf"

        with open(filepath, 'wb') as f:
            f.write(pdf_contents)

        self._cleanup_old_files()
        return session_id

    def get_pdf_path(self, session_id: str) -> Optional[str]:
        """Get file path for session ID"""
        filepath = UPLOAD_DIR / f"{session_id}.pdf"
        if filepath.exists():
            return str(filepath)
        return None

    def delete_session(self, session_id: str):
        """Delete session file"""
        filepath = UPLOAD_DIR / f"{session_id}.pdf"
        if filepath.exists():
            filepath.unlink()

    def _cleanup_old_files(self):
        """Remove files older than SESSION_TIMEOUT"""
        if not UPLOAD_DIR.exists():
            return

        current_time = time.time()
        for filepath in UPLOAD_DIR.glob("*.pdf"):
            if current_time - filepath.stat().st_mtime > SESSION_TIMEOUT:
                filepath.unlink()

session_manager = SessionManager()
