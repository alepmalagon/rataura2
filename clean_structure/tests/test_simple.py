"""
Simple tests for the rataura2 package.
"""
import sys
import os
from pathlib import Path
import unittest

# Add the parent directory to the path so we can import the rataura2 package
sys.path.append(str(Path(__file__).parent.parent))

from rataura2.db.models import Base, Agent, Transition, AgentType, LLMProvider
from rataura2.transitions import BusinessRulesTransition, TransitionController


class TestSimple(unittest.TestCase):
    """Simple tests for the rataura2 package."""

    def test_imports(self):
        """Test that we can import the rataura2 package."""
        self.assertIsNotNone(Base)
        self.assertIsNotNone(Agent)
        self.assertIsNotNone(Transition)
        self.assertIsNotNone(AgentType)
        self.assertIsNotNone(LLMProvider)
        self.assertIsNotNone(BusinessRulesTransition)
        self.assertIsNotNone(TransitionController)


if __name__ == "__main__":
    unittest.main()

