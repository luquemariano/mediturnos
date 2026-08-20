from .base import ObjectNotFoundError, ObjectStorageUnavailable, PresignedDownload, PresignedUpload, StoredObjectMetadata
class R2ObjectStorageProvider:
    def __init__(self, access_key_id, secret_access_key, bucket_name, endpoint, client=None):
        if client is None:
            try:
                import boto3
                client = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name="auto")
            except Exception as error: raise ObjectStorageUnavailable("No se pudo inicializar el almacenamiento R2.") from error
        self._client, self._bucket = client, bucket_name
    def create_upload_url(self, key, content_type, expires_in_seconds):
        try: url = self._client.generate_presigned_url("put_object", Params={"Bucket": self._bucket, "Key": key, "ContentType": content_type}, ExpiresIn=expires_in_seconds, HttpMethod="PUT")
        except Exception as error: raise ObjectStorageUnavailable("No se pudo generar la URL de carga.") from error
        return PresignedUpload(url, expires_in_seconds)
    def create_download_url(self, key, expires_in_seconds):
        try: url = self._client.generate_presigned_url("get_object", Params={"Bucket": self._bucket, "Key": key}, ExpiresIn=expires_in_seconds, HttpMethod="GET")
        except Exception as error: raise ObjectStorageUnavailable("No se pudo generar la URL de descarga.") from error
        return PresignedDownload(url, expires_in_seconds)
    def head_object(self, key):
        try: response = self._client.head_object(Bucket=self._bucket, Key=key)
        except Exception as error:
            code = getattr(error, "response", {}).get("Error", {}).get("Code")
            if code in {"404", "NoSuchKey", "NotFound"}: raise ObjectNotFoundError("El objeto no existe.") from error
            raise ObjectStorageUnavailable("No se pudo consultar el objeto.") from error
        return StoredObjectMetadata(response.get("ContentLength", 0), response.get("ContentType"), response.get("ETag"))
    def delete_object(self, key):
        try: self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception as error: raise ObjectStorageUnavailable("No se pudo eliminar el objeto.") from error
