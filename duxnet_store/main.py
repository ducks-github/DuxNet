"""
DuxOS API/App Store Main Entry Point

Main application entry point for the store service.
Provides CLI interface and server startup functionality.
"""

import argparse
import yaml
import sys
from pathlib import Path

from .store_service import StoreService
from .rating_system import RatingSystem
from .metadata_storage import MetadataStorage
from .api import StoreAPI


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Configuration file {config_path} not found. Using defaults.")
        return {}
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


def create_store_service(config: dict) -> StoreService:
    """Create and configure store service"""
    # Initialize components
    storage_config = config.get("storage", {})
    metadata_storage = MetadataStorage(
        storage_path=storage_config.get("path", "./store_metadata"),
        use_ipfs=storage_config.get("use_ipfs", False)
    )
    
    rating_system = RatingSystem()
    
    # Create store service
    store_service = StoreService(metadata_storage, rating_system)
    
    return store_service


def run_server(config: dict, store_service: StoreService):
    """Run the API server"""
    api_config = config.get("api", {})
    
    # Create API
    api = StoreAPI(store_service)
    
    # Run server
    api.run(
        host=api_config.get("host", "0.0.0.0"),
        port=api_config.get("port", 8000),
        debug=api_config.get("debug", False)
    )


def demo_mode(store_service: StoreService):
    """Run in demo mode with sample data"""
    print("Starting DuxOS Store in demo mode...")
    
    # Create sample services
    sample_services = [
        {
            "name": "Image Recognition API",
            "description": "Advanced image recognition service using deep learning",
            "category": "machine_learning",
            "tags": ["ai", "image", "recognition", "deep-learning"],
            "price_per_call": 0.01,
            "code_hash": "abc123def456",
            "owner_id": "demo_user_1",
            "owner_name": "AI Developer"
        },
        {
            "name": "Text Summarizer",
            "description": "Extractive text summarization service",
            "category": "text_processing",
            "tags": ["nlp", "summarization", "text"],
            "price_per_call": 0.005,
            "code_hash": "def456ghi789",
            "owner_id": "demo_user_2",
            "owner_name": "NLP Expert"
        },
        {
            "name": "Data Visualization",
            "description": "Create beautiful charts and graphs from data",
            "category": "data_analysis",
            "tags": ["visualization", "charts", "graphs"],
            "price_per_call": 0.02,
            "code_hash": "ghi789jkl012",
            "owner_id": "demo_user_3",
            "owner_name": "Data Scientist"
        }
    ]
    
    # Register sample services
    for service_data in sample_services:
        try:
            service = store_service.register_service(service_data, 
                                                   service_data["owner_id"], 
                                                   service_data["owner_name"])
            store_service.publish_service(service.service_id, service_data["owner_id"])
            print(f"Created service: {service.name}")
        except Exception as e:
            print(f"Error creating service {service_data['name']}: {e}")
    
    # Add sample reviews
    sample_reviews = [
        ("Image Recognition API", "user1", "Great accuracy!", 5, "Excellent service", "Very accurate image recognition"),
        ("Image Recognition API", "user2", "Good but slow", 4, "Good service", "Accurate but could be faster"),
        ("Text Summarizer", "user3", "Perfect for my needs", 5, "Excellent", "Exactly what I needed"),
        ("Data Visualization", "user4", "Beautiful charts", 5, "Amazing", "Creates stunning visualizations")
    ]
    
    for service_name, user_id, user_name, rating, title, content in sample_reviews:
        # Find service by name
        services = [s for s in store_service.services.values() if s.name == service_name]
        if services:
            service = services[0]
            try:
                store_service.add_review(service.service_id, user_id, user_name, 
                                       rating, title, content)
                print(f"Added review for {service_name}")
            except Exception as e:
                print(f"Error adding review for {service_name}: {e}")
    
    print("Demo data loaded successfully!")
    print(f"Total services: {len(store_service.services)}")
    print(f"Total reviews: {sum(len(reviews) for reviews in store_service.reviews.values())}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DuxOS API/App Store")
    parser.add_argument("--config", "-c", default="config.yaml", 
                       help="Configuration file path")
    parser.add_argument("--demo", action="store_true", 
                       help="Run in demo mode with sample data")
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments
    if args.host:
        config.setdefault("api", {})["host"] = args.host
    if args.port:
        config.setdefault("api", {})["port"] = args.port
    if args.debug:
        config.setdefault("api", {})["debug"] = True
    
    # Create store service
    store_service = create_store_service(config)
    
    # Demo mode
    if args.demo:
        demo_mode(store_service)
    
    # Run server
    print("Starting DuxOS API/App Store...")
    print(f"API will be available at: http://{config.get('api', {}).get('host', '0.0.0.0')}:{config.get('api', {}).get('port', 8000)}")
    print("Press Ctrl+C to stop")
    
    try:
        run_server(config, store_service)
    except KeyboardInterrupt:
        print("\nShutting down DuxOS Store...")
    except Exception as e:
        print(f"Error running server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 