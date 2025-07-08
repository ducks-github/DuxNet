"""
Integration Tests for Store System

Simple integration tests for the DuxOS API/App Store.
"""

import shutil
import tempfile
from pathlib import Path

from duxos_store.metadata_storage import MetadataStorage
from duxos_store.rating_system import RatingSystem
from duxos_store.store_service import StoreService


def test_store_integration():
    """Test basic store integration"""
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()

    try:
        # Initialize components
        metadata_storage = MetadataStorage(storage_path=temp_dir)
        rating_system = RatingSystem()
        store_service = StoreService(metadata_storage, rating_system)

        # Test service registration
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123",
            "price_per_call": 0.01,
            "tags": ["test", "api"],
        }

        service = store_service.register_service(service_data, "user1", "Test User")
        assert service.name == "Test API"
        assert service.owner_id == "user1"

        # Test service publishing
        published_service = store_service.publish_service(service.service_id, "user1")
        assert published_service is not None
        assert published_service.status.value == "published"

        # Test adding review
        review = store_service.add_review(
            service.service_id, "user2", "Reviewer", 5, "Great service", "This is an excellent API"
        )
        assert review is not None
        assert review.rating == 5

        # Test search
        from duxos_store.models import SearchFilter, ServiceStatus

        search_filter = SearchFilter(query="test", status=ServiceStatus.PUBLISHED)
        results, count = store_service.search_services(search_filter)
        assert len(results) == 1
        assert results[0].name == "Test API"

        print("✅ Store integration test passed!")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_store_integration()
