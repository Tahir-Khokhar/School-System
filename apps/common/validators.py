"""Reusable file validators for upload security.

Without these, Django will happily accept:
  - .exe / .svg (containing JavaScript) / .html files
  - arbitrarily large uploads (denial-of-service via disk exhaustion)

These validators enforce a common allow-list (images + documents + archives)
and a 10 MB cap, which can be relaxed per-field via the upload_to + validator
combination if a specific field needs a different policy.
"""
import os
from django.core.exceptions import ValidationError


# Common allow-list for school-document uploads. SVG is deliberately excluded
# because it can carry JavaScript that runs in the browser when the file is
# served with image/svg+xml and the parent page has access to it.
ALLOWED_FILE_EXTENSIONS = [
    ".pdf", ".doc", ".docx", ".txt", ".csv",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".zip",
]
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file_extension(file_or_name):
    """Validator callable for FileField/ImageField — checks extension.

    Accepts either an UploadedFile (with a `.name` attribute) or a raw filename
    string (used when the validator is invoked by clean_<field> in a form).
    """
    name = getattr(file_or_name, "name", file_or_name)
    if not name:
        raise ValidationError("File has no name.")
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(
            f"File type '{ext}' is not allowed. Allowed: {', '.join(ALLOWED_FILE_EXTENSIONS)}"
        )


def validate_file_size(file):
    """Validator callable — checks file size against MAX_FILE_SIZE_BYTES."""
    size = getattr(file, "size", None)
    if size is None:
        return  # Can't check — let Django's own machinery handle it.
    if size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(
            f"File size ({size // 1024}KB) exceeds maximum ({MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB)."
        )
