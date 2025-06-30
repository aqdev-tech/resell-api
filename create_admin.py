import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("No DATABASE_URL set for connection")

parsed_url = urlparse(DATABASE_URL)
test_db_name = parsed_url.path[1:] + "_test"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

# Create a sessionmaker to manage database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def create_super_admin():
    """Creates the initial SUPER_ADMIN user."""
    db = SessionLocal()
    try:
        username = "hikmaadmin"
        password = "alhikmatech"
        
        # Check if the admin already exists
        existing_admin = db.execute(
            text("SELECT * FROM admins WHERE username = :username"),
            {"username": username}
        ).first()

        if existing_admin:
            print(f"Admin user '{username}' already exists. Skipping creation.")
        else:
            # Hash the password
            hashed_password = get_password_hash(password)
            
            # Insert the new admin into the database
            db.execute(
                text("INSERT INTO admins (username, hashed_password, role, is_active) VALUES (:username, :hashed_password, :role, :is_active)"),
                {"username": username, "hashed_password": hashed_password, "role": 'SUPER_ADMIN', "is_active": True}
            )
            db.commit()
            print(f"SUPER_ADMIN user '{username}' created successfully.")

        # Create the test database
        with engine.connect() as connection:
            connection.execute(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            connection.execute(text(f"CREATE DATABASE {test_db_name}"))
            print(f"Test database '{test_db_name}' created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()

if __name__ == "__main__":
    create_super_admin()