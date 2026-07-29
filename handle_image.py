import uuid
import os
from fastapi import HTTPException

UPLOAD_DIR="uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def handle_image(image): 
    if image:
        


        ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}

        ext = os.path.splitext(image.filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
            status_code=400,
            detail="Unsupported file type."
        )
        
        image_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(UPLOAD_DIR, image_name)

        MAX_SIZE = 5 * 1024 * 1024  

        contents = await image.read()

        if len(contents) > MAX_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Image is too large."
            )

        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        return image_name
    if image is None:
        return None