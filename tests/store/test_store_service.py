"""
Tests for Store Service

Comprehensive test suite for the DuxOS API/App Store service.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from duxos_store.store_service import StoreService
from duxos_store.rating_system import RatingSystem
from duxos_store.metadata_storage import MetadataStorage
from duxos_store.models import Service, Review, Rating, ServiceCategory, ServiceStatus, SearchFilter


class TestStoreService:
    """Test cases for StoreService"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def store_service(self, temp_dir):
        """Create store service for testing"""
        metadata_storage = MetadataStorage(storage_path=temp_dir)
        rating_system = RatingSystem()
        return StoreService(metadata_storage, rating_system)
    
    def test_register_service(self, store_service):
        """Test service registration"""
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123",
            "price_per_call": 0.01,
            "tags": ["test", "api"]
        }
        
        service = store_service.register_service(service_data, "user1", "Test User")
        
        assert service.name == "Test API"
        assert service.owner_id == "user1"
        assert service.category == ServiceCategory.API
        assert service.status == ServiceStatus.DRAFT
        assert service.service_id in store_service.services
        
        # Check that rating and reviews are initialized
        assert service.service_id in store_service.ratings
        assert service.service_id in store_service.reviews
    
    def test_register_service_missing_fields(self, store_service):
        """Test service registration with missing required fields"""
        service_data = {
            "name": "Test API",
            # Missing description, category, code_hash
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            store_service.register_service(service_data, "user1", "Test User")
    
    def test_update_service(self, store_service):
        """Test service updates"""
        # Register a service first
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Update the service
        updates = {
            "name": "Updated Test API",
            "description": "Updated description",
            "price_per_call": 0.02
        }
        
        updated_service = store_service.update_service(service.service_id, updates, "user1")
        
        assert updated_service.name == "Updated Test API"
        assert updated_service.description == "Updated description"
        assert updated_service.price_per_call == 0.02
    
    def test_update_service_unauthorized(self, store_service):
        """Test service update by unauthorized user"""
        # Register a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Try to update with different user
        updates = {"name": "Unauthorized Update"}
        result = store_service.update_service(service.service_id, updates, "user2")
        
        assert result is None
    
    def test_publish_service(self, store_service):
        """Test service publishing"""
        # Register a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Publish the service
        published_service = store_service.publish_service(service.service_id, "user1")
        
        assert published_service.status == ServiceStatus.PUBLISHED
        assert published_service.published_at is not None
    
    def test_suspend_service(self, store_service):
        """Test service suspension"""
        # Register and publish a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        store_service.publish_service(service.service_id, "user1")
        
        # Suspend the service
        suspended_service = store_service.suspend_service(service.service_id, "user1")
        
        assert suspended_service.status == ServiceStatus.SUSPENDED
    
    def test_search_services(self, store_service):
        """Test service search functionality"""
        # Register multiple services
        services_data = [
            {
                "name": "Image API",
                "description": "Image processing service",
                "category": "image_processing",
                "code_hash": "hash1",
                "tags": ["image", "processing"]
            },
            {
                "name": "Text API",
                "description": "Text processing service",
                "category": "text_processing",
                "code_hash": "hash2",
                "tags": ["text", "nlp"]
            },
            {
                "name": "Data API",
                "description": "Data analysis service",
                "category": "data_analysis",
                "code_hash": "hash3",
                "tags": ["data", "analysis"]
            }
        ]
        
        for i, data in enumerate(services_data):
            service = store_service.register_service(data, f"user{i}", f"User{i}")
            store_service.publish_service(service.service_id, f"user{i}")
        
        # Test search by query
        search_filter = SearchFilter(query="image")
        results, count = store_service.search_services(search_filter)
        
        assert len(results) == 1
        assert results[0].name == "Image API"
        assert count == 1
        
        # Test search by category
        search_filter = SearchFilter(category=ServiceCategory.TEXT_PROCESSING)
        results, count = store_service.search_services(search_filter)
        
        assert len(results) == 1
        assert results[0].name == "Text API"
        assert count == 1
    
    def test_add_review(self, store_service):
        """Test adding reviews"""
        # Register a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Add a review
        review = store_service.add_review(
            service.service_id, "user2", "Reviewer",
            5, "Great service", "This is an excellent API"
        )
        
        assert review.rating == 5
        assert review.user_id == "user2"
        assert review.service_id == service.service_id
        
        # Check that rating statistics are updated
        rating = store_service.get_rating(service.service_id)
        assert rating.total_ratings == 1
        assert rating.average_rating == 5.0
    
    def test_add_duplicate_review(self, store_service):
        """Test adding duplicate review by same user"""
        # Register a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Add first review
        store_service.add_review(
            service.service_id, "user2", "Reviewer",
            5, "Great service", "This is an excellent API"
        )
        
        # Try to add duplicate review
        with pytest.raises(ValueError, match="User has already reviewed this service"):
            store_service.add_review(
                service.service_id, "user2", "Reviewer",
                4, "Good service", "This is a good API"
            )
    
    def test_record_service_usage(self, store_service):
        """Test recording service usage"""
        # Register a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Record usage
        usage = store_service.record_service_usage(service.service_id, "user2", 0.01)
        
        assert usage.total_calls == 1
        assert usage.total_spent == 0.01
        assert usage.service_id == service.service_id
        assert usage.user_id == "user2"
        
        # Check service statistics are updated
        updated_service = store_service.get_service(service.service_id)
        assert updated_service.total_calls == 1
        assert updated_service.total_revenue == 0.01
    
    def test_toggle_favorite(self, store_service):
        """Test toggling favorite status"""
        # Register a service
        service_data = {
            "name": "Test API",
            "description": "A test API service",
            "category": "api",
            "code_hash": "test_hash_123"
        }
        service = store_service.register_service(service_data, "user1", "Test User")
        
        # Toggle favorite
        is_favorite = store_service.toggle_favorite(service.service_id, "user2")
        assert is_favorite is True
        
        # Toggle again
        is_favorite = store_service.toggle_favorite(service.service_id, "user2")
        assert is_favorite is False
    
    def test_get_favorites(self, store_service):
        """Test getting user favorites"""
        # Register services
        services_data = [
            {
                "name": "API 1",
                "description": "First API",
                "category": "api",
                "code_hash": "hash1"
            },
            {
                "name": "API 2",
                "description": "Second API",
                "category": "api",
                "code_hash": "hash2"
            }
        ]
        
        for i, data in enumerate(services_data):
            service = store_service.register_service(data, f"user{i}", f"User{i}")
        
        # Add to favorites
        store_service.toggle_favorite(services_data[0]["name"], "user1")
        store_service.toggle_favorite(services_data[1]["name"], "user1")
        
        # Get favorites
        favorites = store_service.get_favorites("user1")
        assert len(favorites) == 2
    
    def test_get_popular_services(self, store_service):
        """Test getting popular services"""
        # Register services with different usage
        services_data = [
            {
                "name": "Popular API",
                "description": "Popular service",
                "category": "api",
                "code_hash": "hash1"
            },
            {
                "name": "Less Popular API",
                "description": "Less popular service",
                "category": "api",
                "code_hash": "hash2"
            }
        ]
        
        for i, data in enumerate(services_data):
            service = store_service.register_service(data, f"user{i}", f"User{i}")
            store_service.publish_service(service.service_id, f"user{i}")
        
        # Add usage to first service
        store_service.record_service_usage(services_data[0]["name"], "user1", 0.01)
        store_service.record_service_usage(services_data[0]["name"], "user2", 0.01)
        
        # Get popular services
        popular = store_service.get_popular_services(limit=2)
        assert len(popular) == 2
        assert popular[0].name == "Popular API"  # Should be first due to usage
    
    def test_get_recent_services(self, store_service):
        """Test getting recent services"""
        # Register services
        services_data = [
            {
                "name": "Old API",
                "description": "Old service",
                "category": "api",
                "code_hash": "hash1"
            },
            {
                "name": "New API",
                "description": "New service",
                "category": "api",
                "code_hash": "hash2"
            }
        ]
        
        for i, data in enumerate(services_data):
            service = store_service.register_service(data, f"user{i}", f"User{i}")
            store_service.publish_service(service.service_id, f"user{i}")
        
        # Get recent services
        recent = store_service.get_recent_services(limit=2)
        assert len(recent) == 2
        assert recent[0].name == "New API"  # Should be first (most recent)
    
    def test_get_service_statistics(self, store_service):
        """Test getting store statistics"""
        # Register some services
        services_data = [
            {
                "name": "API 1",
                "description": "First API",
                "category": "api",
                "code_hash": "hash1"
            },
            {
                "name": "API 2",
                "description": "Second API",
                "category": "utility",
                "code_hash": "hash2"
            }
        ]
        
        for i, data in enumerate(services_data):
            service = store_service.register_service(data, f"user{i}", f"User{i}")
            store_service.publish_service(service.service_id, f"user{i}")
        
        # Add some usage
        store_service.record_service_usage(services_data[0]["name"], "user1", 0.01)
        
        # Get statistics
        stats = store_service.get_service_statistics()
        
        assert stats["total_services"] == 2
        assert stats["published_services"] == 2
        assert stats["total_calls"] == 1
        assert stats["total_revenue"] == 0.01
        assert "api" in stats["category_distribution"]
        assert "utility" in stats["category_distribution"]


class TestRatingSystem:
    """Test cases for RatingSystem"""
    
    @pytest.fixture
    def rating_system(self):
        """Create rating system for testing"""
        return RatingSystem()
    
    def test_add_review(self, rating_system):
        """Test adding a review"""
        review = rating_system.add_review(
            "service1", "user1", "User One",
            5, "Great service", "Excellent API"
        )
        
        assert review.rating == 5
        assert review.service_id == "service1"
        assert review.user_id == "user1"
        
        # Check rating statistics
        rating = rating_system.get_rating("service1")
        assert rating.total_ratings == 1
        assert rating.average_rating == 5.0
    
    def test_duplicate_review(self, rating_system):
        """Test adding duplicate review"""
        rating_system.add_review(
            "service1", "user1", "User One",
            5, "Great service", "Excellent API"
        )
        
        with pytest.raises(ValueError, match="User has already reviewed this service"):
            rating_system.add_review(
                "service1", "user1", "User One",
                4, "Good service", "Good API"
            )
    
    def test_rating_distribution(self, rating_system):
        """Test rating distribution calculation"""
        # Add reviews with different ratings
        ratings = [5, 4, 3, 5, 2]
        for i, rating_val in enumerate(ratings):
            rating_system.add_review(
                "service1", f"user{i}", f"User{i}",
                rating_val, f"Review {i}", f"Content {i}"
            )
        
        rating = rating_system.get_rating("service1")
        distribution = rating.rating_distribution
        
        assert distribution[5] == 2
        assert distribution[4] == 1
        assert distribution[3] == 1
        assert distribution[2] == 1
        assert distribution[1] == 0
    
    def test_weighted_rating(self, rating_system):
        """Test weighted rating calculation"""
        # Add multiple reviews
        for i in range(10):
            rating_system.add_review(
                "service1", f"user{i}", f"User{i}",
                5, f"Review {i}", f"Content {i}"
            )
        
        weighted = rating_system.calculate_weighted_rating("service1")
        assert weighted > 0
        assert weighted <= 5.0


class TestMetadataStorage:
    """Test cases for MetadataStorage"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create metadata storage for testing"""
        return MetadataStorage(storage_path=temp_dir)
    
    def test_store_service_metadata(self, storage):
        """Test storing service metadata"""
        service = Service(
            name="Test Service",
            description="Test description",
            category=ServiceCategory.API,
            owner_id="user1",
            code_hash="test_hash"
        )
        
        content_hash = storage.store_service_metadata(service)
        
        assert content_hash is not None
        assert len(content_hash) == 64  # SHA256 hash length
        
        # Check that metadata can be retrieved
        metadata = storage.get_service_metadata(service.service_id)
        assert metadata is not None
        assert metadata["name"] == "Test Service"
    
    def test_search_services(self, storage):
        """Test service search"""
        # Store multiple services
        services = [
            Service(name="Image API", description="Image processing", category=ServiceCategory.IMAGE_PROCESSING, owner_id="user1", code_hash="hash1"),
            Service(name="Text API", description="Text processing", category=ServiceCategory.TEXT_PROCESSING, owner_id="user2", code_hash="hash2"),
            Service(name="Data API", description="Data analysis", category=ServiceCategory.DATA_ANALYSIS, owner_id="user3", code_hash="hash3")
        ]
        
        for service in services:
            storage.store_service_metadata(service)
        
        # Search by query
        results = storage.search_services("image")
        assert len(results) == 1
        assert results[0]["name"] == "Image API"
        
        # Search by category
        results = storage.search_services("", filters={"category": "text_processing"})
        assert len(results) == 1
        assert results[0]["name"] == "Text API"
    
    def test_get_statistics(self, storage):
        """Test getting storage statistics"""
        # Store some data
        service = Service(name="Test", description="Test", category=ServiceCategory.API, owner_id="user1", code_hash="hash")
        storage.store_service_metadata(service)
        
        stats = storage.get_service_statistics()
        
        assert stats["total_services"] == 1
        assert stats["storage_size"] > 0
        assert stats["cache_size"] >= 0 