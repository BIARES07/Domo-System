import httpx
import asyncio
import sqlite3

async def reset_traps():
    # Direct database reset to ensure everything is OFF
    conn = sqlite3.connect('domo_metrics.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE chaos_config SET is_active = 0")
    conn.commit()
    conn.close()
    print("All traps have been DEACTIVATED in the database.")

if __name__ == "__main__":
    asyncio.run(reset_traps())
