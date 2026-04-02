#!/usr/bin/env python3
"""
将仓库内 app/static/images 下所有文件上传到腾讯云 COS，对象键为 static/images/<相对路径>，
与站点路径 /static/images/... 及 STATIC_CDN_BASE 拼接规则一致。

用法（在项目根目录，已安装依赖 cos-python-sdk-v5）：
    set COS_SECRET_ID=xxx
    set COS_SECRET_KEY=xxx
    set COS_REGION=ap-hongkong
    set COS_BUCKET=meituan-1416142652
    python scripts/sync_static_images_to_cos.py

仅打印将要上传的键、不实际上传：
    python scripts/sync_static_images_to_cos.py --dry-run

环境变量说明见 docs/腾讯云COS与CDN接入说明.md §4。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES_DIR = ROOT / "app" / "static" / "images"

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def _iter_files(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    out: list[Path] = []
    for p in base.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            out.append(p)
    return sorted(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync app/static/images to Tencent COS.")
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=IMAGES_DIR,
        help=f"Local images root (default: {IMAGES_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print object keys only, do not upload",
    )
    args = parser.parse_args()
    base = args.images_dir.resolve()
    if not base.is_dir():
        print(f"目录不存在: {base}", file=sys.stderr)
        return 1

    files = _iter_files(base)
    if not files:
        print(f"未找到可上传文件: {base}")
        return 0

    prefix = "static/images"

    if args.dry_run:
        for fp in files:
            rel = fp.relative_to(base).as_posix()
            print(f"{prefix}/{rel}")
        print(f"[dry-run] 共 {len(files)} 个文件")
        return 0

    secret_id = os.environ.get("COS_SECRET_ID", "").strip()
    secret_key = os.environ.get("COS_SECRET_KEY", "").strip()
    region = os.environ.get("COS_REGION", "").strip()
    bucket = os.environ.get("COS_BUCKET", "").strip()
    if not all([secret_id, secret_key, region, bucket]):
        print(
            "请设置环境变量 COS_SECRET_ID、COS_SECRET_KEY、COS_REGION、COS_BUCKET",
            file=sys.stderr,
        )
        return 1

    try:
        from qcloud_cos import CosConfig, CosS3Client
    except ImportError:
        print("请先安装: pip install cos-python-sdk-v5", file=sys.stderr)
        return 1

    config = CosConfig(
        Region=region,
        SecretId=secret_id,
        SecretKey=secret_key,
        Scheme="https",
    )
    client = CosS3Client(config)

    ok = 0
    for fp in files:
        rel = fp.relative_to(base).as_posix()
        key = f"{prefix}/{rel}"
        client.upload_file(Bucket=bucket, LocalFilePath=str(fp), Key=key)
        print(f"OK {key}")
        ok += 1

    print(f"完成: {ok}/{len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
