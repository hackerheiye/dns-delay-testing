import argparse
import time
from datetime import datetime
import dns.resolver

def test_dns_latency(dns_server, domain, timeout=5, retries=1):
    """测试单次DNS解析延迟"""
    resolver = dns.resolver.Resolver()
    
    # 解析DNS服务器地址和端口
    if ':' in dns_server:
        ip, port = dns_server.split(':', 1)
        resolver.nameservers = [ip]
        resolver.port = int(port)
    else:
        resolver.nameservers = [dns_server]
        resolver.port = 53  # 默认DNS端口
    
    resolver.timeout = timeout  # 超时时间（秒）
    resolver.lifetime = timeout  # 总生命周期（秒）
    
    try:
        start_time = time.perf_counter()
        # 执行A记录查询 - 使用推荐的resolve方法替代query
        resolver.resolve(domain, 'A')
        end_time = time.perf_counter()
        latency = (end_time - start_time) * 1000  # 转换为毫秒
        return True, latency
    except Exception as e:
        # 捕获所有可能的异常（超时、解析失败等）
        return False, str(e)

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description='DNS延迟测试工具',
        epilog="""使用示例:
  python "dns delay testing.py" --dns 8.8.8.8
  python "dns delay testing.py" --dns 8.8.8.8:53 --domain google.com
  python "dns delay testing.py" --dns 43.133.224.74:532 --count 10 --timeout 3
"""
    )
    parser.add_argument('--dns', required=True, help='DNS服务器IP地址（如：8.8.8.8 或 8.8.8.8:532）')
    parser.add_argument('--domain', default='baidu.com', help='测试域名（默认：baidu.com）')
    parser.add_argument('--count', type=int, default=5, help='测试次数（默认：5）')
    parser.add_argument('--timeout', type=int, default=5, help='超时时间（秒，默认：5）')
    args = parser.parse_args()

    print(f"=== DNS延迟测试开始 ===")
    print(f"DNS服务器: {args.dns}")
    print(f"测试域名: {args.domain}")
    print(f"测试次数: {args.count}")
    print(f"超时时间: {args.timeout}秒")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)

    results = []
    success_count = 0
    latency_list = []

    for i in range(args.count):
        print(f"第{i+1}次测试...", end=' ')
        success, result = test_dns_latency(
            dns_server=args.dns,
            domain=args.domain,
            timeout=args.timeout
        )
        
        if success:
            success_count += 1
            latency_list.append(result)
            print(f"成功，延迟: {result:.2f} ms")
        else:
            print(f"失败，原因: {result}")
        
        results.append((success, result))
        # 测试间隔（避免请求过于密集）
        if i < args.count - 1:
            time.sleep(0.5)

    print("-" * 50)
    print(f"=== 测试结果汇总 ===")
    print(f"总测试次数: {args.count}")
    print(f"成功次数: {success_count}")
    print(f"失败次数: {args.count - success_count}")
    print(f"成功率: {success_count/args.count*100:.2f}%")

    if latency_list:
        print(f"最小延迟: {min(latency_list):.2f} ms")
        print(f"最大延迟: {max(latency_list):.2f} ms")
        print(f"平均延迟: {sum(latency_list)/len(latency_list):.2f} ms")

    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # 需安装依赖：pip install dnspython
    main()
    