"""
Store API

REST API layer for the DuxOS API/App Store using FastAPI.
Provides endpoints for service management, search, reviews, and discovery.
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn

from .store_service import StoreService
from .rating_system import RatingSystem
from .metadata_storage import MetadataStorage
from .models import Service, Review, Rating, ServiceCategory, ServiceStatus, SearchFilter


# Pydantic models for API requests/responses
class ServiceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    version: str = Field(default="1.0.0")
    category: str = Field(..., description="Service category")
    tags: List[str] = Field(default_factory=list)
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    price_per_call: float = Field(default=0.0, ge=0.0)
    price_currency: str = Field(default="FLOP")
    free_tier_calls: int = Field(default=0, ge=0)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)
    code_hash: str = Field(..., description="Hash of service code")
    execution_requirements: Dict[str, Any] = Field(default_factory=dict)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    example_input: Optional[Dict[str, Any]] = None
    example_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    documentation_url: Optional[str] = None
    repository_url: Optional[str] = None
    price_per_call: Optional[float] = Field(None, ge=0.0)
    price_currency: Optional[str] = None
    free_tier_calls: Optional[int] = Field(None, ge=0)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1)
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    example_input: Optional[Dict[str, Any]] = None
    example_output: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10, max_length=1000)


class ReviewUpdateRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=10, max_length=1000)


class SearchRequest(BaseModel):
    query: str = Field(default="")
    category: Optional[str] = None
    min_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    max_price: Optional[float] = Field(None, ge=0.0)
    tags: List[str] = Field(default_factory=list)
    owner_id: Optional[str] = None
    status: str = Field(default="published")
    sort_by: str = Field(default="relevance", description="relevance, rating, price, date")
    sort_order: str = Field(default="desc", description="asc, desc")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ServiceResponse(BaseModel):
    service_id: str
    name: str
    description: str
    version: str
    category: str
    status: str
    owner_id: str
    owner_name: str
    tags: List[str]
    documentation_url: Optional[str]
    repository_url: Optional[str]
    price_per_call: float
    price_currency: str
    free_tier_calls: int
    rate_limit_per_hour: Optional[int]
    code_hash: str
    execution_requirements: Dict[str, Any]
    input_schema: Optional[Dict[str, Any]]
    output_schema: Optional[Dict[str, Any]]
    example_input: Optional[Dict[str, Any]]
    example_output: Optional[Dict[str, Any]]
    avg_response_time: Optional[float]
    success_rate: Optional[float]
    uptime_percentage: Optional[float]
    total_calls: int
    total_revenue: float
    rating_count: int
    average_rating: float
    created_at: str
    updated_at: str
    published_at: Optional[str]
    metadata: Dict[str, Any]


class ReviewResponse(BaseModel):
    review_id: str
    service_id: str
    user_id: str
    user_name: str
    rating: int
    title: str
    content: str
    helpful_votes: int
    is_verified_purchase: bool
    created_at: str
    updated_at: str


class RatingResponse(BaseModel):
    service_id: str
    total_ratings: int
    average_rating: float
    rating_distribution: Dict[int, int]
    weighted_score: float
    last_updated: str


class SearchResponse(BaseModel):
    services: List[ServiceResponse]
    total_count: int
    limit: int
    offset: int


class StatisticsResponse(BaseModel):
    total_services: int
    published_services: int
    total_reviews: int
    total_calls: int
    total_revenue: float
    category_distribution: Dict[str, int]


class StoreAPI:
    """FastAPI application for the store"""
    
    def __init__(self, store_service: StoreService):
        self.store_service = store_service
        self.app = FastAPI(
            title="DuxOS API/App Store",
            description="Decentralized marketplace for APIs and applications",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint"""
            return {"message": "DuxOS API/App Store", "version": "1.0.0"}
        
        @self.app.post("/services", response_model=ServiceResponse)
        async def create_service(
            request: ServiceCreateRequest,
            owner_id: str = Query(..., description="Service owner ID"),
            owner_name: str = Query(..., description="Service owner name")
        ):
            """Create a new service"""
            try:
                service_data = request.dict()
                service_data["category"] = request.category
                
                service = self.store_service.register_service(service_data, owner_id, owner_name)
                return ServiceResponse(**service.to_dict())
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
        
        @self.app.get("/services/{service_id}", response_model=ServiceResponse)
        async def get_service(service_id: str = Path(..., description="Service ID")):
            """Get a service by ID"""
            service = self.store_service.get_service(service_id)
            if not service:
                raise HTTPException(status_code=404, detail="Service not found")
            return ServiceResponse(**service.to_dict())
        
        @self.app.put("/services/{service_id}", response_model=ServiceResponse)
        async def update_service(
            request: ServiceUpdateRequest,
            service_id: str = Path(..., description="Service ID"),
            owner_id: str = Query(..., description="Service owner ID")
        ):
            """Update a service"""
            if not request:
                raise HTTPException(status_code=400, detail="Request body required")
            
            # Filter out None values
            updates = {k: v for k, v in request.dict().items() if v is not None}
            
            service = self.store_service.update_service(service_id, updates, owner_id)
            if not service:
                raise HTTPException(status_code=404, detail="Service not found or access denied")
            return ServiceResponse(**service.to_dict())
        
        @self.app.post("/services/{service_id}/publish", response_model=ServiceResponse)
        async def publish_service(
            service_id: str = Path(..., description="Service ID"),
            owner_id: str = Query(..., description="Service owner ID")
        ):
            """Publish a service"""
            service = self.store_service.publish_service(service_id, owner_id)
            if not service:
                raise HTTPException(status_code=404, detail="Service not found or access denied")
            return ServiceResponse(**service.to_dict())
        
        @self.app.post("/services/{service_id}/suspend", response_model=ServiceResponse)
        async def suspend_service(
            service_id: str = Path(..., description="Service ID"),
            owner_id: str = Query(..., description="Service owner ID")
        ):
            """Suspend a service"""
            service = self.store_service.suspend_service(service_id, owner_id)
            if not service:
                raise HTTPException(status_code=404, detail="Service not found or access denied")
            return ServiceResponse(**service.to_dict())
        
        @self.app.get("/services", response_model=SearchResponse)
        async def search_services(
            query: str = Query(default=""),
            category: Optional[str] = Query(None),
            min_rating: float = Query(default=0.0, ge=0.0, le=5.0),
            max_price: Optional[float] = Query(None, ge=0.0),
            tags: List[str] = Query(default_factory=list),
            owner_id: Optional[str] = Query(None),
            status: str = Query(default="published"),
            sort_by: str = Query(default="relevance"),
            sort_order: str = Query(default="desc"),
            limit: int = Query(default=20, ge=1, le=100),
            offset: int = Query(default=0, ge=0)
        ):
            """Search and filter services"""
            try:
                search_filter = SearchFilter(
                    query=query,
                    category=ServiceCategory(category) if category else None,
                    min_rating=min_rating,
                    max_price=max_price,
                    tags=tags,
                    owner_id=owner_id,
                    status=ServiceStatus(status),
                    sort_by=sort_by,
                    sort_order=sort_order,
                    limit=limit,
                    offset=offset
                )
                
                services, total_count = self.store_service.search_services(search_filter)
                
                return SearchResponse(
                    services=[ServiceResponse(**service.to_dict()) for service in services],
                    total_count=total_count,
                    limit=limit,
                    offset=offset
                )
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/services/owner/{owner_id}", response_model=List[ServiceResponse])
        async def get_services_by_owner(
            owner_id: str = Path(..., description="Owner ID"),
            status: Optional[str] = Query(None, description="Service status filter")
        ):
            """Get all services by an owner"""
            try:
                service_status = ServiceStatus(status) if status else None
                services = self.store_service.get_services_by_owner(owner_id, service_status)
                return [ServiceResponse(**service.to_dict()) for service in services]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/services/popular", response_model=List[ServiceResponse])
        async def get_popular_services(
            limit: int = Query(default=10, ge=1, le=50),
            category: Optional[str] = Query(None)
        ):
            """Get popular services"""
            try:
                service_category = ServiceCategory(category) if category else None
                services = self.store_service.get_popular_services(limit, service_category)
                return [ServiceResponse(**service.to_dict()) for service in services]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/services/recent", response_model=List[ServiceResponse])
        async def get_recent_services(limit: int = Query(default=10, ge=1, le=50)):
            """Get recently published services"""
            services = self.store_service.get_recent_services(limit)
            return [ServiceResponse(**service.to_dict()) for service in services]
        
        @self.app.post("/services/{service_id}/reviews", response_model=ReviewResponse)
        async def create_review(
            request: ReviewCreateRequest,
            service_id: str = Path(..., description="Service ID"),
            user_id: str = Query(..., description="User ID"),
            user_name: str = Query(..., description="User name")
        ):
            """Create a review for a service"""
            if not request:
                raise HTTPException(status_code=400, detail="Request body required")
            
            try:
                review = self.store_service.add_review(
                    service_id, user_id, user_name,
                    request.rating, request.title, request.content
                )
                if not review:
                    raise HTTPException(status_code=404, detail="Service not found")
                return ReviewResponse(**review.to_dict())
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.get("/services/{service_id}/reviews", response_model=List[ReviewResponse])
        async def get_service_reviews(
            service_id: str = Path(..., description="Service ID"),
            limit: int = Query(default=20, ge=1, le=100),
            offset: int = Query(default=0, ge=0),
            sort_by: str = Query(default="date", description="date, rating, helpful")
        ):
            """Get reviews for a service"""
            reviews = self.store_service.get_reviews(service_id, limit, offset)
            return [ReviewResponse(**review.to_dict()) for review in reviews]
        
        @self.app.get("/services/{service_id}/rating", response_model=RatingResponse)
        async def get_service_rating(service_id: str = Path(..., description="Service ID")):
            """Get rating statistics for a service"""
            rating = self.store_service.get_rating(service_id)
            if not rating:
                raise HTTPException(status_code=404, detail="Rating not found")
            return RatingResponse(**rating.to_dict())
        
        @self.app.post("/services/{service_id}/reviews/{review_id}/helpful")
        async def vote_review_helpful(
            service_id: str = Path(..., description="Service ID"),
            review_id: str = Path(..., description="Review ID"),
            user_id: str = Query(..., description="User ID")
        ):
            """Vote a review as helpful"""
            success = self.store_service.rating_system.vote_review_helpful(review_id, user_id)
            if not success:
                raise HTTPException(status_code=400, detail="Unable to vote review")
            return {"message": "Vote recorded successfully"}
        
        @self.app.get("/users/{user_id}/reviews", response_model=List[ReviewResponse])
        async def get_user_reviews(
            user_id: str = Path(..., description="User ID"),
            limit: int = Query(default=20, ge=1, le=100),
            offset: int = Query(default=0, ge=0)
        ):
            """Get all reviews by a user"""
            reviews = self.store_service.rating_system.get_user_reviews(user_id, limit, offset)
            return [ReviewResponse(**review.to_dict()) for review in reviews]
        
        @self.app.get("/users/{user_id}/favorites", response_model=List[ServiceResponse])
        async def get_user_favorites(user_id: str = Path(..., description="User ID")):
            """Get user's favorite services"""
            services = self.store_service.get_favorites(user_id)
            return [ServiceResponse(**service.to_dict()) for service in services]
        
        @self.app.post("/services/{service_id}/favorite")
        async def toggle_favorite(
            service_id: str = Path(..., description="Service ID"),
            user_id: str = Query(..., description="User ID")
        ):
            """Toggle favorite status for a service"""
            is_favorite = self.store_service.toggle_favorite(service_id, user_id)
            return {"is_favorite": is_favorite}
        
        @self.app.post("/services/{service_id}/usage")
        async def record_usage(
            service_id: str = Path(..., description="Service ID"),
            user_id: str = Query(..., description="User ID"),
            call_cost: float = Query(default=0.0, ge=0.0, description="Cost of the call")
        ):
            """Record service usage"""
            usage = self.store_service.record_service_usage(service_id, user_id, call_cost)
            if not usage:
                raise HTTPException(status_code=404, detail="Service not found")
            return {"message": "Usage recorded successfully"}
        
        @self.app.get("/statistics", response_model=StatisticsResponse)
        async def get_statistics():
            """Get store statistics"""
            stats = self.store_service.get_service_statistics()
            return StatisticsResponse(**stats)
        
        @self.app.get("/categories", response_model=List[str])
        async def get_categories():
            """Get available service categories"""
            return [category.value for category in ServiceCategory]
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the API server"""
        uvicorn.run(self.app, host=host, port=port, reload=debug)


# Factory function to create the API
def create_store_api(store_service: StoreService) -> StoreAPI:
    """Create a store API instance"""
    return StoreAPI(store_service) 