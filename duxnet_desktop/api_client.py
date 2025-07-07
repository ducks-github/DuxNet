"""
Store API Client for DuxOS Desktop

Handles communication with the DuxOS API/App Store backend.
"""

import requests
from typing import List, Dict, Any, Optional

STORE_API_URL = "http://localhost:8000"  # Can be made configurable

class StoreApiClient:
    def __init__(self, base_url: str = STORE_API_URL):
        self.base_url = base_url.rstrip("/")

    def search_services(self, query: str = "", category: Optional[str] = None, min_rating: float = 0.0,
                       max_price: Optional[float] = None, tags: Optional[List[str]] = None,
                       sort_by: str = "relevance", sort_order: str = "desc", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        params = {
            "query": query,
            "category": category,
            "min_rating": min_rating,
            "max_price": max_price,
            "tags": tags or [],
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        response = requests.get(f"{self.base_url}/services", params=params)
        response.raise_for_status()
        return response.json()

    def get_service(self, service_id: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/services/{service_id}")
        response.raise_for_status()
        return response.json()

    def get_service_reviews(self, service_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        params = {"limit": limit, "offset": offset}
        response = requests.get(f"{self.base_url}/services/{service_id}/reviews", params=params)
        response.raise_for_status()
        return response.json()

    def add_review(self, service_id: str, user_id: str, user_name: str, rating: int, title: str, content: str) -> Dict[str, Any]:
        payload = {"rating": rating, "title": title, "content": content}
        params = {"user_id": user_id, "user_name": user_name}
        response = requests.post(f"{self.base_url}/services/{service_id}/reviews", json=payload, params=params)
        response.raise_for_status()
        return response.json()

    def get_user_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.base_url}/users/{user_id}/favorites")
        response.raise_for_status()
        return response.json()

    def toggle_favorite(self, service_id: str, user_id: str) -> Dict[str, Any]:
        params = {"user_id": user_id}
        response = requests.post(f"{self.base_url}/services/{service_id}/favorite", params=params)
        response.raise_for_status()
        return response.json()

    def get_categories(self) -> List[str]:
        response = requests.get(f"{self.base_url}/categories")
        response.raise_for_status()
        return response.json()

    def get_statistics(self) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/statistics")
        response.raise_for_status()
        return response.json() 