import argparse
import time
from datetime import datetime
import dns.resolver
import socket
import traceback

def test_port_connectivity(ip, port, timeout=2):
    """测试指定IP和端口的连接性"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0  # 如果连接成功返回True
    except Exception as e:
        # 输出更多调试信息
        print(f"  端口连接测试异常: {str(e)}")
        return False

def test_dns_latency(dns_server, domain, timeout=5, retries=1):
    """测试单次DNS解析延迟"""
    resolver = dns.resolver.Resolver()
    
    # 解析DNS服务器地址和端口
    ip = None
    port = 53  # 默认DNS端口
    
    if ':' in dns_server:
        server_part, port_part = dns_server.split(':', 1)
        port = int(port_part)
    else:
        server_part = dns_server
    
    # 尝试将server_part解析为IP地址
    try:
        # 方法1：使用socket库进行域名解析
        ip = socket.gethostbyname(server_part)
    except socket.gaierror:
        try:
            # 方法2：使用系统默认DNS解析器解析DNS服务器域名
            system_resolver = dns.resolver.Resolver()
            system_resolver.timeout = timeout
            system_resolver.lifetime = timeout
            answers = system_resolver.resolve(server_part, 'A')
            ip = str(answers[0])
        except Exception:
            # 如果两种方法都无法解析，则假设server_part已经是IP地址
            ip = server_part
    
    # 测试端口连接性
    port_open = test_port_connectivity(ip, port)
    print(f"  服务器IP: {ip}, 端口: {port}, 端口连接状态: {'开放' if port_open else '关闭或无法连接'}")
    
    resolver.nameservers = [ip]
    resolver.port = port
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
        error_type = type(e).__name__
        error_msg = str(e)
        additional_info = []
        
        # 端口连接性信息
        if not port_open:
            additional_info.append(f"端口{port}无法连接")
        else:
            # 即使端口开放，DNS服务也可能没有正确响应
            additional_info.append("端口开放但DNS服务可能未正常工作")
        
        # 分析常见的DNS错误类型并提供可能的原因
        if "timeout" in error_msg.lower():
            additional_info.append("服务器响应缓慢、网络连接问题或防火墙限制")
        elif "refused" in error_msg.lower():
            additional_info.append("服务器拒绝连接、访问权限问题")
        
        # 显示完整的错误信息和可能原因
        full_error = f"{error_type}: {error_msg}\n可能原因: " + ", ".join(additional_info)
        return False, full_error

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
    parser.add_argument('--dns', required=True, help='DNS服务器（支持IP地址或域名，格式如：8.8.8.8 或 8.8.8.8:532 或 dns.example.com）')
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
    
