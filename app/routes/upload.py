"""浏览器上传辅助：COS 预签名等。"""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app import limiter
from app.cos_presign import (
    content_type_for_ext,
    cos_browser_upload_enabled,
    create_presigned_put,
    ext_from_filename,
)

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")


@upload_bp.route("/cos-presign", methods=["POST"])
@login_required
@limiter.limit("60 per minute")
def cos_presign():
    """为浏览器直传 COS 生成 PUT 预签名 URL（需登录 + CSRF）。"""
    if not cos_browser_upload_enabled():
        return (
            jsonify(
                {
                    "code": 503,
                    "message": "未启用 COS 浏览器直传（需 COS_BROWSER_UPLOAD=1 且配置 STATIC_CDN_BASE 与 COS_*）",
                    "data": None,
                }
            ),
            503,
        )
    data = request.get_json(silent=True) or {}
    upload_type = (data.get("upload_type") or "").strip()
    filename = (data.get("filename") or "").strip()
    content_type = (data.get("content_type") or "").strip() or None
    ext = ext_from_filename(filename)
    if not ext:
        return jsonify({"code": 400, "message": "文件名或扩展名无效", "data": None}), 400
    try:
        url, _key, web_path = create_presigned_put(upload_type, ext, content_type or "")
    except ValueError as e:
        return jsonify({"code": 400, "message": str(e), "data": None}), 400
    except Exception as e:
        return jsonify({"code": 500, "message": f"生成预签名失败: {e}", "data": None}), 500
    ct_out = content_type
    if not ct_out or not ct_out.startswith("image/"):
        ct_out = content_type_for_ext(ext)
    return jsonify(
        {
            "code": 200,
            "message": "ok",
            "data": {
                "presigned_url": url,
                "web_path": web_path,
                "content_type": ct_out,
            },
        }
    )
