import json
from typing import Optional, Any
import redis.asyncio as redis
from app.core.config import settings
from app.models.post import Post
from app.models.tag import Tag

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

POST_CACHE_TTL = 300
TAG_CACHE_TTL = 600
TRENDING_CACHE_TTL = 180

async def get_cached(key: str) -> Optional[Any]:
    """Get cached value"""
    try:
        data = await redis_client.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        print(f"Cache get error: {e}")
        return None

async def set_cached(key: str, value: Any, ttl: int) -> None:
    """Set cached value"""
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        print(f"Cache set error: {e}")

async def invalidate_cached(key: str) -> None:
    """Invalidate single cache key"""
    try: 
        await redis_client.delete(key)
    except Exception as e:
        print(f"Cache delete error: {e}")

async def invalidate_pattern(pattern: str) -> None:
    """Invalidate all keys matching pattern"""
    try: 
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache pattern delete error: {e}")



async def get_cached_post(post_id: int) -> Optional[Any]:
    return await get_cached(f"post:{post_id}")

async def set_cached_post(post_id: int, post_data: Any) -> None:
    await set_cached(f'post:{post_id}', post_data, POST_CACHE_TTL)

async def invalidate_cached_post(post_id: int) -> None:
    await invalidate_cached(f'post:{post_id}')
    await invalidate_pattern(f'post:list*')
    await invalidate_pattern(f'post:feed:*')

async def get_cached_posts_list(key: str) -> Optional[Any]:
    return await get_cached(f'posts:list:{key}')

async def set_cached_posts_list(key: str, posts_data: Any) -> None:
    return await set_cached(f'posts:list:{key}', posts_data, POST_CACHE_TTL)

async def get_cached_posts_feed(key: str) -> Optional[Any]:
    return await get_cached(f'posts:feed:{key}')

async def set_cached_posts_feed(key: str, posts_data: Any) -> None:
    return await set_cached(f'posts:feed:{key}', posts_data, POST_CACHE_TTL)



async def get_cached_tag(slug: str) -> Optional[Any]:
    return await get_cached(f"tag:{slug}")

async def set_cached_tag(slug: str, tag_data: Any) -> None:
    await set_cached(f'tag:{slug}', tag_data, TAG_CACHE_TTL)

async def invalidate_cached_tag(slug: int) -> None:
    await invalidate_cached(f'tag:{slug}')
    await invalidate_pattern(f'tag:list*')
    await invalidate_cached(f'tag:trending')

async def get_cached_tags_list(key: str) -> Optional[Any]:
    return await get_cached(f'tags:list:{key}')

async def set_cached_tags_list(key: str, tags_data: Any) -> None:
    return await set_cached(f'tags:list:{key}', tags_data, TAG_CACHE_TTL)

async def get_cached_tags_trending() -> Optional[Any]:
    return await get_cached(f'tags:trending')

async def set_cached_tags_trending(tags_data: Any) -> None:
    return await set_cached(f'tags:trending', tags_data, TRENDING_CACHE_TTL)