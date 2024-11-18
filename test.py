from dotenv import load_dotenv
import os
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Get database URL from environment
database_url = os.getenv("DBASE_URL")
print("Database URL:", database_url)  # This will help us debug

# Create engine
engine = create_engine(database_url)

# Try to connect
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print(result.fetchone())
except Exception as e:
    print(f"Error: {e}")