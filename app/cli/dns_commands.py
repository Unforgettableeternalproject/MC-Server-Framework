"""
DNS 診斷命令
"""
import typer
from rich.console import Console
from rich.table import Table
import subprocess
import socket

console = Console()


def check_dns_resolution(domain: str) -> dict:
    """檢查 DNS 解析結果"""
    result = {
        'cname': None,
        'srv': None,
        'ipv4': [],
        'ipv6': [],
        'errors': []
    }
    
    try:
        # 檢查 CNAME
        proc = subprocess.run(
            ['nslookup', '-type=CNAME', domain, '8.8.8.8'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'canonical name' in proc.stdout:
            for line in proc.stdout.split('\n'):
                if 'canonical name' in line:
                    result['cname'] = line.split('=')[1].strip()
    except Exception as e:
        result['errors'].append(f"CNAME 查詢失敗: {e}")
    
    try:
        # 檢查 SRV
        srv_domain = f"_minecraft._tcp.{domain}"
        proc = subprocess.run(
            ['nslookup', '-type=SRV', srv_domain, '8.8.8.8'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if 'svr hostname' in proc.stdout:
            srv_info = {}
            for line in proc.stdout.split('\n'):
                if 'priority' in line:
                    srv_info['priority'] = line.split('=')[1].strip()
                elif 'weight' in line:
                    srv_info['weight'] = line.split('=')[1].strip()
                elif 'port' in line:
                    srv_info['port'] = line.split('=')[1].strip()
                elif 'svr hostname' in line:
                    srv_info['target'] = line.split('=')[1].strip()
            result['srv'] = srv_info
    except Exception as e:
        result['errors'].append(f"SRV 查詢失敗: {e}")
    
    try:
        # 檢查 IP 解析
        target = result['cname'] if result['cname'] else domain
        if target:
            target = target.rstrip('.')
            
            # IPv4
            try:
                ipv4_list = socket.getaddrinfo(target, None, socket.AF_INET)
                result['ipv4'] = list(set([ip[4][0] for ip in ipv4_list]))
            except:
                pass
            
            # IPv6
            try:
                ipv6_list = socket.getaddrinfo(target, None, socket.AF_INET6)
                result['ipv6'] = list(set([ip[4][0] for ip in ipv6_list]))
            except:
                pass
    except Exception as e:
        result['errors'].append(f"IP 解析失敗: {e}")
    
    return result


def diagnose_dns_issue(server_name: str, domain: str):
    """診斷 DNS 連接問題"""
    console.print(f"\n[bold cyan]DNS 連接診斷: {domain}[/bold cyan]\n")
    console.print("="*70)
    
    # 檢查 DNS 解析
    console.print("\n[bold]1. DNS 解析檢查[/bold]\n")
    result = check_dns_resolution(domain)
    
    if result['cname']:
        console.print(f"[green]✓[/green] CNAME 記錄: {domain} → {result['cname']}")
    else:
        console.print(f"[yellow]⚠[/yellow] 無 CNAME 記錄（直接使用 A 記錄）")
    
    if result['srv']:
        srv = result['srv']
        console.print(f"[green]✓[/green] SRV 記錄: _minecraft._tcp.{domain}")
        console.print(f"    目標: {srv.get('target', 'N/A')}")
        console.print(f"    端口: {srv.get('port', 'N/A')}")
        console.print(f"    優先級: {srv.get('priority', 'N/A')} / 權重: {srv.get('weight', 'N/A')}")
    else:
        console.print(f"[yellow]⚠[/yellow] 無 SRV 記錄（玩家需手動輸入端口）")
    
    if result['ipv4']:
        console.print(f"[green]✓[/green] IPv4 地址: {', '.join(result['ipv4'])}")
    else:
        console.print(f"[red]✗[/red] 無法解析 IPv4 地址")
    
    if result['ipv6']:
        console.print(f"[green]✓[/green] IPv6 地址: {', '.join(result['ipv6'])}")
    else:
        console.print(f"[dim]  IPv6 地址: 無（正常，不是所有網絡都支持 IPv6）[/dim]")
    
    if result['errors']:
        console.print("\n[red]錯誤:[/red]")
        for error in result['errors']:
            console.print(f"  • {error}")
    
    # 分析問題
    console.print("\n[bold]2. 連接問題分析[/bold]\n")
    
    issues = []
    suggestions = []
    
    # 檢查 CNAME + SRV 配置
    if result['cname'] and result['srv']:
        target = result['cname'].rstrip('.')
        srv_target = result['srv'].get('target', '').rstrip('.')
        if target == srv_target:
            console.print("[green]✓[/green] CNAME 和 SRV 記錄一致")
        else:
            console.print(f"[yellow]⚠[/yellow] CNAME ({target}) 和 SRV ({srv_target}) 目標不一致")
            issues.append("CNAME 和 SRV 記錄指向不同目標")
            suggestions.append("確保 CNAME 和 SRV 記錄都指向相同的 PlayIt 地址")
    
    # IPv6 問題
    if result['ipv6'] and not result['ipv4']:
        issues.append("僅有 IPv6 地址，但許多玩家可能不支持 IPv6")
        suggestions.append("確保 PlayIt 地址同時解析到 IPv4 和 IPv6")
    
    console.print("\n[bold]3. 「部分玩家可以連接，部分不行」的可能原因[/bold]\n")
    
    console.print("[cyan]原因 A: DNS 緩存問題[/cyan]")
    console.print("  • 不能連接的玩家可能緩存了舊的 DNS 記錄")
    console.print("  • 特別是如果最近更改過 DNS 配置")
    console.print("  解決方案：")
    console.print("    1. 玩家執行 'ipconfig /flushdns' (Windows)")
    console.print("    2. 玩家執行 'sudo dscacheutil -flushcache' (Mac)")
    console.print("    3. 等待 DNS TTL 過期（通常 5-30 分鐘）")
    
    console.print("\n[cyan]原因 B: IPv6 vs IPv4 問題[/cyan]")
    if result['ipv6']:
        console.print("  • 你的服務器支持 IPv6")
        console.print("  • 有些玩家的網絡僅支持 IPv4")
        console.print("  • 如果 PlayIt 優先返回 IPv6，純 IPv4 玩家會連接失敗")
        console.print("  解決方案：")
        console.print("    - 確保 PlayIt 隧道同時監聽 IPv4 和 IPv6")
        console.print("    - 或要求玩家禁用 IPv6 (不推薦)")
    
    console.print("\n[cyan]原因 C: 地區性 DNS 污染或延遲[/cyan]")
    console.print("  • 某些地區的 DNS 服務器可能回應不正確")
    console.print("  • 某些 ISP 可能攔截或修改 DNS 查詢")
    console.print("  解決方案：")
    console.print("    - 玩家改用公共 DNS (8.8.8.8, 1.1.1.1)")
    console.print("    - 玩家直接使用 PlayIt 地址連接進行測試")
    
    console.print("\n[cyan]原因 D: Minecraft 客戶端版本差異[/cyan]")
    console.print("  • 較舊的客戶端可能不支持 SRV 記錄查詢")
    console.print("  • 不同啟動器（官方/第三方）的 DNS 處理方式不同")
    console.print("  解決方案：")
    console.print("    - 統一使用相同版本的客戶端")
    console.print("    - 或提供完整地址（域名:端口）")
    
    console.print("\n[cyan]原因 E: PlayIt 節點地區限制[/cyan]")
    console.print("  • PlayIt 的免費節點可能對某些地區連接不佳")
    console.print("  • 某些玩家到特定節點的路由可能被阻斷")
    console.print("  解決方案：")
    console.print("    - 重啟 PlayIt 隧道嘗試獲得不同節點")
    console.print("    - 考慮升級 PlayIt 付費版")
    
    console.print("\n[bold]4. 建議測試步驟[/bold]\n")
    
    test_table = Table(show_header=True, header_style="bold magenta")
    test_table.add_column("步驟", style="cyan", width=5)
    test_table.add_column("測試內容", width=35)
    test_table.add_column("預期結果", width=25)
    
    test_table.add_row(
        "1",
        f"能連接的玩家使用: {domain}",
        "成功連接"
    )
    test_table.add_row(
        "2",
        f"不能連接的玩家使用: {result.get('cname', 'PlayIt地址').rstrip('.')}",
        "如果成功 → DNS問題"
    )
    test_table.add_row(
        "3",
        "不能連接的玩家清除 DNS 緩存",
        "如果成功 → DNS緩存問題"
    )
    test_table.add_row(
        "4",
        "不能連接的玩家改用 8.8.8.8 DNS",
        "如果成功 → ISP DNS問題"
    )
    test_table.add_row(
        "5",
        "對比玩家網絡類型 (WiFi/4G/寬帶)",
        "找出模式"
    )
    
    console.print(test_table)
    
    console.print("\n[bold]5. 快速修復建議[/bold]\n")
    console.print("讓不能連接的玩家嘗試：")
    console.print(f"  1. 清除 DNS 緩存後重試: {domain}")
    console.print(f"  2. 直接使用 PlayIt 地址: {result.get('cname', 'PlayIt地址').rstrip('.')}")
    console.print(f"  3. 使用完整地址: {domain}:25565")
    
    console.print("\n" + "="*70 + "\n")
