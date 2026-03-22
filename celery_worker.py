"""
Celery Worker 启动入口
在 Flask app_context 内运行任务，确保可访问 db、cache 等扩展。

Docker 启动命令（见 docker-compose.yml）：
  celery -A celery_worker.celery worker --loglevel=info
  celery -A celery_worker.celery beat   --loglevel=info
"""
from app import create_app
from app.tasks import make_celery

flask_app = create_app()
celery = make_celery(flask_app)
