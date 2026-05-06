from slugify import slugify
import uuid

def generate_unique_slug(text: str) -> str:
    """Generate unique slug from text"""
    base_slug = slugify(text)
    unique_id = str(uuid.uuid4())[:8]
    return f"{base_slug}-{unique_id}"

def generate_filename(original_filename: str) -> str:
    """Generate unique filename"""
    ext = original_filename.split('.')[-1]
    unique_name = str(uuid.uuid4())
    return f"{unique_name}.{ext}"