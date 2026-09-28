from __future__ import annotations

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError

from app.storage.base import StorageBackend


class AzureBlobStorageBackend(StorageBackend):
    def __init__(self, account_url: str, container: str) -> None:
        credential = DefaultAzureCredential()
        service = BlobServiceClient(account_url=account_url, credential=credential)
        self.container: ContainerClient = service.get_container_client(container)

    def write_bytes(self, key: str, content: bytes) -> str:
        normalized_key = self.normalize_key(key)
        self.container.upload_blob(normalized_key, content, overwrite=True)
        return normalized_key

    def read_bytes(self, reference: str) -> bytes:
        key = self.normalize_key(reference)
        return self.container.download_blob(key).readall()

    def exists(self, reference: str) -> bool:
        try:
            return self.container.get_blob_client(self.normalize_key(reference)).exists()
        except ResourceNotFoundError:
            return False

    def delete_prefix(self, prefix: str) -> None:
        normalized_prefix = self.normalize_key(prefix).rstrip("/") + "/"
        blob_names = [blob.name for blob in self.container.list_blobs(name_starts_with=normalized_prefix)]
        if blob_names:
            self.container.delete_blobs(*blob_names)