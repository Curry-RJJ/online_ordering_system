"""
多级别并发测试脚本
自动运行100、500、1000并发用户测试，并生成对比报告
"""

import subprocess
import time
import json
import statistics
from datetime import datetime
import os

class MultiLevelTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.test_levels = [100, 500, 1000]
        self.results = {}
    
    def run_test_level(self, user_count):
        """运行指定并发级别的测试"""
        print("\n" + "="*80)
        print(f"开始 {user_count} 并发用户测试")
        print("="*80 + "\n")
        
        start_time = time.time()
        
        # 运行测试
        output_file = f'concurrent_test_report_{user_count}users.json'
        cmd = [
            'python', 'tests/concurrent_test.py',
            '--users', str(user_count),
            '--host', self.base_url,
            '--skip-safety',
            '--output', output_file
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                print(result.stdout)
                
                # 读取测试报告
                if os.path.exists(output_file):
                    with open(output_file, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                    
                    self.results[user_count] = {
                        'success': True,
                        'duration': time.time() - start_time,
                        'report': report
                    }
                    
                    print(f"\n✓ {user_count} 并发用户测试完成")
                else:
                    print(f"\n⚠️  测试报告文件未生成: {output_file}")
                    self.results[user_count] = {'success': False, 'error': '报告文件未生成'}
            else:
                print(f"\n✗ 测试失败:")
                print(result.stderr)
                self.results[user_count] = {'success': False, 'error': result.stderr}
                
        except Exception as e:
            print(f"\n✗ 运行测试时出错: {e}")
            self.results[user_count] = {'success': False, 'error': str(e)}
        
        # 等待一段时间再进行下一级别测试
        if user_count < self.test_levels[-1]:
            print("\n等待系统恢复...")
            time.sleep(10)
    
    def run_all_tests(self):
        """运行所有级别的测试"""
        print("\n" + "="*80)
        print(" "*20 + "多级别并发测试开始")
        print(" "*15 + f"测试级别: {', '.join(map(str, self.test_levels))} 并发用户")
        print(f" "*20 + f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        for level in self.test_levels:
            self.run_test_level(level)
    
    def generate_comparison_report(self):
        """生成对比报告"""
        print("\n" + "="*80)
        print(" "*25 + "多级别测试对比报告")
        print("="*80 + "\n")
        
        # 检查是否有成功的测试
        success_tests = {k: v for k, v in self.results.items() if v.get('success')}
        
        if not success_tests:
            print("❌ 所有测试均失败，无法生成对比报告\n")
            return
        
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试服务器: {self.base_url}\n")
        
        # 汇总表格
        print("┌" + "─"*78 + "┐")
        print("│" + " "*25 + "测试结果汇总" + " "*40 + "│")
        print("├" + "─"*15 + "┬" + "─"*15 + "┬" + "─"*15 + "┬" + "─"*15 + "┬" + "─"*14 + "┤")
        print(f"│ {'并发用户数':^13} │ {'总请求数':^13} │ {'成功率':^13} │ {'平均响应时间':^13} │ {'测试用时':^12} │")
        print("├" + "─"*15 + "┼" + "─"*15 + "┼" + "─"*15 + "┼" + "─"*15 + "┼" + "─"*14 + "┤")
        
        for level in self.test_levels:
            if level in success_tests:
                report = success_tests[level]['report']
                
                # 计算统计数据
                total_requests = 0
                success_requests = 0
                all_elapsed = []
                
                for op in ['register', 'login', 'browse_restaurants', 'add_to_cart']:
                    if op in report['results']:
                        results = report['results'][op]
                        total_requests += len(results)
                        success_requests += sum(1 for r in results if r.get('status') == 'success')
                        all_elapsed.extend([r['elapsed'] for r in results if 'elapsed' in r])
                
                success_rate = (success_requests / total_requests * 100) if total_requests > 0 else 0
                avg_time = statistics.mean(all_elapsed) if all_elapsed else 0
                test_duration = success_tests[level]['duration']
                
                print(f"│ {level:>13} │ {total_requests:>13} │ {success_rate:>12.2f}% │ {avg_time:>11.3f}s │ {test_duration:>10.2f}s │")
            else:
                error = self.results[level].get('error', '未知错误')
                print(f"│ {level:>13} │ {'测试失败':^13} │ {'-':^13} │ {'-':^13} │ {'-':^12} │")
        
        print("└" + "─"*15 + "┴" + "─"*15 + "┴" + "─"*15 + "┴" + "─"*15 + "┴" + "─"*14 + "┘")
        
        # 详细对比
        print("\n" + "="*80)
        print("详细性能对比")
        print("="*80 + "\n")
        
        operations = {
            'register': '用户注册',
            'login': '用户登录',
            'browse_restaurants': '浏览餐厅',
            'add_to_cart': '添加购物车'
        }
        
        for op_key, op_name in operations.items():
            print(f"【{op_name}】")
            print(f"{'并发数':<10} {'请求数':<10} {'成功率':<10} {'平均响应':<12} {'最小值':<10} {'最大值':<10} {'中位数':<10}")
            print("-" * 80)
            
            for level in self.test_levels:
                if level in success_tests:
                    report = success_tests[level]['report']
                    
                    if op_key in report['results'] and report['results'][op_key]:
                        results = report['results'][op_key]
                        success = sum(1 for r in results if r.get('status') == 'success')
                        total = len(results)
                        success_rate = (success / total * 100) if total > 0 else 0
                        
                        elapsed = [r['elapsed'] for r in results if 'elapsed' in r]
                        if elapsed:
                            avg_time = statistics.mean(elapsed)
                            min_time = min(elapsed)
                            max_time = max(elapsed)
                            median_time = statistics.median(elapsed)
                            
                            print(f"{level:<10} {total:<10} {success_rate:>8.1f}% {avg_time:>10.3f}s {min_time:>8.3f}s {max_time:>8.3f}s {median_time:>8.3f}s")
                        else:
                            print(f"{level:<10} {total:<10} {success_rate:>8.1f}% {'N/A':<12} {'N/A':<10} {'N/A':<10} {'N/A':<10}")
                    else:
                        print(f"{level:<10} {'无数据':<10}")
                else:
                    print(f"{level:<10} {'测试失败':<10}")
            
            print()
        
        # 性能趋势分析
        print("="*80)
        print("性能趋势分析")
        print("="*80 + "\n")
        
        if len(success_tests) >= 2:
            # 分析响应时间随并发数的变化
            level_times = {}
            for level in sorted(success_tests.keys()):
                report = success_tests[level]['report']
                all_elapsed = []
                for op in ['register', 'login', 'browse_restaurants', 'add_to_cart']:
                    if op in report['results']:
                        all_elapsed.extend([r['elapsed'] for r in report['results'][op] if 'elapsed' in r])
                
                if all_elapsed:
                    level_times[level] = statistics.mean(all_elapsed)
            
            if len(level_times) >= 2:
                levels = sorted(level_times.keys())
                print("平均响应时间变化:")
                for i, level in enumerate(levels):
                    time_val = level_times[level]
                    print(f"  {level:>4} 并发: {time_val:.3f}s", end="")
                    
                    if i > 0:
                        prev_level = levels[i-1]
                        increase = ((time_val - level_times[prev_level]) / level_times[prev_level]) * 100
                        if increase > 0:
                            print(f"  (↑ {increase:.1f}%)")
                        else:
                            print(f"  (↓ {abs(increase):.1f}%)")
                    else:
                        print()
                
                print("\n性能评估:")
                final_level = levels[-1]
                final_time = level_times[final_level]
                
                if final_time < 0.5:
                    print(f"  ✅ 在 {final_level} 并发下，平均响应时间 {final_time:.3f}s < 0.5s，性能优秀")
                elif final_time < 1.0:
                    print(f"  ⚠️  在 {final_level} 并发下，平均响应时间 {final_time:.3f}s < 1.0s，性能良好")
                elif final_time < 2.0:
                    print(f"  ⚠️  在 {final_level} 并发下，平均响应时间 {final_time:.3f}s < 2.0s，性能一般")
                else:
                    print(f"  ❌ 在 {final_level} 并发下，平均响应时间 {final_time:.3f}s > 2.0s，存在性能瓶颈")
        
        print("\n" + "="*80 + "\n")
        
        # 保存对比报告
        comparison_report = {
            'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'base_url': self.base_url,
            'test_levels': self.test_levels,
            'results': self.results
        }
        
        report_file = f'multi_level_test_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_report, f, ensure_ascii=False, indent=2)
        
        print(f"详细对比报告已保存至: {report_file}\n")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='多级别并发测试工具')
    parser.add_argument('-H', '--host', type=str, default='http://localhost:5000',
                        help='目标服务器地址 (默认: http://localhost:5000)')
    parser.add_argument('-l', '--levels', type=int, nargs='+', default=[100, 500, 1000],
                        help='并发测试级别 (默认: 100 500 1000)')
    
    args = parser.parse_args()
    
    # 检查服务是否可用
    import requests
    try:
        response = requests.get(args.host, timeout=5)
        print(f"✓ 服务器连接成功: {args.host}\n")
    except Exception as e:
        print(f"✗ 无法连接到服务器: {args.host}")
        print(f"  错误: {e}")
        print("\n请确保应用正在运行，然后重试。\n")
        exit(1)
    
    # 创建测试器
    tester = MultiLevelTester(base_url=args.host)
    tester.test_levels = sorted(args.levels)
    
    # 运行测试
    tester.run_all_tests()
    
    # 生成对比报告
    tester.generate_comparison_report()
    
    print("所有测试完成！")

