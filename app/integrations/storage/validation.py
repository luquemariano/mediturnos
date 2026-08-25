from uuid import UUID, uuid4
ALLOWED_DOCUMENT_MIME_TYPES = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024
def validate_document_mime_type(mime_type: str) -> str:
    if mime_type not in ALLOWED_DOCUMENT_MIME_TYPES: raise ValueError("Tipo de archivo no permitido.")
    return mime_type
def validate_document_size(size_bytes: int) -> int:
    if size_bytes <= 0 or size_bytes > MAX_DOCUMENT_SIZE_BYTES: raise ValueError("El tamaño del archivo no es válido.")
    return size_bytes
def generate_document_storage_key(mime_type: str, document_uuid: UUID | None = None) -> str:
    validate_document_mime_type(mime_type)
    return f"patient-documents/{document_uuid or uuid4()}.{ALLOWED_DOCUMENT_MIME_TYPES[mime_type]}"
