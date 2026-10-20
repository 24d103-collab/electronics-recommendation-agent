
from app.db.models import Base
from app.db.sessions import engine


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    initialize_database()
