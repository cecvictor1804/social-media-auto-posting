"""Media upload route."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.deps import CurrentUser, DBSession
from app.config import settings
from app.models import MediaAsset
from app.schemas import MediaOut
from app.storage import get_storage, new_key

router = APIRouter(prefix="/api", tags=["media"])


@router.post("/media", response_model=MediaOut)
async def upload_media(user: CurrentUser, session: DBSession, file: UploadFile = File(...)):
    content_type = file.content_type or ""
    allowed = settings.allowed_image_type_set | settings.allowed_video_type_set
    if content_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported media type: {content_type or 'unknown'}")

    data = await file.read()
    is_image = content_type in settings.allowed_image_type_set
    max_mb = settings.media_max_image_mb if is_image else settings.media_max_video_mb
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {max_mb} MB).")

    key = new_key(content_type)
    public_url = get_storage().save(data, key, content_type)
    asset = MediaAsset(
        filename=file.filename or key,
        content_type=content_type,
        storage_path=key,
        public_url=public_url,
    )
    session.add(asset)
    session.commit()
    return MediaOut.from_orm_asset(asset)
