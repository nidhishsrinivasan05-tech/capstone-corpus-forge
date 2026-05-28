import os
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".pdf", ".py", ".js", ".html", ".css", ".java", ".c", ".cpp",
    ".json", ".xml", ".csv", ".docx", ".ts", ".jsx", ".tsx", ".go", ".rb",
    ".php", ".swift", ".kt", ".cs", ".sh", ".bash", ".yaml", ".yml", ".toml",
    ".rst", ".tex", ".markdown"
}

# Code file extensions for syntax highlighting
CODE_EXTENSIONS = {
    ".py", ".js", ".html", ".css", ".java", ".c", ".cpp", ".ts", ".jsx", ".tsx",
    ".go", ".rb", ".php", ".swift", ".kt", ".cs", ".sh", ".bash", ".yaml", ".yml"
}

# Binary file patterns to skip
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".exe", ".dll", ".so", ".dylib",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv",
    ".ttf", ".otf", ".woff", ".woff2", ".eot"
}

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
MIN_EXTRACTED_CHARACTERS = 20
MAX_LARGE_FILE_SIZE = 500 * 1024  # 500KB for text extraction limit warning


class DocumentProcessingError(ValueError):
    pass


def allowed_file(filename: str) -> bool:
    """Check if file extension is supported for processing."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in SUPPORTED_EXTENSIONS


def is_binary_file(filename: str) -> bool:
    """Check if file is likely binary based on extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in BINARY_EXTENSIONS


def is_code_file(filename: str) -> bool:
    """Check if file is a code file for syntax highlighting."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in CODE_EXTENSIONS


def validate_upload(path: str) -> None:
    """Validate uploaded file exists and meets size requirements."""
    file_path = Path(path)
    if not file_path.exists():
        raise DocumentProcessingError("The uploaded file was not saved correctly.")

    size = file_path.stat().st_size
    if size > MAX_FILE_SIZE_BYTES:
        raise DocumentProcessingError(
            f"File is too large ({size / 1024 / 1024:.1f}MB). "
            "Keep uploads under 5MB for the local demo version."
        )
    if size == 0:
        raise DocumentProcessingError("File is empty.")

    logger.info(f"Validating file: {path} ({size} bytes)")


def extract_text(path: str) -> str:
    """Extract text from file based on extension with robust error handling."""
    validate_upload(path)
    extension = os.path.splitext(path)[1].lower()

    logger.info(f"Extracting text from {path} (extension: {extension})")

    try:
        if extension == ".pdf":
            text = extract_pdf_text(path)
        elif extension == ".csv":
            text = extract_csv_text(path)
        elif extension == ".docx":
            text = extract_docx_text(path)
        elif extension == ".json":
            text = extract_json_text(path)
        elif extension == ".html":
            text = extract_html_text(path)
        else:
            text = read_text_file(path)

        # Apply normalization based on file type
        if is_code_file(path):
            text = normalize_code_text(text)
        else:
            text = normalize_text(text)

        if len(text) < MIN_EXTRACTED_CHARACTERS:
            raise DocumentProcessingError(
                f"Not enough readable text was extracted ({len(text)} chars). "
                "Scanned PDFs may need OCR."
            )

        logger.info(f"Successfully extracted {len(text)} characters from {path}")
        return text

    except DocumentProcessingError:
        raise
    except Exception as e:
        logger.error(f"Failed to extract text from {path}: {e}")
        raise DocumentProcessingError(f"Failed to process file: {e}") from e


def normalize_text(text: str) -> str:
    """Normalize plain text by cleaning whitespace."""
    lines = [line.strip() for line in text.replace("\x00", " ").replace("\r\n", "\n").splitlines()]
    return "\n".join(line for line in lines if line)


def normalize_code_text(text: str) -> str:
    """Normalize code files preserving structure."""
    lines = [line.rstrip() for line in text.replace("\x00", " ").replace("\r\n", "\n").splitlines()]
    # Remove leading blank lines
    while lines and not lines[0].strip():
        lines.pop(0)
    # Remove trailing blank lines
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def read_text_file(path: str) -> str:
    """Read text file with automatic encoding detection."""
    data = Path(path).read_bytes()
    size = len(data)

    logger.debug(f"Reading text file: {path} ({size} bytes)")

    # Check for BOM and encoding markers
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        # UTF-16 LE/BE
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError as e:
            logger.warning(f"UTF-16 decode failed for {path}: {e}")

    if data.startswith(b"\xef\xbb\xbf"):
        # UTF-8 BOM
        return data.decode("utf-8-sig", errors="ignore")

    # Check for binary content (null bytes in first portion)
    head = data[: min(200, size)]
    null_ratio = head.count(b"\x00") / max(len(head), 1)

    if null_ratio > 0.3:
        raise DocumentProcessingError(
            f"File appears to be binary (detected null bytes). "
            "Only text files are supported."
        )

    # Try UTF-8 first
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass

    # Fallback to Latin-1 which covers all byte values 0-255
    try:
        return data.decode("latin-1", errors="ignore")
    except Exception as e:
        raise DocumentProcessingError(f"Unable to decode file encoding: {e}")


def extract_csv_text(path: str) -> str:
    """Extract and format CSV content."""
    import csv

    try:
        out_lines = []
        with open(path, newline='', encoding='utf-8', errors='replace') as fh:
            reader = csv.reader(fh)
            for row_num, row in enumerate(reader, 1):
                # Format: pipe-separated values with row number
                out_lines.append(f"Row {row_num}: {' | '.join(row)}")

        result = "\n".join(out_lines)
        logger.debug(f"CSV extraction got {len(out_lines)} rows")
        return result

    except Exception as e:
        raise DocumentProcessingError(f"Failed to parse CSV file: {e}") from e


def extract_docx_text(path: str) -> str:
    """Extract text from DOCX files."""
    try:
        from docx import Document
    except ImportError:
        raise DocumentProcessingError('DOCX support not installed. Install python-docx.')

    try:
        doc = Document(path)
        paragraphs = [
            p.text.strip() for p in doc.paragraphs
            if p.text and p.text.strip()
        ]
        result = "\n".join(paragraphs)
        logger.debug(f"DOCX extraction got {len(paragraphs)} paragraphs")
        return result
    except Exception as e:
        raise DocumentProcessingError(f"Failed to parse DOCX file: {e}") from e


def extract_json_text(path: str) -> str:
    """Extract and format JSON content."""
    import json

    try:
        data = Path(path).read_bytes()

        # Try UTF-8 first
        try:
            obj = json.loads(data.decode('utf-8'))
        except UnicodeDecodeError:
            obj = json.loads(data.decode('latin-1'))

        # Flatten JSON into readable text format
        lines = _flatten_json(obj)
        result = "\n".join(lines)
        logger.debug(f"JSON extraction got {len(lines)} lines")
        return result

    except json.JSONDecodeError as e:
        raise DocumentProcessingError(f"Invalid JSON file: {e}") from e
    except Exception as e:
        raise DocumentProcessingError(f"Failed to parse JSON file: {e}") from e


def _flatten_json(obj, prefix: str = '', max_list_items: int = 50) -> list:
    """Recursively flatten JSON object into lines."""
    lines = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            key_prefix = f"{prefix}{k}"
            if isinstance(v, dict):
                lines.append(f"{key_prefix}:")
                lines.extend(_flatten_json(v, prefix=key_prefix + '.', max_list_items=max_list_items))
            elif isinstance(v, list):
                lines.append(f"{key_prefix}: [{len(v)} items]")
                for i, item in enumerate(v[:max_list_items]):
                    if isinstance(item, dict):
                        lines.append(f"  [{i}]")
                        lines.extend(_flatten_json(item, prefix=f"  {key_prefix}[{i}].", max_list_items=max_list_items))
                    else:
                        lines.append(f"  [{i}] {item}")
                if len(v) > max_list_items:
                    lines.append(f"  ... ({len(v) - max_list_items} more items)")
            else:
                lines.append(f"{key_prefix}: {v}")

    elif isinstance(obj, list):
        lines.append(f"[{len(obj)} items]")
        for i, item in enumerate(obj[:max_list_items]):
            if isinstance(item, dict):
                lines.append(f"[{i}]")
                lines.extend(_flatten_json(item, prefix=f"[{i}].", max_list_items=max_list_items))
            else:
                lines.append(f"[{i}] {item}")
        if len(obj) > max_list_items:
            lines.append(f"... ({len(obj) - max_list_items} more items)")

    else:
        lines.append(str(obj))

    return lines


def extract_pdf_text(path: str) -> str:
    """Extract text from PDF files with size limits."""
    from pypdf import PdfReader

    try:
        reader = PdfReader(path)
        num_pages = len(reader.pages)

        logger.debug(f"PDF has {num_pages} pages")

        if num_pages > 80:
            raise DocumentProcessingError(
                f"PDF has too many pages ({num_pages}). "
                "Maximum 80 pages for local demo version."
            )

        text_parts = []
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(f"[Page {page_num}]\n{page_text}")

        result = "\n".join(text_parts)
        logger.debug(f"PDF extraction got {len(text_parts)} pages with text")
        return result

    except DocumentProcessingError:
        raise
    except Exception as e:
        raise DocumentProcessingError(f"Failed to parse PDF file: {e}") from e


def extract_html_text(path: str) -> str:
    """Extract text content from HTML files."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        # Fallback: just read as plain text if bs4 not available
        return read_text_file(path)

    try:
        data = Path(path).read_bytes()
        # Try to decode as UTF-8
        try:
            html_content = data.decode('utf-8')
        except UnicodeDecodeError:
            html_content = data.decode('latin-1', errors='ignore')

        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements
        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        # Get text
        text = soup.get_text(separator='\n', strip=True)

        # Clean up excessive newlines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text)

        logger.debug(f"HTML extraction got {len(text)} characters")
        return text

    except Exception as e:
        raise DocumentProcessingError(f"Failed to parse HTML file: {e}") from e