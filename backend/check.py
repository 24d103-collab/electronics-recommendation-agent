
from app.db.sessions import check_database_connection

if check_database_connection():
    print("Database connection successful!")
