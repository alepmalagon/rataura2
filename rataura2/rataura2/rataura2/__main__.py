"""
Main entry point for the application.
"""
import logging
import argparse
from dotenv import load_dotenv

from rataura2.db.session import create_tables, get_db
from rataura2.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("rataura2")


def main():
    """Main entry point for the application."""
    # Load environment variables
    load_dotenv()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Rataura2 - EVE Online conversational agent")
    parser.add_argument("--init-db", action="store_true", help="Initialize the database")
    args = parser.parse_args()
    
    # Initialize the database if requested
    if args.init_db:
        logger.info("Initializing database...")
        create_tables()
        logger.info("Database initialized successfully")
        return
    
    # Main application logic would go here
    logger.info("Starting Rataura2...")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Livekit URL: {settings.livekit_url}")
    logger.info(f"Voice enabled: {settings.voice_enabled}")
    
    # Example of using the database session
    db = next(get_db())
    try:
        # Database operations would go here
        pass
    finally:
        db.close()
    
    logger.info("Rataura2 started successfully")


if __name__ == "__main__":
    main()

