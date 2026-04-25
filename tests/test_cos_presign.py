"""cos_presign 路径校验与辅助函数单测（不调用腾讯云 API）。"""

import pytest

from app.cos_presign import (
    content_type_for_ext,
    cos_browser_upload_enabled,
    ext_from_filename,
    validate_cos_web_path,
)


def test_validate_cos_web_path_valid():
    uid = "550e8400-e29b-41d4-a716-446655440000"
    assert validate_cos_web_path(f"/static/images/dishes/{uid}.png", "dishes") is True
    assert validate_cos_web_path(f"/static/images/logos/{uid}.jpg", "logos") is True
    assert validate_cos_web_path(f"/static/images/banners/{uid}.webp", "banners") is True


def test_validate_cos_web_path_invalid():
    assert validate_cos_web_path("", "dishes") is False
    assert validate_cos_web_path("/static/images/dishes/../x.png", "dishes") is False
    assert validate_cos_web_path("/static/images/logos/not-uuid.png", "logos") is False
    assert validate_cos_web_path("/static/images/dishes/550e8400-e29b-41d4-a716-446655440000.png/extra", "dishes") is False
    assert validate_cos_web_path("/static/images/wrong/550e8400-e29b-41d4-a716-446655440000.png", "dishes") is False
    assert validate_cos_web_path("/static/images/dishes/550e8400-e29b-41d4-a716-446655440000.png", "invalid_type") is False


def test_ext_from_filename():
    assert ext_from_filename("a.PNG") == "png"
    assert ext_from_filename("x.jpeg") == "jpeg"
    assert ext_from_filename("noext") is None


def test_content_type_for_ext():
    assert content_type_for_ext("jpg") == "image/jpeg"
    assert content_type_for_ext("webp") == "image/webp"


def test_cos_browser_upload_enabled_env(monkeypatch):
    monkeypatch.delenv("COS_BROWSER_UPLOAD", raising=False)
    monkeypatch.delenv("STATIC_CDN_BASE", raising=False)
    assert cos_browser_upload_enabled() is False

    monkeypatch.setenv("COS_BROWSER_UPLOAD", "1")
    monkeypatch.setenv("STATIC_CDN_BASE", "https://cdn.example.com")
    monkeypatch.setenv("COS_SECRET_ID", "id")
    monkeypatch.setenv("COS_SECRET_KEY", "key")
    monkeypatch.setenv("COS_REGION", "ap-hongkong")
    monkeypatch.setenv("COS_BUCKET", "b-1250000000")
    assert cos_browser_upload_enabled() is True

    monkeypatch.setenv("COS_BROWSER_UPLOAD", "0")
    assert cos_browser_upload_enabled() is False
