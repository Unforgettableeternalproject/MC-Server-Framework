"""
CLI 指令介面

提供所有命令列指令
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
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

app = typer.Typer(
    help="Minecraft 伺服器管理框架 - 快速部署、管理和監控 Minecraft 伺服器",
    add_completion=False
)
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
def setup(force: bool = typer.Option(False, "--force", "-f", help="強制重新初始化（覆蓋現有配置）")):
    """
    初始化框架（創建目錄結構和配置文件）
    
    首次使用時會自動執行，也可以手動執行以重置配置。
    
    範例:
        python -m app.main setup           # 初始化（如果尚未初始化）
        python -m app.main setup --force   # 強制重新初始化
    """
    from ..core.initializer import run_initialization
    
    if force:
        console.print("[yellow]⚠️  強制重新初始化將覆蓋配置文件模板[/yellow]")
        if not typer.confirm("確定要繼續嗎？", default=False):
            console.print("[dim]已取消[/dim]")
            return
    
    run_initialization(force=force)


@app.command()
def info():
    """顯示系統資訊和使用指南"""
    
    # 標題
    title = Text("MC Server Framework", style="bold cyan")
    subtitle = Text("Minecraft 伺服器管理框架 v0.1.0", style="dim")
    
    console.print()
    console.print(Panel.fit(
        title + "\n" + subtitle,
        border_style="cyan"
    ))
    
    # 系統簡介
    console.print("\n[bold]📋 系統簡介[/bold]")
    console.print("""
這是一個全功能的 Minecraft 伺服器管理框架，支援：
  • 多版本伺服器管理（Vanilla、Forge、Fabric 等）
  • 自動化部署和啟動
  • Java 版本管理
  • DNS 動態更新（支援 Cloudflare）
  • 隧道穿透（支援 PlayIt.gg，解決 CGNAT 問題）
  • RCON 遠端控制
  • 自動備份和還原
  • 實時日誌查看
""")
    
    # 快速入門
    console.print("\n[bold]🚀 快速入門[/bold]")
    
    quick_start = Table(show_header=True, header_style="bold magenta", box=None)
    quick_start.add_column("步驟", style="cyan", width=5)
    quick_start.add_column("命令", style="green", width=35)
    quick_start.add_column("說明", width=30)
    
    quick_start.add_row("0", "閱讀 GETTING_STARTED.txt", "詳細入門指南")
    quick_start.add_row("1", "scan", "掃描所有伺服器")
    quick_start.add_row("2", "list", "列出伺服器名稱")
    quick_start.add_row("3", "start <name>", "啟動伺服器")
    quick_start.add_row("4", "status <name>", "查看運行狀態")
    quick_start.add_row("5", "logs <name> --follow", "查看實時日誌")
    
    console.print(quick_start)
    
    # 主要指令分類
    console.print("\n[bold]📚 指令分類[/bold]\n")
    
    # 伺服器管理
    console.print("[cyan]● 伺服器管理[/cyan]")
    console.print("  start <name>         啟動伺服器")
    console.print("  stop <name>          停止伺服器")
    console.print("  restart <name>       重啟伺服器")
    console.print("  status <name>        查看狀態")
    console.print("  logs <name>          查看日誌")
    
    # RCON 控制台
    console.print("\n[cyan]● RCON 控制台[/cyan]")
    console.print("  console <name>       進入互動式控制台")
    console.print("  send <name> <cmd>    發送單個指令")
    
    # 隧道管理
    console.print("\n[cyan]● 隧道管理（穿透 CGNAT）[/cyan]")
    console.print("  tunnel status <name>   查看隧道狀態")
    console.print("  tunnel start <name>    啟動隧道")
    console.print("  tunnel stop <name>     停止隧道")
    console.print("  tunnel cleanup <name>  清理孤立隧道")
    console.print("  tunnel diagnose <name> 診斷隧道問題")
    
    # DNS 管理
    console.print("\n[cyan]● DNS 管理[/cyan]")
    console.print("  dns status <name>    查看 DNS 狀態")
    console.print("  dns update <name>    更新 DNS 記錄")
    console.print("  dns test <name>      測試 DNS 配置")
    console.print("  dns diagnose <name>  診斷 DNS 連接問題")
    
    # Java 管理
    console.print("\n[cyan]● Java 管理[/cyan]")
    console.print("  java list            列出所有 Java Profile")
    console.print("  java scan            掃描系統中的 Java")
    console.print("  java validate        驗證 Java 配置")
    
    # 備份管理
    console.print("\n[cyan]● 備份管理[/cyan]")
    console.print("  backup create <name> 創建備份")
    console.print("  backup list <name>   列出備份")
    console.print("  backup restore <name> <file>  還原備份")
    
    # 診斷工具
    console.print("\n[cyan]● 診斷工具[/cyan]")
    console.print("  check                系統診斷（檢查所有配置）")
    console.print("  diagnose <name>      網絡診斷")
    
    # 配置範例
    console.print("\n[bold]⚙️  配置文件[/bold]\n")
    console.print("  config/app.yml           全局配置（API keys、tunnel 路徑）")
    console.print("  config/java_registry.yml Java 版本配置")
    console.print("  servers/<name>/server.yml 伺服器配置")
    
    # 常見使用場景
    console.print("\n[bold]💡 常見使用場景[/bold]\n")
    
    console.print("[yellow]場景 0: 移植到新電腦後無法運行[/yellow]")
    console.print("  python -m app.main check  # 執行完整系統診斷")
    console.print()
    
    console.print("[yellow]場景 1: 首次啟動伺服器[/yellow]")
    console.print("  1. python -m app.main start dc")
    console.print("  2. python -m app.main logs dc --follow")
    console.print()
    
    console.print("[yellow]場景 2: 使用 RCON 管理伺服器[/yellow]")
    console.print("  python -m app.main console dc")
    console.print("  > op PlayerName")
    console.print("  > whitelist add PlayerName")
    console.print()
    
    console.print("[yellow]場景 3: 解決部分玩家無法連接[/yellow]")
    console.print("  1. python -m app.main dns diagnose dc")
    console.print("  2. 請玩家清除 DNS 緩存: ipconfig /flushdns")
    console.print("  3. 請玩家改用公共 DNS: 8.8.8.8")
    console.print()
    
    console.print("[yellow]場景 4: 伺服器從遊戲內關閉後清理隧道[/yellow]")
    console.print("  python -m app.main tunnel cleanup dc")
    console.print()
    
    # 幫助信息
    console.print("[bold]❓ 獲取幫助[/bold]\n")
    console.print("  python -m app.main --help           查看所有命令")
    console.print("  python -m app.main <command> --help 查看特定命令幫助")
    console.print()
    
    # 文檔鏈接
    console.print("[dim]詳細文檔: docs/ 目錄中的 Markdown 文件[/dim]")
    console.print()


@app.command()
def scan():
    """掃描並顯示所有伺服器實例的配置資訊"""
    scanner = get_scanner()
    instances = scanner.scan_all()
    
    if not instances:
        console.print()
        console.print(Panel(
            "[yellow]未找到任何伺服器實例[/yellow]\n\n"
            "提示: 使用 'init <name>' 創建新的伺服器實例",
            title="[bold]伺服器掃描[/bold]",
            border_style="yellow"
        ))
        console.print()
        return
    
    console.print()
    console.print(f"[bold cyan]📦 找到 {len(instances)} 個伺服器實例[/bold cyan]\n")
    
    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("名稱", style="cyan", no_wrap=True)
    table.add_column("顯示名稱", style="white")
    table.add_column("類型", style="blue")
    table.add_column("Java", style="yellow")
    table.add_column("🌐 DNS", justify="center")
    table.add_column("🔗 Tunnel", justify="center")
    table.add_column("🎮 RCON", justify="center")
    
    for config in instances:
        dns_icon = "✅" if config.dns.enabled else "⭕"
        tunnel_icon = "✅" if (hasattr(config, 'tunnel') and config.tunnel.enabled) else "⭕"
        rcon_icon = "✅" if (hasattr(config, 'rcon') and config.rcon.enabled) else "⭕"
        
        table.add_row(
            config.meta.name,
            config.meta.display_name,
            config.server.loader.capitalize(),
            config.java.profile,
            dns_icon,
            tunnel_icon,
            rcon_icon
        )
    
    console.print(table)
    console.print()
    console.print("[dim]提示: 使用 'status <name>' 查看詳細狀態[/dim]")
    console.print()


@app.command()
def list():
    """列出所有伺服器名稱（簡單清單格式）"""
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
    """初始化新的伺服器實例，創建目錄結構和配置檔"""
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
    """啟動伺服器（自動配置 RCON 和隧道）
    
    範例:
        python -m app.main start dc              # 後台啟動
        python -m app.main start dc --attach     # 附加模式，顯示即時日誌
    """
    from ..core.launcher import ServerLauncher
    from ..utils.yaml_loader import load_server_config
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print()
        console.print(Panel(
            f"[red]找不到伺服器 '{server_name}'[/red]\n\n"
            "使用 'scan' 或 'list' 查看可用的伺服器",
            title="[bold red]錯誤[/bold red]",
            border_style="red"
        ))
        console.print()
        raise typer.Exit(1)
    
    # 載入設定
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    # 啟動伺服器
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    
    if not attach:
        console.print()
        console.print(f"[bold cyan]🚀 啟動伺服器: {config.meta.display_name}[/bold cyan]")
        console.print()
    
    if launcher.start(attach=attach):
        if not attach:
            console.print()
            console.print(Panel(
                f"[green]✅ 伺服器已成功啟動[/green]\n\n"
                f"PID: [cyan]{launcher.status.pid}[/cyan]\n"
                f"狀態: [green]{launcher.status.state.value}[/green]\n\n"
                f"[dim]查看日誌: python -m app.main logs {server_name} --follow[/dim]\n"
                f"[dim]進入控制台: python -m app.main console {server_name}[/dim]",
                title=f"[bold green]伺服器 {server_name} 運行中[/bold green]",
                border_style="green"
            ))
            console.print()
    else:
        console.print()
        console.print(Panel(
            "[red]啟動失敗，請檢查配置和日誌[/red]\n\n"
            f"[dim]查看日誌: python -m app.main logs {server_name}[/dim]",
            title="[bold red]錯誤[/bold red]",
            border_style="red"
        ))
        console.print()
        raise typer.Exit(1)


@app.command()
def stop(server_name: str):
    """停止正在運行的伺服器（會自動停止隧道）
    
    範例:
        python -m app.main stop dc
    """
    from ..core.launcher import ServerLauncher
    from ..utils.yaml_loader import load_server_config
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print()
        console.print(Panel(
            f"[red]找不到伺服器 '{server_name}'[/red]",
            title="[bold red]錯誤[/bold red]",
            border_style="red"
        ))
        console.print()
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    java_resolver = get_java_resolver()
    launcher = ServerLauncher(config, java_resolver)
    
    console.print()
    console.print(f"[bold yellow]⏹️  停止伺服器: {config.meta.display_name}[/bold yellow]")
    console.print()
    
    if launcher.stop():
        console.print()
        console.print(Panel(
            "[green]✅ 伺服器已成功停止[/green]\n\n"
            "[dim]提示: 使用 'start' 命令重新啟動伺服器[/dim]",
            title=f"[bold green]伺服器 {server_name} 已停止[/bold green]",
            border_style="green"
        ))
        console.print()
    else:
        console.print()
        console.print(Panel(
            "[red]停止失敗，伺服器可能未在運行[/red]\n\n"
            f"[dim]檢查狀態: python -m app.main status {server_name}[/dim]",
            title="[bold red]錯誤[/bold red]",
            border_style="red"
        ))
        console.print()
        raise typer.Exit(1)


@app.command()
def logs(
    server_name: str,
    follow: bool = typer.Option(False, "--follow", "-f", help="跟隨即時日誌（類似 tail -f）"),
    lines: int = typer.Option(50, "--lines", "-n", help="顯示最後 N 行日誌")
):
    """查看伺服器日誌檔
    
    範例:
        python -m app.main logs dc              # 顯示最後 50 行
        python -m app.main logs dc --follow     # 即時追蹤日誌
        python -m app.main logs dc -n 100       # 顯示最後 100 行
    """
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
    """重啟伺服器（停止後重新啟動）
    
    範例:
        python -m app.main restart dc
    """
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
    """查看伺服器運行狀態和 DNS 資訊
    
    範例:
        python -m app.main status dc
    """
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
    
    # 使用 Panel 顯示伺服器狀態
    from rich.tree import Tree
    
    # 狀態顏色
    state_colors = {
        "STOPPED": "red",
        "STARTING": "yellow",
        "RUNNING": "green",
        "STOPPING": "yellow",
        "ERROR": "red"
    }
    state_icons = {
        "STOPPED": "⭕",
        "STARTING": "🔄",
        "RUNNING": "✅",
        "STOPPING": "🔄",
        "ERROR": "❌"
    }
    
    status_color = state_colors.get(server_status.state.value, "white")
    status_icon = state_icons.get(server_status.state.value, "●")
    
    # 創建狀態樹
    tree = Tree(f"[bold cyan]{config.meta.display_name}[/bold cyan] ({server_name})")
    
    # 伺服器狀態分支
    server_branch = tree.add(f"[bold]{status_icon} 伺服器狀態[/bold]")
    server_branch.add(f"狀態: [bold {status_color}]{server_status.state.value}[/bold {status_color}]")
    server_branch.add(f"PID: {server_status.pid if server_status.pid else 'N/A'}")
    server_branch.add(f"運行時間: {server_status.get_uptime_string()}")
    server_branch.add(f"Java: {config.java.profile}")
    
    # 網絡配置分支
    network_branch = tree.add("[bold]🌐 網絡配置[/bold]")
    
    # DNS 狀態
    if config.dns.enabled:
        from ..utils.yaml_loader import load_global_config
        dns_manager = DNSManager(config, load_global_config())
        dns_status = dns_manager.get_status()
        dns_sub = network_branch.add(f"DNS: [green]✓ 啟用[/green]")
        dns_sub.add(f"網域: {dns_status.domain}")
        dns_sub.add(f"當前 IP: {dns_status.current_ip if dns_status.current_ip else '未設定'}")
        dns_sub.add(f"狀態: {dns_status.get_status_text()}")
    else:
        network_branch.add("DNS: [dim]停用[/dim]")
    
    # 隧道狀態
    if hasattr(config, 'tunnel') and config.tunnel.enabled:
        from ..core.tunnel_manager import TunnelManager
        from ..utils.yaml_loader import load_global_config
        tunnel_mgr = TunnelManager(config, load_global_config())
        tunnel_status = tunnel_mgr.get_status()
        
        tunnel_running = tunnel_status.get('running', False)
        tunnel_sub = network_branch.add(f"隧道: {'[green]✓ 運行中[/green]' if tunnel_running else '[yellow]已停止[/yellow]'}")
        tunnel_sub.add(f"類型: {tunnel_status.get('type', 'N/A')}")
        if tunnel_status.get('address'):
            tunnel_sub.add(f"地址: {tunnel_status['address']}")
        if tunnel_status.get('orphaned'):
            tunnel_sub.add("[yellow]⚠️  孤立狀態（建議執行 cleanup）[/yellow]")
    else:
        network_branch.add("隧道: [dim]停用[/dim]")
    
    # RCON 狀態
    if hasattr(config, 'rcon') and config.rcon.enabled:
        network_branch.add(f"RCON: [green]✓ 啟用[/green] (端口: {config.rcon.port})")
    else:
        network_branch.add("RCON: [dim]停用[/dim]")
    
    console.print()
    console.print(Panel(tree, title="[bold]伺服器資訊[/bold]", border_style="cyan"))
    console.print()


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
def check():
    """系統診斷 - 檢查框架運行環境和配置
    
    檢查項目：
      • Python 版本和依賴套件
      • 目錄結構
      • 配置文件格式
      • Java 安裝和配置
      • 伺服器實例
      • PlayIt 隧道配置
      • 文件權限
    
    範例:
        python -m app.main check
    """
    from .system_check import run_diagnostics
    run_diagnostics()


@app.command()
def cleanup(server_name: str):
    """
    清理孤立的 PID 文件
    
    當伺服器或通道進程被強制終止（如使用 taskkill 或系統崩潰）時，
    PID 文件可能會殘留，導致框架誤認為進程仍在運行。
    此命令會清理這些孤立的 PID 文件，讓系統恢復正常狀態。
    
    使用場景:
        - 伺服器顯示 "運行中" 但實際沒有進程
        - 無法正常啟動伺服器（提示已在運行）
        - 強制終止進程後需要重置狀態
    
    範例:
        python -m app.main cleanup myserver
    """
    from ..utils.yaml_loader import load_server_config
    from rich.panel import Panel
    from pathlib import Path
    import psutil
    import json
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    runtime_path = instance_path / "runtime"
    server_pid_file = runtime_path / "server.pid"
    tunnel_pid_file = runtime_path / "playit.pid"
    
    cleaned = []
    orphaned = []
    running = []
    
    # 檢查伺服器 PID
    if server_pid_file.exists():
        try:
            with open(server_pid_file, 'r') as f:
                data = json.load(f)
                pid = data.get("pid")
                if pid:
                    try:
                        process = psutil.Process(pid)
                        if process.is_running():
                            running.append(("伺服器", pid))
                        else:
                            orphaned.append(("伺服器", pid, server_pid_file))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        orphaned.append(("伺服器", pid, server_pid_file))
        except Exception as e:
            console.print(f"[yellow]警告: 無法讀取伺服器 PID 文件 - {e}[/yellow]")
    
    # 檢查通道 PID
    if tunnel_pid_file.exists():
        try:
            with open(tunnel_pid_file, 'r') as f:
                data = json.load(f)
                pid = data.get("pid")
                if pid:
                    try:
                        process = psutil.Process(pid)
                        if process.is_running():
                            running.append(("通道", pid))
                        else:
                            orphaned.append(("通道", pid, tunnel_pid_file))
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        orphaned.append(("通道", pid, tunnel_pid_file))
        except Exception as e:
            console.print(f"[yellow]警告: 無法讀取通道 PID 文件 - {e}[/yellow]")
    
    # 清理孤立的 PID 文件
    if orphaned:
        console.print(f"\n[yellow]發現 {len(orphaned)} 個孤立的 PID 文件:[/yellow]\n")
        for name, pid, pid_file in orphaned:
            console.print(f"  • {name} (PID: {pid}) - 進程不存在")
            try:
                pid_file.unlink()
                cleaned.append(name)
                console.print(f"    [green]✓ 已清理: {pid_file.name}[/green]")
            except Exception as e:
                console.print(f"    [red]✗ 清理失敗: {e}[/red]")
    
    # 顯示正在運行的進程
    if running:
        console.print(f"\n[blue]正在運行的進程:[/blue]\n")
        for name, pid in running:
            console.print(f"  • {name} (PID: {pid}) - 進程正常運行")
    
    # 總結
    if cleaned:
        console.print(Panel(
            f"[green]✓ 清理完成[/green]\n\n"
            f"已清理 {len(cleaned)} 個孤立的 PID 文件\n"
            f"現在可以正常啟動伺服器了",
            title=f"🧹 清理成功",
            border_style="green"
        ))
    elif orphaned:
        console.print(Panel(
            f"[red]✗ 部分清理失敗[/red]\n\n"
            f"請檢查檔案權限或手動刪除 PID 文件",
            title="⚠️  清理失敗",
            border_style="red"
        ))
    elif running:
        console.print(Panel(
            f"[blue]進程正在運行[/blue]\n\n"
            f"所有進程都正常運行中，無需清理\n"
            f"如需停止伺服器，請使用: stop {server_name}",
            title="ℹ️  無需清理",
            border_style="blue"
        ))
    else:
        console.print(Panel(
            f"[green]✓ 狀態正常[/green]\n\n"
            f"沒有發現孤立的 PID 文件",
            title="✓ 檢查完成",
            border_style="green"
        ))


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


@dns_app.command("diagnose")
def dns_diagnose_cmd(server_name: str):
    """診斷 DNS 連接問題（針對部分玩家無法連接的情況）"""
    from ..utils.yaml_loader import load_server_config
    from .dns_commands import diagnose_dns_issue
    
    scanner = get_scanner()
    instance_path = scanner.find_instance(server_name)
    
    if not instance_path:
        console.print(f"[red]錯誤: 找不到伺服器 '{server_name}'[/red]")
        raise typer.Exit(1)
    
    config = load_server_config(instance_path)
    if not config:
        console.print("[red]無法載入伺服器設定[/red]")
        raise typer.Exit(1)
    
    domain = config.dns.domain
    if not domain:
        console.print("[yellow]未設定網域名稱[/yellow]")
        raise typer.Exit(1)
    
    diagnose_dns_issue(server_name, domain)


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
