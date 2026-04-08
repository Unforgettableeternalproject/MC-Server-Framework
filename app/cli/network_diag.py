"""
網路診斷工具

幫助診斷伺服器連接問題
"""

import socket
import subprocess
import requests
from typing import Dict, Any
from rich.console import Console
from rich.table import Table

console = Console()


def get_local_ip() -> str:
    """取得本地 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "無法檢測"


def get_public_ip() -> str:
    """取得公網 IP"""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        return response.text.strip()
    except Exception:
        return "無法檢測"


def test_port_listening(port: int) -> bool:
    """測試本地端口是否在監聽"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_firewall_rule(port: int) -> Dict[str, Any]:
    """檢查 Windows 防火牆規則"""
    try:
        # 檢查入站規則
        cmd = f'netsh advfirewall firewall show rule name=all | findstr /i "Minecraft {port}"'
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        has_rule = len(result.stdout.strip()) > 0
        return {
            'has_rule': has_rule,
            'details': result.stdout[:200] if has_rule else None
        }
    except Exception as e:
        return {'has_rule': False, 'error': str(e)}


def test_dns_resolution(domain: str) -> Dict[str, Any]:
    """測試 DNS 解析"""
    try:
        ip = socket.gethostbyname(domain)
        return {'success': True, 'ip': ip}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def diagnose_network(domain: str, port: int = 25565) -> Dict[str, Any]:
    """執行完整網路診斷"""
    
    console.print("\n[bold cyan]🔍 網路診斷報告[/bold cyan]\n")
    console.print("="*60)
    
    # 1. IP 檢測
    console.print("\n[yellow]1. IP 位址檢測[/yellow]")
    local_ip = get_local_ip()
    public_ip = get_public_ip()
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("類型", style="cyan")
    table.add_column("位址", style="green")
    table.add_row("本地 IP", local_ip)
    table.add_row("公網 IP", public_ip)
    console.print(table)
    
    # 2. DNS 解析
    console.print(f"\n[yellow]2. DNS 解析測試[/yellow]")
    dns_result = test_dns_resolution(domain)
    if dns_result['success']:
        console.print(f"✓ {domain} → {dns_result['ip']}")
        if dns_result['ip'] == public_ip:
            console.print("[green]✓ DNS 指向正確的公網 IP[/green]")
        else:
            console.print(f"[red]✗ DNS IP ({dns_result['ip']}) 不符合公網 IP ({public_ip})[/red]")
            console.print("[yellow]建議：執行 'python -m app.main dns update <server> --force'[/yellow]")
    else:
        console.print(f"[red]✗ DNS 解析失敗: {dns_result.get('error')}[/red]")
    
    # 3. 本地端口監聽
    console.print(f"\n[yellow]3. 伺服器端口檢測[/yellow]")
    is_listening = test_port_listening(port)
    if is_listening:
        console.print(f"[green]✓ 伺服器正在監聽端口 {port}[/green]")
    else:
        console.print(f"[red]✗ 端口 {port} 沒有程序監聽[/red]")
        console.print("[yellow]建議：確認伺服器是否正在運行[/yellow]")
    
    # 4. 防火牆檢查
    console.print(f"\n[yellow]4. Windows 防火牆檢查[/yellow]")
    fw_result = check_firewall_rule(port)
    if fw_result.get('has_rule'):
        console.print(f"[green]✓ 發現相關防火牆規則[/green]")
    else:
        console.print(f"[red]✗ 沒有發現端口 {port} 的防火牆規則[/red]")
        console.print("\n[yellow]建議：在 PowerShell (管理員) 執行以下指令：[/yellow]")
        console.print(f"[cyan]New-NetFirewallRule -DisplayName 'Minecraft Server' -Direction Inbound -LocalPort {port} -Protocol TCP -Action Allow[/cyan]")
        console.print(f"[cyan]New-NetFirewallRule -DisplayName 'Minecraft Server UDP' -Direction Inbound -LocalPort {port} -Protocol UDP -Action Allow[/cyan]")
    
    # 5. 路由器端口轉發提示
    console.print(f"\n[yellow]5. 路由器端口轉發檢查[/yellow]")
    console.print("⚠️  無法自動檢測，請手動確認：")
    console.print(f"   • 在路由器管理介面設定端口轉發")
    console.print(f"   • 外部端口：{port}")
    console.print(f"   • 內部 IP：{local_ip}")
    console.print(f"   • 內部端口：{port}")
    console.print(f"   • 協議：TCP + UDP")
    
    # 6. 連接測試建議
    console.print(f"\n[yellow]6. 連接測試步驟[/yellow]")
    console.print("\n測試順序：")
    console.print(f"   1️⃣  本地測試：localhost:{port}")
    console.print(f"   2️⃣  內網測試：{local_ip}:{port}")
    console.print(f"   3️⃣  IP 測試：{public_ip}:{port}")
    console.print(f"   4️⃣  網域測試：{domain}")
    
    if not is_listening:
        console.print("\n[red]⛔ 伺服器未運行！先啟動伺服器：[/red]")
        console.print("[cyan]python -m app.main start dc[/cyan]")
    elif dns_result['success'] and dns_result['ip'] != public_ip:
        console.print("\n[yellow]⚠️  DNS 記錄過期！更新 DNS：[/yellow]")
        console.print("[cyan]python -m app.main dns update dc --force[/cyan]")
    elif not fw_result.get('has_rule'):
        console.print("\n[yellow]⚠️  可能被防火牆阻擋！請設定防火牆規則（見上方）[/yellow]")
    else:
        console.print("\n[yellow]⚠️  如果外網仍無法連接，請檢查：[/yellow]")
        console.print("   • 路由器端口轉發是否正確設定")
        console.print("   • ISP 是否限制端口 25565")
        console.print("   • 使用線上工具測試端口開放狀態：")
        console.print(f"     https://www.yougetsignal.com/tools/open-ports/")
        console.print(f"     輸入 IP: {public_ip}，端口: {port}")
    
    console.print("\n" + "="*60 + "\n")
    
    return {
        'local_ip': local_ip,
        'public_ip': public_ip,
        'dns_ok': dns_result['success'] and dns_result.get('ip') == public_ip,
        'port_listening': is_listening,
        'firewall_ok': fw_result.get('has_rule', False)
    }


if __name__ == "__main__":
    # 測試用
    diagnose_network("mc.unforgettableeternalproject.com", 25565)
