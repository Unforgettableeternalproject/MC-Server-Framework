# Minecraft Local Server Host Manager — SPEC

## 1. 專案定位

本專案名稱暫定為 **Minecraft Local Server Host Manager**。

它是一個本機用的「Minecraft Java 伺服器宿主框架」，負責管理多個獨立伺服器實例，提供統一的資料夾規範、啟動流程、Java 版本切換、備份策略與未來擴充接口。

這個專案的定位不是 Minecraft 核心本身，也不是完整的遠端管理面板，而是位於本機上的 **宿主層（host layer）**。

---

## 2. 核心目標

系統需要滿足以下目標：

- 有一個總資料夾專門放所有伺服器實例
- 每個伺服器實例是一個獨立子資料夾
- 新增伺服器時，只要新增子資料夾並放入 `server.jar` 或伺服器包
- 系統可掃描、辨識、管理、啟動、停止、驗證與備份伺服器
- 每個伺服器可指定不同 Java 版本
- Minecraft 伺服器實際工作目錄需標準化
- 世界檔、模組、設定、logs、libraries、crash-reports 等需有統一接口
- 備份策略必須可配置，避免與整合包內建備份重複
- **支援網域名稱管理，讓玩家可透過固定網址連線**
- **自動更新動態 DNS，確保網域始終指向正確 IP**

---

## 3. 專案範圍

### 3.1 本專案負責的內容

- 掃描伺服器實例
- 讀取實例設定檔
- 選擇正確 Java profile
- 啟動 / 停止 / 重啟伺服器
- 驗證實例是否可啟動
- 管理宿主側 runtime 狀態
- 執行內建備份策略
- 提供統一的目錄與路徑接口
- **管理網域名稱與動態 DNS 更新**
- **整合 DNS 服務商 API（如 Cloudflare、DuckDNS 等）**
- **自動設定 Minecraft SRV 記錄**
- 預留未來 GUI / Web / RCON / 排程 / 更新器擴充能力

### 3.2 本專案不負責的內容

- 修改 Minecraft 核心程式
- 自動安裝所有 mod loader 與 modpack
- 深度解析所有 loader 的內部邏輯
- 幫使用者下載整合包內容
- **取代專業 DNS 服務商的完整功能（僅整合必要的更新介面）**
- 直接取代專業面板型管理系統

---

## 4. 分期開發目標

## Phase 1：核心可用版

目標：讓多個伺服器實例可以被穩定掃描、驗證、啟動、停止與備份，並能透過固定網域對外開放。

功能包含：

- 掃描 `servers/` 下所有子資料夾
- 找出可用伺服器實例
- 每個實例讀取 `server.yml`
- 根據設定選擇 Java
- 啟動與停止伺服器
- 顯示基本狀態與 log 輸出
- 執行基本備份
- 支援略過備份或標記為外部備份
- **管理伺服器的網域名稱與 DNS 設定**
- **自動更新動態 IP 到 DNS 服務商**
- **支援 Cloudflare、DuckDNS 等常見 DDNS 服務**

這一版的核心目標：

> 只要新增一個伺服器資料夾並補好設定檔，就能被系統管理，並從外網透過網域名稱連線。

---

## Phase 2：智能偵測與更完整接口

目標：讓使用者更接近「丟進去就能讀」的體驗。

功能包含：

- 自動偵測 `server.jar`
- 自動偵測常見 loader：
  - vanilla
  - paper
  - purpur
  - spigot
  - forge
  - fabric
  - neoforge
- 無設定檔時自動建立 `server.yml` 草稿
- EULA 狀態提示
- 自動偵測世界資料夾
- 自動偵測模組與設定目錄
- 支援 `pre-start` / `post-stop` / `backup` hooks

這一版的核心目標：

> 新增伺服器子資料夾並放入 jar 或整包內容後，系統能幫忙補齊大部分設定。

---

## Phase 3：進階管理版

目標：做成長期可使用的本機宿主平台。

功能包含：

- 更完整的 CLI
- 顯示世界列表與重要路徑
- 內建排程
- 備份保留策略
- 壓縮格式選擇
- Java registry 管理工具
- 可擴充的 loader adapter
- TUI 或簡易 Web UI

---

## 5. 建議技術選型

### 語言

- Python

### 原因

本專案本質偏向：

- 本機流程控制
- 檔案掃描
- 子程序管理
- 壓縮與備份
- 結構化 CLI 工具

Python 對這種用途非常直觀，也適合後續由 Copilot 協助生成與維護。

### 建議使用套件 / 標準庫

- CLI：`typer` 或 `argparse`
- 設定檔：`PyYAML`
- 子程序管理：`subprocess`
- 路徑管理：`pathlib`
- 備份壓縮：`zipfile` / `shutil.make_archive`
- 時間與檔案處理：標準庫即可

---

## 6. 專案結構建議

```text
mc-host-manager/
  app/
    __init__.py
    main.py
    cli/
      __init__.py
      commands.py
    core/
      scanner.py
      instance.py
      launcher.py
      java_resolver.py
      backup_manager.py
      log_manager.py
      package_detector.py
      path_resolver.py
    models/
      server_config.py
      java_profile.py
      backup_policy.py
      instance_status.py
    services/
      server_service.py
      backup_service.py
      java_service.py
    utils/
      fs.py
      process.py
      yaml_loader.py
      time_utils.py
      archive.py
  config/
    app.yml
    java_registry.yml
  servers/
    example-survival/
      server.yml
      runtime/
      backups/
      temp/
      server/
        server.jar
    example-modded/
      server.yml
      runtime/
      backups/
      temp/
      server/
        forge-installer.jar
  templates/
    default_server.yml
  docs/
    architecture.md
    server-structure.md
  tests/
```

---

## 7. 實例資料夾規範

每個伺服器 instance 使用以下標準結構：

```text
servers/
  my-server/
    server.yml
    server/
      server.jar
      eula.txt
      server.properties
      world/
      world_nether/
      world_the_end/
      logs/
      crash-reports/
      libraries/
      mods/
      config/
      defaultconfigs/
      kubejs/
      scripts/
    runtime/
      pid.txt
      last_start.json
      session.log
    backups/
    temp/
```

### 7.1 `server/`

Minecraft 真正的工作目錄。

啟動時的 `cwd` 必須設為這個資料夾。  
所有 Minecraft 原生輸出應自然落在這裡，例如：

- `world/`
- `logs/`
- `mods/`
- `config/`
- `libraries/`
- `crash-reports/`

### 7.2 `runtime/`

宿主框架自己的執行狀態資料夾，避免與 Minecraft 原生輸出混在一起。

用途包含：

- PID
- 啟動紀錄
- 狀態快照
- lock file
- 宿主管理日誌

### 7.3 `backups/`

每個實例自己的備份資料夾。

### 7.4 `temp/`

暫存用途，例如：

- 解壓縮
- 更新中介檔
- 暫存輸出

---

## 8. `server.yml` 設計

每個伺服器實例都應有 `server.yml` 作為主要設定介面。

範例：

```yaml
meta:
  name: "my-server"
  display_name: "My Survival Server"
  description: "Local survival world"

server:
  root_dir: "server"
  startup_target: "server.jar"
  type: "minecraft-java"
  loader: "auto"
  working_dir: "server"

java:
  mode: "profile"
  profile: "java21"

launch:
  min_memory: "2G"
  max_memory: "6G"
  jvm_args: []
  server_args:
    - "nogui"
  prelaunch_hooks: []
  postlaunch_hooks: []
  stop_command: "stop"

detection:
  auto_detect_loader: true
  auto_detect_worlds: true
  auto_detect_mods: true

world:
  mode: "auto"
  include:
    - "world*"
  exclude: []

backup:
  enabled: true
  mode: "manual"
  provider: "internal"
  schedule: null
  retention:
    keep_last: 10
    keep_days: 14
  compression: "zip"
  include:
    - "world*"
    - "server.properties"
    - "ops.json"
    - "whitelist.json"
    - "banned-players.json"
    - "banned-ips.json"
  exclude:
    - "logs/**"
    - "crash-reports/**"
    - "libraries/**"
    - "mods/**"
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

dns:
  enabled: true
  mode: "cloudflare"  # cloudflare, duckdns, custom, disabled
  domain: "mc.unforgettableeternalproject.net"
  update_interval: 300  # 秒，每 5 分鐘檢查一次
  srv_record:
    enabled: true
    priority: 0
    weight: 5
  config:
    # Cloudflare 設定
    api_token: "<YOUR_API_TOKEN>"
    zone_id: "<YOUR_ZONE_ID>"
    # DuckDNS 設定
    # token: "<YOUR_DUCKDNS_TOKEN>"
```

---

## 9. Java 版本切換設計

不要在每個 `server.yml` 直接寫死 Java 可執行檔路徑。  
應建立全域 Java registry。

### `config/java_registry.yml`

```yaml
profiles:
  java8:
    path: "C:/Program Files/Java/jdk1.8.0_381/bin/java.exe"
    version: "8"

  java17:
    path: "C:/Program Files/Java/jdk-17/bin/java.exe"
    version: "17"

  java21:
    path: "C:/Program Files/Java/jdk-21/bin/java.exe"
    version: "21"
```

### 每個伺服器只引用 profile

```yaml
java:
  mode: "profile"
  profile: "java17"
```

### 設計原則

- Java 安裝位置集中管理
- 更換 Java 路徑時只需修改 registry 一次
- 每個伺服器維持簡潔設定
- 後續可擴充自動選擇機制

### 後續可擴充方向

```yaml
java:
  mode: "auto"
  preferred: ["java21", "java17"]
```

未來可依據 Minecraft 版本或 loader 類型推估合適 Java，但在 Phase 1 不建議太自動，先以明確指定 profile 為主。

---

## 10. DNS 與網域管理設計

為了讓玩家能透過固定網域（如 `mc.unforgettableeternalproject.net`）連接到您的伺服器，即使您的公網 IP 會變動，系統需要整合動態 DNS（DDNS）功能。

### 10.1 支援的 DNS 服務商

Phase 1 建議優先支援：

#### Cloudflare

- 功能完整，支援 API 管理
- 可設定 A 記錄與 SRV 記錄
- 免費方案即可使用
- 需要 API Token 與 Zone ID

#### DuckDNS

- 簡單易用的免費 DDNS 服務
- 適合個人使用
- 僅需一組 Token
- 自動更新 IP

#### 自定義 Webhook

- 允許使用者自行串接其他 DNS 服務
- 提供 HTTP POST 介面

### 10.2 DNS 更新流程

1. **定期檢查公網 IP**
   - 每隔指定時間（預設 5 分鐘）檢查當前公網 IP
   - 可透過 `https://api.ipify.org` 等服務取得

2. **比對 IP 是否變更**
   - 將當前 IP 與上次記錄比對
   - 僅在 IP 變更時才執行更新

3. **呼叫 DNS 服務商 API**
   - Cloudflare: 更新 A 記錄與 SRV 記錄
   - DuckDNS: 呼叫更新 URL
   - 自定義: 觸發 webhook

4. **記錄更新狀態**
   - 將最新 IP 與更新時間寫入 `runtime/dns_state.json`
   - 記錄成功/失敗狀態

### 10.3 SRV 記錄設定

Minecraft 支援 SRV 記錄，讓玩家可以不用輸入端口號：

- 玩家輸入：`mc.unforgettableeternalproject.net`
- 實際連接：`your-ip:25565`

SRV 記錄格式：
```
_minecraft._tcp.mc.unforgettableeternalproject.net
```

### 10.4 全域 DNS 設定檔

建議在 `config/app.yml` 加入全域 DNS 設定：

```yaml
dns:
  enabled: true
  check_interval: 300  # 秒
  ip_check_service: "https://api.ipify.org"
  
  providers:
    cloudflare:
      api_token: "<YOUR_CLOUDFLARE_API_TOKEN>"
      zone_id: "<YOUR_CLOUDFLARE_ZONE_ID>"
    
    duckdns:
      token: "<YOUR_DUCKDNS_TOKEN>"
```

### 10.5 每個伺服器的 DNS 設定

在 `server.yml` 中加入（見前面第 8 章範例）：

```yaml
dns:
  enabled: true
  mode: "cloudflare"
  domain: "mc.unforgettableeternalproject.net"
  update_interval: 300
  srv_record:
    enabled: true
    priority: 0
    weight: 5
```

### 10.6 DNS 更新器設計原則

- **背景執行**: DNS 更新應在背景持續運行
- **容錯機制**: API 失敗時應重試，避免頻繁更新造成 rate limit
- **狀態透明**: 使用者應能隨時查看 DNS 狀態與最後更新時間
- **安全性**: API Token 應妥善保護，不要寫死在程式碼中

### 10.7 CLI 指令支援

```bash
# 立即更新 DNS
mc-host dns update my-server

# 查看 DNS 狀態
mc-host dns status my-server

# 測試 DNS 設定
mc-host dns test my-server

# 啟動 DNS 背景服務
mc-host dns start my-server

# 停止 DNS 背景服務
mc-host dns stop my-server
```

---

## 11. 伺服器偵測規則

為了支援「丟進去就能讀」，需要實作 detector。

### 偵測順序

#### 1. 優先讀取 `server.yml`

若存在則直接依設定處理。

#### 2. 若沒有 `server.yml`，進行自動掃描

可檢查：

- 是否有單一 `*.jar`
- 是否有 `server.jar`
- 是否有 `forge-*.jar`
- 是否有 `fabric-server-launch.jar`
- 是否有 `neoforge-*.jar`
- 是否有 `mods/`
- 是否有 `libraries/`
- 是否有 `eula.txt`

系統應根據偵測結果生成一份 `server.yml` 草稿。

#### 3. 若是完整整合包或解壓包

常見內容可能包含：

- `mods/`
- `config/`
- `libraries/`
- `.bat` / `.sh` 啟動腳本
- loader 專用 jar

未來可考慮：

- 讀取原始 `.bat` / `.sh` 解析其 Java 與啟動 jar 設定
- 自動生成更接近原始伺服器需求的設定草稿

Phase 1 可先保留架構，不必完整實作 `.bat` 解析。

---

## 12. 路徑接口設計

不要硬把所有 Minecraft 輸出重新搬動或重新分類，而是提供一層統一接口。

建議實作 `path_resolver.py`，對外提供下列方法：

- `get_server_root(instance)`
- `get_world_paths(instance)`
- `get_mods_path(instance)`
- `get_config_path(instance)`
- `get_logs_path(instance)`
- `get_libraries_path(instance)`
- `get_crash_reports_path(instance)`
- `get_backup_path(instance)`
- `get_runtime_path(instance)`

使用方式示例：

```python
worlds = instance.paths.get_world_paths()
logs = instance.paths.get_logs_path()
mods = instance.paths.get_mods_path()
```

### 設計原則

- 所有模組都透過 path interface 存取目錄
- GUI、CLI、備份、分析模組都共用同一套接口
- 後續結構調整時，不必全專案到處改路徑邏輯

---

## 13. 備份策略設計

備份不可一律強制執行，必須支援策略化設定。

### 建議 provider

- `internal`：由宿主框架執行備份
- `external`：該伺服器有自己的備份機制，宿主只記錄
- `disabled`：完全不處理備份

### 範例：停用備份

```yaml
backup:
  enabled: false
  provider: "disabled"
```

### 範例：使用外部備份

```yaml
backup:
  enabled: true
  provider: "external"
  note: "Modpack has built-in backup system"
```

### `internal` 備份的預設原則

應優先備份：

- 世界資料夾
- `server.properties`
- `ops.json`
- `whitelist.json`
- `banned-players.json`
- `banned-ips.json`

預設不備份：

- `logs/`
- `crash-reports/`
- `libraries/`
- `mods/`

### 原因

- `libraries/` 體積通常很大
- `logs/` 與 `crash-reports/` 不屬於核心世界資料
- `mods/` 通常可由整合包本體重新取得
- 備份重點應放在不可逆的遊戲狀態與核心設定

---

## 14. 啟動流程設計

每次啟動應遵循固定流程：

1. 讀取 `server.yml`
2. 驗證 `server root` 是否存在
3. 驗證 Java profile 是否存在
4. 驗證啟動目標是否存在
5. 必要時提示 EULA 狀態
6. 組合 Java 啟動指令
7. 設定 working directory = `server/`
8. 啟動子程序
9. 將 PID、開始時間寫入 `runtime/`
10. 持續輸出宿主管理 log

### 指令組合原則

最終啟動格式大致為：

```bash
<java path> -Xms<min_memory> -Xmx<max_memory> <jvm_args...> -jar <startup_target> <server_args...>
```

---

## 15. CLI 規劃

初期 CLI 指令建議如下：

```bash
mc-host scan
mc-host list
mc-host init my-server
mc-host detect my-server
mc-host start my-server
mc-host stop my-server
mc-host restart my-server
mc-host status my-server
mc-host backup my-server
mc-host paths my-server
mc-host validate my-server
mc-host java list
mc-host java validate
mc-host dns update <server>
mc-host dns status <server>
mc-host dns test <server>
```

### 指令功能說明

#### `scan`

掃描所有實例並顯示其狀態。

#### `list`

列出可用伺服器實例名稱。

#### `init <server>`

建立標準 instance 目錄與預設 `server.yml`。

#### `detect <server>`

掃描指定伺服器資料夾並產生或補全設定草稿。

#### `start <server>`

啟動指定伺服器。

#### `stop <server>`

停止指定伺服器。

#### `restart <server>`

重啟指定伺服器。

#### `status <server>`

查看指定伺服器當前狀態。

#### `backup <server>`

對指定伺服器執行備份（依設定檔決定是否允許）。

#### `paths <server>`

顯示該伺服器的重要路徑。

#### `validate <server>`

檢查設定是否完整、Java 是否存在、啟動目標是否存在。

#### `java list`

列出 Java registry 中所有 profiles。

#### `java validate`

檢查 Java registry 中的路徑是否有效。

#### `dns update <server>`

立即更新指定伺服器的 DNS 記錄。

#### `dns status <server>`

查看指定伺服器的 DNS 狀態與最後更新時間。

#### `dns test <server>`

測試 DNS 設定是否正確，驗證 API Token 與網域設定。

---

## 16. 核心模組切分

專案邏輯應拆成下列核心模組：

### `scanner`

負責掃描 `servers/` 下的所有伺服器 instance，辨識哪些資料夾可視為有效實例。

### `launcher`

負責組合並執行 Java 啟動命令，管理子程序生命週期。

### `java_resolver`

負責從 `java_registry.yml` 解析 profile 並驗證 Java 可執行檔路徑。

### `backup_manager`

負責依照 `server.yml` 的 backup 設定執行備份。

### `path_resolver`

負責統一回傳 Minecraft 與宿主框架相關目錄。

### `dns_manager`

負責檢查公網 IP 變更、呼叫 DNS 服務商 API、更新 A 記錄與 SRV 記錄、管理 DNS 背景服務。

### `models`

負責描述資料結構，例如：

- `ServerConfig`
- `JavaProfile`
- `BackupPolicy`
- `InstanceStatus`

---

## 17. 建議的實作順序

不要一次讓 Copilot 生完整專案，建議照以下順序逐步生成與串接：

1. `models/server_config.py`
2. `utils/yaml_loader.py`
3. `core/scanner.py`
4. `core/java_resolver.py`
5. `core/path_resolver.py`
6. `core/launcher.py`
7. `core/backup_manager.py`
8. `core/dns_manager.py`
9. `cli/commands.py`
10. `main.py`

### 原因

這樣可以先穩定資料模型與設定讀取，再逐步建立掃描、Java 解析、啟動與備份能力，最後再掛到 CLI。

可避免一開始生成過多高耦合程式碼，導致後續難以維護。

---

## 18. 給 Copilot 的起始提示詞

以下內容可直接提供給 Copilot 作為初始需求：

---

請幫我建立一個 Python 專案，名稱為 `mc-host-manager`，用途是管理本機多個 Minecraft Java 伺服器實例。

需求如下：

1. 專案需要掃描 `servers/` 資料夾下的每個子資料夾，每個子資料夾都代表一個獨立伺服器實例。

2. 每個伺服器實例至少包含：

- `server.yml`
- `server/`
- `runtime/`
- `backups/`
- `temp/`

3. `server/` 是 Minecraft 真正的工作目錄，裡面可能包含：

- `server.jar`
- `eula.txt`
- `server.properties`
- `world/`
- `mods/`
- `config/`
- `logs/`
- `crash-reports/`
- `libraries/`

4. 專案要支援從 `server.yml` 讀取：

- 伺服器名稱
- loader 類型
- startup jar
- Java profile
- 記憶體設定
- JVM args
- 備份設定

5. 專案需要有全域 Java registry，檔案位於 `config/java_registry.yml`，每個 profile 對應一個 `java.exe` 路徑。

6. 啟動伺服器時，要根據 `server.yml` 指定的 Java profile 組合啟動指令，並在 `server/` 目錄作為 working directory 執行。

7. 專案需提供 CLI 指令：

- `scan`
- `list`
- `start <server>`
- `stop <server>`
- `status <server>`
- `backup <server>`
- `validate <server>`

8. `backup` 需要支援設定檔控制，可選 `internal` / `external` / `disabled`。

- `internal` 時只備份世界與核心設定
- 預設不要備份 `logs/`、`crash-reports/`、`libraries/`、`mods/`

9. 請把邏輯拆分為：

- scanner
- launcher
- java_resolver
- backup_manager
- path_resolver
- dns_manager
- models

10. 使用 `pathlib` 管理路徑，使用 `yaml` 讀取設定，使用 `subprocess` 啟動 Java process。

11. 需要支援 DNS 功能：

- 整合 Cloudflare 或 DuckDNS API
- 定期檢查公網 IP 變更
- 自動更新 A 記錄與 SRV 記錄
- 管理 DNS 背景服務
- 支援網域如 `mc.unforgettableeternalproject.net`

12. 先實作 Phase 1，可穩定啟動、停止、掃描、備份、驗證、DNS 管理，不需要 GUI。

13. 請先產生完整專案結構與核心檔案骨架，並在每個模組留下清楚註解與 TODO。

---

## 19. 設計結論

這個專案的真正關鍵，不是把 Minecraft 特判寫很多，而是先把「宿主層」抽象做好。

最重要的幾個設計原則是：

- 每個伺服器都是一個標準化 instance
- `server/` 是真實工作目錄
- `runtime/` 放宿主狀態，不混用 Minecraft 原生輸出
- Java 透過全域 registry 管理
- 備份是策略化，而不是強制整包壓縮
- 所有資料夾都經由統一路徑接口存取
- **DNS 管理與宿主框架解耦，但提供統一的配置與管理介面**

只要這一層先做好，之後擴充：

- Forge / Fabric / NeoForge 支援
- 自動偵測
- GUI
- 自動更新
- RCON
- 排程重啟
- **DNS 管理**
- Web Dashboard

都會順很多。

---

## 20. Phase 1 驗收標準

Phase 1 完成時，至少需達成以下驗收條件：

- 可以正確掃描 `servers/` 下的伺服器實例
- 可以讀取每個 instance 的 `server.yml`
- 可以根據 Java registry 解析並使用正確 Java
- 可以啟動指定伺服器
- 可以停止指定伺服器
- 可以檢查設定是否完整
- 可以依 backup policy 執行或跳過備份
- 可以將宿主 runtime 資料與 Minecraft 工作目錄分離
- CLI 可正常執行核心指令
- **可以整合 Cloudflare 或 DuckDNS 等 DNS 服務**
- **可以自動偵測 IP 變更並更新 DNS 記錄**
- **可以設定伺服器的網域名稱（如 mc.unforgettableeternalproject.net）**
- **可以查看 DNS 更新狀態與歷史**

---

## 21. 未來可擴充方向

後續版本可考慮加入：

- `.bat` / `.sh` 啟動腳本解析器
- loader adapter 架構
- RCON 整合
- Web UI / TUI
- 排程重啟與排程備份
- 自動 EULA 初始化
- 更新器
- 世界資訊摘要
- 伺服器資源監控
- 崩潰後自動處理策略
- 多平台相容（Windows / Linux）
- **多網域管理（一個實例多個網域）**
- **自定義 DNS 服務商支援**
- **IPv6 支援**
- **自動 SSL 證書管理（若未來加入 Web 管理介面）**

---

以上規格以 **Phase 1 穩定可用** 為優先。若要開始實作，請先建立完整專案骨架與資料模型，再逐步串接掃描、Java 解析、啟動器與備份模組。
