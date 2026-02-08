"""
Script to promote a user to admin role
Usage: python make_admin.py <user_email>
"""
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def make_admin(email):
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Find user by email
    user = await db.users.find_one({"email": email})
    
    if not user:
        print(f"❌ User with email '{email}' not found")
        return False
    
    # Update user role to admin
    result = await db.users.update_one(
        {"email": email},
        {"$set": {"role": "admin"}}
    )
    
    if result.modified_count > 0:
        print(f"✅ User '{email}' has been promoted to admin!")
        print(f"   Name: {user.get('name')}")
        print(f"   User ID: {user.get('id')}")
        return True
    else:
        print(f"⚠️  User '{email}' is already an admin")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <user_email>")
        print("Example: python make_admin.py admin@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    asyncio.run(make_admin(email))
