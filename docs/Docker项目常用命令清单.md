# Docker 项目常用命令清单

适用于本项目：`online_ordering_system`

说明：
- 默认在项目根目录 `d:\projects\online_ordering_system` 执行。
- 优先使用 `docker compose`；如果你的环境较老，也可把命令替换为 `docker-compose`。

## 1. 启动与停止

```bash
# 首次/更新后启动（后台 + 重新构建）
docker compose up -d --build

# 常规启动（不重建）
docker compose up -d

# 停止并保留数据卷
docker compose down

# 停止并删除数据卷（危险：会清空 MySQL/Redis 数据）
docker compose down -v

# 重启全部服务
docker compose restart
```

## 2. 只操作单个服务

```bash
# 启动单个服务
docker compose up -d web

# 重启单个服务
docker compose restart web

docker compose restart nginx
docker compose restart mysql
docker compose restart redis
docker compose restart celery_worker
docker compose restart celery_beat

# 停止单个服务
docker compose stop web
```

## 3. 查看状态与日志

```bash
# 查看服务状态
docker compose ps

# 查看全部日志
docker compose logs

# 实时跟踪全部日志
docker compose logs -f

# 查看最近 200 行并持续跟踪
docker compose logs --tail=200 -f web
docker compose logs --tail=200 -f nginx
docker compose logs --tail=200 -f mysql
docker compose logs --tail=200 -f redis
docker compose logs --tail=200 -f celery_worker
docker compose logs --tail=200 -f celery_beat
```

## 4. 进入容器排查

```bash
# 进入 Web 容器（多数镜像可用 sh）
docker compose exec web sh

# 进入 Nginx / MySQL / Redis 容器
docker compose exec nginx sh
docker compose exec mysql sh
docker compose exec redis sh

# Web 容器内执行 Flask 命令
# 例：数据库迁移
docker compose exec web flask db upgrade
```

## 5. 数据库与缓存常用命令

```bash
# 进入 MySQL
docker compose exec mysql mysql -u root -p

# 查看数据库列表
docker compose exec mysql mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "SHOW DATABASES;"

# 查看 Redis 连通性
docker compose exec redis redis-cli ping

# 如果 Redis 设置了密码
docker compose exec redis redis-cli -a "${REDIS_PASSWORD}" ping
```

## 6. 重新构建与发布常用流程

```bash
# 代码更新后（推荐流程）
git pull
docker compose up -d --build

# 仅重建某个服务
docker compose build web
docker compose up -d web

# 拉取基础镜像后重建
docker compose pull
docker compose up -d --build
```

## 7. 资源与健康检查

```bash
# 查看容器资源占用
docker stats

# 查看容器详情
docker inspect online_ordering_web

# 应用健康检查（项目内接口）
curl http://localhost:5000/health
```

## 8. 备份与恢复（MySQL）

```bash
# 备份（导出到宿主机当前目录）
docker compose exec mysql sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > backup.sql

# 恢复（从宿主机 backup.sql 导入）
cat backup.sql | docker compose exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
```

## 9. 清理命令（谨慎）

```bash
# 查看磁盘占用
docker system df

# 清理悬空镜像
docker image prune -f

# 清理未使用资源（危险：可能删除未使用网络/镜像）
docker system prune -f
```

## 10. 本项目常见故障快速处理

```bash
# 1) 页面 502/打不开：优先看 nginx + web 日志
docker compose logs --tail=200 nginx
docker compose logs --tail=200 web

# 2) 数据库连接失败：重启 mysql 并查看日志
docker compose restart mysql
docker compose logs --tail=200 mysql

# 3) 异步任务不执行：检查 worker/beat
docker compose ps
docker compose logs --tail=200 celery_worker
docker compose logs --tail=200 celery_beat

# 4) 静态文件异常：重启 web + nginx
docker compose restart web nginx
```

## 11. 服务名与容器名对照

- 服务名：`web` -> 容器名：`online_ordering_web`
- 服务名：`mysql` -> 容器名：`online_ordering_mysql`
- 服务名：`redis` -> 容器名：`online_ordering_redis`
- 服务名：`nginx` -> 容器名：`online_ordering_nginx`
- 服务名：`celery_worker` -> 容器名：`online_ordering_celery_worker`
- 服务名：`celery_beat` -> 容器名：`online_ordering_celery_beat`
