# DNS 功能測試指南

完成 DNS 設定後，請按照以下步驟測試功能。

## 📋 測試前準備

1. **確認已設定 server.yml**
   - 填入 Cloudflare API Token
   - 填入 Zone ID
   - 設定網域名稱

2. **確認網域已加入 Cloudflare**
   - 登入 Cloudflare Dashboard
   - 確認 `unforgettableeternalproject.net` 存在

## 🧪 測試步驟

### 步驟 1：測試連線

```powershell
.\env\Scripts\Activate.ps1
python -m app.main dns test dc
```

**成功輸出範例：**
```
測試 DNS 連線...
✓ Cloudflare API 連線正常 (IP: 123.45.67.89)
```

**如果失敗：**
- 檢查 API Token 是否正確
- 檢查 Zone ID 是否正確
- 確認網路連線正常

### 步驟 2：手動更新 DNS

```powershell
python -m app.main dns update dc
```

**成功輸出範例：**
```
更新 DNS: mc.unforgettableeternalproject.net
偵測到 IP 變更: None -> 123.45.67.89
DNS 更新成功: mc.unforgettableeternalproject.net -> 123.45.67.89
✓ DNS 已更新
網域: mc.unforgettableeternalproject.net
IP: 123.45.67.89
```

### 步驟 3：查看 DNS 狀態

```powershell
python -m app.main dns status dc
```

**輸出範例：**
```
DNS 狀態: dc

啟用: 是
網域: mc.unforgettableeternalproject.net
當前 IP: 123.45.67.89
最後更新: 剛剛
更新次數: 1
錯誤次數: 0
```

### 步驟 4：在 Cloudflare 驗證

1. 登入 Cloudflare Dashboard
2. 選擇網域
3. 進入 **DNS → Records**
4. 確認看到：

**A 記錄：**
- Type: `A`
- Name: `mc`
- Content: `您的公網IP`
- Proxy status: `DNS only` (灰色雲朵)

**SRV 記錄（如果啟用）：**
- Type: `SRV`
- Name: `_minecraft._tcp.mc`
- Priority: `0`
- Weight: `5`
- Port: `25565`
- Target: `mc.unforgettableeternalproject.net`

### 步驟 5：測試玩家連線

使用 Minecraft 客戶端測試：

1. 開啟 Minecraft
2. 多人遊戲 → 新增伺服器
3. 伺服器位址輸入：`mc.unforgettableeternalproject.net`
4. 儲存並嘗試連線

**如果啟用了 SRV 記錄：**
- ✅ 不需要輸入端口號
- 客戶端會自動找到正確的端口

**如果沒有啟用 SRV 記錄：**
- 需要輸入：`mc.unforgettableeternalproject.net:25565`

## 🔍 問題排查

### 問題 1: API Token 無效

**錯誤訊息：**
```
錯誤: Cloudflare API 錯誤: 401
```

**解決方法：**
1. 重新建立 API Token
2. 確認權限包含 DNS Edit 和 Zone Read
3. 複製正確的 Token 到 server.yml

### 問題 2: Zone ID 錯誤

**錯誤訊息：**
```
錯誤: Cloudflare API 錯誤: 404
```

**解決方法：**
1. 登入 Cloudflare Dashboard
2. 選擇網域
3. 右側找到 Zone ID 並重新複製

### 問題 3: 無法取得公網 IP

**錯誤訊息：**
```
錯誤: 無法取得公網 IP
```

**解決方法：**
1. 檢查網路連線
2. 確認防火牆沒有阻擋
3. 手動測試：`curl https://api.ipify.org`

### 問題 4: DNS 記錄未更新

**解決方法：**
1. 等待幾分鐘（DNS 傳播需要時間）
2. 清除 DNS 快取：
   ```powershell
   ipconfig /flushdns
   ```
3. 使用線上工具檢查：https://dnschecker.org/

### 問題 5: 玩家無法連線

**可能原因：**

1. **防火牆阻擋**
   ```powershell
   # 確認端口開放
   New-NetFirewallRule -DisplayName "Minecraft" -Direction Inbound -Protocol TCP -LocalPort 25565 -Action Allow
   ```

2. **路由器沒有設定端口轉發**
   - 登入路由器管理介面
   - 設定端口轉發：外部 25565 → 內部伺服器 IP:25565

3. **伺服器未啟動**
   ```powershell
   .\mc-host.bat status dc
   ```

4. **DNS 未更新**
   - 使用 `nslookup` 檢查：
   ```powershell
   nslookup mc.unforgettableeternalproject.net
   ```

## ✅ 測試檢查清單

完成以下檢查確保一切正常：

- [ ] DNS test 指令成功
- [ ] DNS update 指令成功
- [ ] Cloudflare Dashboard 看到 A 記錄
- [ ] Cloudflare Dashboard 看到 SRV 記錄（如有啟用）
- [ ] `nslookup` 回傳正確 IP
- [ ] Minecraft 客戶端可以解析網域
- [ ] 防火牆已開放端口
- [ ] 路由器已設定端口轉發
- [ ] 伺服器正常運行
- [ ] 玩家可以成功連線

## 🎉 測試成功後

恭喜！您的 DNS 設定完成。現在：

1. **設定自動更新**
   - DNS 會在伺服器啟動時自動更新
   - 框架會每 5 分鐘檢查 IP 變更

2. **分享給朋友**
   - 玩家只需輸入：`mc.unforgettableeternalproject.net`
   - 不需要記住複雜的 IP 位址

3. **打包分發**
   - 測試成功後可以打包成 .exe
   - 在其他電腦上也能輕鬆使用

---

**下一步**: 如果測試成功，可以進行打包！
請參考 [打包指南](PACKAGING.md)
