"""
Test OpenAI API connection
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv()

print("Testing OpenAI API connection...")

try:
    # Initialize client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No API key found in .env file")
        exit(1)
    
    print(f"✓ API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    client = OpenAI(api_key=api_key)
    
    # Test with a simple request
    print("Sending test request...")
    start_time = time.time()
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Connection successful!'"}],
        max_tokens=10,
        timeout=30  # 30 second timeout
    )
    
    elapsed = time.time() - start_time
    print(f"✓ Response received in {elapsed:.2f} seconds: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    
    # Additional diagnostics
    print("\nDiagnostics:")
    print("1. Check your internet connection")
    print("2. Verify your API key is valid at: https://platform.openai.com/api-keys")
    print("3. Check if you have credits/billing set up")
    print("4. Try using a VPN if you're behind a corporate firewall"