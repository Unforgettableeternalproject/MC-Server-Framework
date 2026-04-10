"""
MC Server Framework - 主程式入口

Minecraft 本機伺服器宿主管理框架
"""

import sys
from pathlib import Path

# 確保可以匯入 app 模組
sys.path.insert(0, str(Path(__file__).parent))

from app.cli.commands import app


def main():
    """主函式"""
    # 確保必要目錄存在
    servers_dir = Path("servers")
    config_dir = Path("config")
    logs_dir = Path("logs")
    
    servers_dir.mkdir(exist_ok=True)
    config_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    # 檢查是否有命令行參數
    # sys.argv[0] 是腳本名稱，所以如果只有一個元素表示沒有參數
    if len(sys.argv) == 1:
        # 沒有參數，啟動互動式介面
        from app.cli.interactive import run_interactive
        run_interactive()
    else:
        # 有參數，使用標準 CLI
        app()


if __name__ == "__main__":
    main()
