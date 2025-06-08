"""
Migration script to add the BusinessRulesTransition table to the database.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import Column, Integer, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine import Engine

from rataura2.db.session import engine, create_tables
from rataura2.db.models.base import Base
from rataura2.transitions.business_rules_adapter import BusinessRulesTransition


def run_migration():
    """Run the migration to add the BusinessRulesTransition table."""
    print("Running migration to add BusinessRulesTransition table...")
    
    # Create the table
    BusinessRulesTransition.__table__.create(engine, checkfirst=True)
    
    print("Migration completed successfully.")


if __name__ == "__main__":
    run_migration()

