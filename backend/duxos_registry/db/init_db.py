from ..models.database_models import Capability, Node, ReputationEvent
from .database import Base, SessionLocal, engine
from .repository import CapabilityRepository, NodeRepository, ReputationRepository


def init_database():
    """Initialize the database by creating all tables"""
    Base.metadata.create_all(bind=engine)


def create_sample_data():
    """Create sample data for testing"""
    db = SessionLocal()
    try:
        # Create sample capabilities
        cap_repo = CapabilityRepository(db)
        sample_capabilities = [
            ("gpu_compute", "GPU Computing", "1.0"),
            ("cpu_compute", "CPU Computing", "1.0"),
            ("storage", "Storage Services", "1.0"),
            ("network", "Network Services", "1.0"),
            ("ai_inference", "AI Inference", "1.0"),
            ("wallet", "Wallet Services", "1.0"),
            ("blockchain", "Blockchain Services", "1.0"),
        ]

        for name, desc, version in sample_capabilities:
            if not cap_repo.get_capability(name):
                cap_repo.create_capability(name, desc, version)

        # Create sample nodes
        node_repo = NodeRepository(db)
        sample_nodes = [
            ("node_001", "192.168.1.100:8080", ["gpu_compute", "ai_inference"]),
            ("node_002", "192.168.1.101:8080", ["cpu_compute", "storage"]),
            ("node_003", "192.168.1.102:8080", ["network", "storage"]),
        ]

        for node_id, address, capabilities in sample_nodes:
            if not node_repo.get_node(node_id):
                node_repo.create_node(node_id, address, capabilities)

        print("Sample data created successfully!")

    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")

    print("Creating sample data...")
    create_sample_data()
