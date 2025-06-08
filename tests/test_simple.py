"""
Simple test to verify that the package structure is correct.
"""
import unittest
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from rataura2.db.models.base import Base
from rataura2.db.models.agent import Agent, Tool, Transition


class TestSimple(unittest.TestCase):
    """Simple test case."""
    
    def test_import(self):
        """Test that we can import the rataura2 package."""
        self.assertIsNotNone(Base)
        self.assertIsNotNone(Agent)
        self.assertIsNotNone(Tool)
        self.assertIsNotNone(Transition)


if __name__ == "__main__":
    unittest.main()

