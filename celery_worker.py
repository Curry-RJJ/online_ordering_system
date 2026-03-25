"""
Celery Worker 启动入口
在 Flask app_context 内运行任务，确保可访问 db、cache 等扩展。

Docker 启动命令（见 docker-compose.yml）：
  celery -A celery_worker.celery worker --loglevel=info
  celery -A celery_worker.celery beat   --loglevel=info
"""
# BUG-02 修复：不再新建第二个 Celery 实例，而是复用 app.tasks 中的单例
# 并将 Flask app_context 注入到该实例的 Task 基类，确保任务注册在同一实例上。
from app import create_app
from app.tasks import celery_app

flask_app = create_app()


class ContextTask(celery_app.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


celery_app.Task = ContextTask

# 保持变量名 `celery`，与 docker-compose 启动命令 `-A celery_worker.celery` 对应
celery = celery_app
