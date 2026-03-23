"""File service: upload handling and text extraction from PDF/TXT files."""

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from backend.app.config import get_settings

settings = get_settings()

_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}


async def save_upload(
    file: UploadFile,
    subfolder: str = "",
) -> tuple[str, str]:
    """Save an uploaded file to the configured upload directory.

    Validates the file extension and size before saving.

    Args:
        file: The uploaded file from the request.
        subfolder: Optional subdirectory within the upload root.

    Returns:
        A tuple of ``(original_filename, saved_filepath)``.

    Raises:
        HTTPException: If the file type or size is invalid.
    """
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File type '{ext}' not allowed. "
                f"Accepted: {_ALLOWED_EXTENSIONS}"
            ),
        )

    content = await file.read()

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_file_size_mb}MB limit",
        )

    upload_dir = settings.upload_path / subfolder
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = upload_dir / safe_name

    with open(filepath, "wb") as f:
        f.write(content)

    return file.filename or "unknown", str(filepath)


def extract_text_from_pdf(filepath: str) -> str:
    """Extract text content from a PDF file.

    Args:
        filepath: Absolute path to the PDF file.

    Returns:
        The extracted text as a single string.

    Raises:
        HTTPException: If extraction fails or no text is found.
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(filepath)
        text_parts: list[str] = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        full_text = "\n".join(text_parts).strip()
        if not full_text:
            raise ValueError("No text could be extracted from the PDF")
        return full_text

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyPDF2 not installed. Run: pip install PyPDF2",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract text from PDF: {exc}",
        )


def extract_text_from_file(filepath: str) -> str:
    """Extract text from a file based on its extension.

    Delegates to specialised extractors for each file type.

    Args:
        filepath: Absolute path to the file.

    Returns:
        The extracted text content.

    Raises:
        HTTPException: If the file type is unsupported or extraction fails.
    """
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(filepath)
    if ext in (".txt", ".md"):
        with open(filepath, encoding="utf-8") as f:
            return f.read()
    if ext in (".doc", ".docx"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="DOCX parsing not yet implemented. Upload as PDF or TXT.",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported file type: {ext}",
    )
