"""
首次運行初始化器

負責在首次運行時創建必要的目錄結構、配置文件和說明文檔
"""

from pathlib import Path
from typing import Optional
import shutil
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


class FrameworkInitializer:
    """框架初始化器"""
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化器
        
        Args:
            base_path: 框架根目錄（預設為當前目錄）
        """
        self.base_path = base_path or Path.cwd()
        self.config_path = self.base_path / "config"
        self.servers_path = self.base_path / "servers"
        self.logs_path = self.base_path / "logs"
        self.templates_path = self.base_path / "templates"
    
    def is_initialized(self) -> bool:
        """
        檢查框架是否已初始化
        
        Returns:
            是否已初始化
        """
        # 檢查關鍵目錄和文件是否存在
        required_items = [
            self.config_path / "app.yml",
            self.config_path / "java_registry.yml",
            self.servers_path,
            self.logs_path
        ]
        
        return all(item.exists() for item in required_items)
    
    def initialize(self, force: bool = False) -> bool:
        """
        執行初始化
        
        Args:
            force: 是否強制重新初始化
            
        Returns:
            是否成功
        """
        if self.is_initialized() and not force:
            console.print("[yellow]框架已初始化[/yellow]")
            return True
        
        console.print(Panel(
            "[bold cyan]MC Server Framework - 首次運行初始化[/bold cyan]\n\n"
            "正在創建必要的目錄結構和配置文件...",
            title="🎮 歡迎",
            border_style="cyan"
        ))
        
        try:
            # 創建目錄結構
            self._create_directories()
            
            # 創建配置文件
            self._create_config_files()
            
            # 創建說明文檔
            self._create_documentation()
            
            # 顯示完成訊息
            self._show_completion_message()
            
            return True
            
        except Exception as e:
            console.print(f"[red]初始化失敗: {e}[/red]")
            return False
    
    def _create_directories(self):
        """創建必要的目錄結構"""
        directories = [
            self.servers_path,
            self.config_path,
            self.logs_path,
            self.templates_path,
            self.base_path / "runtime"
        ]
        
        for directory in directories:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                console.print(f"[green]✓[/green] 創建目錄: {directory.relative_to(self.base_path)}")
            else:
                console.print(f"[dim]○[/dim] 目錄已存在: {directory.relative_to(self.base_path)}")
    
    def _create_config_files(self):
        """創建配置文件模板"""
        # app.yml
        app_yml_path = self.config_path / "app.yml"
        if not app_yml_path.exists():
            app_yml_content = self._get_app_yml_template()
            with open(app_yml_path, 'w', encoding='utf-8') as f:
                f.write(app_yml_content)
            console.print(f"[green]✓[/green] 創建配置: {app_yml_path.relative_to(self.base_path)}")
        else:
            console.print(f"[dim]○[/dim] 配置已存在: {app_yml_path.relative_to(self.base_path)}")
        
        # java_registry.yml
        java_yml_path = self.config_path / "java_registry.yml"
        if not java_yml_path.exists():
            java_yml_content = self._get_java_registry_template()
            with open(java_yml_path, 'w', encoding='utf-8') as f:
                f.write(java_yml_content)
            console.print(f"[green]✓[/green] 創建配置: {java_yml_path.relative_to(self.base_path)}")
        else:
            console.print(f"[dim]○[/dim] 配置已存在: {java_yml_path.relative_to(self.base_path)}")
        
        # default_server.yml 模板
        server_template_path = self.templates_path / "default_server.yml"
        if not server_template_path.exists():
            server_template_content = self._get_server_template()
            with open(server_template_path, 'w', encoding='utf-8') as f:
                f.write(server_template_content)
            console.print(f"[green]✓[/green] 創建模板: {server_template_path.relative_to(self.base_path)}")
        else:
            console.print(f"[dim]○[/dim] 模板已存在: {server_template_path.relative_to(self.base_path)}")
    
    def _create_documentation(self):
        """創建說明文檔"""
        getting_started_path = self.base_path / "GETTING_STARTED.txt"
        if not getting_started_path.exists():
            doc_content = self._get_getting_started_content()
            with open(getting_started_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            console.print(f"[green]✓[/green] 創建文檔: {getting_started_path.relative_to(self.base_path)}")
        else:
            console.print(f"[dim]○[/dim] 文檔已存在: {getting_started_path.relative_to(self.base_path)}")
        
        # 創建伺服器範例說明
        servers_readme = self.servers_path / "README.txt"
        if not servers_readme.exists():
            readme_content = self._get_servers_readme_content()
            with open(servers_readme, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            console.print(f"[green]✓[/green] 創建說明: {servers_readme.relative_to(self.base_path)}")
    
    def _show_completion_message(self):
        """顯示初始化完成訊息"""
        console.print()
        console.print(Panel(
            "[bold green]✓ 初始化完成！[/bold green]\n\n"
            "目錄結構已建立，配置文件已創建。\n\n"
            "[cyan]下一步:[/cyan]\n"
            "1. 閱讀 [bold]GETTING_STARTED.txt[/bold] 了解如何使用\n"
            "2. 配置 [bold]config/app.yml[/bold] 中的全域設定\n"
            "3. 註冊 Java 版本到 [bold]config/java_registry.yml[/bold]\n"
            "4. 在 [bold]servers/[/bold] 目錄下放置您的伺服器\n\n"
            "[dim]執行 [bold]python -m app.main info[/bold] 查看詳細說明[/dim]",
            title="🎉 完成",
            border_style="green"
        ))
    
    def _get_app_yml_template(self) -> str:
        """獲取 app.yml 模板內容"""
        return """# MC Server Framework - 全域配置文件
# 此文件包含框架的全局設定，可被個別伺服器配置覆寫

app:
  name: "MC Server Framework"
  version: "0.2.0"

# 伺服器目錄設定
servers:
  root: "servers"  # 伺服器實例存放目錄

# DNS 全域設定
dns:
  enabled: true
  check_interval: 300  # 秒，檢查 IP 變更的間隔
  ip_check_service: "https://api.ipify.org"
  
  # Cloudflare 全域設定
  # 如果您有多個伺服器使用同一組憑證，可在此統一設定
  cloudflare:
    api_token: ""  # 您的 Cloudflare API Token
    zone_id: ""    # 您的 Zone ID
  
  # DuckDNS 全域設定
  duckdns:
    token: ""  # 您的 DuckDNS Token

# 備份全域設定
backup:
  default_retention_days: 14
  default_keep_last: 10
  default_compression: "zip"

# 隧道服務設定（PlayIt.gg 等）
tunnel:
  # PlayIt.gg Agent 路徑
  # 下載地址: https://playit.gg/download
  playit:
    executable_path: ""  # 例如: "C:\\Program Files\\playit_gg\\bin\\playit.exe"
    # 或使用相對路徑: "bin/playit.exe"
  
  # 其他隧道服務（未來支援）
  ngrok:
    executable_path: ""
  cloudflared:
    executable_path: ""

# 日誌設定
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/mc-host-manager.log"
  max_size: 10485760  # 10MB
  backup_count: 5
"""
    
    def _get_java_registry_template(self) -> str:
        """獲取 java_registry.yml 模板內容"""
        return """# Java 版本註冊表
# 在此註冊您系統中的 Java 安裝路徑，供伺服器使用

profiles:
  # Java 8 - 適用於 Minecraft 1.7 - 1.16
  # java8:
  #   version: "1.8"
  #   path: "C:\\Program Files\\Java\\jdk1.8.0_XXX\\bin\\java.exe"
  #   min_mc_version: "1.7"
  #   max_mc_version: "1.16"
  
  # Java 17 - 適用於 Minecraft 1.17 - 1.20.4
  # java17:
  #   version: "17"
  #   path: "C:\\Program Files\\Java\\jdk-17\\bin\\java.exe"
  #   min_mc_version: "1.17"
  #   max_mc_version: "1.20.4"
  
  # Java 21 - 適用於 Minecraft 1.20.5+
  # java21:
  #   version: "21"
  #   path: "C:\\Program Files\\Java\\jdk-21\\bin\\java.exe"
  #   min_mc_version: "1.20.5"
  #   max_mc_version: null

# 如何查找 Java 路徑:
# Windows: 在命令提示字元執行 'where java'
# Linux/Mac: 在終端執行 'which java'
#
# 如何驗證配置:
# 執行: python -m app.main java list
# 執行: python -m app.main java validate --profile <profile_name>
"""
    
    def _get_server_template(self) -> str:
        """獲取伺服器配置模板"""
        return """# Minecraft Server 配置文件
# 複製此文件到您的伺服器目錄並重命名為 server.yml

meta:
  name: "my-server"  # 伺服器識別名稱（英文、數字、連字符）
  display_name: "My Minecraft Server"  # 顯示名稱
  description: "我的 Minecraft 伺服器"

server:
  root_dir: "server"  # 伺服器文件根目錄（相對於此配置文件）
  startup_target: "server.jar"  # 啟動 JAR 文件
  type: "minecraft-java"
  loader: "auto"  # 自動檢測 | vanilla | paper | purpur | spigot | forge | fabric | neoforge
  working_dir: "server"  # 工作目錄

java:
  mode: "profile"  # profile（使用註冊表） | auto（自動偵測） | custom（自訂路徑）
  profile: "java21"  # 使用的 Java profile（需在 java_registry.yml 中註冊）
  # custom_path: "C:/custom/java/bin/java.exe"  # mode=custom 時使用

launch:
  min_memory: "2G"  # 最小記憶體
  max_memory: "6G"  # 最大記憶體
  jvm_args: []  # JVM 額外參數
  server_args:
    - "nogui"  # 伺服器參數
  stop_command: "stop"  # 停止指令

# RCON 遠端控制台設定
rcon:
  enabled: false  # 設為 true 啟用 RCON
  host: "localhost"
  port: 25575
  password: ""  # RCON 密碼（需與 server.properties 中的相同）

# DNS 動態更新設定
dns:
  enabled: false  # 設為 true 以啟用 DNS 自動更新
  mode: "cloudflare"  # cloudflare | duckdns
  domain: "mc.yourdomain.com"  # 您的網域
  server_port: 25565  # Minecraft 端口
  update_interval: 300  # 更新間隔（秒）
  
  srv_record:
    enabled: true  # SRV 記錄（讓玩家無需輸入端口）
    priority: 0
    weight: 5
    port: 25565
  
  config:
    # Cloudflare（會使用 app.yml 中的全域設定，也可在此覆寫）
    api_token: ""
    zone_id: ""

# PlayIt.gg 隧道設定（用於穿透 CGNAT）
tunnel:
  enabled: false  # 設為 true 啟用隧道
  type: "playit"  # playit | ngrok | cloudflared
  executable_path: ""  # PlayIt agent 路徑（留空則使用 app.yml 中的設定）
  auto_start: true  # 隨伺服器自動啟動/停止

# 備份設定
backup:
  enabled: true
  mode: "manual"  # manual | scheduled
  provider: "internal"
  retention:
    keep_last: 10
    keep_days: 14
  compression: "zip"
  
  # 備份包含的文件
  include:
    - "world*"
    - "server.properties"
    - "ops.json"
    - "whitelist.json"
  
  # 備份排除的文件
  exclude:
    - "logs/**"
    - "crash-reports/**"
    - "libraries/**"
  
  # 備份前後執行的指令
  hooks:
    before_backup:
      - "save-off"
      - "save-all"
    after_backup:
      - "save-on"

features:
  allow_internal_backup: true
  allow_auto_restart: false
  allow_monitoring: true
"""
    
    def _get_getting_started_content(self) -> str:
        """獲取入門指南內容"""
        return """
================================================================================
          MC Server Framework - 快速入門指南
================================================================================

歡迎使用 MC Server Framework！這份指南將幫助您快速上手。

--------------------------------------------------------------------------------
📁 目錄結構說明
--------------------------------------------------------------------------------

MC-Server-Framework/
├── servers/              ← 伺服器實例存放目錄
│   ├── my-server-1/      ← 單一伺服器實例
│   │   ├── server.yml    ← 伺服器配置文件（必需）
│   │   ├── server/       ← 伺服器文件目錄
│   │   │   ├── server.jar
│   │   │   ├── server.properties
│   │   │   ├── world/
│   │   │   └── ...
│   │   ├── logs/         ← 伺服器日誌
│   │   └── runtime/      ← 運行時文件（PID 等）
│   └── my-server-2/
│       └── ...
│
├── config/               ← 全域配置目錄
│   ├── app.yml           ← 框架全域設定
│   └── java_registry.yml ← Java 版本註冊表
│
├── templates/            ← 配置模板
│   └── default_server.yml ← 伺服器配置模板
│
└── logs/                 ← 框架日誌

--------------------------------------------------------------------------------
🚀 快速開始（5 分鐘設置）
--------------------------------------------------------------------------------

步驟 1: 註冊 Java 版本
------------------------
編輯 config/java_registry.yml，添加您系統中的 Java 安裝路徑：

profiles:
  java21:
    version: "21"
    path: "C:\\Program Files\\Java\\jdk-21\\bin\\java.exe"

💡 如何找到 Java 路徑？
   Windows: 在 CMD 執行 'where java'
   Linux/Mac: 在終端執行 'which java'

✅ 驗證配置:
   python -m app.main java list


步驟 2: 創建您的第一個伺服器
----------------------------
方式 A - 使用現有伺服器:
1. 在 servers/ 下創建目錄，例如: servers/survival/
2. 複製您的伺服器文件到 servers/survival/server/
3. 複製 templates/default_server.yml 到 servers/survival/server.yml
4. 編輯 server.yml，設定伺服器資訊

方式 B - 從零開始:
1. 下載 Minecraft 伺服器 JAR（例如 Paper、Purpur、Vanilla）
2. 在 servers/ 下創建目錄並放置 JAR
3. 創建 server.yml 配置文件
4. 首次啟動時會自動生成必要文件


步驟 3: 配置並啟動伺服器
------------------------
編輯 servers/<伺服器名稱>/server.yml：

meta:
  name: "survival"        # 伺服器 ID
  display_name: "生存服務器"

java:
  profile: "java21"       # 使用註冊的 Java

launch:
  min_memory: "2G"
  max_memory: "6G"

✅ 掃描並啟動:
   python -m app.main scan      # 查看所有伺服器
   python -m app.main start survival


步驟 4: 查看狀態和管理
----------------------
python -m app.main status survival   # 查看伺服器狀態
python -m app.main logs survival     # 查看日誌
python -m app.main stop survival     # 停止伺服器

--------------------------------------------------------------------------------
🔧 進階功能配置
--------------------------------------------------------------------------------

1. RCON 遠端控制台
------------------
在 server.yml 中啟用 RCON：

rcon:
  enabled: true
  port: 25575
  password: "your-secure-password"

並在 server/server.properties 中設定相同密碼：
enable-rcon=true
rcon.port=25575
rcon.password=your-secure-password

✅ 使用 RCON:
   python -m app.main console survival          # 互動式控制台
   python -m app.main send survival "say Hi"    # 發送單一指令


2. Cloudflare DNS 自動更新
---------------------------
適用於家用網路（動態 IP），讓玩家通過固定網域連接。

A. 準備工作:
   - Cloudflare 帳號（免費）
   - 一個網域（可在 Cloudflare 或其他註冊商購買）
   - API Token（Cloudflare 控制台 → 我的個人資料 → API Tokens）

B. 全域設定（config/app.yml）:
   dns:
     cloudflare:
       api_token: "YOUR_API_TOKEN"
       zone_id: "YOUR_ZONE_ID"

C. 伺服器設定（server.yml）:
   dns:
     enabled: true
     mode: "cloudflare"
     domain: "mc.yourdomain.com"
     server_port: 25565
     srv_record:
       enabled: true  # 讓玩家只需輸入網域，不需端口

✅ 更新 DNS:
   python -m app.main dns update survival
   python -m app.main dns status survival


3. PlayIt.gg 隧道（穿透 CGNAT）
--------------------------------
如果您的網路有 CGNAT（無法端口轉發），PlayIt.gg 可以幫您穿透。

A. 下載 PlayIt Agent:
   訪問: https://playit.gg/download
   下載適合您系統的版本並安裝

B. 配置（config/app.yml）:
   tunnel:
     playit:
       executable_path: "C:\\Program Files\\playit_gg\\bin\\playit.exe"

C. 伺服器設定（server.yml）:
   tunnel:
     enabled: true
     type: "playit"
     auto_start: true  # 隨伺服器自動啟動

D. 首次設置:
   1. 手動啟動 PlayIt（執行 playit.exe）
   2. 登入您的 PlayIt 帳號並設定隧道
   3. 添加 Minecraft TCP 隧道，端口 25565
   4. 記住分配給您的網域（例如 xxx.gl.joinmc.link）

E. 整合 DNS（進階）:
   在 Cloudflare 中設定 CNAME 記錄：
   mc.yourdomain.com -> xxx.gl.joinmc.link

✅ 管理隧道:
   python -m app.main tunnel status survival
   python -m app.main tunnel start survival
   python -m app.main tunnel stop survival


4. 自動備份
-----------
server.yml 中配置備份策略：

backup:
  enabled: true
  retention:
    keep_last: 10     # 保留最近 10 份備份
    keep_days: 14     # 保留 14 天內的備份
  include:
    - "world*"        # 包含所有世界
    - "server.properties"
  exclude:
    - "logs/**"       # 排除日誌
    - "libraries/**"  # 排除庫文件

✅ 創建備份:
   python -m app.main backup create survival
   python -m app.main backup list survival

--------------------------------------------------------------------------------
📚 常用指令速查
--------------------------------------------------------------------------------

伺服器管理:
  python -m app.main                    # 互動式選單
  python -m app.main scan               # 掃描所有伺服器
  python -m app.main start <server>     # 啟動伺服器
  python -m app.main stop <server>      # 停止伺服器
  python -m app.main restart <server>   # 重啟伺服器
  python -m app.main status <server>    # 查看狀態
  python -m app.main logs <server>      # 查看日誌

RCON 控制台:
  python -m app.main console <server>   # 進入互動式控制台
  python -m app.main send <server> "<cmd>"  # 發送指令

DNS 管理:
  python -m app.main dns update <server>    # 更新 DNS
  python -m app.main dns status <server>    # DNS 狀態

隧道管理:
  python -m app.main tunnel start <server>  # 啟動隧道
  python -m app.main tunnel stop <server>   # 停止隧道
  python -m app.main tunnel status <server> # 隧道狀態

Java 管理:
  python -m app.main java list              # 列出所有 Java
  python -m app.main java validate <profile> # 驗證 Java

系統工具:
  python -m app.main info                   # 系統資訊和說明
  python -m app.main check                  # 系統診斷
  python -m app.main cleanup <server>       # 清理孤立 PID
  python -m app.main diagnose <server>      # 網路診斷

--------------------------------------------------------------------------------
❓ 常見問題排查
--------------------------------------------------------------------------------

Q: 啟動伺服器失敗，提示找不到 Java
A: 1. 執行 'python -m app.main java list' 檢查 Java 是否註冊
   2. 執行 'python -m app.main java validate <profile>' 驗證路徑
   3. 檢查 server.yml 中的 java.profile 是否正確

Q: 伺服器顯示運行中但實際沒有進程
A: 執行 'python -m app.main cleanup <server>' 清理孤立的 PID 文件

Q: DNS 更新失敗
A: 1. 檢查 API Token 是否正確
   2. 檢查 Zone ID 是否正確
   3. 執行 'python -m app.main diagnose <server>' 進行網路診斷

Q: PlayIt 隧道無法啟動
A: 1. 確認 PlayIt agent 已下載並安裝
   2. 檢查 config/app.yml 中的 executable_path 是否正確
   3. 首次使用需先手動啟動 PlayIt 完成登入設定

Q: 移植到新電腦後無法運行
A: 執行 'python -m app.main check' 進行系統診斷，根據提示修復問題

--------------------------------------------------------------------------------
📞 更多幫助
--------------------------------------------------------------------------------

詳細文檔: 執行 'python -m app.main info' 查看完整說明
系統診斷: 執行 'python -m app.main check' 檢查配置
互動模式: 執行 'python -m app.main' 進入選單式操作

GitHub: https://github.com/Unforgettableeternalproject/MC-Server-Framework

祝您使用愉快！🎮

================================================================================
"""
    
    def _get_servers_readme_content(self) -> str:
        """獲取 servers 目錄說明內容"""
        return """
================================================================================
                    伺服器實例存放目錄
================================================================================

此目錄用於存放所有 Minecraft 伺服器實例。

--------------------------------------------------------------------------------
📂 如何添加伺服器
--------------------------------------------------------------------------------

每個伺服器需要遵循以下結構：

servers/
└── <伺服器名稱>/          ← 伺服器根目錄（名稱自訂）
    ├── server.yml         ← 配置文件（必需）
    ├── server/            ← 伺服器文件目錄（可自訂名稱）
    │   ├── server.jar     ← Minecraft 伺服器 JAR
    │   ├── server.properties
    │   ├── world/
    │   ├── world_nether/
    │   ├── world_the_end/
    │   └── ...
    ├── logs/              ← 日誌（自動創建）
    └── runtime/           ← 運行時文件（自動創建）

--------------------------------------------------------------------------------
🎯 範例 1: 添加新伺服器
--------------------------------------------------------------------------------

1. 創建伺服器目錄:
   servers/survival/

2. 創建 server.yml:
   複製 ../templates/default_server.yml 到此處並重命名

3. 放置伺服器文件:
   下載 Paper/Purpur/Vanilla JAR，放到 servers/survival/server/

4. 編輯 server.yml:
   設定名稱、Java 版本、記憶體等

5. 掃描並啟動:
   python -m app.main scan
   python -m app.main start survival

--------------------------------------------------------------------------------
🎯 範例 2: 導入現有伺服器
--------------------------------------------------------------------------------

如果您已經有一個正在運行的伺服器：

1. 將整個伺服器目錄複製到 servers/ 下:
   servers/my-old-server/
       └── <您的伺服器文件>

2. 創建 server.yml 配置文件:
   複製模板並根據實際情況配置

3. 調整 server.yml 中的路徑:
   server:
     root_dir: "."        # 如果文件在當前目錄
     startup_target: "paper.jar"  # JAR 文件名

--------------------------------------------------------------------------------
✅ 驗證配置
--------------------------------------------------------------------------------

添加伺服器後，執行以下指令驗證：

python -m app.main scan                # 應該能看到您的伺服器
python -m app.main status <server>     # 檢查狀態
python -m app.main check               # 系統診斷

--------------------------------------------------------------------------------
📋 注意事項
--------------------------------------------------------------------------------

1. 每個伺服器目錄必須包含 server.yml 配置文件
2. 伺服器名稱（meta.name）必須唯一
3. 確保 Java 版本與 Minecraft 版本相容
4. 首次啟動前需同意 EULA（eula.txt）

有問題？執行 'python -m app.main info' 查看完整文檔。

================================================================================
"""


def run_initialization(force: bool = False) -> bool:
    """
    運行初始化流程
    
    Args:
        force: 是否強制重新初始化
        
    Returns:
        是否成功
    """
    initializer = FrameworkInitializer()
    return initializer.initialize(force=force)


def check_initialization() -> bool:
    """
    檢查框架是否已初始化
    
    Returns:
        是否已初始化
    """
    initializer = FrameworkInitializer()
    return initializer.is_initialized()
