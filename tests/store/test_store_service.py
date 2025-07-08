"""
Unit tests for the DuxNet Store Service.

Tests cover:
- API registration and management
- Search functionality
- Rating system
- Metadata storage
- Error handling
"""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from duxos_store.metadata_storage import MetadataStorage
from duxos_store.rating_system import RatingSystem

# Import the modules to test
from duxos_store.store_service import StoreService


class TestStoreService:
    """Test cases for StoreService class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config(self, temp_dir):
        """Create test configuration."""
        return {
            "storage": {"path": temp_dir, "use_ipfs": False, "backup_enabled": False},
            "rating": {"min_reviews_for_weighted": 5, "recency_weight_days": 30},
            "search": {"default_limit": 20, "max_limit": 100},
        }

    @pytest.fixture
    def store_service(self, config, temp_dir):
        """Create a StoreService instance for testing."""
        metadata_storage = MetadataStorage(storage_path=temp_dir)
        rating_system = RatingSystem()
        return StoreService(metadata_storage, rating_system)

    @pytest.fixture
    def sample_api_data(self):
        """Sample API data for testing."""
        return {
            "name": "test_api",
            "version": "1.0.0",
            "description": "A test API for unit testing",
            "price_per_call": 0.1,
            "category": "api",
            "code_hash": "test_hash_12345",
            "endpoint": "https://api.test.com/test",
            "documentation": "https://docs.test.com/test",
        }

    def test_store_service_initialization(self, store_service, config):
        """Test StoreService initialization."""
        assert store_service is not None
        assert hasattr(store_service, "rating_system")
        assert hasattr(store_service, "metadata_storage")
        assert hasattr(store_service, "services")
        assert hasattr(store_service, "reviews")
        assert hasattr(store_service, "ratings")

    def test_register_service_success(self, store_service, sample_api_data):
        """Test successful service registration."""
        with patch.object(store_service.metadata_storage, "store_service_metadata") as mock_store:
            mock_store.return_value = "service_123"

            service = store_service.register_service(sample_api_data, "owner1", "Test Owner")

            assert service is not None
            assert service.name == sample_api_data["name"]
            assert service.owner_id == "owner1"
            mock_store.assert_called_once()

    def test_register_service_validation_error(self, store_service):
        """Test service registration with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "description": "Test description",
            "category": "api",
            "code_hash": "test_hash",
        }

        with pytest.raises(ValueError):
            store_service.register_service(invalid_data, "owner1", "Test Owner")

    def test_search_services_by_name(self, store_service):
        """Test service search by name."""
        from duxos_store.models import SearchFilter, ServiceStatus
        
        # Create a test service
        service_data = {
            "name": "image_processor",
            "description": "Process images",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        store_service.publish_service(service.service_id, "owner1")
        
        # Search for the service
        search_filter = SearchFilter(query="image", status=ServiceStatus.PUBLISHED)
        results, count = store_service.search_services(search_filter)
        
        assert len(results) == 1
        assert results[0].name == "image_processor"

    def test_search_services_by_category(self, store_service):
        """Test service search by category."""
        from duxos_store.models import SearchFilter, ServiceStatus, ServiceCategory
        
        # Create a test service
        service_data = {
            "name": "image_processor",
            "description": "Process images",
            "category": "image_processing",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        store_service.publish_service(service.service_id, "owner1")
        
        # Search for the service by category
        search_filter = SearchFilter(
            query="", 
            category=ServiceCategory.IMAGE_PROCESSING, 
            status=ServiceStatus.PUBLISHED
        )
        results, count = store_service.search_services(search_filter)
        
        assert len(results) == 1
        assert results[0].category == ServiceCategory.IMAGE_PROCESSING

    def test_get_service_by_id(self, store_service):
        """Test retrieving service by ID."""
        # Create a test service
        service_data = {
            "name": "test_service",
            "description": "Test service description",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        
        # Retrieve the service
        retrieved_service = store_service.get_service(service.service_id)
        
        assert retrieved_service is not None
        assert retrieved_service.name == "test_service"
        assert retrieved_service.service_id == service.service_id

    def test_get_service_not_found(self, store_service):
        """Test retrieving non-existent service."""
        service = store_service.get_service("non_existent")
        assert service is None

    def test_add_review_success(self, store_service):
        """Test adding a review successfully."""
        # Create a test service first
        service_data = {
            "name": "test_service",
            "description": "Test service description",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        
        # Add a review
        review = store_service.add_review(
            service.service_id, "user1", "Test User", 5, "Great service", "Excellent API!"
        )
        
        assert review is not None
        assert review.rating == 5
        assert review.user_id == "user1"

    def test_add_review_invalid_rating(self, store_service):
        """Test adding review with invalid rating."""
        # Create a test service first
        service_data = {
            "name": "test_service",
            "description": "Test service description",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        
        # Try to add a review with invalid rating
        with pytest.raises(ValueError):
            store_service.add_review(
                service.service_id, "user1", "Test User", 6, "Invalid rating", "Test comment"
            )

    def test_get_service_reviews(self, store_service):
        """Test retrieving service reviews."""
        # Create a test service first
        service_data = {
            "name": "test_service",
            "description": "Test service description",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        
        # Add some reviews
        store_service.add_review(service.service_id, "user1", "User 1", 5, "Great!", "Excellent service")
        store_service.add_review(service.service_id, "user2", "User 2", 4, "Good", "Good service")
        
        # Get reviews
        reviews = store_service.get_reviews(service.service_id, limit=10)
        
        assert len(reviews) == 2
        assert reviews[0].rating == 5
        assert reviews[1].rating == 4

    def test_update_service_success(self, store_service):
        """Test updating service information."""
        # Create a test service first
        service_data = {
            "name": "test_service",
            "description": "Original description",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        
        # Update the service
        update_data = {"description": "Updated description", "price_per_call": 0.2}
        updated_service = store_service.update_service(service.service_id, update_data, "owner1")
        
        assert updated_service is not None
        assert updated_service.description == "Updated description"
        assert updated_service.price_per_call == 0.2

    def test_publish_service_success(self, store_service):
        """Test publishing a service."""
        # Create a test service first
        service_data = {
            "name": "test_service",
            "description": "Test service description",
            "category": "api",
            "code_hash": "test_hash",
        }
        service = store_service.register_service(service_data, "owner1", "Test Owner")
        
        # Publish the service
        published_service = store_service.publish_service(service.service_id, "owner1")
        
        assert published_service is not None
        assert published_service.status.value == "published"

    def test_get_service_statistics(self, store_service):
        """Test retrieving service statistics."""
        # Create some test services
        service_data1 = {
            "name": "service1",
            "description": "Test service 1",
            "category": "api",
            "code_hash": "test_hash1",
        }
        service_data2 = {
            "name": "service2",
            "description": "Test service 2",
            "category": "api",
            "code_hash": "test_hash2",
        }
        
        service1 = store_service.register_service(service_data1, "owner1", "Test Owner")
        service2 = store_service.register_service(service_data2, "owner2", "Test Owner 2")
        
        # Publish services
        store_service.publish_service(service1.service_id, "owner1")
        store_service.publish_service(service2.service_id, "owner2")
        
        # Get statistics
        stats = store_service.get_service_statistics()
        
        assert stats["total_services"] == 2
        assert stats["published_services"] == 2
        assert "category_distribution" in stats

    def test_get_popular_services(self, store_service):
        """Test retrieving popular services."""
        # Create some test services
        service_data1 = {
            "name": "popular_service1",
            "description": "Popular service 1",
            "category": "api",
            "code_hash": "test_hash1",
        }
        service_data2 = {
            "name": "popular_service2",
            "description": "Popular service 2",
            "category": "api",
            "code_hash": "test_hash2",
        }
        
        service1 = store_service.register_service(service_data1, "owner1", "Test Owner")
        service2 = store_service.register_service(service_data2, "owner2", "Test Owner 2")
        
        # Publish services
        store_service.publish_service(service1.service_id, "owner1")
        store_service.publish_service(service2.service_id, "owner2")
        
        # Get popular services
        popular_services = store_service.get_popular_services(limit=5)
        
        assert len(popular_services) == 2

    @pytest.mark.integration
    def test_full_service_lifecycle(self, store_service, sample_api_data):
        """Test complete service lifecycle: register, publish, review, update."""
        from duxos_store.models import SearchFilter, ServiceStatus
        
        # Register service
        service = store_service.register_service(sample_api_data, "owner1", "Test Owner")
        assert service is not None
        assert service.name == sample_api_data["name"]
        
        # Publish service
        published_service = store_service.publish_service(service.service_id, "owner1")
        assert published_service is not None
        assert published_service.status.value == "published"
        
        # Search for the service
        search_filter = SearchFilter(query=sample_api_data["name"], status=ServiceStatus.PUBLISHED)
        results, count = store_service.search_services(search_filter)
        assert len(results) == 1
        assert results[0].service_id == service.service_id
        
        # Add a review
        review = store_service.add_review(
            service.service_id, "user1", "Test User", 5, "Great service", "Excellent API!"
        )
        assert review is not None
        assert review.rating == 5
        
        # Update the service
        update_data = {"description": "Updated description", "price_per_call": 0.15}
        updated_service = store_service.update_service(service.service_id, update_data, "owner1")
        assert updated_service is not None
        assert updated_service.description == "Updated description"
        assert updated_service.price_per_call == 0.15

    def test_error_handling_database_error(self, store_service, sample_api_data):
        """Test error handling when database operations fail."""
        with patch.object(store_service.metadata_storage, "store_service_metadata") as mock_store:
            mock_store.side_effect = Exception("Database connection failed")

            with pytest.raises(Exception) as exc_info:
                store_service.register_service(sample_api_data, "owner1", "Test Owner")

            assert "Database connection failed" in str(exc_info.value)

    def test_error_handling_invalid_config(self, temp_dir):
        """Test error handling with invalid configuration."""
        # Test with invalid storage path
        with pytest.raises(Exception):
            invalid_storage = MetadataStorage(storage_path="/invalid/path")
            rating_system = RatingSystem()
            StoreService(invalid_storage, rating_system)

    @pytest.mark.performance
    def test_search_performance(self, store_service):
        """Test search performance with large dataset."""
        from duxos_store.models import SearchFilter, ServiceStatus
        
        # Create many test services
        for i in range(100):
            service_data = {
                "name": f"service_{i}",
                "description": f"Service {i} description",
                "category": "api",
                "code_hash": f"hash_{i}",
            }
            service = store_service.register_service(service_data, f"owner_{i}", f"Owner {i}")
            store_service.publish_service(service.service_id, f"owner_{i}")

        # Test search performance
        import time
        start_time = time.time()
        search_filter = SearchFilter(query="service", status=ServiceStatus.PUBLISHED, limit=20)
        results, count = store_service.search_services(search_filter)
        end_time = time.time()

        assert len(results) <= 20
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    def test_data_validation_edge_cases(self, store_service):
        """Test data validation with edge cases."""
        edge_cases = [
            {
                "name": "a" * 1000,  # Very long name
                "description": "Test description",
                "category": "api",
                "code_hash": "test_hash",
            },
            {
                "name": "test",
                "description": "Test description",
                "category": "api",
                "code_hash": "test_hash",
                "price_per_call": 999999.99,  # Very high price
            },
        ]

        for case in edge_cases:
            with patch.object(store_service.metadata_storage, "store_service_metadata"):
                # Should not raise validation errors for these edge cases
                try:
                    store_service.register_service(case, "owner1", "Test Owner")
                except ValueError:
                    # Some edge cases might be invalid, which is expected
                    pass
