"""
Initialize the DuxOS Escrow database using SQLAlchemy models.
"""
from duxos_escrow.models import Base
from sqlalchemy import create_engine

if __name__ == "__main__":
    engine = create_engine("sqlite:///duxos_escrow.db")
    Base.metadata.create_all(engine)
    print("Database initialized using SQLAlchemy models.") 