from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class PresignedUpload:
    url: str
    expires_in_seconds: int
@dataclass(frozen=True)
class PresignedDownload:
    url: str
    expires_in_seconds: int
@dataclass(frozen=True)
class StoredObjectMetadata:
    size_bytes: int
    content_type: str | None = None
    etag: str | None = None
class ObjectStorageError(RuntimeError): pass
class ObjectNotFoundError(ObjectStorageError): pass
class ObjectStorageUnavailable(ObjectStorageError): pass
class BaseObjectStorageProvider(Protocol):
    def create_upload_url(self, key: str, content_type: str, expires_in_seconds: int) -> PresignedUpload: ...
    def create_download_url(self, key: str, expires_in_seconds: int) -> PresignedDownload: ...
    def head_object(self, key: str) -> StoredObjectMetadata: ...
    def delete_object(self, key: str) -> None: ...
