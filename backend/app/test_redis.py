import redis.asyncio as redis
import asyncio

async def test():
    r = redis.Redis.from_url(
        "redis://default:utkarsh30938@redis-18742.crce263.ap-south-1-1.ec2.cloud.redislabs.com:18742/0",
        decode_responses=True,
    )
    print(await r.ping())  # should print True

asyncio.run(test())

# asyncio.run(test("redis://default:3ujk3luzxFjiOAPatBumOcXcG9xRpH@redis-18742.crce263.ap-south-1-1.ec2.cloud.redislabs.com:18742/0"))