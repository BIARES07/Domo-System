import httpx
import asyncio

async def activate():
    async with httpx.AsyncClient() as client:
        # Activate Schema Drift
        await client.post('http://127.0.0.1:8000/api/v1/admin/traps/schema_drift', 
                         json={'is_active': True, 'severity': 1.0})
        # Activate Inconsistent Paging
        await client.post('http://127.0.0.1:8000/api/v1/admin/traps/inconsistent_paging', 
                         json={'is_active': True, 'severity': 1.0})
        # Activate Launch Window Fragmentation
        await client.post('http://127.0.0.1:8000/api/v1/admin/traps/launch_window_fragmentation',
                         json={'is_active': True, 'severity': 1.0})
        # Activate Conjunction Signal Scramble
        await client.post('http://127.0.0.1:8000/api/v1/admin/traps/conjunction_signal_scramble',
                         json={'is_active': True, 'severity': 1.0})
        print("Advanced Traps (Schema Drift, Paging, Launch Fragmentation & Conjunction Scramble) are now ACTIVE.")

if __name__ == "__main__":
    asyncio.run(activate())
