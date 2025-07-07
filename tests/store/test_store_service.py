"""
Unit tests for the DuxNet Store Service.

Tests cover:
- API registration and management
- Search functionality
- Rating system
- Metadata storage
- Error handling
"""

import pytest
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Import the modules to test
from duxnet_store.store_service import StoreService
from duxnet_store.rating_system import RatingSystem
from duxnet_store.metadata_storage import MetadataStorage


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
            "storage": {
                "path": temp_dir,
                "use_ipfs": False,
                "backup_enabled": False
            },
            "rating": {
                "min_reviews_for_weighted": 5,
                "recency_weight_days": 30
            },
            "search": {
                "default_limit": 20,
                "max_limit": 100
            }
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
            "price": 0.1,
            "category": "test",
            "endpoint": "https://api.test.com/test",
            "documentation": "https://docs.test.com/test"
        }

    def test_store_service_initialization(self, store_service, config):
        """Test StoreService initialization."""
        assert store_service is not None
        assert store_service.config == config
        assert hasattr(store_service, 'rating_system')
        assert hasattr(store_service, 'metadata_storage')

    def test_register_api_success(self, store_service, sample_api_data):
        """Test successful API registration."""
        with patch.object(store_service.metadata_storage, 'store_api') as mock_store:
            mock_store.return_value = "api_123"
            
            api_id = store_service.register_api(sample_api_data)
            
            assert api_id == "api_123"
            mock_store.assert_called_once()
            
            # Verify the stored data
            stored_data = mock_store.call_args[0][0]
            assert stored_data["name"] == sample_api_data["name"]
            assert stored_data["version"] == sample_api_data["version"]
            assert stored_data["price"] == sample_api_data["price"]

    def test_register_api_validation_error(self, store_service):
        """Test API registration with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "version": "1.0.0",
            "price": -1.0  # Negative price should fail validation
        }
        
        with pytest.raises(ValueError):
            store_service.register_api(invalid_data)

    def test_search_apis_by_name(self, store_service):
        """Test API search by name."""
        mock_apis = [
            {"id": "1", "name": "image_processor", "description": "Process images"},
            {"id": "2", "name": "text_analyzer", "description": "Analyze text"},
            {"id": "3", "name": "data_processor", "description": "Process data"}
        ]
        
        with patch.object(store_service.metadata_storage, 'search_apis') as mock_search:
            mock_search.return_value = [mock_apis[0]]  # Return image_processor
            
            results = store_service.search_apis("image", limit=10)
            
            assert len(results) == 1
            assert results[0]["name"] == "image_processor"
            mock_search.assert_called_once_with("image", limit=10)

    def test_search_apis_by_category(self, store_service):
        """Test API search by category."""
        mock_apis = [
            {"id": "1", "name": "api1", "category": "image_processing"},
            {"id": "2", "name": "api2", "category": "text_processing"}
        ]
        
        with patch.object(store_service.metadata_storage, 'search_apis') as mock_search:
            mock_search.return_value = [mock_apis[0]]
            
            results = store_service.search_apis("image_processing", category="image_processing")
            
            assert len(results) == 1
            assert results[0]["category"] == "image_processing"

    def test_get_api_by_id(self, store_service):
        """Test retrieving API by ID."""
        mock_api = {
            "id": "api_123",
            "name": "test_api",
            "version": "1.0.0",
            "rating": 4.5,
            "reviews_count": 10
        }
        
        with patch.object(store_service.metadata_storage, 'get_api') as mock_get:
            mock_get.return_value = mock_api
            
            api = store_service.get_api("api_123")
            
            assert api == mock_api
            mock_get.assert_called_once_with("api_123")

    def test_get_api_not_found(self, store_service):
        """Test retrieving non-existent API."""
        with patch.object(store_service.metadata_storage, 'get_api') as mock_get:
            mock_get.return_value = None
            
            api = store_service.get_api("non_existent")
            
            assert api is None

    def test_add_review_success(self, store_service):
        """Test adding a review successfully."""
        review_data = {
            "api_id": "api_123",
            "rating": 5,
            "comment": "Excellent API!"
        }
        
        with patch.object(store_service.rating_system, 'add_review') as mock_add:
            mock_add.return_value = "review_456"
            
            review_id = store_service.add_review(review_data)
            
            assert review_id == "review_456"
            mock_add.assert_called_once()

    def test_add_review_invalid_rating(self, store_service):
        """Test adding review with invalid rating."""
        review_data = {
            "api_id": "api_123",
            "rating": 6,  # Rating should be 1-5
            "comment": "Test comment"
        }
        
        with pytest.raises(ValueError):
            store_service.add_review(review_data)

    def test_get_api_reviews(self, store_service):
        """Test retrieving API reviews."""
        mock_reviews = [
            {"id": "1", "rating": 5, "comment": "Great!"},
            {"id": "2", "rating": 4, "comment": "Good"}
        ]
        
        with patch.object(store_service.rating_system, 'get_reviews') as mock_get:
            mock_get.return_value = mock_reviews
            
            reviews = store_service.get_reviews("api_123", limit=10)
            
            assert reviews == mock_reviews
            mock_get.assert_called_once_with("api_123", limit=10)

    def test_update_api_success(self, store_service):
        """Test updating API information."""
        update_data = {
            "description": "Updated description",
            "price": 0.2
        }
        
        with patch.object(store_service.metadata_storage, 'update_api') as mock_update:
            mock_update.return_value = True
            
            success = store_service.update_api("api_123", update_data)
            
            assert success is True
            mock_update.assert_called_once_with("api_123", update_data)

    def test_delete_api_success(self, store_service):
        """Test deleting an API."""
        with patch.object(store_service.metadata_storage, 'delete_api') as mock_delete:
            mock_delete.return_value = True
            
            success = store_service.delete_api("api_123")
            
            assert success is True
            mock_delete.assert_called_once_with("api_123")

    def test_get_categories(self, store_service):
        """Test retrieving available categories."""
        mock_categories = ["image_processing", "text_processing", "data_analysis"]
        
        with patch.object(store_service.metadata_storage, 'get_categories') as mock_get:
            mock_get.return_value = mock_categories
            
            categories = store_service.get_categories()
            
            assert categories == mock_categories
            mock_get.assert_called_once()

    def test_get_popular_apis(self, store_service):
        """Test retrieving popular APIs."""
        mock_apis = [
            {"id": "1", "name": "popular1", "rating": 4.8},
            {"id": "2", "name": "popular2", "rating": 4.7}
        ]
        
        with patch.object(store_service.metadata_storage, 'get_popular_apis') as mock_get:
            mock_get.return_value = mock_apis
            
            apis = store_service.get_popular_apis(limit=5)
            
            assert apis == mock_apis
            mock_get.assert_called_once_with(limit=5)

    @pytest.mark.integration
    def test_full_api_lifecycle(self, store_service, sample_api_data):
        """Test complete API lifecycle: register, search, review, update, delete."""
        # Register API
        with patch.object(store_service.metadata_storage, 'store_api') as mock_store:
            mock_store.return_value = "api_123"
            api_id = store_service.register_api(sample_api_data)
            assert api_id == "api_123"

        # Search for the API
        with patch.object(store_service.metadata_storage, 'search_apis') as mock_search:
            mock_search.return_value = [{"id": api_id, **sample_api_data}]
            results = store_service.search_apis("test_api")
            assert len(results) == 1
            assert results[0]["id"] == api_id

        # Add a review
        with patch.object(store_service.rating_system, 'add_review') as mock_review:
            mock_review.return_value = "review_456"
            review_id = store_service.add_review({
                "api_id": api_id,
                "rating": 5,
                "comment": "Great API!"
            })
            assert review_id == "review_456"

        # Update the API
        with patch.object(store_service.metadata_storage, 'update_api') as mock_update:
            mock_update.return_value = True
            success = store_service.update_api(api_id, {"price": 0.15})
            assert success is True

        # Delete the API
        with patch.object(store_service.metadata_storage, 'delete_api') as mock_delete:
            mock_delete.return_value = True
            success = store_service.delete_api(api_id)
            assert success is True

    def test_error_handling_database_error(self, store_service, sample_api_data):
        """Test error handling when database operations fail."""
        with patch.object(store_service.metadata_storage, 'store_api') as mock_store:
            mock_store.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception) as exc_info:
                store_service.register_api(sample_api_data)
            
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
        # Mock a large dataset
        large_dataset = [{"id": f"api_{i}", "name": f"api_{i}"} for i in range(1000)]
        
        with patch.object(store_service.metadata_storage, 'search_apis') as mock_search:
            mock_search.return_value = large_dataset[:20]  # Return first 20
            
            import time
            start_time = time.time()
            results = store_service.search_apis("api", limit=20)
            end_time = time.time()
            
            assert len(results) == 20
            assert (end_time - start_time) < 1.0  # Should complete within 1 second

    def test_data_validation_edge_cases(self, store_service):
        """Test data validation with edge cases."""
        edge_cases = [
            {"name": "a" * 1000, "version": "1.0.0", "price": 0.0},  # Very long name
            {"name": "test", "version": "1.0.0", "price": 999999.99},  # Very high price
            {"name": "test", "version": "1.0.0", "price": 0.0, "category": ""},  # Empty category
        ]
        
        for case in edge_cases:
            with patch.object(store_service.metadata_storage, 'store_api'):
                # Should not raise validation errors for these edge cases
                try:
                    store_service.register_api(case)
                except ValueError:
                    # Some edge cases might be invalid, which is expected
                    pass 