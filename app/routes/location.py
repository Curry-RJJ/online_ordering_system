from flask import Blueprint, request, redirect, url_for, session, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Address

location_bp = Blueprint('location', __name__)


@location_bp.route('/setup-location', methods=['GET', 'POST'])
@login_required
def setup_location():
    if request.method == 'POST':
        # 解析坐标
        try:
            lat = float(request.form['latitude'])
            lng = float(request.form['longitude'])
        except (KeyError, ValueError, TypeError):
            flash('请在地图上选择有效位置', 'error')
            return redirect(url_for('location.setup_location'))

        address_text = request.form.get('address', '').strip()

        # 写入 session，供后续距离计算使用
        session['user_lat']     = lat
        session['user_lng']     = lng
        session['user_address'] = address_text

        # 若用户还没有默认地址，则以此次位置创建一条
        has_default = Address.query.filter_by(
            user_id=current_user.id, is_default=True
        ).first()
        if not has_default:
            addr = Address(
                user_id   = current_user.id,
                name      = current_user.username,
                phone     = current_user.phone or '',
                address   = address_text or None,
                latitude  = lat,
                longitude = lng,
                is_default=True,
            )
            db.session.add(addr)

        # 标记该用户已完成首次位置设置
        current_user.location_confirmed = True
        db.session.commit()

        return redirect(url_for('restaurant.list_restaurants'))

    return redirect(url_for('restaurant.list_restaurants'))


@location_bp.route('/location/detect-by-ip', methods=['POST'])
@login_required
def detect_by_ip():
    """后端 IP 定位：用客户端 IP 调高德 Web 服务接口，无需浏览器授权弹窗"""
    from app.utils import amap_ip_locate
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or '')
    if ',' in ip:
        ip = ip.split(',')[0].strip()

    result = amap_ip_locate(ip) if ip else None
    if result:
        lat, lng, city = result
        session['user_lat']     = lat
        session['user_lng']     = lng
        session['user_address'] = city or '当前城市'

    current_user.location_confirmed = True
    db.session.commit()

    if result:
        lat, lng, city = result
        return jsonify({'success': True, 'address': city or '当前城市'})
    return jsonify({'success': False, 'message': '定位失败，已跳过位置设置'})


@location_bp.route('/location/skip', methods=['POST'])
@login_required
def skip_location():
    """跳过位置设置：标记 location_confirmed 并清除 session 中的位置数据"""
    session.pop('user_lat',     None)
    session.pop('user_lng',     None)
    session.pop('user_address', None)
    current_user.location_confirmed = True
    db.session.commit()
    return jsonify({'success': True})
