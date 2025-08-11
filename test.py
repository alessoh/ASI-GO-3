"""
test_asi_go.py - Test script to verify ASI-GO is working
"""
import os
from dotenv import load_dotenv

# Test the components individually
def test_components():
    print("Testing ASI-GO components...")
    
    # Test imports
    try:
        from llm_interface import LLMInterface
        print("✓ LLM Interface imported")
    except Exception as e:
        print(f"✗ LLM Interface import failed: {e}")
        return
    
    try:
        from cognition_base import CognitionBase
        print("✓ Cognition Base imported")
    except Exception as e:
        print(f"✗ Cognition Base import failed: {e}")
        return
        
    try:
        from researcher import Researcher
        print("✓ Researcher imported")
    except Exception as e:
        print(f"✗ Researcher import failed: {e}")
        return
        
    try:
        from engineer import Engineer
        print("✓ Engineer imported")
    except Exception as e:
        print(f"✗ Engineer import failed: {e}")
        return
        
    try:
        from analyst import Analyst
        print("✓ Analyst imported")
    except Exception as e:
        print(f"✗ Analyst import failed: {e}")
        return
    
    # Test initialization
    load_dotenv()
    
    try:
        llm = LLMInterface()
        print("✓ LLM Interface initialized")
    except Exception as e:
        print(f"✗ LLM Interface initialization failed: {e}")
        print("  Check your .env file and API keys")
        return
    
    print("\nAll components working!")

if __name__ == "__main__":
    test_components()