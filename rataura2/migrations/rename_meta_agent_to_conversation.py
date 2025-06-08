"""
Migration script to rename MetaAgent to Conversation.

This script renames the MetaAgent table to Conversation and updates all related tables.
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import Table, Column, Integer, ForeignKey, MetaData, text
from sqlalchemy.engine import Engine

from rataura2.db.session import engine


def run_migration():
    """Run the migration to rename MetaAgent to Conversation."""
    print("Running migration to rename MetaAgent to Conversation...")
    
    # Create a connection
    with engine.connect() as conn:
        # Start a transaction
        with conn.begin():
            # Rename the MetaAgent table to Conversation
            conn.execute(text("ALTER TABLE \"MetaAgent\" RENAME TO \"Conversation\""))
            
            # Rename the meta_agent_agent_association table to conversation_agent_association
            conn.execute(text("ALTER TABLE \"meta_agent_agent_association\" RENAME TO \"conversation_agent_association\""))
            
            # Rename the meta_agent_id column in the association table
            conn.execute(text("ALTER TABLE \"conversation_agent_association\" RENAME COLUMN \"meta_agent_id\" TO \"conversation_id\""))
            
            # Update the foreign key constraint in the association table
            conn.execute(text("ALTER TABLE \"conversation_agent_association\" DROP CONSTRAINT \"meta_agent_agent_association_meta_agent_id_fkey\""))
            conn.execute(text("ALTER TABLE \"conversation_agent_association\" ADD CONSTRAINT \"conversation_agent_association_conversation_id_fkey\" FOREIGN KEY (\"conversation_id\") REFERENCES \"Conversation\" (\"id\")"))
    
    print("Migration completed successfully.")


if __name__ == "__main__":
    run_migration()

