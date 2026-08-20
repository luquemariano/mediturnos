import sys
from types import SimpleNamespace
import pytest
from app.integrations.storage.fake import FakeObjectStorageProvider
from app.integrations.storage.base import ObjectNotFoundError, ObjectStorageUnavailable
from app.integrations.storage.validation import *
from app.integrations.storage.r2 import R2ObjectStorageProvider
from app.integrations.storage.factory import get_object_storage_provider
from app.core.config import Settings

def test_document_validation_and_key():
    assert validate_document_size(1) == 1
    assert validate_document_size(MAX_DOCUMENT_SIZE_BYTES) == MAX_DOCUMENT_SIZE_BYTES
    key = generate_document_storage_key("image/jpeg")
    assert key.startswith("patient-documents/") and key.endswith(".jpg")
    assert key != generate_document_storage_key("image/jpeg")
    with pytest.raises(ValueError): validate_document_mime_type("application/x-msdownload")
    with pytest.raises(ValueError): validate_document_size(0)
    with pytest.raises(ValueError): validate_document_size(MAX_DOCUMENT_SIZE_BYTES + 1)

def test_fake_provider_lifecycle():
    provider = FakeObjectStorageProvider()
    upload = provider.create_upload_url("patient-documents/x.pdf", "application/pdf", 600)
    assert upload.expires_in_seconds == 600
    provider.register_object("patient-documents/x.pdf", 12, "application/pdf", '"abc"')
    assert provider.head_object("patient-documents/x.pdf").size_bytes == 12
    provider.delete_object("patient-documents/x.pdf")
    with pytest.raises(ObjectNotFoundError): provider.head_object("patient-documents/x.pdf")

def test_r2_provider_usa_cliente_s3_y_parametros():
    calls = []
    class Client:
        def generate_presigned_url(self, *args, **kwargs): calls.append((args, kwargs)); return "https://signed.test/url"
        def head_object(self, **kwargs): return {"ContentLength": 4, "ContentType": "application/pdf", "ETag": '"e"'}
        def delete_object(self, **kwargs): calls.append(("delete", kwargs))
    fake_boto3 = SimpleNamespace(client=lambda *args, **kwargs: (calls.append(("client", args, kwargs)) or Client()))
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    try:
        provider = R2ObjectStorageProvider("access", "secret", "bucket", "https://account.r2.cloudflarestorage.com")
        assert calls[0][0] == "client" and calls[0][1] == ("s3",)
        assert calls[0][2]["region_name"] == "auto"
        provider.create_upload_url("patient-documents/x.pdf", "application/pdf", 600)
        provider.create_download_url("patient-documents/x.pdf", 300)
        assert calls[1][1]["Params"] == {"Bucket": "bucket", "Key": "patient-documents/x.pdf", "ContentType": "application/pdf"}
        assert calls[1][1]["ExpiresIn"] == 600 and calls[2][1]["ExpiresIn"] == 300
        assert provider.head_object("patient-documents/x.pdf").size_bytes == 4
        provider.delete_object("patient-documents/x.pdf")
    finally: monkeypatch.undo()

def test_r2_traduce_objeto_inexistente():
    class Client:
        def head_object(self, **kwargs): raise Exception("not found")
    provider = R2ObjectStorageProvider("a", "s", "b", "https://r2.test", client=Client())
    with pytest.raises(ObjectStorageUnavailable): provider.head_object("x")

def test_config_r2_production_incompleta_y_completa():
    base = dict(app_env="production", database_url="postgresql+psycopg://u:p@db/mediturnos", jwt_secret_key="x" * 40, cors_allowed_origins=["https://app.example"], frontend_url="https://app.example", email_provider="resend", resend_api_key="key", email_from="a@app.example", object_storage_provider="r2")
    with pytest.raises(ValueError): Settings(_env_file=None, **base)
    config = Settings(_env_file=None, **base, r2_access_key_id="access", r2_secret_access_key="secret", r2_bucket_name="bucket", r2_endpoint="https://account.r2.cloudflarestorage.com")
    assert config.r2_secret_access_key.get_secret_value() == "secret"
    assert "r2_secret_access_key=SecretStr('**********')" in repr(config)

def test_factory_fake_y_r2():
    assert isinstance(get_object_storage_provider(Settings(_env_file=None, jwt_secret_key="x")), FakeObjectStorageProvider)
    config = Settings(_env_file=None, jwt_secret_key="x", object_storage_provider="r2", r2_access_key_id="a", r2_secret_access_key="s", r2_bucket_name="b", r2_endpoint="https://r2.test")
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setitem(sys.modules, "boto3", SimpleNamespace(client=lambda *args, **kwargs: object()))
    try: assert isinstance(get_object_storage_provider(config), R2ObjectStorageProvider)
    finally: monkeypatch.undo()

def test_config_storage_validation():
    assert Settings(_env_file=None, jwt_secret_key="x", r2_presigned_upload_ttl_seconds=600).object_storage_provider == "fake"
    with pytest.raises(ValueError): Settings(_env_file=None, jwt_secret_key="x", r2_presigned_upload_ttl_seconds=0)
    with pytest.raises(ValueError): Settings(_env_file=None, jwt_secret_key="x", r2_presigned_download_ttl_seconds=0)
    with pytest.raises(ValueError): Settings(_env_file=None, jwt_secret_key="x", object_storage_provider="invalid")
