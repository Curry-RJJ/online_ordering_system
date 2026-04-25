"""
腾讯云 COS 浏览器直传：预签名 PUT URL 与路径校验。
需环境变量：COS_SECRET_ID、COS_SECRET_KEY、COS_REGION、COS_BUCKET、STATIC_CDN_BASE；
可选 COS_BROWSER_UPLOAD=1 启用直传。
"""

from __future__ import annotations

import os
import re
import uuid
from typing import Optional, Tuple

ALLOWED_UPLOAD_TYPES = frozenset({"dishes", "logos", "banners", "restaurants"})


def cos_browser_upload_enabled() -> bool:
    """是否启用浏览器直传（预签名 PUT）。"""
    flag = os.environ.get("COS_BROWSER_UPLOAD", "").strip().lower()
    if flag not in ("1", "true", "yes"):
        return False
    if not os.environ.get("STATIC_CDN_BASE", "").strip():
        return False
    if not all(
        [
            os.environ.get("COS_SECRET_ID", "").strip(),
            os.environ.get("COS_SECRET_KEY", "").strip(),
            os.environ.get("COS_REGION", "").strip(),
            os.environ.get("COS_BUCKET", "").strip(),
        ]
    ):
        return False
    return True


def _normalize_bucket(raw: str) -> str:
    s = raw.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        s = s[1:-1].strip()
    return s


def validate_cos_web_path(path: str, upload_type: str) -> bool:
    """
    校验前端提交的站内路径，防路径穿越与类型伪造。
    期望格式：/static/images/{upload_type}/{uuid}.{ext}
    """
    if upload_type not in ALLOWED_UPLOAD_TYPES:
        return False
    if not path or ".." in path:
        return False
    prefix = f"/static/images/{upload_type}/"
    if not path.startswith(prefix):
        return False
    rest = path[len(prefix) :]
    if "/" in rest or not rest:
        return False
    return bool(
        re.match(r"^[0-9a-fA-F-]{36}\.(png|jpg|jpeg|gif|webp)$", rest)
    )


def ext_from_filename(filename: str) -> Optional[str]:
    if not filename or "." not in filename:
        return None
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        return None
    return ext


def content_type_for_ext(ext: str) -> str:
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext.lower(), "application/octet-stream")


def build_cos_client():
    from qcloud_cos import CosConfig, CosS3Client

    secret_id = os.environ.get("COS_SECRET_ID", "").strip().strip("\"'")
    secret_key = os.environ.get("COS_SECRET_KEY", "").strip().strip("\"'")
    region = os.environ.get("COS_REGION", "").strip().strip("\"'")
    bucket = _normalize_bucket(os.environ.get("COS_BUCKET", ""))
    if not all([secret_id, secret_key, region, bucket]):
        raise RuntimeError("COS 凭证未配置完整")
    config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Scheme="https")
    return CosS3Client(config), bucket


def create_presigned_put(upload_type: str, ext: str, content_type: str) -> Tuple[str, str, str]:
    """
    生成 PUT 预签名 URL 与对象键、站内路径。
    返回 (presigned_url, cos_key, web_path)
    """
    if upload_type not in ALLOWED_UPLOAD_TYPES:
        raise ValueError("upload_type 非法")
    if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
        raise ValueError("扩展名不允许")
    client, bucket = build_cos_client()
    filename = f"{uuid.uuid4()}.{ext}"
    cos_key = f"static/images/{upload_type}/{filename}"
    web_path = f"/static/images/{upload_type}/{filename}"
    ct = (content_type or "").strip()
    if not ct or not ct.startswith("image/"):
        ct = content_type_for_ext(ext)
    headers = {"Content-Type": ct}
    url = client.get_presigned_url(
        Bucket=bucket,
        Key=cos_key,
        Method="PUT",
        Expired=600,
        Headers=headers,
    )
    return url, cos_key, web_path
