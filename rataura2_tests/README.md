# Rataura2 Test Suite

This directory contains the test suite for the Rataura2 project, a Livekit 1.x project for AI conversational agents specialized in the EVE Online universe.

## Overview

The test suite is designed to validate the functionality of various components of the Rataura2 system, ensuring that they work as expected both individually and together. The tests use Python's built-in `unittest` framework and are organized by component.

## Test Structure

Tests are organized by component, with each test file focusing on a specific module or functionality:

- `test_business_rules.py`: Tests for the Business Rules transitions module, which handles agent transitions based on configurable rules.
- `__init__.py`: Makes the tests directory a proper Python package, which is required for unittest discovery to work correctly.

## Running Tests

### Prerequisites

Before running the tests, ensure you have installed all the required dependencies:

```bash
pip install -r requirements.txt
```

### Running All Tests

To run all tests, navigate to the project root directory and run:

```bash
python -m unittest discover tests
```

### Running Specific Tests

To run a specific test file:

```bash
python -m unittest tests/test_business_rules.py
```

To run a specific test case or method:

```bash
python -m unittest tests.test_business_rules.TestBusinessRulesTransitions
python -m unittest tests.test_business_rules.TestBusinessRulesTransitions.test_check_transitions
```

## Test Components

### Business Rules Tests (`test_business_rules.py`)

These tests validate the Business Rules transitions module, which allows for defining complex transition rules between agents using a business rules engine.

Key functionalities tested:

1. **Creating Business Rules Transitions**: Tests the creation of business rules transitions and verifies that they are correctly stored in the database.

2. **Retrieving Business Rules Transitions**: Tests the retrieval of business rules transitions from the database.

3. **Deleting Business Rules Transitions**: Tests the deletion of business rules transitions from the database.

4. **Transition Checking**: Tests the logic for checking if a transition should be triggered based on the conversation context.

5. **Web UI Functions**: Tests the functions that generate UI configuration and handle JSON serialization/deserialization of rules.

6. **API Functions**: Tests the API functions for managing business rules transitions, including creating, updating, retrieving, and deleting transitions.

## Writing New Tests

When adding new functionality to the project, please also add corresponding tests. Follow these guidelines:

1. Create a new test file if you're adding a new component, or add to an existing file if extending an existing component.

2. Use descriptive test method names that clearly indicate what is being tested.

3. Include docstrings for test classes and methods to explain what they're testing.

4. Use `setUp` and `tearDown` methods to handle common initialization and cleanup.

5. Use in-memory SQLite databases for testing database operations to avoid affecting any production data.

6. Mock external dependencies when appropriate to isolate the component being tested.

Example test structure:

```python
class TestNewComponent(unittest.TestCase):
    """Tests for the new component."""
    
    def setUp(self):
        """Set up the test case."""
        # Initialize test resources
        
    def tearDown(self):
        """Clean up after the test."""
        # Clean up test resources
        
    def test_specific_functionality(self):
        """Test a specific functionality of the component."""
        # Test code here
        self.assertEqual(expected_result, actual_result)
```

## Test Coverage

Currently, the test suite covers:

- Business Rules transitions module (CRUD operations, rule evaluation, API functions)

Future test coverage should include:

- Database models and relationships
- Graph management for agent transitions
- Livekit agent integration
- API endpoints
- Conversation controller logic

## Continuous Integration

Tests are automatically run as part of the CI/CD pipeline when changes are pushed to the repository. Ensure that all tests pass before submitting a pull request.

## Troubleshooting

If you encounter issues with the tests:

1. Ensure all dependencies are installed correctly
2. Check that the database models are up to date
3. Verify that the test database is being created correctly
4. Look for any changes in the API or component interfaces that might affect the tests

### Common Errors

#### ImportError: Start directory is not importable

If you see this error:
```
ImportError: Start directory is not importable: 'tests'
```

This means that the `tests` directory is not recognized as a Python package. Make sure:
- The `tests` directory contains an `__init__.py` file
- You're running the command from the project root directory
- The directory structure is correct

For more complex issues, please open an issue in the repository with details about the problem and any error messages.
