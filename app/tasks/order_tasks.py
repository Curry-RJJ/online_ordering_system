"""
订单相关异步任务
任务说明：
  - notify_new_order            : 新订单通知（下单成功后触发，通知商家）
  - notify_order_status_change  : 订单状态变更通知（通知用户）
  - cleanup_expired_orders      : 定时清理超时未支付订单（每小时由 Beat 触发）
"""
import logging
from datetime import datetime, timedelta
from app.tasks import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,   # 失败后 60 秒重试
    name='app.tasks.order_tasks.notify_new_order',
)
def notify_new_order(self, order_id: int, order_no: str,
                     restaurant_name: str, total_amount: float):
    """
    新订单商家通知任务。
    生产环境可对接短信 SDK / WebSocket 推送 / 钉钉机器人等。
    此处以结构化日志模拟通知效果，体现任务解耦设计。
    """
    try:
        logger.info(
            '[Celery] 新订单通知 | order_id=%s order_no=%s '
            'restaurant=%s total=%.2f',
            order_id, order_no, restaurant_name, total_amount
        )
        # ── 模拟耗时操作（如发 HTTP 请求到短信网关）──────────────
        # import time; time.sleep(0.5)

        # 实际项目中可替换为：
        # sms_client.send(merchant_phone, f"您有新订单 {order_no}，金额 {total_amount} 元")
        # push_client.notify(restaurant_id, {"type": "new_order", "order_id": order_id})

        logger.info('[Celery] 新订单通知发送成功 | order_no=%s', order_no)
        return {'status': 'ok', 'order_id': order_id}

    except Exception as exc:
        logger.error('[Celery] 新订单通知失败 | order_no=%s error=%s',
                     order_no, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name='app.tasks.order_tasks.notify_order_status_change',
)
def notify_order_status_change(self, order_id: int, order_no: str,
                               new_status: str, user_phone: str):
    """
    订单状态变更用户通知任务。
    当管理员或商家更新订单状态时异步触发，通知用户当前进展。
    """
    status_desc = {
        'confirmed':  '已确认，商家正在备餐',
        'preparing':  '备餐中，请耐心等待',
        'delivering': '已出餐，配送员正在配送',
        'completed':  '已完成，感谢您的惠顾！',
        'cancelled':  '已取消',
    }
    desc = status_desc.get(new_status, new_status)

    try:
        logger.info(
            '[Celery] 状态变更通知 | order_no=%s new_status=%s user_phone=%s',
            order_no, new_status, user_phone
        )

        # 实际项目中可替换为：
        # sms_client.send(user_phone, f"您的订单 {order_no} {desc}")

        logger.info('[Celery] 状态变更通知发送成功 | order_no=%s → %s',
                    order_no, desc)
        return {'status': 'ok', 'order_id': order_id, 'new_status': new_status}

    except Exception as exc:
        logger.error('[Celery] 状态变更通知失败 | order_no=%s error=%s',
                     order_no, str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name='app.tasks.order_tasks.cleanup_expired_orders')
def cleanup_expired_orders():
    """
    定时任务：自动取消超过 30 分钟仍处于 pending 状态的订单。
    由 Celery Beat 每小时触发一次。

    设计意义：
    - 防止订单长期占用库存（若有库存扣减逻辑）
    - 释放未支付订单，保持数据整洁
    - 体现「定时任务 + 业务规则自动化」的工程实践
    """
    from app import db
    from app.models import Order

    cutoff_time = datetime.utcnow() - timedelta(minutes=30)

    try:
        expired_orders = Order.query.filter(
            Order.status == 'pending',
            Order.created_at < cutoff_time,
        ).all()

        if not expired_orders:
            logger.info('[Celery Beat] 无过期订单需要处理')
            return {'cancelled': 0}

        order_nos = [o.order_no for o in expired_orders]
        for order in expired_orders:
            order.status = 'cancelled'

        db.session.commit()

        logger.info('[Celery Beat] 已自动取消 %d 个过期订单: %s',
                    len(expired_orders), order_nos)
        return {'cancelled': len(expired_orders), 'order_nos': order_nos}

    except Exception as exc:
        db.session.rollback()
        logger.error('[Celery Beat] 清理过期订单失败: %s', str(exc))
        raise
