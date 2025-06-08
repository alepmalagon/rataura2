"""
A simple test file to verify that unittest discovery is working.
"""
import unittest

class TestSimple(unittest.TestCase):
    """A simple test case."""
    
    def test_true(self):
        """Test that True is True."""
        self.assertTrue(True)
    
    def test_equal(self):
        """Test that 1 equals 1."""
        self.assertEqual(1, 1)

if __name__ == "__main__":
    unittest.main()

