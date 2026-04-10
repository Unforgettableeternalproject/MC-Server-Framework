"""
系統診斷工具
檢查框架運行所需的所有條件
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from pathlib import Path
import sys
import subprocess
import platform

console = Console()


def check_python_version():
    """檢查 Python 版本"""
    version = sys.version_info
    required_major = 3
    required_minor = 8
    
    status = version.major >= required_major and version.minor >= required_minor
    
    return {
        'name': 'Python 版本',
        'status': status,
        'value': f"{version.major}.{version.minor}.{version.micro}",
        'required': f">= {required_major}.{required_minor}",
        'details': f"當前版本: {sys.version}"
    }


def check_dependencies():
    """檢查 Python 依賴套件"""
    dependencies = [
        'typer',
        'rich',
        'PyYAML',
        'requests',
        'psutil'
    ]
    
    results = []
    all_installed = True
    
    for dep in dependencies:
        try:
            __import__(dep.lower().replace('-', '_'))
            results.append({'name': dep, 'status': True, 'version': 'Installed'})
        except ImportError:
            results.append({'name': dep, 'status': False, 'version': 'Missing'})
            all_installed = False
    
    return {
        'name': 'Python 依賴套件',
        'status': all_installed,
        'items': results
    }


def check_directory_structure():
    """檢查目錄結構"""
    required_dirs = {
        'servers': '伺服器實例目錄',
        'config': '配置文件目錄',
        'logs': '日誌目錄',
        'app': '應用程序目錄'
    }
    
    results = []
    all_exist = True
    
    for dir_name, desc in required_dirs.items():
        path = Path(dir_name)
        exists = path.exists() and path.is_dir()
        results.append({
            'name': dir_name,
            'desc': desc,
            'status': exists,
            'path': str(path.absolute())
        })
        if not exists:
            all_exist = False
    
    return {
        'name': '目錄結構',
        'status': all_exist,
        'items': results
    }


def check_config_files():
    """檢查配置文件"""
    config_files = {
        'config/app.yml': '全局配置',
        'config/java_registry.yml': 'Java 配置'
    }
    
    results = []
    all_exist = True
    
    for file_path, desc in config_files.items():
        path = Path(file_path)
        exists = path.exists() and path.is_file()
        
        # 檢查文件內容
        valid = False
        error = None
        if exists:
            try:
                import yaml
                with open(path, 'r', encoding='utf-8') as f:
                    yaml.safe_load(f)
                valid = True
            except Exception as e:
                error = str(e)
        
        results.append({
            'name': file_path,
            'desc': desc,
            'status': exists and valid,
            'exists': exists,
            'valid': valid,
            'error': error
        })
        
        if not (exists and valid):
            all_exist = False
    
    return {
        'name': '配置文件',
        'status': all_exist,
        'items': results
    }


def check_java_installation():
    """檢查 Java 安裝"""
    try:
        # 讀取 java_registry.yml
        import yaml
        java_registry = Path('config/java_registry.yml')
        
        if not java_registry.exists():
            return {
                'name': 'Java 配置',
                'status': False,
                'error': 'java_registry.yml 不存在'
            }
        
        with open(java_registry, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        profiles = config.get('profiles', {})
        results = []
        
        for profile_name, profile_data in profiles.items():
            java_path = profile_data.get('java_home')
            if java_path:
                java_exe = Path(java_path) / 'bin' / 'java.exe'
                exists = java_exe.exists()
                
                version = None
                if exists:
                    try:
                        result = subprocess.run(
                            [str(java_exe), '-version'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        version = result.stderr.split('\n')[0] if result.stderr else 'Unknown'
                    except:
                        version = 'Unable to get version'
                
                results.append({
                    'profile': profile_name,
                    'path': java_path,
                    'status': exists,
                    'version': version
                })
        
        all_valid = all(r['status'] for r in results)
        
        return {
            'name': 'Java 配置',
            'status': all_valid and len(results) > 0,
            'items': results
        }
    
    except Exception as e:
        return {
            'name': 'Java 配置',
            'status': False,
            'error': str(e)
        }


def check_servers():
    """檢查伺服器實例"""
    servers_dir = Path('servers')
    
    if not servers_dir.exists():
        return {
            'name': '伺服器實例',
            'status': False,
            'error': 'servers 目錄不存在'
        }
    
    # 掃描伺服器
    results = []
    for server_dir in servers_dir.iterdir():
        if not server_dir.is_dir():
            continue
        
        server_yml = server_dir / 'server.yml'
        server_folder = server_dir / 'server'
        
        issues = []
        
        # 檢查 server.yml
        if not server_yml.exists():
            issues.append('缺少 server.yml')
        else:
            try:
                import yaml
                with open(server_yml, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    
                # 檢查必要字段
                if 'meta' not in config:
                    issues.append('server.yml 缺少 meta 區段')
                if 'server' not in config:
                    issues.append('server.yml 缺少 server 區段')
            except Exception as e:
                issues.append(f'server.yml 格式錯誤: {e}')
        
        # 檢查 server 目錄
        if not server_folder.exists():
            issues.append('缺少 server 子目錄')
        
        results.append({
            'name': server_dir.name,
            'status': len(issues) == 0,
            'issues': issues,
            'path': str(server_dir.absolute())
        })
    
    return {
        'name': '伺服器實例',
        'status': len(results) > 0 and all(r['status'] for r in results),
        'items': results,
        'count': len(results)
    }


def check_tunnel_config():
    """檢查 PlayIt 隧道配置"""
    try:
        import yaml
        app_config = Path('config/app.yml')
        
        if not app_config.exists():
            return {
                'name': 'PlayIt 隧道配置',
                'status': False,
                'error': 'app.yml 不存在'
            }
        
        with open(app_config, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        tunnel_config = config.get('tunnel', {})
        playit_config = tunnel_config.get('playit', {})
        playit_path = playit_config.get('executable_path', '')
        
        if playit_path:
            path = Path(playit_path)
            exists = path.exists()
            
            return {
                'name': 'PlayIt 隧道配置',
                'status': exists,
                'path': playit_path,
                'exists': exists,
                'note': '已在 app.yml 配置' if exists else f'路徑不存在: {playit_path}'
            }
        else:
            return {
                'name': 'PlayIt 隧道配置',
                'status': True,
                'note': '未配置全局路徑（將使用相對路徑）'
            }
    
    except Exception as e:
        return {
            'name': 'PlayIt 隧道配置',
            'status': False,
            'error': str(e)
        }


def check_permissions():
    """檢查文件權限"""
    critical_paths = [
        Path('servers'),
        Path('config'),
        Path('logs')
    ]
    
    results = []
    all_ok = True
    
    for path in critical_paths:
        if not path.exists():
            continue
        
        try:
            # 嘗試創建測試文件
            test_file = path / '.write_test'
            test_file.write_text('test')
            test_file.unlink()
            writable = True
        except:
            writable = False
            all_ok = False
        
        results.append({
            'path': str(path),
            'writable': writable
        })
    
    return {
        'name': '文件權限',
        'status': all_ok,
        'items': results
    }


def run_diagnostics():
    """執行完整診斷"""
    console.print()
    console.print(Panel(
        "[bold cyan]系統診斷工具[/bold cyan]\n"
        "檢查框架運行所需的所有條件",
        border_style="cyan"
    ))
    console.print()
    
    # 系統信息
    console.print(f"[bold]系統信息:[/bold]")
    console.print(f"  作業系統: {platform.system()} {platform.release()}")
    console.print(f"  當前目錄: {Path.cwd()}")
    console.print()
    
    # 執行檢查
    checks = [
        check_python_version(),
        check_dependencies(),
        check_directory_structure(),
        check_config_files(),
        check_java_installation(),
        check_servers(),
        check_tunnel_config(),
        check_permissions()
    ]
    
    # 顯示結果
    tree = Tree("[bold]診斷結果[/bold]")
    
    issues_found = []
    
    for check in checks:
        status_icon = "✅" if check['status'] else "❌"
        status_color = "green" if check['status'] else "red"
        
        branch = tree.add(f"{status_icon} [{status_color}]{check['name']}[/{status_color}]")
        
        if 'value' in check:
            branch.add(f"值: {check['value']}")
            if 'required' in check:
                branch.add(f"要求: {check['required']}")
        
        if 'error' in check:
            branch.add(f"[red]錯誤: {check['error']}[/red]")
            issues_found.append(f"{check['name']}: {check['error']}")
        
        if 'items' in check:
            for item in check['items']:
                item_status = "✓" if item.get('status', True) else "✗"
                item_color = "green" if item.get('status', True) else "red"
                
                if 'profile' in item:
                    # Java profile
                    sub = branch.add(f"[{item_color}]{item_status} {item['profile']}[/{item_color}]")
                    sub.add(f"路徑: {item['path']}")
                    if item.get('version'):
                        sub.add(f"版本: {item['version']}")
                    if not item['status']:
                        issues_found.append(f"Java Profile '{item['profile']}' 路徑無效: {item['path']}")
                
                elif 'name' in item and 'desc' in item:
                    # Directory
                    sub = branch.add(f"[{item_color}]{item_status} {item['name']}[/{item_color}] - {item['desc']}")
                    if not item['status']:
                        issues_found.append(f"目錄缺失: {item['name']}")
                
                elif 'name' in item and 'version' in item:
                    # Dependency
                    sub = branch.add(f"[{item_color}]{item_status} {item['name']}[/{item_color}]")
                    if not item['status']:
                        issues_found.append(f"依賴缺失: {item['name']}")
                
                elif 'name' in item and 'issues' in item:
                    # Server instance
                    sub = branch.add(f"[{item_color}]{item_status} {item['name']}[/{item_color}]")
                    if item['issues']:
                        for issue in item['issues']:
                            sub.add(f"[yellow]• {issue}[/yellow]")
                            issues_found.append(f"伺服器 '{item['name']}': {issue}")
                
                else:
                    # Config files or other items
                    if 'desc' in item:
                        sub = branch.add(f"[{item_color}]{item_status} {item.get('name', 'Unknown')}[/{item_color}] - {item['desc']}")
                        if 'error' in item and item['error']:
                            sub.add(f"[red]錯誤: {item['error']}[/red]")
                            issues_found.append(f"{item['name']}: {item['error']}")
                    elif 'writable' in item:
                        # Permission check
                        perm_status = "可寫" if item['writable'] else "無法寫入"
                        perm_color = "green" if item['writable'] else "red"
                        sub = branch.add(f"[{perm_color}]{item['path']}: {perm_status}[/{perm_color}]")
                        if not item['writable']:
                            issues_found.append(f"權限不足: {item['path']}")
        
        if 'path' in check and 'exists' in check:
            if check['exists']:
                branch.add(f"[green]路徑: {check['path']}[/green]")
            else:
                branch.add(f"[red]路徑不存在: {check['path']}[/red]")
                issues_found.append(f"{check['name']}: 路徑不存在 {check['path']}")
        
        if 'note' in check:
            branch.add(f"[dim]{check['note']}[/dim]")
        
        if 'count' in check:
            branch.add(f"找到 {check['count']} 個實例")
    
    console.print(tree)
    console.print()
    
    # 總結
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c['status'])
    
    if passed_checks == total_checks:
        console.print(Panel(
            f"[bold green]✅ 所有檢查通過 ({passed_checks}/{total_checks})[/bold green]\n\n"
            "系統配置正確，可以正常運行",
            title="[bold green]診斷完成[/bold green]",
            border_style="green"
        ))
    else:
        console.print(Panel(
            f"[bold red]❌ 發現 {total_checks - passed_checks} 個問題 ({passed_checks}/{total_checks} 通過)[/bold red]\n\n"
            "[bold]發現的問題:[/bold]\n" + 
            "\n".join(f"  • {issue}" for issue in issues_found[:10]) +
            (f"\n  ... 還有 {len(issues_found) - 10} 個問題" if len(issues_found) > 10 else ""),
            title="[bold red]診斷完成[/bold red]",
            border_style="red"
        ))
    
    console.print()
    
    # 修復建議
    if not all(c['status'] for c in checks):
        console.print("[bold yellow]修復建議:[/bold yellow]\n")
        
        # Python 依賴
        dep_check = next((c for c in checks if c['name'] == 'Python 依賴套件'), None)
        if dep_check and not dep_check['status']:
            console.print("[cyan]1. 安裝缺失的依賴:[/cyan]")
            console.print("   pip install -r requirements.txt")
            console.print("   或")
            console.print("   pip install typer[all] rich PyYAML requests psutil")
            console.print()
        
        # Java 配置
        java_check = next((c for c in checks if c['name'] == 'Java 配置'), None)
        if java_check and not java_check['status']:
            console.print("[cyan]2. 修正 Java 配置:[/cyan]")
            console.print("   編輯 config/java_registry.yml")
            console.print("   確保 java_home 路徑指向正確的 Java 安裝目錄")
            console.print("   執行: python -m app.main java scan")
            console.print()
        
        # PlayIt 配置
        tunnel_check = next((c for c in checks if c['name'] == 'PlayIt 隧道配置'), None)
        if tunnel_check and not tunnel_check['status']:
            console.print("[cyan]3. 修正 PlayIt 配置:[/cyan]")
            console.print("   編輯 config/app.yml")
            console.print("   確保 tunnel.playit.executable_path 指向正確的 playit.exe 路徑")
            console.print()
        
        # 伺服器配置
        server_check = next((c for c in checks if c['name'] == '伺服器實例'), None)
        if server_check and not server_check['status']:
            console.print("[cyan]4. 修正伺服器配置:[/cyan]")
            console.print("   檢查 servers/<name>/server.yml 格式是否正確")
            console.print("   確保 servers/<name>/server/ 目錄存在")
            console.print()
    
    console.print()

