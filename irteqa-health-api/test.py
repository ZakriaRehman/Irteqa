# test_connection.py
import asyncio
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            user='postgres',
            password='Meezan@2134',  # Use raw password in Python
            database='irteqa_health',
            host='localhost',
            port=5432
        )
        print("✅ Connected successfully!")
        await conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

asyncio.run(test())