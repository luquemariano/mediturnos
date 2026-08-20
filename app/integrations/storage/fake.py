from dataclasses import dataclass
from urllib.parse import quote
from .base import ObjectNotFoundError, PresignedDownload, PresignedUpload, StoredObjectMetadata
@dataclass
class FakeObjectStorageProvider:
    objects: dict[str, StoredObjectMetadata] | None = None
    def __post_init__(self): self.objects = {} if self.objects is None else self.objects
    def create_upload_url(self, key, content_type, expires_in_seconds): return PresignedUpload(f"https://fake-object-storage.test/upload/{quote(key, safe='/')}?expires={expires_in_seconds}", expires_in_seconds)
    def create_download_url(self, key, expires_in_seconds): return PresignedDownload(f"https://fake-object-storage.test/download/{quote(key, safe='/')}?expires={expires_in_seconds}", expires_in_seconds)
    def head_object(self, key):
        if key not in self.objects: raise ObjectNotFoundError("El objeto no existe.")
        return self.objects[key]
    def delete_object(self, key): self.objects.pop(key, None)
    def register_object(self, key, size_bytes, content_type=None, etag=None): self.objects[key] = StoredObjectMetadata(size_bytes, content_type, etag)
