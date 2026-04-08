# DNS 設定完整指南

## 🌐 DNS 功能說明

本框架的 DNS 功能會：
1. **自動偵測您的公網 IP** - 使用 `https://api.ipify.org` 等服務
2. **自動更新 Cloudflare DNS 記錄** - 當 IP 變更時自動更新
3. **設定 SRV 記錄** - 讓玩家可以直接輸入網域而不需要加端口號

## 📋 前置準備

### 1. 在 Cloudflare 新增網域

確保您的網域（例如 `unforgettableeternalproject.net`）已經加入 Cloudflare。

### 2. 取得 API Token 和 Zone ID

#### 取得 Zone ID：
1. 登入 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 選擇您的網域
3. 右側可看到 **Zone ID**，複製它

#### 建立 API Token：
1. 點選右上角頭像 → **我的個人資料**
2. 左側選單 → **API Tokens**
3. 點選 **建立權杖**
4. 選擇 **編輯區域 DNS** 範本（或自訂權限）
5. 設定權限：
   - **Zone - DNS - Edit**
   - **Zone - Zone - Read**
6. 選擇要套用的網域
7. 建立並複製 Token

## ⚙️ 設定 server.yml

編輯 `servers/dc/server.yml` 的 DNS 區塊：

```yaml
dns:
  enabled: true  # 啟用 DNS 功能
  mode: "cloudflare"  # 使用 Cloudflare
  domain: "mc.unforgettableeternalproject.net"  # 您的子網域
  server_port: 25565  # 您的 Minecraft 伺服器端口
  update_interval: 300  # 每 5 分鐘檢查一次 IP
  srv_record:
    enabled: true  # 啟用 SRV 記錄
    priority: 0
    weight: 5
    port: 25565  # SRV 記錄的端口
  config:
    api_token: "YOUR_CLOUDFLARE_API_TOKEN_HERE"  # 貼上您的 API Token
    zone_id: "YOUR_ZONE_ID_HERE"  # 貼上您的 Zone ID
```

## 🚀 使用方式

### 方法一：手動更新 DNS

```powershell
# 啟用虛擬環境
.\env\Scripts\Activate.ps1

# 更新 DNS（框架會自動偵測 IP 並更新 Cloudflare）
python -m app.main dns update dc

# 查看 DNS 狀態
python -m app.main dns status dc

# 測試 DNS 連線
python -m app.main dns test dc
```

### 方法二：啟動伺服器時自動更新

當您啟動伺服器時，如果 DNS 功能已啟用，框架會自動更新 DNS：

```powershell
python -m app.main start dc
```

### 方法三：自動背景更新（未來版本）

未來版本會支援背景自動更新，每隔指定時間自動檢查 IP 變更。

## 📝 DNS 記錄說明

框架會在 Cloudflare 建立兩種記錄：

### A 記錄
- **類型**: A
- **名稱**: `mc` (完整網域: mc.unforgettableeternalproject.net)
- **內容**: 您的公網 IP（自動偵測）
- **TTL**: 300 秒
- **Proxy**: 關閉

### SRV 記錄（如果啟用）
- **類型**: SRV
- **名稱**: `_minecraft._tcp.mc` (完整: _minecraft._tcp.mc.unforgettableeternalproject.net)
- **優先級**: 0
- **權重**: 5
- **端口**: 25565（或您設定的端口）
- **目標**: mc.unforgettableeternalproject.net

## 🎮 玩家如何連線

### 啟用 SRV 記錄時
玩家可以直接輸入：
```
mc.unforgettableeternalproject.net
```
不需要加端口號！

### 未啟用 SRV 記錄時
玩家需要輸入：
```
mc.unforgettableeternalproject.net:25565
```

## 🔧 設定不同端口

如果您的伺服器不使用預設的 25565 端口：

### 修改 server.properties
```properties
server-port=25566  # 改成您要的端口
```

### 同步更新 server.yml
```yaml
dns:
  server_port: 25566  # 與 server.properties 一致
  srv_record:
    port: 25566  # 與 server_port 一致
```

### 檢查防火牆
確保防火牆允許該端口的連線：
```powershell
# Windows 防火牆新增規則（以系統管理員執行）
New-NetFirewallRule -DisplayName "Minecraft Server" -Direction Inbound -Protocol TCP -LocalPort 25566 -Action Allow
```

## ❓ 常見問題

### Q: 我需要在 Cloudflare 手動建立 A 記錄嗎？
**A**: 不需要！框架會自動建立。但如果您想手動建立，IPv4 可以隨便填（例如 1.1.1.1），框架會自動更新。

### Q: 我的 IP 會自動更新嗎？
**A**: 是的！當您執行 `dns update` 或啟動伺服器時，框架會自動偵測 IP 變更並更新。

### Q: 可以使用其他 DNS 服務嗎？
**A**: 目前支援 Cloudflare 和 DuckDNS。其他服務需要自行擴充。

### Q: SRV 記錄是什麼？
**A**: SRV 記錄讓玩家可以不用輸入端口號。Minecraft 客戶端會自動查詢 SRV 記錄來找到正確的端口。

### Q: 為什麼要關閉 Cloudflare Proxy（橘色雲朵）？
**A**: Minecraft 使用 TCP 協定，Cloudflare 的 Proxy 只支援 HTTP/HTTPS。必須關閉 Proxy 才能讓 Minecraft 連線正常運作。

### Q: 我的公網 IP 是什麼？
**A**: 執行以下指令查看：
```powershell
curl https://api.ipify.org
```
或使用框架：
```powershell
python -m app.main dns test dc
```

## 🔒 安全性建議

1. **不要公開 API Token** - 將 `server.yml` 加入 `.gitignore`
2. **使用最小權限** - API Token 只給必要的權限（DNS Edit）
3. **定期更換 Token** - 建議每 3-6 個月更換一次
4. **使用環境變數** - 未來版本可支援從環境變數讀取 Token

## 📊 監控與除錯

### 查看 DNS 狀態
```powershell
python -m app.main dns status dc
```

輸出範例：
```
DNS 狀態: dc

啟用: 是
網域: mc.unforgettableeternalproject.net
當前 IP: 123.45.67.89
最後更新: 2 分鐘前
更新次數: 5
錯誤次數: 0
```

### 測試連線
```powershell
python -m app.main dns test dc
```

### 查看 DNS 狀態檔案
框架會將 DNS 狀態保存到：
```
servers/dc/runtime/dns_state.json
```

## 🎯 完整範例

假設您的設定如下：
- **網域**: `unforgettableeternalproject.net`（已在 Cloudflare）
- **子網域**: `mc.unforgettableeternalproject.net`
- **伺服器端口**: `25565`
- **公網 IP**: `123.45.67.89`（會自動偵測）

### server.yml 設定
```yaml
dns:
  enabled: true
  mode: "cloudflare"
  domain: "mc.unforgettableeternalproject.net"
  server_port: 25565
  update_interval: 300
  srv_record:
    enabled: true
    priority: 0
    weight: 5
    port: 25565
  config:
    api_token: "abc123_your_token_here"
    zone_id: "xyz789_your_zone_id"
```

### 執行更新
```powershell
.\env\Scripts\Activate.ps1
python -m app.main dns update dc
```

### Cloudflare 上會看到
- **A 記錄**: `mc` → `123.45.67.89`
- **SRV 記錄**: `_minecraft._tcp.mc` → `mc.unforgettableeternalproject.net:25565`

### 玩家連線
直接輸入：`mc.unforgettableeternalproject.net`

---

**提示**: 第一次設定時建議先執行 `dns test` 確認 API Token 和 Zone ID 正確！
