/**
 * 美团外卖 - 现代化交互脚本
 * 提供丰富的用户体验和动画效果
 */

class MeituanUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupAnimations();
        this.setupTooltips();
        this.setupImageLazyLoading();
        this.setupSmoothScrolling();
        this.setupFormEnhancements();
        this.setupCardHoverEffects();
        this.setupSearchEnhancements();
        this.setupNotifications();
    }

    // 设置动画效果
    setupAnimations() {
        // 页面加载动画
        window.addEventListener('load', () => {
            document.body.classList.add('loaded');
            this.animateOnScroll();
        });

        // 滚动动画
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // 观察所有卡片元素
        document.querySelectorAll('.card-modern, .restaurant-card, .dish-card').forEach(card => {
            observer.observe(card);
        });
    }

    // 滚动时的动画效果
    animateOnScroll() {
        let ticking = false;

        const updateAnimations = () => {
            const scrolled = window.pageYOffset;
            const parallax = document.querySelectorAll('.parallax');
            
            parallax.forEach(element => {
                const speed = element.dataset.speed || 0.5;
                const yPos = -(scrolled * speed);
                element.style.transform = `translateY(${yPos}px)`;
            });

            ticking = false;
        };

        window.addEventListener('scroll', () => {
            if (!ticking) {
                requestAnimationFrame(updateAnimations);
                ticking = true;
            }
        });
    }

    // 设置工具提示
    setupTooltips() {
        // 初始化Bootstrap工具提示
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // 图片懒加载
    setupImageLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        img.classList.add('loaded');
                        imageObserver.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    // 平滑滚动
    setupSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // 表单增强
    setupFormEnhancements() {
        // 浮动标签效果
        document.querySelectorAll('.form-floating input, .form-floating textarea').forEach(input => {
            input.addEventListener('focus', () => {
                input.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', () => {
                if (!input.value) {
                    input.parentElement.classList.remove('focused');
                }
            });
        });

        // 实时验证
        document.querySelectorAll('input[type="email"]').forEach(input => {
            input.addEventListener('blur', this.validateEmail);
        });

        document.querySelectorAll('input[type="tel"]').forEach(input => {
            input.addEventListener('blur', this.validatePhone);
        });
    }

    // 邮箱验证
    validateEmail(e) {
        const email = e.target.value;
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const isValid = emailRegex.test(email);
        
        e.target.classList.toggle('is-valid', isValid && email);
        e.target.classList.toggle('is-invalid', !isValid && email);
    }

    // 手机号验证
    validatePhone(e) {
        const phone = e.target.value;
        const phoneRegex = /^1[3-9]\d{9}$/;
        const isValid = phoneRegex.test(phone);
        
        e.target.classList.toggle('is-valid', isValid);
        e.target.classList.toggle('is-invalid', !isValid && phone);
    }

    // 卡片悬停效果
    setupCardHoverEffects() {
        document.querySelectorAll('.restaurant-card, .dish-card').forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.transform = 'translateY(-8px) scale(1.02)';
                this.style.boxShadow = '0 25px 50px rgba(0,0,0,0.15)';
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = '';
                this.style.boxShadow = '';
            });
        });
    }

    // 搜索增强
    setupSearchEnhancements() {
        const searchInputs = document.querySelectorAll('.search-box');
        
        searchInputs.forEach(input => {
            let searchTimeout;
            
            input.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        this.performSearch(query);
                    }, 300);
                }
            });

            // 搜索建议
            input.addEventListener('focus', () => {
                this.showSearchSuggestions(input);
            });

            input.addEventListener('blur', () => {
                setTimeout(() => {
                    this.hideSearchSuggestions(input);
                }, 200);
            });
        });
    }

    // 执行搜索
    performSearch(query) {
        // 这里可以添加实际的搜索逻辑
        console.log('搜索:', query);
    }

    // 显示搜索建议
    showSearchSuggestions(input) {
        // 创建建议下拉框
        const suggestions = document.createElement('div');
        suggestions.className = 'search-suggestions';
        suggestions.innerHTML = `
            <div class="suggestion-item">热门搜索</div>
            <div class="suggestion-item">川菜</div>
            <div class="suggestion-item">火锅</div>
            <div class="suggestion-item">烧烤</div>
        `;
        
        input.parentElement.appendChild(suggestions);
    }

    // 隐藏搜索建议
    hideSearchSuggestions(input) {
        const suggestions = input.parentElement.querySelector('.search-suggestions');
        if (suggestions) {
            suggestions.remove();
        }
    }

    // 通知系统
    setupNotifications() {
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.className = 'notification-container';
        document.body.appendChild(this.notificationContainer);
    }

    // 显示通知
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        
        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <i class="fas fa-${icon} me-2"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;

        this.notificationContainer.appendChild(notification);

        // 自动移除
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 300);
            }
        }, duration);

        return notification;
    }

    // 获取通知图标
    getNotificationIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    // 购物车动画
    addToCartAnimation(button, targetSelector = '#cart-count') {
        const target = document.querySelector(targetSelector);
        if (!target) return;

        // 创建飞行元素
        const flyingElement = document.createElement('div');
        flyingElement.className = 'flying-cart-item';
        flyingElement.innerHTML = '<i class="fas fa-plus"></i>';

        // 设置起始位置
        const buttonRect = button.getBoundingClientRect();
        const targetRect = target.getBoundingClientRect();

        flyingElement.style.left = buttonRect.left + 'px';
        flyingElement.style.top = buttonRect.top + 'px';

        document.body.appendChild(flyingElement);

        // 动画到目标位置
        setTimeout(() => {
            flyingElement.style.left = targetRect.left + 'px';
            flyingElement.style.top = targetRect.top + 'px';
            flyingElement.style.transform = 'scale(0)';
        }, 10);

        // 移除元素
        setTimeout(() => {
            flyingElement.remove();
            // 购物车图标动画
            target.classList.add('cart-bounce');
            setTimeout(() => target.classList.remove('cart-bounce'), 600);
        }, 800);
    }

    // 图片预览
    setupImagePreview() {
        document.querySelectorAll('.preview-image').forEach(img => {
            img.addEventListener('click', () => {
                this.showImageModal(img.src, img.alt);
            });
        });
    }

    // 显示图片模态框
    showImageModal(src, alt) {
        const modal = document.createElement('div');
        modal.className = 'image-modal';
        modal.innerHTML = `
            <div class="image-modal-backdrop" onclick="this.parentElement.remove()"></div>
            <div class="image-modal-content">
                <img src="${src}" alt="${alt}">
                <button class="image-modal-close" onclick="this.closest('.image-modal').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 添加键盘事件
        const handleKeydown = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleKeydown);
            }
        };
        
        document.addEventListener('keydown', handleKeydown);
    }

    // 加载状态管理
    showLoading(element) {
        element.classList.add('loading');
        element.disabled = true;
        
        const originalText = element.textContent;
        element.dataset.originalText = originalText;
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>加载中...';
    }

    hideLoading(element) {
        element.classList.remove('loading');
        element.disabled = false;
        element.textContent = element.dataset.originalText || '确定';
    }

    // 数字动画
    animateNumber(element, start, end, duration = 1000) {
        const startTime = performance.now();
        const difference = end - start;

        const step = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            const current = start + (difference * this.easeOutQuart(progress));
            element.textContent = Math.floor(current);

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        };

        requestAnimationFrame(step);
    }

    // 缓动函数
    easeOutQuart(t) {
        return 1 - (--t) * t * t * t;
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    window.meituanUI = new MeituanUI();
});

// 全局工具函数
window.showNotification = (message, type, duration) => {
    if (window.meituanUI) {
        return window.meituanUI.showNotification(message, type, duration);
    }
};

window.addToCartAnimation = (button, target) => {
    if (window.meituanUI) {
        window.meituanUI.addToCartAnimation(button, target);
    }
};

// CSS动画类
const style = document.createElement('style');
style.textContent = `
    .animate-in {
        animation: slideInUp 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
    }

    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .notification-container {
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
    }

    .notification {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        border-left: 4px solid #06c755;
        animation: slideInRight 0.3s ease-out;
        position: relative;
        display: flex;
        align-items: center;
    }

    .notification-success { border-left-color: #06c755; }
    .notification-error { border-left-color: #ff4757; }
    .notification-warning { border-left-color: #ffa502; }
    .notification-info { border-left-color: #3742fa; }

    .notification-close {
        background: none;
        border: none;
        margin-left: auto;
        padding: 4px;
        border-radius: 4px;
        color: #94a3b8;
        cursor: pointer;
        transition: color 0.2s;
    }

    .notification-close:hover {
        color: #64748b;
    }

    .fade-out {
        animation: fadeOut 0.3s ease-out forwards;
    }

    @keyframes fadeOut {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }

    .flying-cart-item {
        position: fixed;
        z-index: 9999;
        width: 30px;
        height: 30px;
        background: #ffd900;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #333;
        font-size: 14px;
        transition: all 0.8s cubic-bezier(0.4, 0.0, 0.2, 1);
        pointer-events: none;
    }

    .cart-bounce {
        animation: cartBounce 0.6s ease-out;
    }

    @keyframes cartBounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }

    .image-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.3s ease-out;
    }

    .image-modal-backdrop {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        cursor: pointer;
    }

    .image-modal-content {
        position: relative;
        max-width: 90%;
        max-height: 90%;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 25px 50px rgba(0,0,0,0.3);
    }

    .image-modal-content img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        display: block;
    }

    .image-modal-close {
        position: absolute;
        top: 16px;
        right: 16px;
        background: rgba(0,0,0,0.5);
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        color: white;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: background 0.2s;
    }

    .image-modal-close:hover {
        background: rgba(0,0,0,0.7);
    }

    .search-suggestions {
        position: absolute;
        top: 100%;
        left: 0;
        right: 0;
        background: white;
        border-radius: 0 0 12px 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        z-index: 1000;
        overflow: hidden;
    }

    .suggestion-item {
        padding: 12px 20px;
        cursor: pointer;
        transition: background 0.2s;
        border-bottom: 1px solid #f1f5f9;
    }

    .suggestion-item:hover {
        background: #f8fafc;
    }

    .suggestion-item:last-child {
        border-bottom: none;
    }

    .loading {
        opacity: 0.7;
        pointer-events: none;
    }

    .lazy {
        opacity: 0;
        transition: opacity 0.3s;
    }

    .lazy.loaded {
        opacity: 1;
    }
`;

document.head.appendChild(style); 