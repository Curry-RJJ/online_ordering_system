"""
Celery 实例工厂
- Broker / Backend 均使用已有的 Redis 服务（docker-compose 中的 redis 容器）
- 通过 celery_app.conf 统一配置序列化、时区、定时任务
"""
from celery import Celery
from celery.schedules import crontab
import os


def make_celery(app=None):
    """
    创建 Celery 实例。
    既支持在 Flask app_context 内调用（任务可访问 db / config），
    也支持作为独立 Worker 进程启动（通过 celery_worker.py）。
    """
    broker_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    result_backend = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

    celery = Celery(
        'online_ordering',
        broker=broker_url,
        backend=result_backend,
        include=['app.tasks.order_tasks'],
    )

    celery.conf.update(
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        timezone='Asia/Shanghai',
        enable_utc=True,
        # 任务结果保留 1 小时后自动清理
        result_expires=3600,
        # Worker 并发数（容器内默认跟 CPU 核心数一致，这里固定 2 避免过载）
        worker_concurrency=2,
        # 定时任务调度表（由 celery beat 服务执行）
        beat_schedule={
            'cleanup-expired-orders-every-hour': {
                'task': 'app.tasks.order_tasks.cleanup_expired_orders',
                'schedule': crontab(minute=0),  # 每小时整点执行
            },
        },
    )

    if app is not None:
        # 让任务在 Flask app_context 内执行，可访问 db、cache 等扩展
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

    return celery


# 模块级单例（Worker 进程直接 import 使用）
celery_app = make_celery()
