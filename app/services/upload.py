import os
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import aiofiles
from app.core.config import settings
from app.utils.slug import generate_filename
class UploadService:

    @staticmethod
    async def validate_file(file: UploadFile) -> bytes:
        """Validate file type and size"""

        content = await file.read()

        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'File too large. Max size: {settings.MAX_FILE_SIZE / 1024 / 1024:.1f}MB'
            )

        ext = file.filename.split('.')[-1].lower()
        allowed = settings.allowed_extensions_list
        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'file type not allowed. Allowed: {', '.join(allowed)}'
            )
        
        return content
        
    @staticmethod
    async def save_local(file: UploadFile, folder: str = 'avatars') -> str:
        """Save file locally"""

        content = await UploadService.validate_file(file)

        upload_path = os.path.join(settings.UPLOAD_DIR, folder)
        os.makedirs(upload_path, exist_ok=True)

        filename = generate_filename(file.filename)
        file_path = os.path.join(upload_path, filename)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content) 

        UploadService.optimize_image(file_path)

        return f'/{folder}/{filename}'
    
    @staticmethod
    def optimize_image(file_path: str, max_size: tuple = (800, 800)) -> None:
        """Optimize image size and quality"""

        try:
            with Image.open(file_path) as img:

                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)

        except Exception as e:
            print(f"Image optimization failed: {e}")

    @staticmethod
    def delete_local(file_url: str) -> None:
        """Delete local file"""
        file_path = os.path.join(settings.UPLOAD_DIR, file_url.lstrip('/'))
        if os.path.exists(file_path):
            os.remove(file_path)


try:
    import cloudinary
    import cloudinary.uploader

    if settings.CLOUDINARY_CLOUD_NAME:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )

    class CloudinaryService:

        @staticmethod
        async def upload(file: UploadFile, folder: str = "avatars") -> str:
            """Upload to Cloudinary"""

            content = await UploadService.validate_file(file)
            
            result = cloudinary.uploader.upload(
                content,
                folder=f'blog-api/{folder}',
                transformation=[
                    {'width': 800, 'height': 800, 'crop': 'limit'},
                    {'quality': 'auto'},
                    {'fetch_format': 'auto'}
                ]
            )

            return result['secure_url']
        
        @staticmethod
        def delete(url: str) -> None:
            """Delete from Cloudinary"""
            parts = url.split('/')
            upload_index = parts.index('upload')
            public_id = '/'.join(parts[upload_index + 2:])
            public_id = os.path.splitext(public_id)[0]
            cloudinary.uploader.destroy(public_id)

except ImportError:
    cloudinaryService = None