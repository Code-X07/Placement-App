import json
from app import redis_client

def cache_get(key):
    if redis_client is None:
        return None
    val = redis_client.get(key)
    return json.loads(val) if val else None

def cache_set(key, value, ttl=300):
    if redis_client is None:
        return
    redis_client.setex(key, ttl, json.dumps(value, default=str))

def cache_delete(*keys):
    if redis_client and keys:
        redis_client.delete(*keys)
