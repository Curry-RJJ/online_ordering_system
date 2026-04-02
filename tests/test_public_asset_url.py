"""public_asset_url（STATIC_CDN_BASE）"""
import pytest


def test_public_asset_url_empty():
    from app.utils import public_asset_url
    assert public_asset_url(None) == ''
    assert public_asset_url('') == ''


def test_public_asset_url_absolute_unchanged():
    from app.utils import public_asset_url
    assert public_asset_url('https://cdn.example.com/x.png') == 'https://cdn.example.com/x.png'
    assert public_asset_url('http://a/b') == 'http://a/b'


def test_public_asset_url_with_cdn_env(monkeypatch):
    from app.utils import public_asset_url
    monkeypatch.delenv('STATIC_CDN_BASE', raising=False)
    monkeypatch.setenv('STATIC_CDN_BASE', 'https://img.test.com')
    assert public_asset_url('/static/images/a.jpg') == 'https://img.test.com/static/images/a.jpg'


def test_public_asset_url_strips_base_slash(monkeypatch):
    from app.utils import public_asset_url
    monkeypatch.setenv('STATIC_CDN_BASE', 'https://img.test.com/')
    assert public_asset_url('/static/x.png') == 'https://img.test.com/static/x.png'


def test_public_asset_url_app_config(app, monkeypatch):
    from app.utils import public_asset_url
    monkeypatch.delenv('STATIC_CDN_BASE', raising=False)
    app.config['STATIC_CDN_BASE'] = 'https://cdn.app'
    with app.app_context():
        assert public_asset_url('/static/a.jpg') == 'https://cdn.app/static/a.jpg'
