"""
并发测试脚本 - 使用 Python 标准库
测试在线订餐系统在高并发场景下的性能和稳定性
"""

import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
from datetime import datetime
import random
import string
import sys
import argparse

# 默认测试配置
BASE_URL = "http://localhost:5000"
CONCURRENT_USERS = 50  # 并发用户数
TEST_DURATION = 60  # 测试持续时间（秒）

class ConcurrentTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.results = {
            'register': [],
            'login': [],
            'browse_restaurants': [],
            'add_to_cart': [],
            'create_order': [],
            'errors': []
        }
    
    def generate_random_username(self):
        """生成随机用户名"""
        return 'testuser_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    def generate_random_password(self):
        """生成随机密码"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    def register_user(self, user_id):
        """测试用户注册"""
        start_time = time.time()
        session = requests.Session()
        
        try:
            # 获取注册页面（获取CSRF token）
            response = session.get(f"{self.base_url}/auth/register")
            
            username = self.generate_random_username()
            password = self.generate_random_password()
            
            # 提交注册
            register_data = {
                'username': username,
                'password': password,
                'confirm_password': password,
                'email': f'{username}@test.com',
                'phone': f'138{random.randint(10000000, 99999999)}'
            }
            
            response = session.post(
                f"{self.base_url}/auth/register",
                data=register_data,
                allow_redirects=True
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                self.results['register'].append({
                    'user_id': user_id,
                    'username': username,
                    'elapsed': elapsed,
                    'status': 'success'
                })
                return {'success': True, 'username': username, 'password': password}
            else:
                self.results['register'].append({
                    'user_id': user_id,
                    'elapsed': elapsed,
                    'status': 'failed',
                    'error': f'Status code: {response.status_code}'
                })
                return {'success': False}
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.results['errors'].append({
                'operation': 'register',
                'user_id': user_id,
                'error': str(e),
                'elapsed': elapsed
            })
            return {'success': False, 'error': str(e)}
    
    def login_user(self, username, password, user_id):
        """测试用户登录"""
        start_time = time.time()
        session = requests.Session()
        
        try:
            # 获取登录页面
            response = session.get(f"{self.base_url}/auth/login")
            
            # 提交登录
            login_data = {
                'username': username,
                'password': password
            }
            
            response = session.post(
                f"{self.base_url}/auth/login",
                data=login_data,
                allow_redirects=True
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200 and 'login' not in response.url:
                self.results['login'].append({
                    'user_id': user_id,
                    'elapsed': elapsed,
                    'status': 'success'
                })
                return {'success': True, 'session': session}
            else:
                self.results['login'].append({
                    'user_id': user_id,
                    'elapsed': elapsed,
                    'status': 'failed'
                })
                return {'success': False}
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.results['errors'].append({
                'operation': 'login',
                'user_id': user_id,
                'error': str(e),
                'elapsed': elapsed
            })
            return {'success': False}
    
    def browse_restaurants(self, session, user_id):
        """测试浏览餐厅"""
        start_time = time.time()
        
        try:
            response = session.get(f"{self.base_url}/restaurant/")
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                self.results['browse_restaurants'].append({
                    'user_id': user_id,
                    'elapsed': elapsed,
                    'status': 'success'
                })
                return {'success': True}
            else:
                self.results['browse_restaurants'].append({
                    'user_id': user_id,
                    'elapsed': elapsed,
                    'status': 'failed'
                })
                return {'success': False}
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.results['errors'].append({
                'operation': 'browse_restaurants',
                'user_id': user_id,
                'error': str(e),
                'elapsed': elapsed
            })
            return {'success': False}
    
    def add_to_cart(self, session, user_id):
        """测试添加商品到购物车"""
        start_time = time.time()
        
        try:
            # 随机选择一个菜品ID（1-10）
            dish_id = random.randint(1, 10)
            quantity = random.randint(1, 3)
            
            response = session.post(
                f"{self.base_url}/cart/add",
                json={'dish_id': dish_id, 'quantity': quantity},
                headers={'Content-Type': 'application/json'}
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.results['add_to_cart'].append({
                        'user_id': user_id,
                        'elapsed': elapsed,
                        'status': 'success'
                    })
                    return {'success': True}
            
            self.results['add_to_cart'].append({
                'user_id': user_id,
                'elapsed': elapsed,
                'status': 'failed'
            })
            return {'success': False}
                
        except Exception as e:
            elapsed = time.time() - start_time
            self.results['errors'].append({
                'operation': 'add_to_cart',
                'user_id': user_id,
                'error': str(e),
                'elapsed': elapsed
            })
            return {'success': False}
    
    def user_workflow(self, user_id):
        """模拟完整的用户工作流程"""
        print(f"[用户 {user_id}] 开始测试")
        
        # 1. 注册
        register_result = self.register_user(user_id)
        if not register_result['success']:
            print(f"[用户 {user_id}] 注册失败")
            return
        
        time.sleep(0.5)  # 模拟用户思考时间
        
        # 2. 登录
        login_result = self.login_user(
            register_result['username'],
            register_result['password'],
            user_id
        )
        if not login_result['success']:
            print(f"[用户 {user_id}] 登录失败")
            return
        
        session = login_result['session']
        time.sleep(0.5)
        
        # 3. 浏览餐厅
        self.browse_restaurants(session, user_id)
        time.sleep(0.5)
        
        # 4. 添加到购物车（执行多次）
        for _ in range(random.randint(2, 5)):
            self.add_to_cart(session, user_id)
            time.sleep(0.3)
        
        print(f"[用户 {user_id}] 测试完成")
    
    def run_concurrent_test(self, num_users):
        """运行并发测试"""
        print(f"\n{'='*60}")
        print(f"开始并发测试 - {num_users} 个并发用户")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(self.user_workflow, i)
                for i in range(num_users)
            ]
            
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"任务执行出错: {e}")
        
        total_time = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"并发测试完成 - 总耗时: {total_time:.2f} 秒")
        print(f"{'='*60}\n")
        
        return total_time
    
    def print_statistics(self):
        """打印统计结果"""
        print("\n" + "="*80)
        print(" "*30 + "测试结果统计")
        print("="*80 + "\n")
        
        operations = ['register', 'login', 'browse_restaurants', 'add_to_cart']
        operation_names = {
            'register': '用户注册',
            'login': '用户登录',
            'browse_restaurants': '浏览餐厅',
            'add_to_cart': '添加购物车'
        }
        
        for op in operations:
            results = self.results[op]
            if not results:
                continue
            
            success_count = sum(1 for r in results if r['status'] == 'success')
            total_count = len(results)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            
            elapsed_times = [r['elapsed'] for r in results]
            
            print(f"【{operation_names[op]}】")
            print(f"  总请求数: {total_count}")
            print(f"  成功数: {success_count}")
            print(f"  失败数: {total_count - success_count}")
            print(f"  成功率: {success_rate:.2f}%")
            
            if elapsed_times:
                print(f"  响应时间:")
                print(f"    - 最小值: {min(elapsed_times):.3f}s")
                print(f"    - 最大值: {max(elapsed_times):.3f}s")
                print(f"    - 平均值: {statistics.mean(elapsed_times):.3f}s")
                print(f"    - 中位数: {statistics.median(elapsed_times):.3f}s")
                if len(elapsed_times) > 1:
                    print(f"    - 标准差: {statistics.stdev(elapsed_times):.3f}s")
            print()
        
        # 错误统计
        if self.results['errors']:
            print("【错误详情】")
            error_types = {}
            for error in self.results['errors']:
                error_key = error['operation']
                if error_key not in error_types:
                    error_types[error_key] = []
                error_types[error_key].append(error['error'])
            
            for op, errors in error_types.items():
                print(f"  {operation_names.get(op, op)}: {len(errors)} 个错误")
                # 只显示前3个错误
                for err in errors[:3]:
                    print(f"    - {err}")
            print()
        
        print("="*80 + "\n")
    
    def save_report(self, filename='concurrent_test_report.json'):
        """保存测试报告"""
        report = {
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'concurrent_users': CONCURRENT_USERS,
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"详细测试报告已保存至: {filename}\n")


def test_concurrent_registration():
    """专门测试并发注册的唯一性约束"""
    print("\n" + "="*60)
    print("测试场景: 高并发注册相同用户名")
    print("="*60 + "\n")
    
    same_username = 'concurrent_test_user_' + str(int(time.time()))
    password = 'TestPass123'
    
    def try_register(thread_id):
        session = requests.Session()
        try:
            register_data = {
                'username': same_username,
                'password': password,
                'confirm_password': password,
                'email': f'{same_username}@test.com',
                'phone': f'138{random.randint(10000000, 99999999)}'
            }
            
            response = session.post(
                f"{BASE_URL}/auth/register",
                data=register_data,
                allow_redirects=True
            )
            
            if '用户名已存在' in response.text or 'username already exists' in response.text.lower():
                return {'thread_id': thread_id, 'result': 'duplicate_detected'}
            elif response.status_code == 200:
                return {'thread_id': thread_id, 'result': 'success'}
            else:
                return {'thread_id': thread_id, 'result': 'failed', 'status': response.status_code}
                
        except Exception as e:
            return {'thread_id': thread_id, 'result': 'error', 'error': str(e)}
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(try_register, i) for i in range(10)]
        for future in as_completed(futures):
            results.append(future.result())
    
    success_count = sum(1 for r in results if r['result'] == 'success')
    duplicate_count = sum(1 for r in results if r['result'] == 'duplicate_detected')
    error_count = sum(1 for r in results if r['result'] == 'error')
    
    print("测试结果:")
    print(f"  成功注册: {success_count} 个")
    print(f"  检测到重复: {duplicate_count} 个")
    print(f"  错误: {error_count} 个")
    
    if success_count == 1 and duplicate_count == 9:
        print("\n✅ 并发安全性测试通过：唯一约束正确处理")
    elif success_count > 1:
        print("\n❌ 并发安全性测试失败：存在竞态条件，多个相同用户名被注册")
    else:
        print("\n⚠️  并发安全性测试异常：请检查错误详情")
    
    print()


if __name__ == '__main__':
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='在线订餐系统并发测试工具')
    parser.add_argument('-u', '--users', type=int, default=50,
                        help='并发用户数量 (默认: 50)')
    parser.add_argument('-H', '--host', type=str, default='http://localhost:5000',
                        help='目标服务器地址 (默认: http://localhost:5000)')
    parser.add_argument('--skip-safety', action='store_true',
                        help='跳过并发安全性测试')
    parser.add_argument('-o', '--output', type=str,
                        help='测试报告输出文件名 (默认: concurrent_test_report.json)')
    
    args = parser.parse_args()
    
    BASE_URL = args.host
    CONCURRENT_USERS = args.users
    
    # 检查服务是否可用
    try:
        response = requests.get(BASE_URL, timeout=5)
        print(f"✓ 服务器连接成功: {BASE_URL}\n")
    except Exception as e:
        print(f"✗ 无法连接到服务器: {BASE_URL}")
        print(f"  错误: {e}")
        print("\n请确保应用正在运行，然后重试。\n")
        exit(1)
    
    # 运行并发安全性测试
    if not args.skip_safety:
        test_concurrent_registration()
    
    # 运行完整并发测试
    tester = ConcurrentTester(BASE_URL)
    tester.run_concurrent_test(CONCURRENT_USERS)
    tester.print_statistics()
    
    # 保存报告
    if args.output:
        tester.save_report(args.output)
    else:
        tester.save_report(f'concurrent_test_report_{CONCURRENT_USERS}users.json')
    
    print("\n测试完成！")

