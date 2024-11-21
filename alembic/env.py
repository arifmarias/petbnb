# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.append(str(Path(__file__).parents[1]))

# Load .env file
load_dotenv()

# this is the Alembic Config object
config = context.config

# Get database URL from environment
database_url = os.getenv("DATABASE_URL")
if database_url is None:
    raise Exception("DATABASE_URL not found in environment variables")

# Override sqlalchemy.url with environment variable
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models
from app.models.user import User
from app.models.pet import Pet
from app.models.caregiver import CaregiverProfile
from app.models.booking import Booking
from app.models.review import Review
from app.core.database import Base

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()