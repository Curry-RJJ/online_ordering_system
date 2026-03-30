#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 侧不再通过本文件插入业务用户数据（历史遗留占位）。

管理员与演示用户由 **web 容器 entrypoint** 在首次空库时创建，密码与账号来自环境变量
`INITIAL_ADMIN_*` / `SEED_DEMO_USERS`，见 `app/bootstrap_admin.py` 与 `entrypoint.sh`。

若需本地用 MySQL 全量灌库，请配置 `DATABASE_URL` 后运行：
`python database/init_data.py`（会 drop 并重建表）。
"""
