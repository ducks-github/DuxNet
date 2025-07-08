"""
DuxOS API/App Store

A decentralized marketplace for publishing, discovering, and monetizing
APIs and applications on the DuxOS network.
"""

from .api import StoreAPI
from .metadata_storage import MetadataStorage
from .models import Rating, Review, Service, ServiceCategory, ServiceStatus
from .rating_system import RatingSystem
from .store_service import StoreService

__version__ = "1.0.0"
__all__ = [
    "StoreService",
    "RatingSystem",
    "MetadataStorage",
    "Service",
    "Review",
    "Rating",
    "ServiceCategory",
    "ServiceStatus",
    "StoreAPI",
]
