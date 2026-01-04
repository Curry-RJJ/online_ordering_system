"""
并发压力测试 - 使用 Locust 框架
运行方式: locust -f tests/locust_test.py --host=http://localhost:5000

Web UI: http://localhost:8089
"""

from locust import HttpUser, task, between, events
import random
import string
import time

class OrderingSystemUser(HttpUser):
    """模拟在线订餐系统的用户行为"""
    
    # 用户在任务之间等待的时间（秒）
    wait_time = between(1, 3)
    
    def on_start(self):
        """每个用户开始时执行的初始化操作"""
        self.username = None
        self.password = None
        self.is_logged_in = False
        
        # 尝试注册并登录
        if self.register():
            self.login()
    
    def generate_random_username(self):
        """生成随机用户名"""
        return 'locust_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def generate_random_password(self):
        """生成随机密码"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    def register(self):
        """注册新用户"""
        self.username = self.generate_random_username()
        self.password = self.generate_random_password()
        
        register_data = {
            'username': self.username,
            'password': self.password,
            'confirm_password': self.password,
            'email': f'{self.username}@test.com',
            'phone': f'138{random.randint(10000000, 99999999)}'
        }
        
        with self.client.post(
            "/auth/register",
            data=register_data,
            catch_response=True,
            name="注册用户"
        ) as response:
            if response.status_code == 200:
                response.success()
                return True
            else:
                response.failure(f"注册失败: {response.status_code}")
                return False
    
    def login(self):
        """用户登录"""
        login_data = {
            'username': self.username,
            'password': self.password
        }
        
        with self.client.post(
            "/auth/login",
            data=login_data,
            catch_response=True,
            name="用户登录"
        ) as response:
            if response.status_code == 200 and 'login' not in response.url:
                self.is_logged_in = True
                response.success()
                return True
            else:
                response.failure(f"登录失败: {response.status_code}")
                return False
    
    @task(10)
    def browse_restaurants(self):
        """浏览餐厅列表（高频操作）"""
        with self.client.get("/restaurant/", catch_response=True, name="浏览餐厅") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"浏览失败: {response.status_code}")
    
    @task(8)
    def view_restaurant_detail(self):
        """查看餐厅详情"""
        restaurant_id = random.randint(1, 10)
        with self.client.get(
            f"/restaurant/{restaurant_id}",
            catch_response=True,
            name="查看餐厅详情"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看失败: {response.status_code}")
    
    @task(5)
    def add_to_cart(self):
        """添加商品到购物车"""
        if not self.is_logged_in:
            return
        
        dish_id = random.randint(1, 20)
        quantity = random.randint(1, 3)
        
        with self.client.post(
            "/cart/add",
            json={'dish_id': dish_id, 'quantity': quantity},
            headers={'Content-Type': 'application/json'},
            catch_response=True,
            name="添加购物车"
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('success'):
                        response.success()
                    else:
                        response.failure(f"添加失败: {result.get('message')}")
                except:
                    response.failure("响应格式错误")
            else:
                response.failure(f"请求失败: {response.status_code}")
    
    @task(3)
    def view_cart(self):
        """查看购物车"""
        if not self.is_logged_in:
            return
        
        with self.client.get("/cart/", catch_response=True, name="查看购物车") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看失败: {response.status_code}")
    
    @task(2)
    def update_cart(self):
        """更新购物车商品数量"""
        if not self.is_logged_in:
            return
        
        cart_item_id = random.randint(1, 10)
        quantity = random.randint(1, 5)
        
        with self.client.post(
            f"/cart/update/{cart_item_id}",
            json={'quantity': quantity},
            headers={'Content-Type': 'application/json'},
            catch_response=True,
            name="更新购物车"
        ) as response:
            # 购物车项可能不存在，这是正常的
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"更新失败: {response.status_code}")
    
    @task(3)
    def search_restaurants(self):
        """搜索餐厅"""
        keywords = ['美食', '火锅', '川菜', '快餐', '小吃', '烧烤']
        keyword = random.choice(keywords)
        
        with self.client.get(
            f"/restaurant/?keyword={keyword}",
            catch_response=True,
            name="搜索餐厅"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"搜索失败: {response.status_code}")
    
    @task(1)
    def view_orders(self):
        """查看订单列表"""
        if not self.is_logged_in:
            return
        
        with self.client.get("/order/", catch_response=True, name="查看订单") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看失败: {response.status_code}")
    
    @task(1)
    def view_profile(self):
        """查看个人资料"""
        if not self.is_logged_in:
            return
        
        with self.client.get("/auth/profile", catch_response=True, name="查看个人资料") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看失败: {response.status_code}")


class MerchantAdminUser(HttpUser):
    """模拟商家管理员的操作"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """使用预先创建的商家管理员账号登录"""
        # 注意：需要预先在系统中创建商家管理员账号
        self.username = "merchant_test"
        self.password = "merchant123"
        self.login()
    
    def login(self):
        """登录"""
        login_data = {
            'username': self.username,
            'password': self.password
        }
        
        with self.client.post(
            "/auth/login",
            data=login_data,
            catch_response=True,
            name="商家管理员登录"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"登录失败: {response.status_code}")
    
    @task(5)
    def view_dashboard(self):
        """查看商家管理后台"""
        with self.client.get(
            "/restaurant/merchant/dashboard",
            catch_response=True,
            name="查看商家后台"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"查看失败: {response.status_code}")
    
    @task(2)
    def view_change_requests(self):
        """查看修改请求"""
        with self.client.get(
            "/restaurant/admin/change_requests",
            catch_response=True,
            name="查看修改请求"
        ) as response:
            # 商家管理员可能无权访问，这是预期的
            if response.status_code in [200, 403]:
                response.success()
            else:
                response.failure(f"请求失败: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的钩子"""
    print("\n" + "="*60)
    print("开始 Locust 压力测试")
    print("="*60)
    print(f"目标主机: {environment.host}")
    print()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时的钩子"""
    print("\n" + "="*60)
    print("Locust 压力测试结束")
    print("="*60)
    
    # 输出统计信息
    stats = environment.stats
    print("\n请求统计:")
    print(f"  总请求数: {stats.total.num_requests}")
    print(f"  总失败数: {stats.total.num_failures}")
    print(f"  失败率: {stats.total.fail_ratio * 100:.2f}%")
    print(f"  平均响应时间: {stats.total.avg_response_time:.2f}ms")
    print(f"  中位数响应时间: {stats.total.median_response_time:.2f}ms")
    print(f"  95%响应时间: {stats.total.get_response_time_percentile(0.95):.2f}ms")
    print(f"  99%响应时间: {stats.total.get_response_time_percentile(0.99):.2f}ms")
    print(f"  RPS: {stats.total.total_rps:.2f}")
    print()

