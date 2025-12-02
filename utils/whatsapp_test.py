#!/usr/bin/env python3
"""
WhatsApp Bot Testing Utility
Consolidates all testing functions
"""

import sys
import os
import asyncio
import httpx
from dotenv import load_dotenv

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "api"))
from whatsapp_client import WhatsAppClient

load_dotenv()

async def test_credentials():
    """Test WhatsApp API credentials"""
    
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    
    print("=" * 60)
    print("  🔍 WhatsApp Configuration Test")
    print("=" * 60)
    print()
    print(f"Phone Number ID: {phone_number_id}")
    print(f"Access Token: {access_token[:30]}...")
    print()
    
    # Try to get phone number info
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    print("📡 Testing API connection...")
    print(f"   GET {url}")
    print()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Phone Number ID is valid!")
                print(f"   Verified Name: {data.get('verified_name', 'N/A')}")
                print(f"   Display Phone: {data.get('display_phone_number', 'N/A')}")
                print(f"   Quality Rating: {data.get('quality_rating', 'N/A')}")
            else:
                print("❌ Phone Number ID might be incorrect!")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

async def send_test_message(phone_number):
    """Send test message to a number"""
    
    print("=" * 60)
    print(f"  📤 Sending Test Message to {phone_number}")
    print("=" * 60)
    print()
    
    try:
        client = WhatsAppClient()
        
        # Try template message first (works outside 24h window)
        print("Sending 'hello_world' template message...")
        response = await client.send_template_message(
            phone_number,
            "hello_world",
            "en_US"
        )
        print("✅ Template message sent successfully!")
        print(f"   Response: {response}")
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        print()
        print("Possible reasons:")
        print("1. The phone number is not added to the 'Test Numbers' list in Meta")
        print("2. The 'hello_world' template is not available or approved")

async def test_client_init():
    """Test WhatsApp client initialization"""
    
    print("=" * 60)
    print("  🧪 Testing WhatsApp Client Initialization")
    print("=" * 60)
    print()
    
    try:
        client = WhatsAppClient()
        print("✅ WhatsApp client initialized successfully!")
        print()
        print(f"📱 Phone Number ID: {client.phone_number_id}")
        print(f"🔑 Access Token: {client.access_token[:30]}...")
        print(f"🌐 Base URL: {client.base_url}")
        
    except Exception as e:
        print(f"❌ Failed to initialize client: {e}")

def print_usage():
    """Print usage instructions"""
    print("=" * 60)
    print("  WhatsApp Bot Testing Utility")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python utils/whatsapp_test.py <command> [args]")
    print()
    print("Commands:")
    print("  credentials          - Test WhatsApp API credentials")
    print("  send <phone_number>  - Send test message to a number")
    print("  init                 - Test client initialization")
    print()
    print("Examples:")
    print("  python utils/whatsapp_test.py credentials")
    print("  python utils/whatsapp_test.py send 972522731568")
    print("  python utils/whatsapp_test.py init")
    print()

async def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "credentials":
        await test_credentials()
    elif command == "send":
        if len(sys.argv) < 3:
            print("❌ Error: Phone number required")
            print("Usage: python utils/whatsapp_test.py send <phone_number>")
            return
        phone_number = sys.argv[2]
        await send_test_message(phone_number)
    elif command == "init":
        await test_client_init()
    else:
        print(f"❌ Unknown command: {command}")
        print()
        print_usage()

if __name__ == "__main__":
    asyncio.run(main())
