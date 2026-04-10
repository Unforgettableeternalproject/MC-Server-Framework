"""
互動式 CLI 入口介面
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.text import Text
from pathlib import Path
import sys

console = Console()


def show_welcome():
    """顯示歡迎畫面"""
    title = Text("MC Server Framework", style="bold cyan")
    subtitle = Text("Minecraft 伺服器管理框架", style="dim")
    
    welcome_text = f"""
{title}
{subtitle}

一個全功能的 Minecraft 伺服器管理解決方案
支援多版本、DNS 管理、隧道穿透、RCON 控制等功能

版本: 0.1.0
    """
    
    console.print()
    console.print(Panel(
        welcome_text.strip(),
        border_style="cyan",
        padding=(1, 2)
    ))
    console.print()


def show_main_menu():
    """顯示主選單"""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("選項", style="cyan", width=8)
    table.add_column("說明", style="white")
    
    table.add_row("1", "📋 查看所有伺服器")
    table.add_row("2", "🚀 啟動伺服器")
    table.add_row("3", "⏹️  停止伺服器")
    table.add_row("4", "🔄 重啟伺服器")
    table.add_row("5", "📊 查看伺服器狀態")
    table.add_row("6", "📜 查看伺服器日誌")
    table.add_row("7", "🎮 進入 RCON 控制台")
    table.add_row("8", "🔧 管理工具菜單")
    table.add_row("9", "ℹ️  系統資訊和說明")
    table.add_row("c", "🔍 系統診斷（檢查配置）")
    table.add_row("0", "❌ 離開")
    
    console.print(Panel(table, title="[bold]主選單[/bold]", border_style="cyan"))
    console.print()


def show_tools_menu():
    """顯示管理工具選單"""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("選項", style="cyan", width=8)
    table.add_column("說明", style="white")
    
    table.add_row("1", "🔗 隧道管理")
    table.add_row("2", "🌐 DNS 管理")
    table.add_row("3", "☕ Java 管理")
    table.add_row("4", "💾 備份管理")
    table.add_row("5", "🔍 網絡診斷")
    table.add_row("6", "🧹 清理孤立 PID")
    table.add_row("0", "⬅️  返回主選單")
    
    console.print(Panel(table, title="[bold]管理工具[/bold]", border_style="yellow"))
    console.print()


def show_tunnel_menu():
    """顯示隧道管理選單"""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("選項", style="cyan", width=8)
    table.add_column("說明", style="white")
    
    table.add_row("1", "查看隧道狀態")
    table.add_row("2", "啟動隧道")
    table.add_row("3", "停止隧道")
    table.add_row("4", "清理孤立隧道")
    table.add_row("5", "診斷隧道問題")
    table.add_row("0", "返回")
    
    console.print(Panel(table, title="[bold]隧道管理[/bold]", border_style="blue"))
    console.print()


def show_dns_menu():
    """顯示 DNS 管理選單"""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("選項", style="cyan", width=8)
    table.add_column("說明", style="white")
    
    table.add_row("1", "查看 DNS 狀態")
    table.add_row("2", "更新 DNS 記錄")
    table.add_row("3", "測試 DNS 配置")
    table.add_row("4", "診斷 DNS 問題")
    table.add_row("0", "返回")
    
    console.print(Panel(table, title="[bold]DNS 管理[/bold]", border_style="green"))
    console.print()


def get_server_list():
    """獲取伺服器列表"""
    try:
        from ..core.scanner import ServerScanner
        scanner = ServerScanner(Path("servers"))
        names = scanner.list_instances()
        return names
    except Exception as e:
        console.print(f"[red]獲取伺服器列表失敗: {e}[/red]")
        return []


def select_server():
    """讓使用者選擇伺服器"""
    servers = get_server_list()
    
    if not servers:
        console.print("[yellow]⚠️  未找到任何伺服器[/yellow]")
        console.print("[dim]提示: 請先創建伺服器實例[/dim]")
        return None
    
    if len(servers) == 1:
        console.print(f"[cyan]自動選擇伺服器: {servers[0]}[/cyan]")
        return servers[0]
    
    console.print("[bold]請選擇伺服器:[/bold]")
    for i, server in enumerate(servers, 1):
        console.print(f"  {i}. {server}")
    console.print()
    
    choice = Prompt.ask(
        "請輸入編號",
        choices=[str(i) for i in range(1, len(servers) + 1)],
        default="1"
    )
    
    return servers[int(choice) - 1]


def run_command(command: str):
    """執行命令"""
    import subprocess
    try:
        # 使用 subprocess 執行命令
        result = subprocess.run(
            f"python -m app.main {command}",
            shell=True,
            cwd=Path.cwd(),
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        console.print(f"[red]執行失敗: {e}[/red]")
        return False


def handle_main_menu():
    """處理主選單選擇"""
    while True:
        show_main_menu()
        choice = Prompt.ask("請選擇功能", choices=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "c", "C"], default="1")
        
        console.print()
        
        if choice == "0":
            console.print("[yellow]再見！👋[/yellow]")
            return False
        
        elif choice == "1":
            # 查看所有伺服器
            run_command("scan")
            console.print()
            Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "2":
            # 啟動伺服器
            server = select_server()
            if server:
                console.print()
                attach = Confirm.ask("是否附加到終端（顯示即時日誌）", default=False)
                attach_flag = "--attach" if attach else ""
                run_command(f"start {server} {attach_flag}")
                if not attach:
                    console.print()
                    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "3":
            # 停止伺服器
            server = select_server()
            if server:
                console.print()
                if Confirm.ask(f"確定要停止伺服器 {server} 嗎？", default=True):
                    run_command(f"stop {server}")
                    console.print()
                    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "4":
            # 重啟伺服器
            server = select_server()
            if server:
                console.print()
                if Confirm.ask(f"確定要重啟伺服器 {server} 嗎？", default=True):
                    run_command(f"restart {server}")
                    console.print()
                    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "5":
            # 查看狀態
            server = select_server()
            if server:
                console.print()
                run_command(f"status {server}")
                console.print()
                Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "6":
            # 查看日誌
            server = select_server()
            if server:
                console.print()
                follow = Confirm.ask("是否跟隨即時日誌", default=True)
                follow_flag = "--follow" if follow else ""
                run_command(f"logs {server} {follow_flag}")
                if not follow:
                    console.print()
                    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "7":
            # RCON 控制台
            server = select_server()
            if server:
                console.print()
                console.print("[cyan]進入 RCON 控制台...[/cyan]")
                console.print("[dim]輸入 'exit' 或 'quit' 離開控制台[/dim]")
                console.print()
                run_command(f"console {server}")
                console.print()
                Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "8":
            # 管理工具
            handle_tools_menu()
        
        elif choice == "9":
            # 系統資訊
            run_command("info")
            console.print()
            Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice.lower() == "c":
            # 系統診斷
            run_command("check")
            console.print()
            Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        console.print()


def handle_tools_menu():
    """處理工具選單"""
    while True:
        show_tools_menu()
        choice = Prompt.ask("請選擇工具", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")
        
        console.print()
        
        if choice == "0":
            return
        
        elif choice == "1":
            handle_tunnel_menu()
        
        elif choice == "2":
            handle_dns_menu()
        
        elif choice == "3":
            handle_java_menu()
        
        elif choice == "4":
            handle_backup_menu()
        
        elif choice == "5":
            server = select_server()
            if server:
                console.print()
                run_command(f"diagnose {server}")
                console.print()
                Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")
        
        elif choice == "6":
            # 清理孤立 PID
            server = select_server()
            if server:
                console.print()
                console.print("[yellow]此操作將清理孤立的 PID 文件（進程已死但文件還在）[/yellow]")
                if Confirm.ask(f"確定要清理伺服器 {server} 的 PID 文件嗎？", default=True):
                    run_command(f"cleanup {server}")
                    console.print()
                    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")


def handle_tunnel_menu():
    """處理隧道選單"""
    while True:
        show_tunnel_menu()
        choice = Prompt.ask("請選擇操作", choices=["0", "1", "2", "3", "4", "5"], default="0")
        
        console.print()
        
        if choice == "0":
            return
        
        server = select_server()
        if not server:
            continue
        
        console.print()
        
        if choice == "1":
            run_command(f"tunnel status {server}")
        elif choice == "2":
            run_command(f"tunnel start {server}")
        elif choice == "3":
            run_command(f"tunnel stop {server}")
        elif choice == "4":
            run_command(f"tunnel cleanup {server}")
        elif choice == "5":
            run_command(f"tunnel diagnose {server}")
        
        console.print()
        Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")


def handle_dns_menu():
    """處理 DNS 選單"""
    while True:
        show_dns_menu()
        choice = Prompt.ask("請選擇操作", choices=["0", "1", "2", "3", "4"], default="0")
        
        console.print()
        
        if choice == "0":
            return
        
        server = select_server()
        if not server:
            continue
        
        console.print()
        
        if choice == "1":
            run_command(f"dns status {server}")
        elif choice == "2":
            run_command(f"dns update {server}")
        elif choice == "3":
            run_command(f"dns test {server}")
        elif choice == "4":
            run_command(f"dns diagnose {server}")
        
        console.print()
        Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")


def handle_java_menu():
    """處理 Java 選單"""
    console.print("[bold cyan]Java 管理[/bold cyan]\n")
    console.print("1. 列出所有 Java Profile")
    console.print("2. 掃描系統中的 Java")
    console.print("3. 驗證 Java 配置")
    console.print("0. 返回")
    console.print()
    
    choice = Prompt.ask("請選擇操作", choices=["0", "1", "2", "3"], default="0")
    
    console.print()
    
    if choice == "0":
        return
    elif choice == "1":
        run_command("java list")
    elif choice == "2":
        run_command("java scan")
    elif choice == "3":
        run_command("java validate")
    
    console.print()
    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")


def handle_backup_menu():
    """處理備份選單"""
    console.print("[bold cyan]備份管理[/bold cyan]\n")
    console.print("1. 創建備份")
    console.print("2. 列出備份")
    console.print("3. 還原備份")
    console.print("0. 返回")
    console.print()
    
    choice = Prompt.ask("請選擇操作", choices=["0", "1", "2", "3"], default="0")
    
    console.print()
    
    if choice == "0":
        return
    
    server = select_server()
    if not server:
        return
    
    console.print()
    
    if choice == "1":
        run_command(f"backup {server}")
    elif choice == "2":
        console.print(f"[yellow]查看備份: servers/{server}/backups/[/yellow]")
    elif choice == "3":
        console.print("[yellow]還原備份功能開發中...[/yellow]")
    
    console.print()
    Prompt.ask("[dim]按 Enter 繼續[/dim]", default="")


def run_interactive():
    """運行互動式介面"""
    try:
        show_welcome()
        handle_main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]操作已取消[/yellow]")
        return
    except Exception as e:
        console.print(f"\n[red]發生錯誤: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_interactive()
