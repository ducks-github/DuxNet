"""
Metadata Storage

Handles distributed storage of service metadata using IPFS or DHT.
Provides decentralized storage for service information, reviews, and ratings.
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.duxnet_store.models import Rating, Review, Service


class MetadataStorage:
    """Distributed metadata storage for services"""

    def __init__(self, storage_path: str = "./store_metadata", use_ipfs: bool = False):
        self.storage_path = Path(storage_path)
        self.use_ipfs = use_ipfs
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}

        # Create storage directory
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Subdirectories for different types of metadata
        self.services_path = self.storage_path / "services"
        self.reviews_path = self.storage_path / "reviews"
        self.ratings_path = self.storage_path / "ratings"
        self.index_path = self.storage_path / "index"

        for path in [self.services_path, self.reviews_path, self.ratings_path, self.index_path]:
            path.mkdir(exist_ok=True)

    def store_service_metadata(self, service: Service) -> str:
        """Store service metadata and return content hash"""
        metadata = service.to_dict()

        # Calculate content hash
        content_hash = self._calculate_content_hash(metadata)

        # Store metadata
        metadata_file = self.services_path / f"{content_hash}.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Update index
        self._update_service_index(service.service_id, content_hash, metadata)

        # Cache metadata
        self.metadata_cache[service.service_id] = metadata

        return content_hash

    def get_service_metadata(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve service metadata by ID"""
        # Check cache first
        if service_id in self.metadata_cache:
            return self.metadata_cache[service_id]

        # Check index
        index_entry = self._get_service_index_entry(service_id)
        if not index_entry:
            return None

        content_hash = index_entry.get("content_hash")
        if not content_hash:
            return None

        # Load from file
        metadata_file = self.services_path / f"{content_hash}.json"
        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                self.metadata_cache[service_id] = metadata
                return metadata
        except Exception as e:
            print(f"Error loading service metadata: {e}")
            return None

    def store_reviews(self, service_id: str, reviews: List[Review]) -> str:
        """Store reviews for a service"""
        reviews_data = [review.to_dict() for review in reviews]

        # Calculate content hash
        content_hash = self._calculate_content_hash(reviews_data)

        # Store reviews
        reviews_file = self.reviews_path / f"{service_id}_{content_hash}.json"
        with open(reviews_file, "w") as f:
            json.dump(reviews_data, f, indent=2)

        # Update index
        self._update_reviews_index(service_id, content_hash, len(reviews))

        return content_hash

    def get_reviews(self, service_id: str) -> List[Dict[str, Any]]:
        """Retrieve reviews for a service"""
        index_entry = self._get_reviews_index_entry(service_id)
        if not index_entry:
            return []

        content_hash = index_entry.get("content_hash")
        if not content_hash:
            return []

        reviews_file = self.reviews_path / f"{service_id}_{content_hash}.json"
        if not reviews_file.exists():
            return []

        try:
            with open(reviews_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading reviews: {e}")
            return []

    def store_rating(self, service_id: str, rating: Rating) -> str:
        """Store rating statistics for a service"""
        rating_data = rating.to_dict()

        # Calculate content hash
        content_hash = self._calculate_content_hash(rating_data)

        # Store rating
        rating_file = self.ratings_path / f"{service_id}_{content_hash}.json"
        with open(rating_file, "w") as f:
            json.dump(rating_data, f, indent=2)

        # Update index
        self._update_rating_index(service_id, content_hash)

        return content_hash

    def get_rating(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve rating statistics for a service"""
        index_entry = self._get_rating_index_entry(service_id)
        if not index_entry:
            return None

        content_hash = index_entry.get("content_hash")
        if not content_hash:
            return None

        rating_file = self.ratings_path / f"{service_id}_{content_hash}.json"
        if not rating_file.exists():
            return None

        try:
            with open(rating_file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading rating: {e}")
            return None

    def search_services(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search services by query and filters"""
        services = []

        # Load all service indices
        index_file = self.index_path / "services.json"
        if not index_file.exists():
            return services

        try:
            with open(index_file, "r") as f:
                service_indices = json.load(f)
        except Exception as e:
            print(f"Error loading service index: {e}")
            return services

        # Search through indices
        for service_id, index_entry in service_indices.items():
            metadata = index_entry.get("metadata", {})

            # Apply text search
            if query:
                query_lower = query.lower()
                name_match = query_lower in metadata.get("name", "").lower()
                desc_match = query_lower in metadata.get("description", "").lower()
                tag_match = any(query_lower in tag.lower() for tag in metadata.get("tags", []))

                if not (name_match or desc_match or tag_match):
                    continue

            # Apply filters
            if filters:
                if not self._apply_filters(metadata, filters):
                    continue

            services.append(metadata)

        return services

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            "total_services": 0,
            "total_reviews": 0,
            "total_ratings": 0,
            "storage_size": 0,
            "cache_size": len(self.metadata_cache),
        }

        # Count services
        index_file = self.index_path / "services.json"
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    service_indices = json.load(f)
                    stats["total_services"] = len(service_indices)
            except Exception:
                pass

        # Count reviews
        reviews_index_file = self.index_path / "reviews.json"
        if reviews_index_file.exists():
            try:
                with open(reviews_index_file, "r") as f:
                    review_indices = json.load(f)
                    stats["total_reviews"] = sum(
                        entry.get("count", 0) for entry in review_indices.values()
                    )
            except Exception:
                pass

        # Count ratings
        ratings_index_file = self.index_path / "ratings.json"
        if ratings_index_file.exists():
            try:
                with open(ratings_index_file, "r") as f:
                    rating_indices = json.load(f)
                    stats["total_ratings"] = len(rating_indices)
            except Exception:
                pass

        # Calculate storage size
        stats["storage_size"] = self._calculate_storage_size()

        return stats

    def backup_metadata(self, backup_path: str) -> bool:
        """Create a backup of all metadata"""
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy all files
            import shutil

            shutil.copytree(self.storage_path, backup_dir / "metadata", dirs_exist_ok=True)

            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False

    def restore_metadata(self, backup_path: str) -> bool:
        """Restore metadata from backup"""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                return False

            # Clear current storage
            import shutil

            shutil.rmtree(self.storage_path)

            # Restore from backup
            shutil.copytree(backup_dir / "metadata", self.storage_path)

            # Clear cache
            self.metadata_cache.clear()

            return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

    def _calculate_content_hash(self, data: Any) -> str:
        """Calculate content hash for data"""
        content = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode()).hexdigest()

    def _update_service_index(self, service_id: str, content_hash: str, metadata: Dict[str, Any]):
        """Update service index"""
        index_file = self.index_path / "services.json"

        # Load existing index
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    indices = json.load(f)
            except Exception:
                indices = {}
        else:
            indices = {}

        # Update index
        indices[service_id] = {
            "content_hash": content_hash,
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": metadata,
        }

        # Save index
        with open(index_file, "w") as f:
            json.dump(indices, f, indent=2)

    def _get_service_index_entry(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get service index entry"""
        index_file = self.index_path / "services.json"
        if not index_file.exists():
            return None

        try:
            with open(index_file, "r") as f:
                indices = json.load(f)
                return indices.get(service_id)
        except Exception:
            return None

    def _update_reviews_index(self, service_id: str, content_hash: str, count: int):
        """Update reviews index"""
        index_file = self.index_path / "reviews.json"

        # Load existing index
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    indices = json.load(f)
            except Exception:
                indices = {}
        else:
            indices = {}

        # Update index
        indices[service_id] = {
            "content_hash": content_hash,
            "count": count,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Save index
        with open(index_file, "w") as f:
            json.dump(indices, f, indent=2)

    def _get_reviews_index_entry(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get reviews index entry"""
        index_file = self.index_path / "reviews.json"
        if not index_file.exists():
            return None

        try:
            with open(index_file, "r") as f:
                indices = json.load(f)
                return indices.get(service_id)
        except Exception:
            return None

    def _update_rating_index(self, service_id: str, content_hash: str):
        """Update rating index"""
        index_file = self.index_path / "ratings.json"

        # Load existing index
        if index_file.exists():
            try:
                with open(index_file, "r") as f:
                    indices = json.load(f)
            except Exception:
                indices = {}
        else:
            indices = {}

        # Update index
        indices[service_id] = {
            "content_hash": content_hash,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Save index
        with open(index_file, "w") as f:
            json.dump(indices, f, indent=2)

    def _get_rating_index_entry(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get rating index entry"""
        index_file = self.index_path / "ratings.json"
        if not index_file.exists():
            return None

        try:
            with open(index_file, "r") as f:
                indices = json.load(f)
                return indices.get(service_id)
        except Exception:
            return None

    def _apply_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Apply filters to metadata"""
        for filter_key, filter_value in filters.items():
            if filter_key == "category" and metadata.get("category") != filter_value:
                return False
            elif filter_key == "min_rating" and metadata.get("average_rating", 0) < filter_value:
                return False
            elif filter_key == "max_price" and metadata.get("price_per_call", 0) > filter_value:
                return False
            elif filter_key == "owner_id" and metadata.get("owner_id") != filter_value:
                return False
            elif filter_key == "status" and metadata.get("status") != filter_value:
                return False

        return True

    def _calculate_storage_size(self) -> int:
        """Calculate total storage size in bytes"""
        total_size = 0

        for root, dirs, files in os.walk(self.storage_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.exists():
                    total_size += file_path.stat().st_size

        return total_size
