"""Basic tests to ensure core functionality works."""

import pytest
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that core modules can be imported."""
    try:
        import strava_assistant
        import photo_processor
        import caption_generator
    except ImportError as e:
        pytest.fail(f"Failed to import core modules: {e}")

def test_requirements_exist():
    """Test that requirements.txt exists and has content."""
    req_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'requirements.txt')
    assert os.path.exists(req_path), "requirements.txt should exist"
    
    with open(req_path) as f:
        content = f.read().strip()
    assert content, "requirements.txt should not be empty"