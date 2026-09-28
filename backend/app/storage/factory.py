from functools import lru_cache

from app.core.config import settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorageBackend


@lru_cache(maxsize=1)
def get_storage_backend() -> StorageBackend:
    if settings.storage_backend == "azure_blob":
        from app.storage.azure_blob import AzureBlobStorageBackend

        return AzureBlobStorageBackend(
            account_url=settings.azure_storage_account_url or "",
            container=settings.azure_storage_container,
        )

    return LocalStorageBackend(settings.local_storage_root)