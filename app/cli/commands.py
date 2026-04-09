"""
CLI 指令介面

提供所有命令列指令
"""

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from pathlib import Path
from typing import Optional

# 暫時使用相對路徑，實際執行時會從 main.py 正確設定
# from ..core.scanner import ServerScanner
# from ..core.java_resolver import JavaResolver
# from..core.launcher import ServerLauncher
# from ..core.backup_manager import BackupManager
# from ..core.dns_manager import DNSManager
# from ..utils.yaml_loader import create_default_server_config
# from ..utils.fs import create_instance_directories

app = typer.Typer()
console = Console()

# 全域設定
SERVERS_ROOT = Path("servers")
CONFIG_ROOT = Path("config")


def get_scanner():
    """取得伺服器掃描器"""
    from ..core.scanner import ServerScanner
    return ServerScanner(SERVERS_ROOT)


def get_java_resolver():
    """取得 Java 解析器"""
    from ..core.java_resolver import JavaResolver
    return JavaResolver(CONFIG_ROOT / "java_registry.yml")


@app.command()
def scan():
    """掃描所有伺服器實例"""
    scanner = get_scanner()
    instances = scanner.scan_all()
    
    if not instances:
        console.print("[yellow]未找到任何伺服器實例[/yellow]")
        return
    
    console.print(f"\n[green]找到 {len(instances)} 個伺服器實例:[/green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("名稱", style="cyan")
    table.add_column("顯示名稱")
    table.add_column("類型")
    table.add_column("Java", style="yellow")
    table.add_column("DNS", style="green")
    
    for config in instances:
        dns_status = "✓" if config.dns.enabled else "-"
        table.add_row(
            config.meta.name,
            config.meta.display_name,
            config.server.loader,
            config.java.profile,
            dns_status
        )
    
    console.print(table)


@app.command()
def list():
    """列出所有伺服器名稱"""
    scanner = get_scanner()
    names = scanner.list_instances()
    
    if not names:
        console.print("[yellow]未找到任何伺服器[/yellow]")
        return
    
    console.print(f"\n[green]伺服器列表:[/green]")
    for name in names:
        console.print(f"  • {name}")


@app.command()
def init(server_name: str):
    """初始化新的伺服器實例"""
    from ..utils.yaml_loader import create_default_server_config
    from ..utils.fs import create_instance_directories
    
    instance_path = SERVERS_ROOT / server_name
    
    if instance_path.exists():
        console.print(f"[red]錯誤: 伺服器 '{server_name}' 已存在[/red]")
        raise typer.Exit(1)
    
    console.print(f"建立伺服器實例: {server_name}")
    
    # 建立目錄結構
    if not create_instance_directories(instance_path):
        console.print("[red]建立目錄失敗[/red]")
        raise typer.Exit(1)
    
    # 建立預設設定檔
    if not create_default_server_config(server_name, instance_path):
        console.print("[red]建立設定檔失敗[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]✓ 伺服器實例已建立: {instance_path}[/green]")
    console.print(f"\n請將 server.jar 放到: {instance_path / 'server'}")
    console.print(f"然後編輯設定檔: {instance_path / 'server.yml'}")


@app.command()
def start(
    server_name: str,
    attach: bool = typer.Option(False, "--attach", "-a", help="附加到終端，顯示即時日誌")
):
    """啟動伺服器"""
    from ..core.launcher import ServerLauncher
    from ..utils.yaml_loader import load_server_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    # 載入設定
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 啟動伺服器
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    
    console.print(f"啟動伺服器: {server_name}")
    if launcher.start(attach=attach):
        if not attach:
            console.print(f"[green]✓ 伺服器已在背景啟動 (PID: {launcher.status.pid})[/green]")
            console.print(f"\n提示: 使用 'python -m app.main logs {server_name} --follow' 查看即時日誌")
    else:
        console.print("[red]啟動失敗[/red]")
        raise typer.Exit(1)


@app.command()
def stop(server_name: str):
    """停止伺服器"""
    from ..core.launcher import ServerLauncher
    from ..utils.yaml_loader import load_server_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    
    console.print(f"停止伺服器: {server_name}")
    if launcher.stop():
        console.print("[green]✓ 伺服器已停止[/green]")
    else:
        console.print("[red]停止失敗[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    server_name: str,
    follow: bool = typer.Option(False, "--follow", "-f", help="跟隨即時日誌（類似 tail -f）"),
    lines: int = typer.Option(50, "--lines", "-n", help="顯示最後 N 行日誌")
):
    """查看伺服器日誌"""
    from ..utils.yaml_loader import load_server_config
    from ..core.path_resolver import PathResolver
    import time
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    paths = PathResolver(config)
    log_file = paths.get_session_log()
    
    if not log_file.exists():
        console.print(f"[yellow]日誌檔案不存在: {log_file}[/yellow]")
        console.print("提示: 伺服器可能尚未啟動過")
        raise typer.Exit(1)
    
    try:
        if follow:
            # 即時跟隨模式
            console.print(f"[cyan]跟隨日誌: {log_file}[/cyan]")
            console.print(f"[dim]按 Ctrl+C 停止[/dim]\n")
            console.print("="*60)
            
            # 先顯示最後 N 行
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line, end='')
            
            # 然後跟隨新內容
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 移到檔案末尾
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        print(line, end='')
                    else:
                        time.sleep(0.1)
        else:
            # 顯示最後 N 行
            console.print(f"[cyan]日誌檔案: {log_file}[/cyan]")
            console.print(f"[dim]顯示最後 {lines} 行[/dim]\n")
            console.print("="*60)
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                for line in all_lines[-lines:]:
                    print(line, end='')
    
    except KeyboardInterrupt:
        console.print("\n\n" + "="*60)
        console.print("[yellow]已停止跟隨日誌[/yellow]")
    except Exception as e:
        console.print(f"[red]讀取日誌失敗: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def restart(server_name: str):
    """重啟伺服器"""
    from ..core.launcher import ServerLauncher
    from ..utils.yaml_loader import load_server_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    
    console.print(f"重啟伺服器: {server_name}")
    if launcher.restart():
        console.print(f"[green]✓ 伺服器已重啟[/green]")
    else:
        console.print("[red]重啟失敗[/red]")
        raise typer.Exit(1)


@app.command()
def status(server_name: str):
    """查看伺服器狀態"""
    from ..core.launcher import ServerLauncher
    from ..core.dns_manager import DNSManager
    from ..utils.yaml_loader import load_server_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 取得狀態
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    server_status = launcher.get_status()
    
    # 顯示狀態
    console.print(f"\n[bold]伺服器狀態: {server_name}[/bold]\n")
    console.print(f"狀態: {server_status.state.value}")
    console.print(f"PID: {server_status.pid if server_status.pid else 'N/A'}")
    console.print(f"運行時間: {server_status.get_uptime_string()}")
    
    # DNS 狀態
    if config.dns.enabled:
        dns_manager = DNSManager(config)
        dns_status = dns_manager.get_status()
        console.print(f"\n[bold]DNS 狀態:[/bold]")
        console.print(f"網域: {dns_status.domain}")
        console.print(f"當前 IP: {dns_status.current_ip if dns_status.current_ip else '未設定'}")
        console.print(f"狀態: {dns_status.get_status_text()}")


@app.command()
def backup(server_name: str):
    """執行備份"""
    from ..core.launcher import ServerLauncher
    from ..core.backup_manager import BackupManager
    from ..utils.yaml_loader import load_server_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 建立備份管理器
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    backup_manager = BackupManager(config, launcher)
    
    # 執行備份
    record = backup_manager.create_backup()
    if record and record.is_success():
        console.print(f"[green]✓ 備份完成: {record.backup_file.name}[/green]")
        console.print(f"大小: {record.get_size_mb():.2f} MB")
        console.print(f"耗時: {record.duration_seconds:.1f} 秒")
    else:
        console.print("[red]備份失敗[/red]")
        if record and record.error_message:
            console.print(f"錯誤: {record.error_message}")
        raise typer.Exit(1)


@app.command()
def diagnose(server_name: str):
    """網路診斷工具 - 排查連接問題"""
    from ..utils.yaml_loader import load_server_config
    from .network_diag import diagnose_network
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 執行診斷
    domain = config.dns.domain if config.dns.enabled else "未設定"
    port = config.dns.server_port if config.dns.enabled else 25565
    
    if domain == "未設定":
        console.print("[yellow]⚠️  DNS 功能未啟用，將只測試端口狀態[/yellow]\n")
        domain = "localhost"
    
    diagnose_network(domain, port)


# DNS 相關指令
dns_app = typer.Typer()
app.add_typer(dns_app, name="dns", help="DNS 管理指令")


@dns_app.command("update")
def dns_update(server_name: str, force: bool = False):
    """更新 DNS 記錄"""
    from ..core.dns_manager import DNSManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    dns_manager = DNSManager(config, global_config)
    
    if not dns_manager.is_enabled():
        console.print("[yellow]DNS 功能未啟用[/yellow]")
        return
    
    console.print(f"更新 DNS: {config.dns.domain}")
    if dns_manager.update_dns(force=force):
        status = dns_manager.get_status()
        console.print(f"[green]✓ DNS 已更新[/green]")
        console.print(f"網域: {status.domain}")
        console.print(f"IP: {status.current_ip}")
    else:
        console.print("[red]DNS 更新失敗[/red]")
        raise typer.Exit(1)


@dns_app.command("status")
def dns_status_cmd(server_name: str):
    """查看 DNS 狀態"""
    from ..core.dns_manager import DNSManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    from ..utils.time_utils import format_timestamp, get_time_ago_string
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    dns_manager = DNSManager(config, global_config)
    status = dns_manager.get_status()
    
    console.print(f"\n[bold]DNS 狀態: {server_name}[/bold]\n")
    console.print(f"啟用: {'是' if status.enabled else '否'}")
    console.print(f"網域: {status.domain}")
    console.print(f"當前 IP: {status.current_ip if status.current_ip else '未設定'}")
    console.print(f"最後更新: {get_time_ago_string(status.last_update)}")
    console.print(f"更新次數: {status.update_count}")
    console.print(f"錯誤次數: {status.error_count}")
    
    if status.last_error:
        console.print(f"[red]最後錯誤: {status.last_error}[/red]")


@dns_app.command("test")
def dns_test(server_name: str):
    """測試 DNS 連線和配置"""
    from ..core.dns_manager import DNSManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    dns_manager = DNSManager(config, global_config)
    
    console.print(f"\n[bold]DNS 連線測試: {server_name}[/bold]\n")
    
    result = dns_manager.test_connection()
    
    console.print(f"狀態: {'✓ 啟用' if result['enabled'] else '✗ 停用'}")
    console.print(f"模式: {result['mode']}")
    console.print(f"網域: {result['domain']}")
    console.print(f"當前 IP: {result['current_ip'] or '無法檢測'}")
    
    if result['mode'].lower() == 'cloudflare':
        api_token = config.dns.config.get('api_token', '')
        zone_id = config.dns.config.get('zone_id', '')
        console.print(f"\nCloudflare 配置:")
        console.print(f"  API Token: {'✓ 已設定 (' + api_token[:8] + '...' + api_token[-4:] + ')' if api_token else '✗ 未設定'}")
        console.print(f"  Zone ID: {'✓ 已設定 (' + zone_id[:8] + '...)' if zone_id else '✗ 未設定'}")
        console.print(f"  API 連線: {'✓ 成功' if result['api_test'] else '✗ 失敗'}")
        console.print(f"  SRV 記錄: {'✓ 啟用' if config.dns.srv_record.enabled else '✗ 停用'}")
    
    if result['errors']:
        console.print(f"\n[yellow]⚠️  發現問題:[/yellow]")
        for error in result['errors']:
            console.print(f"  • {error}")
    
    if result['success']:
        console.print(f"\n[green]✓ DNS 配置正確[/green]")
        console.print("提示: 使用 'dns update' 指令更新 DNS 記錄")
    else:
        console.print(f"\n[red]✗ DNS 配置有誤，請修正上方問題[/red]")
        raise typer.Exit(1)


# Java 相關指令
java_app = typer.Typer()
app.add_typer(java_app, name="java", help="Java 管理指令")


@java_app.command("list")
def java_list():
    """列出所有 Java Profiles"""
    java_resolver = get_java_resolver()
    profiles = java_resolver.list_profiles()
    
    if not profiles:
        console.print("[yellow]未找到任何 Java Profile[/yellow]")
        return
    
    console.print(f"\n[green]Java Profiles:[/green]\n")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("名稱", style="cyan")
    table.add_column("版本")
    table.add_column("路徑")
    table.add_column("狀態", style="green")
    
    results = java_resolver.validate_all()
    
    for name in profiles:
        profile = java_resolver.get_profile(name)
        is_valid, error = results.get(name, (False, "未知"))
        status = "✓" if is_valid else "✗"
        
        table.add_row(
            name,
            profile.version,
            str(profile.path),
            status
        )
    
    console.print(table)


@java_app.command("validate")
def java_validate():
    """驗證所有 Java Profiles"""
    java_resolver = get_java_resolver()
    results = java_resolver.validate_all()
    
    console.print("\n[bold]驗證結果:[/bold]\n")
    
    valid_count = 0
    for name, (is_valid, error) in results.items():
        if is_valid:
            console.print(f"[green]✓ {name}[/green]")
            valid_count += 1
        else:
            console.print(f"[red]✗ {name}: {error}[/red]")
    
    console.print(f"\n有效: {valid_count} / {len(results)}")


# Tunnel 相關指令
tunnel_app = typer.Typer()
app.add_typer(tunnel_app, name="tunnel", help="隧道管理指令")


@tunnel_app.command("status")
def tunnel_status(server_name: str):
    """查看隧道狀態"""
    from ..core.tunnel_manager import TunnelManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    tunnel_mgr = TunnelManager(config, global_config)
    status = tunnel_mgr.get_status()
    
    console.print(f"\n[bold]隧道狀態: {server_name}[/bold]\n")
    console.print(f"啟用: {'是' if status['enabled'] else '否'}")
    
    if status['enabled']:
        console.print(f"類型: {status['type']}")
        console.print(f"隧道狀態: {'運行中' if status['running'] else '已停止'}")
        console.print(f"伺服器狀態: {'運行中' if status['server_running'] else '已停止'}")
        
        if status['running'] and status['pid']:
            console.print(f"PID: {status['pid']}")
        if status['address']:
            console.print(f"隧道地址: {status['address']}")
        
        # 檢查孤立狀態
        if status['orphaned']:
            console.print("\n[yellow]⚠️  警告: 隧道處於孤立狀態[/yellow]")
            console.print("[yellow]伺服器已停止但隧道仍在運行，建議執行清理:[/yellow]")
            console.print("[dim]python -m app.main tunnel cleanup " + server_name + "[/dim]")


@tunnel_app.command("start")
def tunnel_start(server_name: str):
    """手動啟動隧道"""
    from ..core.tunnel_manager import TunnelManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    tunnel_mgr = TunnelManager(config, global_config)
    
    # 啟動前先檢查並清理孤立的隧道
    if tunnel_mgr.check_and_cleanup(verbose=True):
        console.print("")
    
    if not tunnel_mgr.is_enabled():
        console.print("[yellow]隧道功能未啟用[/yellow]")
        console.print("請在 server.yml 中設定 tunnel.enabled: true")
        raise typer.Exit(1)
    
    console.print(f"啟動隧道: {server_name}")
    if tunnel_mgr.start():
        console.print("[green]✓ 隧道已啟動[/green]")
        status = tunnel_mgr.get_status()
        if status['address']:
            console.print(f"隧道地址: {status['address']}")
    else:
        console.print("[red]隧道啟動失敗[/red]")
        raise typer.Exit(1)


@tunnel_app.command("stop")
def tunnel_stop(server_name: str):
    """手動停止隧道"""
    from ..core.tunnel_manager import TunnelManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    tunnel_mgr = TunnelManager(config, global_config)
    
    console.print(f"停止隧道: {server_name}")
    if tunnel_mgr.stop():
        console.print("[green]✓ 隧道已停止[/green]")
    else:
        console.print("[yellow]隧道未運行或停止失敗[/yellow]")


@tunnel_app.command("cleanup")
def tunnel_cleanup(server_name: str):
    """清理孤立的隧道（伺服器已停止但隧道仍在運行）"""
    from ..core.tunnel_manager import TunnelManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    tunnel_mgr = TunnelManager(config, global_config)
    
    console.print(f"檢查隧道狀態: {server_name}")
    
    if tunnel_mgr.check_and_cleanup(verbose=True):
        console.print("[green]✓ 清理完成[/green]")
    else:
        console.print("[dim]無需清理（隧道未運行或伺服器仍在運行）[/dim]")


@tunnel_app.command("diagnose")
def tunnel_diagnose(server_name: str):
    """診斷隧道連接問題"""
    from ..core.tunnel_manager import TunnelManager
    from ..utils.yaml_loader import load_server_config, load_global_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    global_config = load_global_config()
    tunnel_mgr = TunnelManager(config, global_config)
    status = tunnel_mgr.get_status()
    
    console.print(f"\n[bold cyan]隧道連接診斷: {server_name}[/bold cyan]\n")
    console.print("="*60)
    
    # 檢查基本狀態
    console.print("\n[bold]1. 基本狀態檢查[/bold]")
    console.print(f"隧道啟用: {'✓' if status['enabled'] else '✗'}")
    console.print(f"隧道運行: {'✓' if status['running'] else '✗'}")
    console.print(f"伺服器運行: {'✓' if status['server_running'] else '✗'}")
    
    if status['orphaned']:
        console.print("[yellow]⚠️  警告: 隧道處於孤立狀態（伺服器已停止）[/yellow]")
    
    # 連接重置問題診斷
    console.print("\n[bold]2. Connection Reset 問題診斷[/bold]")
    console.print("\n如果玩家遇到 'Internal Exception: Connection Reset' 錯誤，")
    console.print("可能的原因和解決方案：\n")
    
    console.print("[cyan]原因 1: 伺服器實際已關閉但隧道仍在運行[/cyan]")
    if status['orphaned']:
        console.print("  [yellow]✗ 檢測到此問題！[/yellow]")
        console.print(f"  解決方案: 執行 'python -m app.main tunnel cleanup {server_name}'")
    else:
        console.print("  [green]✓ 無此問題[/green]")
    
    console.print("\n[cyan]原因 2: 網絡不穩定或 ISP 限制[/cyan]")
    console.print("  • 某些 ISP 可能會限制或重置長時間的 TCP 連接")
    console.print("  • 移動網絡（4G/5G）可能不穩定")
    console.print("  解決方案:")
    console.print("    - 玩家可以嘗試使用 VPN")
    console.print("    - 玩家可以嘗試切換網絡（如從移動網絡切換到 Wi-Fi）")
    console.print("    - 檢查防火牆或路由器設置")
    
    console.print("\n[cyan]原因 3: PlayIt 隧道節點問題[/cyan]")
    console.print("  • PlayIt 的某些節點可能與特定地區的玩家連接不佳")
    console.print("  解決方案:")
    console.print("    - 重新啟動隧道可能會分配到不同的節點")
    console.print("    - 考慮升級到 PlayIt 付費版以獲得更穩定的節點")
    
    console.print("\n[cyan]原因 4: Minecraft 版本或 Mod 不匹配[/cyan]")
    console.print("  • 玩家的遊戲版本與伺服器不一致")
    console.print("  • 玩家缺少必要的 Mod")
    console.print("  解決方案:")
    console.print(f"    - 確認伺服器版本: {config.meta.display_name}")
    console.print("    - 確保玩家安裝了相同版本的 Forge 和所有 Mod")
    
    console.print("\n[cyan]原因 5: server.properties 配置問題[/cyan]")
    console.print("  • max-players 已滿")
    console.print("  • 玩家被 ban")
    console.print("  • online-mode 設置問題")
    console.print("  解決方案: 檢查 server.properties 和白名單設置")
    
    console.print("\n[bold]3. 建議的檢查步驟[/bold]\n")
    console.print("1. 確認伺服器正在運行")
    console.print("2. 檢查伺服器日誌是否有錯誤訊息")
    console.print("3. 請能連接的玩家和不能連接的玩家比較:")
    console.print("   - 使用的網絡環境（家庭寬帶 vs 移動網絡）")
    console.print("   - 所在地區")
    console.print("   - 遊戲版本和 Mod 清單")
    console.print("4. 如果問題持續，可以嘗試重啟隧道:")
    console.print(f"   python -m app.main tunnel stop {server_name}")
    console.print(f"   python -m app.main tunnel start {server_name}")
    
    console.print("\n" + "="*60)


@app.command("console")
def server_console(server_name: str):
    """連接到伺服器 RCON 控制台（互動模式）"""
    from ..core.rcon_manager import RCONManager, RCONError, get_rcon_config_from_properties
    from ..utils.yaml_loader import load_server_config
    from ..core.path_resolver import PathResolver
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 檢查 RCON 是否啟用
    if not config.rcon.enabled:
        console.print("[yellow]RCON 功能未啟用[/yellow]")
        console.print("請在 server.yml 中設定 rcon.enabled: true")
        raise typer.Exit(1)
    
    # 從 server.properties 讀取實際配置
    path_resolver = PathResolver(config)
    properties_file = path_resolver.get_server_root() / "server.properties"
    
    if not properties_file.exists():
        console.print("[red]server.properties 不存在，請先啟動伺服器一次[/red]")
        raise typer.Exit(1)
    
    rcon_config = get_rcon_config_from_properties(properties_file)
    if not rcon_config or not rcon_config['enabled']:
        console.print("[red]RCON 在 server.properties 中未啟用[/red]")
        console.print("請執行一次 'start' 命令以自動配置 RCON")
        raise typer.Exit(1)
    
    # 使用實際配置
    password = config.rcon.password or rcon_config['password']
    if not password:
        console.print("[red]RCON 密碼未設定[/red]")
        raise typer.Exit(1)
    
    console.print(f"\n[bold cyan]連接到 {server_name} RCON 控制台...[/bold cyan]")
    console.print(f"主機: {config.rcon.host}:{rcon_config['port']}\n")
    
    try:
        rcon = RCONManager(
            host=config.rcon.host,
            port=rcon_config['port'],
            password=password
        )
        
        rcon.connect()
        console.print("[green]✓ 已連接[/green]")
        console.print("\n輸入指令（不需要前綴 /），輸入 'exit' 或 'quit' 離開\n")
        
        while True:
            try:
                # 讀取用戶輸入
                command = input("> ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['exit', 'quit']:
                    break
                
                # 發送命令
                response = rcon.send_command(command)
                if response:
                    console.print(f"[dim]{response}[/dim]")
                
            except KeyboardInterrupt:
                console.print("\n")
                break
            except EOFError:
                break
        
        rcon.disconnect()
        console.print("[yellow]已斷開連接[/yellow]")
        
    except RCONError as e:
        console.print(f"[red]RCON 錯誤: {e}[/red]")
        console.print("\n可能的原因:")
        console.print("  1. 伺服器未運行")
        console.print("  2. RCON 密碼錯誤")
        console.print("  3. RCON 端口被占用")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]未預期的錯誤: {e}[/red]")
        raise typer.Exit(1)


@app.command("send")
def server_send(
    server_name: str,
    command: str = typer.Argument(..., help="要執行的指令（不需要前綴 /）")
):
    """發送單個指令到伺服器 RCON"""
    from ..core.rcon_manager import RCONManager, RCONError, get_rcon_config_from_properties
    from ..utils.yaml_loader import load_server_config
    from ..core.path_resolver import PathResolver
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 檢查 RCON 是否啟用
    if not config.rcon.enabled:
        console.print("[yellow]RCON 功能未啟用[/yellow]")
        raise typer.Exit(1)
    
    # 從 server.properties 讀取實際配置
    path_resolver = PathResolver(config)
    properties_file = path_resolver.get_server_root() / "server.properties"
    
    if not properties_file.exists():
        console.print("[red]server.properties 不存在[/red]")
        raise typer.Exit(1)
    
    rcon_config = get_rcon_config_from_properties(properties_file)
    if not rcon_config or not rcon_config['enabled']:
        console.print("[red]RCON 未啟用[/red]")
        raise typer.Exit(1)
    
    password = config.rcon.password or rcon_config['password']
    if not password:
        console.print("[red]RCON 密碼未設定[/red]")
        raise typer.Exit(1)
    
    try:
        with RCONManager(config.rcon.host, rcon_config['port'], password) as rcon:
            response = rcon.send_command(command)
            if response:
                console.print(response)
            else:
                console.print("[dim]（無回應）[/dim]")
                
    except RCONError as e:
        console.print(f"[red]RCON 錯誤: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]錯誤: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
