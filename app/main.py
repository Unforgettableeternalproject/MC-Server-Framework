"""
MC Server Framework - 主程式入口

Minecraft 本機伺服器宿主管理框架
"""

import sys
from pathlib import Path

# 確保可以匯入 app 模組
sys.path.insert(0, str(Path(__file__).parent))

from app.cli.commands import app
from app.core.initializer import check_initialization, run_initialization


def main():
    """主函式"""
    # 檢查框架是否已初始化
    if not check_initialization():
        # 首次運行，執行初始化
        success = run_initialization()
        if not success:
            print("初始化失敗，請檢查錯誤訊息")
            sys.exit(1)
        print()  # 空行
    
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
