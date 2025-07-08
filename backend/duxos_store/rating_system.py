"""
Rating System

Handles service reviews, ratings, and reputation management for the store.
"""

import json
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from .models import Rating, Review, Service


class RatingSystem:
    """Manages service ratings and reviews"""

    def __init__(self) -> None:
        self.reviews: Dict[str, List[Review]] = {}  # service_id -> reviews
        self.ratings: Dict[str, Rating] = {}  # service_id -> rating stats
        self.user_reviews: Dict[str, List[str]] = {}  # user_id -> review_ids
        self.review_helpful_votes: Dict[str, List[str]] = (
            {}
        )  # review_id -> user_ids who voted helpful

    def add_review(
        self,
        service_id: str,
        user_id: str,
        user_name: str,
        rating: int,
        title: str,
        content: str,
        is_verified_purchase: bool = False,
    ) -> Review:
        """Add a new review for a service"""

        # Validate rating
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        # Check if user already reviewed this service
        existing_review = self.get_user_review_for_service(service_id, user_id)
        if existing_review:
            raise ValueError("User has already reviewed this service")

        # Create review
        review = Review(
            service_id=service_id,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            title=title,
            content=content,
            is_verified_purchase=is_verified_purchase,
        )

        # Store review
        if service_id not in self.reviews:
            self.reviews[service_id] = []
        self.reviews[service_id].append(review)

        # Track user reviews
        if user_id not in self.user_reviews:
            self.user_reviews[user_id] = []
        self.user_reviews[user_id].append(review.review_id)

        # Update rating statistics
        self._update_rating_statistics(service_id)

        return review

    def update_review(
        self,
        review_id: str,
        user_id: str,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Optional[Review]:
        """Update an existing review"""

        review = self.get_review(review_id)
        if not review or review.user_id != user_id:
            return None

        # Update fields
        if rating is not None:
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be between 1 and 5")
            review.rating = rating

        if title is not None:
            review.title = title

        if content is not None:
            review.content = content

        review.updated_at = datetime.utcnow()

        # Update rating statistics
        self._update_rating_statistics(review.service_id)

        return review

    def delete_review(self, review_id: str, user_id: str) -> bool:
        """Delete a review"""
        review = self.get_review(review_id)
        if not review or review.user_id != user_id:
            return False

        # Remove from storage
        service_id = review.service_id
        if service_id in self.reviews:
            self.reviews[service_id] = [
                r for r in self.reviews[service_id] if r.review_id != review_id
            ]

        # Remove from user tracking
        if user_id in self.user_reviews:
            self.user_reviews[user_id] = [
                rid for rid in self.user_reviews[user_id] if rid != review_id
            ]

        # Remove helpful votes
        if review_id in self.review_helpful_votes:
            del self.review_helpful_votes[review_id]

        # Update rating statistics
        self._update_rating_statistics(service_id)

        return True

    def get_review(self, review_id: str) -> Optional[Review]:
        """Get a review by ID"""
        for reviews in self.reviews.values():
            for review in reviews:
                if review.review_id == review_id:
                    return review
        return None

    def get_service_reviews(
        self, service_id: str, limit: int = 20, offset: int = 0, sort_by: str = "date"
    ) -> List[Review]:
        """Get reviews for a service with pagination and sorting"""
        reviews = self.reviews.get(service_id, [])

        # Sort reviews
        if sort_by == "rating":
            reviews.sort(key=lambda r: r.rating, reverse=True)
        elif sort_by == "helpful":
            reviews.sort(key=lambda r: r.helpful_votes, reverse=True)
        else:  # date
            reviews.sort(key=lambda r: r.created_at, reverse=True)

        return reviews[offset : offset + limit]

    def get_user_review_for_service(self, service_id: str, user_id: str) -> Optional[Review]:
        """Get a user's review for a specific service"""
        reviews = self.reviews.get(service_id, [])
        for review in reviews:
            if review.user_id == user_id:
                return review
        return None

    def get_user_reviews(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Review]:
        """Get all reviews by a user"""
        user_review_ids = self.user_reviews.get(user_id, [])
        reviews = []

        for review_id in user_review_ids[offset : offset + limit]:
            review = self.get_review(review_id)
            if review:
                reviews.append(review)

        return reviews

    def vote_review_helpful(self, review_id: str, user_id: str) -> bool:
        """Vote a review as helpful"""
        review = self.get_review(review_id)
        if not review:
            return False

        # Check if user already voted
        if review_id not in self.review_helpful_votes:
            self.review_helpful_votes[review_id] = []

        if user_id in self.review_helpful_votes[review_id]:
            return False  # Already voted

        # Add vote
        self.review_helpful_votes[review_id].append(user_id)
        review.helpful_votes = len(self.review_helpful_votes[review_id])

        return True

    def get_rating(self, service_id: str) -> Optional[Rating]:
        """Get rating statistics for a service"""
        return self.ratings.get(service_id)

    def get_top_rated_services(
        self, limit: int = 10, min_reviews: int = 5
    ) -> List[Tuple[str, float]]:
        """Get top rated services based on average rating and minimum review count"""
        top_services = []

        for service_id, rating in self.ratings.items():
            if rating.total_ratings >= min_reviews:
                top_services.append((service_id, rating.average_rating))

        # Sort by average rating (descending)
        top_services.sort(key=lambda x: x[1], reverse=True)

        return top_services[:limit]

    def get_rating_distribution(self, service_id: str) -> Dict[int, int]:
        """Get rating distribution for a service (1-5 stars)"""
        rating = self.ratings.get(service_id)
        if not rating:
            return {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        return rating.rating_distribution

    def calculate_weighted_rating(self, service_id: str) -> float:
        """Calculate weighted rating that considers review count and recency"""
        rating = self.ratings.get(service_id)
        if not rating or rating.total_ratings == 0:
            return 0.0

        # Base score from average rating
        base_score = rating.average_rating

        # Confidence boost based on number of reviews
        # More reviews = higher confidence = higher weight
        confidence_factor = min(rating.total_ratings / 100.0, 1.0)

        # Recency boost (recent reviews weighted more)
        recent_reviews = self._get_recent_reviews(service_id, days=30)
        recency_factor = len(recent_reviews) / max(rating.total_ratings, 1)

        # Calculate weighted score
        weighted_score = base_score * (1 + confidence_factor * 0.2 + recency_factor * 0.1)

        return min(weighted_score, 5.0)  # Cap at 5.0

    def _get_recent_reviews(self, service_id: str, days: int = 30) -> List[Review]:
        """Get reviews from the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        reviews = self.reviews.get(service_id, [])

        return [r for r in reviews if r.created_at >= cutoff_date]

    def _update_rating_statistics(self, service_id: str) -> None:
        """Update rating statistics for a service"""
        reviews = self.reviews.get(service_id, [])

        if not reviews:
            # Remove rating if no reviews
            if service_id in self.ratings:
                del self.ratings[service_id]
            return

        # Calculate statistics
        total_ratings = len(reviews)
        total_score = sum(r.rating for r in reviews)
        average_rating = total_score / total_ratings

        # Calculate distribution
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in reviews:
            distribution[review.rating] += 1

        # Create or update rating
        rating = Rating(
            service_id=service_id,
            total_ratings=total_ratings,
            average_rating=average_rating,
            rating_distribution=distribution,
        )
        rating.calculate_weighted_score()

        self.ratings[service_id] = rating

    def get_review_analytics(self, service_id: str) -> Dict[str, Any]:
        """Get detailed analytics for service reviews"""
        reviews = self.reviews.get(service_id, [])
        rating = self.ratings.get(service_id)

        if not reviews:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "verified_purchases": 0,
                "recent_reviews": 0,
                "helpful_reviews": 0,
            }

        # Calculate analytics
        verified_purchases = len([r for r in reviews if r.is_verified_purchase])
        recent_reviews = len(self._get_recent_reviews(service_id, days=30))
        helpful_reviews = len([r for r in reviews if r.helpful_votes > 0])

        return {
            "total_reviews": len(reviews),
            "average_rating": rating.average_rating if rating else 0.0,
            "rating_distribution": (
                rating.rating_distribution if rating else {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            ),
            "verified_purchases": verified_purchases,
            "recent_reviews": recent_reviews,
            "helpful_reviews": helpful_reviews,
            "weighted_rating": self.calculate_weighted_rating(service_id),
        }

    def export_reviews(self, service_id: str) -> List[Dict[str, Any]]:
        """Export reviews for a service as JSON-serializable data"""
        reviews = self.reviews.get(service_id, [])
        return [review.to_dict() for review in reviews]

    def import_reviews(self, service_id: str, reviews_data: List[Dict[str, Any]]) -> None:
        """Import reviews from JSON data"""
        for review_data in reviews_data:
            try:
                review = Review(
                    review_id=review_data.get("review_id", str(uuid.uuid4())),
                    service_id=service_id,
                    user_id=review_data.get("user_id", ""),
                    user_name=review_data.get("user_name", ""),
                    rating=review_data.get("rating", 0),
                    title=review_data.get("title", ""),
                    content=review_data.get("content", ""),
                    helpful_votes=review_data.get("helpful_votes", 0),
                    is_verified_purchase=review_data.get("is_verified_purchase", False),
                )

                # Parse timestamps
                if review_data.get("created_at"):
                    review.created_at = datetime.fromisoformat(review_data["created_at"])
                if review_data.get("updated_at"):
                    review.updated_at = datetime.fromisoformat(review_data["updated_at"])

                # Store review
                if service_id not in self.reviews:
                    self.reviews[service_id] = []
                self.reviews[service_id].append(review)

                # Track user reviews
                if review.user_id not in self.user_reviews:
                    self.user_reviews[review.user_id] = []
                self.user_reviews[review.user_id].append(review.review_id)

            except Exception as e:
                print(f"Error importing review: {e}")
                continue

        # Update rating statistics
        self._update_rating_statistics(service_id)
