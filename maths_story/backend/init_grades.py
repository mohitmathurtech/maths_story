"""
Script to initialize default grades (Grade 1 to Grade 12)
Usage: python init_grades.py
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def init_grades():
    mongo_url = os.environ['MONGO_URL']
    db_name = os.environ['DB_NAME']
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Check if grades already exist
    existing_count = await db.grades.count_documents({})
    if existing_count > 0:
        print(f"⚠️  Found {existing_count} existing grades. Skipping initialization.")
        print("   Use admin panel to manage grades or delete existing grades first.")
        return
    
    # Create Grade 1 to Grade 12
    grades = []
    for i in range(1, 13):
        grade = {
            "id": str(uuid.uuid4()),
            "name": f"Grade {i}",
            "order": i,
            "created_at": asyncio.get_event_loop().time()
        }
        grades.append(grade)
    
    # Insert grades
    result = await db.grades.insert_many(grades)
    
    print(f"✅ Successfully created {len(result.inserted_ids)} grades!")
    print("\nGrades created:")
    for grade in grades:
        print(f"   - {grade['name']} (Order: {grade['order']})")
    
    print("\n📝 Note: You can manage these grades from the Admin Panel")
    print("   Add, edit, or remove grades as needed for your curriculum")

if __name__ == "__main__":
    asyncio.run(init_grades())
