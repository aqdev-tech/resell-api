import getpass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Define the database URL
DATABASE_URL = "sqlite:///./reselling.db"

# Create a SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a sessionmaker to manage database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def create_admin():
    """Creates a new admin user with a securely hashed password."""
    db = SessionLocal()
    try:
        print("Creating a new admin user...")
        username = input("Enter username: ")
        password = getpass.getpass("Enter password: ")
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Insert the new admin into the database
        db.execute(
            text("INSERT INTO admins (username, hashed_password) VALUES (:username, :hashed_password)"),
            {"username": username, "hashed_password": hashed_password}
        )
        db.commit()
        print(f"Admin user '{username}' created successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()