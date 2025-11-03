/**
 * 美团风格订餐系统 - 主JavaScript文件
 */

// 全局变量
let cartCount = 0;

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
    // 初始化购物车数量
    updateCartCount();
    
    // 绑定事件监听器
    bindEventListeners();
    
    // 初始化组件
    initializeComponents();
}

/**
 * 绑定事件监听器
 */
function bindEventListeners() {
    // 添加到购物车按钮
    document.addEventListener('click', function(e) {
        if (e.target.closest('.add-to-cart')) {
            const button = e.target.closest('.add-to-cart');
            const dishId = button.getAttribute('data-dish-id');
            if (dishId) {
                addToCart(dishId);
            }
        }
    });
    
    // 搜索表单提交
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const keyword = this.querySelector('input[name="keyword"]').value.trim();
            if (!keyword) {
                e.preventDefault();
                showToast('请输入搜索关键词', 'warning');
            }
        });
    }
    
    // 分类导航点击
    const categoryLinks = document.querySelectorAll('.category-link');
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 更新活动状态
            categoryLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // 滚动到对应区域
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                smoothScrollTo(targetElement);
            }
        });
    });
}

/**
 * 初始化组件
 */
function initializeComponents() {
    // 初始化图片懒加载
    initializeLazyLoading();
    
    // 初始化工具提示
    initializeTooltips();
    
    // 初始化动画
    initializeAnimations();
}

/**
 * 添加到购物车
 * @param {number} dishId 菜品ID
 */
function addToCart(dishId) {
    // 显示加载状态
    showLoading();
    
    fetch('/cart/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            dish_id: dishId,
            quantity: 1
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            updateCartDisplay(data.cart_count);
            showToast('已添加到购物车', 'success');
            
            // 添加动画效果
            animateAddToCart();
        } else {
            showToast(data.message || '添加失败', 'error');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showToast('网络错误，请重试', 'error');
    });
}

/**
 * 更新购物车显示
 * @param {number} count 购物车数量
 */
function updateCartDisplay(count) {
    cartCount = count;
    
    const floatingCart = document.getElementById('floating-cart');
    const cartCountElement = document.getElementById('floating-cart-count');
    const navCartCount = document.getElementById('cart-count');
    
    if (count > 0) {
        if (floatingCart) floatingCart.style.display = 'block';
        if (cartCountElement) cartCountElement.textContent = count;
        if (navCartCount) {
            navCartCount.textContent = count;
            navCartCount.style.display = 'flex';
        }
    } else {
        if (floatingCart) floatingCart.style.display = 'none';
        if (navCartCount) navCartCount.style.display = 'none';
    }
}

/**
 * 更新购物车数量
 */
function updateCartCount() {
    fetch('/cart/count')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartDisplay(data.count);
            }
        })
        .catch(error => {
            console.error('Error fetching cart count:', error);
        });
}

/**
 * 显示Toast消息
 * @param {string} message 消息内容
 * @param {string} type 消息类型 (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${getBootstrapAlertClass(type)} toast-message`;
    
    const icon = getToastIcon(type);
    toast.innerHTML = `<i class="${icon} me-2"></i>${message}`;
    
    document.body.appendChild(toast);
    
    // 自动移除
    setTimeout(() => {
        if (document.body.contains(toast)) {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }
    }, 3000);
}

/**
 * 获取Bootstrap警告类
 * @param {string} type 消息类型
 * @returns {string} Bootstrap类名
 */
function getBootstrapAlertClass(type) {
    const classMap = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return classMap[type] || 'info';
}

/**
 * 获取Toast图标
 * @param {string} type 消息类型
 * @returns {string} 图标类名
 */
function getToastIcon(type) {
    const iconMap = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    return iconMap[type] || 'fas fa-info-circle';
}

/**
 * 平滑滚动到元素
 * @param {Element} element 目标元素
 */
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

/**
 * 显示加载状态
 */
function showLoading() {
    // 可以添加全局加载指示器
    document.body.style.cursor = 'wait';
}

/**
 * 隐藏加载状态
 */
function hideLoading() {
    document.body.style.cursor = 'default';
}

/**
 * 添加到购物车动画
 */
function animateAddToCart() {
    const floatingCart = document.getElementById('floating-cart');
    if (floatingCart) {
        floatingCart.style.animation = 'bounce 0.5s ease-out';
        setTimeout(() => {
            floatingCart.style.animation = '';
        }, 500);
    }
}

/**
 * 初始化图片懒加载
 */
function initializeLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => imageObserver.observe(img));
    } else {
        // 降级处理
        images.forEach(img => {
            img.src = img.dataset.src;
        });
    }
}

/**
 * 初始化工具提示
 */
function initializeTooltips() {
    // 如果使用Bootstrap，可以初始化tooltips
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * 初始化动画
 */
function initializeAnimations() {
    // 添加淡入动画到卡片
    const cards = document.querySelectorAll('.restaurant-card, .dish-card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in');
    });
}

/**
 * 工具函数：防抖
 * @param {Function} func 要防抖的函数
 * @param {number} wait 等待时间
 * @returns {Function} 防抖后的函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 工具函数：节流
 * @param {Function} func 要节流的函数
 * @param {number} limit 限制时间
 * @returns {Function} 节流后的函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 添加CSS动画样式
const style = document.createElement('style');
style.textContent = `
    @keyframes bounce {
        0%, 20%, 60%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        80% { transform: translateY(-5px); }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
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