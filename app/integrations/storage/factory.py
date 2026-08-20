from .fake import FakeObjectStorageProvider
from .r2 import R2ObjectStorageProvider
from .base import ObjectStorageUnavailable
def get_object_storage_provider(config=None):
    if config is None:
        from app.core.config import settings
        config = settings
    if config.object_storage_provider == "fake": return FakeObjectStorageProvider()
    if config.object_storage_provider == "r2":
        if not config.r2_access_key_id or not config.r2_secret_access_key or not config.r2_bucket_name or not config.r2_endpoint:
            raise ObjectStorageUnavailable("El proveedor R2 no está configurado.")
        return R2ObjectStorageProvider(config.r2_access_key_id, config.r2_secret_access_key.get_secret_value(), config.r2_bucket_name, config.r2_endpoint)
    raise ValueError("Proveedor de object storage desconocido.")
