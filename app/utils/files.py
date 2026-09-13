import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed_image(filename: str) -> bool:
    return _extension(filename) in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def is_allowed_file(filename: str) -> bool:
    return _extension(filename) in current_app.config["ALLOWED_FILE_EXTENSIONS"]


def save_upload(file_storage, subfolder: str) -> str:
    """
    Validates and saves an uploaded werkzeug FileStorage object.
    Returns the relative path (under UPLOAD_FOLDER) it was saved to, or
    raises ValueError if validation fails. Filenames are regenerated with a
    uuid to avoid path traversal / collisions / information leakage.
    """
    if not file_storage or not file_storage.filename:
        raise ValueError("No file provided.")

    original = secure_filename(file_storage.filename)
    ext = _extension(original)
    if not is_allowed_file(original):
        raise ValueError(f"File type '.{ext}' is not allowed.")

    target_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(target_dir, exist_ok=True)

    new_name = f"{uuid.uuid4().hex}.{ext}"
    full_path = os.path.join(target_dir, new_name)
    file_storage.save(full_path)

    return os.path.join(subfolder, new_name)
