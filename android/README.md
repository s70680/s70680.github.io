# 頭頂星空 Android（Trusted Web Activity）建置說明

這個資料夾把 <https://s70680.github.io/sky/> 這個 PWA 包成 Android App（TWA），
用 GitHub Actions 自動產生 Google Play 需要的 `.aab` 與側載測試用的 `.apk`。

| 項目 | 值 |
| --- | --- |
| 套件名稱（applicationId） | `io.github.s70680.sky` |
| App／啟動器名稱 | 頭頂星空 |
| 網址 | `https://s70680.github.io/sky/`（主機 `s70680.github.io`） |
| 版本 | versionCode `1`、versionName `1.0.0`（在 `twa-manifest.json`） |
| SDK | minSdk 21、compileSdk 36、targetSdk 36（Google Play 2026-08-31 起的要求） |
| 主題／背景／導覽列顏色 | `#080C1F` |
| 通知委派 | 關閉；定位由 Chrome 自己跳提示，不做 location delegation |
| 權限 | 只有 AndroidX 自動加入的 `io.github.s70680.sky.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`（signature 等級、只給 App 自己用）；**沒有**定位、廣告 ID（AD_ID）、網路、通知權限——網頁由 Chrome 載入 |
| 產生器 | `@bubblewrap/core` 1.25.0（版本鎖在 `package-lock.json`） |
| 已簽章檔案 | 1.0.0 已手動簽章（見下方「手動簽章」），檔案在 Jack 手上的 `deliverables/android/`；設好 Secrets 後 CI 也會發布 `android-v<版本>` 預先發布 |

## 檔案說明

- `twa-manifest.json`：TWA 設定檔。由 `TwaManifest.fromWebManifestJson()` 讀取
  `sky/manifest.webmanifest` 產生，再固定套件名、名稱、顏色、版本等欄位。
  **要改版本、名稱、顏色都改這裡。**
- `generate.mjs`：呼叫 `TwaGenerator.createTwaProject()` 產出 Android 專案
  （輸出到 `android/build/twa/`，已被 `.gitignore` 排除），並把 compileSdk／targetSdk
  設成 `TARGET_SDK`（目前 36）、把已停用的 `jcenter()` 換成 `mavenCentral()`。
- `package.json`／`package-lock.json`：鎖定產生器版本，CI 用 `npm ci` 安裝。
- `../.github/workflows/android.yml`：GitHub Actions 建置流程（見下）。
- `../.well-known/assetlinks.json`：Digital Asset Links，讓 App 開啟網站時不顯示網址列。

## 建置流程做了什麼

1. `actions/checkout` → 安裝 JDK 17（Temurin）與 Node.js 22。
2. 在 `android/` 執行 `npm ci`，再 `node generate.mjs` 產生 Android 專案
   （圖示從 `https://s70680.github.io/sky/icon-512.png` 與 `icon-maskable-512.png` 下載，
   所以**網站必須已經上線**）。
3. 用 `sdkmanager` 安裝 `platforms;android-36` 與 `build-tools;36.0.0`。
4. `./gradlew bundleRelease assembleRelease` 產生未簽章的 `.aab` 與 `.apk`。
5. 上傳為工作流程產物（artifact，保留 90 天），並發布到預先發布
   **`android-build-unsigned`**（每次執行都刪掉重建，只留最新一次）：
   <https://github.com/s70680/s70680.github.io/releases/tag/android-build-unsigned>
6. **選用**：若四個簽章 Secrets 都存在（見下），會再用 `jarsigner` 簽 `.aab`、
   `zipalign + apksigner` 簽 `.apk`，上傳為 artifact 並發布到預先發布 **`android-v<版本>`**。
   沒有 Secrets 時這三個步驟會顯示「skipped」，不算失敗。

未簽章的檔案不能上傳 Play 也不能安裝到手機；要先簽章（自動或手動）。

## 怎麼重新建置

1. 到 GitHub repo → **Actions** → 左側選「**Android TWA build**」。
2. 右側按 **Run workflow** → 選 `main` → **Run workflow**。
3. 約 1～3 分鐘完成（2026-09-29 實測約 1～2 分鐘；Gradle 快取失效時會久一點）。
   結果在該次執行頁面的 **Artifacts**，以及 Releases 的
   `android-build-unsigned`（有 Secrets 時另有 `android-v<版本>`）。

另外只要把 `android/**` 或工作流程檔的變更推到 `main`，也會自動建置。

## 怎麼改版本號（每次上傳 Play 都要加 versionCode）

編輯 `android/twa-manifest.json`：

```json
  "appVersionName": "1.0.1",
  "appVersionCode": 2,
```

規則：

- `appVersionCode` 是整數，**每次上傳 Google Play 都必須比上一次大**（1 → 2 → 3 …）。
- `appVersionName` 是給人看的字串（`1.0.1`、`1.1.0`…），檔名會跟著變成
  `toudingxingkong-<appVersionName>.aab`。
- 改完 commit 推到 `main` 就會自動建置；或手動 Run workflow。

> `generate.mjs` 以 `appVersionName` 為準（bubblewrap 舊欄位 `appVersion` 會自動同步），只要改這兩行。

## 讓 CI 自動簽章（選用，設定四個 Secrets）

上傳金鑰檔 `upload-keystore.p12`（別名 `upload`）與密碼在 Jack 手上的
`deliverables/android/upload-key-info.txt`，**不在 git 裡**。

先把金鑰檔轉成 base64 單行文字：

- Windows PowerShell：

  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\upload-keystore.p12")) | Set-Clipboard
  # 已複製到剪貼簿；或改成 | Out-File -Encoding ascii keystore.b64
  ```

- macOS／Linux：

  ```bash
  base64 -w0 upload-keystore.p12 > keystore.b64     # Linux
  base64 -i upload-keystore.p12 | tr -d '\n' > keystore.b64   # macOS
  ```

再到 GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**，
新增這四個（名稱要一模一樣）：

| Secret 名稱 | 值 |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | 上面 base64 的內容（單行，不要有換行） |
| `ANDROID_KEYSTORE_PASSWORD` | 金鑰庫密碼（見 upload-key-info.txt） |
| `ANDROID_KEY_ALIAS` | `upload` |
| `ANDROID_KEY_PASSWORD` | 金鑰密碼（與金鑰庫密碼相同） |

設好之後再 Run workflow 一次，就會多出已簽章的 `toudingxingkong-<版本>.aab`／`.apk`
與預先發布 `android-v<版本>`。CI log 不會印出密碼或金鑰內容。

> 若 `android-v<版本>` 已經存在，CI 會先刪掉再重建，換成 CI 簽章的檔案。CI 與手動簽章用的是
> 同一把上傳金鑰，擇一上傳 Play 即可；同一個 versionCode 在 Play 只能上傳一次。

### 手動簽章（沒設 Secrets 時）

從 `android-build-unsigned` 下載 `*-unsigned.aab`／`*-unsigned.apk`，在有 JDK 與
Android build-tools 的電腦上：

```bash
# .aab（Play 接受 JAR 簽章）
jarsigner -keystore upload-keystore.p12 -storepass <密碼> -keypass <密碼> \
  -sigalg SHA256withRSA -digestalg SHA-256 \
  -signedjar toudingxingkong-1.0.0.aab toudingxingkong-1.0.0-unsigned.aab upload
jarsigner -verify -keystore upload-keystore.p12 -storepass <密碼> -strict toudingxingkong-1.0.0.aab
# 要加 -keystore：上傳金鑰是自簽憑證，不加的話會顯示「jar verified, with signer errors」
# 並回傳 exit 4（簽章本身沒問題）。加了之後應只顯示「jar verified.」。

# .apk（一定要先 zipalign 再 apksigner）
zipalign -p -f 4 toudingxingkong-1.0.0-unsigned.apk aligned.apk
apksigner sign --ks upload-keystore.p12 --ks-key-alias upload --out toudingxingkong-1.0.0.apk aligned.apk
apksigner verify --print-certs toudingxingkong-1.0.0.apk
```

沒有 Android SDK 的話，`.apk` 可以改用 [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer)
（1.3.0，內建 zipalign 與 apksigner，簽 v1＋v2＋v3）：

```bash
java -jar uber-apk-signer.jar --apks toudingxingkong-1.0.0-unsigned.apk -o out \
  --ks upload-keystore.p12 --ksAlias upload \
  --verifySha256 1e16e7b44fbeae35c5c34881bff54c653cb1d0c9f2854decc9a4af446fa0541f
```

會詢問兩次密碼（金鑰庫、金鑰，兩者相同）；輸出是 `out/toudingxingkong-1.0.0-unsigned-aligned-signed.apk`
（另有一個 `.idsig`，用不到），改名成 `toudingxingkong-1.0.0.apk` 即可。
`.aab` 仍然要用上面的 `jarsigner`（uber-apk-signer 不處理 .aab）。

2026-09-29 交給 Jack 的 1.0.0 已簽章檔（`deliverables/android/toudingxingkong-1.0.0.aab`／`.apk`）
就是用這兩個方式簽的，來源是 `android-build-unsigned`（commit `2583f10`、工作流程執行
36512511015）的未簽章檔，並已用 `bundletool validate`、`jarsigner -verify`、
`apksigner verify --print-certs` 核對過。

## 上傳 Google Play 後：把 Play 的簽署金鑰指紋加進 assetlinks.json（必做）

Google Play 會用 **Play App Signing** 的「應用程式簽署金鑰」重新簽署你的 App，
所以從 Play 安裝的 App 憑證指紋和上傳金鑰**不同**。如果 `assetlinks.json` 只有上傳金鑰的
指紋，從 Play 安裝的 App 開啟時會出現瀏覽器網址列（TWA 驗證失敗）。

1. 第一次上傳 `.aab` 並建立版本後，到 Play Console → 選擇 App →
   **由 Google Play 保護 → Play 商店發行 → 前往 Play 應用程式簽署**
   （英文介面：Protected with Play → Play Store distribution → Go to Play app signing；
   依 Play 說明中心〈使用 Play 應用程式簽署〉，2026-09-29 查核。Play Console 常改版，
   找不到時用上方搜尋框搜「應用程式簽署」；較舊的名稱是「測試與發布／設定 → 應用程式完整性 → 應用程式簽署」）。
2. 複製「**應用程式簽署金鑰憑證**」區塊的 **SHA-256 憑證指紋**（不是上傳金鑰憑證那一組）。
3. 編輯 repo 根目錄的 `.well-known/assetlinks.json`，把它加進陣列（**兩組都保留**，
   上傳金鑰那組讓側載測試的 APK 也能通過驗證）：

   ```json
   [
     {
       "relation": ["delegate_permission/common.handle_all_urls"],
       "target": {
         "namespace": "android_app",
         "package_name": "io.github.s70680.sky",
         "sha256_cert_fingerprints": [
           "1E:16:E7:B4:4F:BE:AE:35:C5:C3:48:81:BF:F5:4C:65:3C:B1:D0:C9:F2:85:4D:EC:C9:A4:AF:44:6F:A0:54:1F",
           "AA:BB:CC:...（貼上 Play 應用程式簽署金鑰的 SHA-256）"
         ]
       }
     }
   ]
   ```

4. Commit 推到 `main`，等 GitHub Pages 部署完（1～2 分鐘），打開
   <https://s70680.github.io/.well-known/assetlinks.json> 確認內容已更新。
5. 可用 Google 的驗證工具檢查：
   `https://digitalassetlinks.googleapis.com/v1/statements:list?source.web.site=https://s70680.github.io&relation=delegate_permission/common.handle_all_urls`

指紋格式：大寫十六進位、冒號分隔，Play Console 顯示的格式可直接貼上。

## 側載測試 APK

1. 把已簽章的 `toudingxingkong-1.0.0.apk` 傳到 Android 手機（Line、雲端硬碟、USB 都可以）。
2. 點開安裝；手機會問是否允許這個來源安裝未知應用程式，允許即可。
   或用電腦：`adb install -r toudingxingkong-1.0.0.apk`。
3. 手機要有 **Chrome**（或其他支援 TWA 的瀏覽器）且**有網路**；第一次開啟需要連線載入網站。
4. 打開「頭頂星空」：畫面上方**沒有網址列**，代表 Digital Asset Links 驗證成功。
   如果看到 Chrome 的網址列／自訂分頁標題，表示驗證失敗，依序檢查：
   - `https://s70680.github.io/.well-known/assetlinks.json` 打得開、內容是合法 JSON、
     `package_name` 是 `io.github.s70680.sky`；
   - 裡面的 SHA-256 跟簽這個 APK 的金鑰一致
     （`apksigner verify --print-certs xxx.apk` 或 `keytool -printcert -jarfile xxx.apk`）；
   - Chrome 會快取驗證結果，改完 assetlinks 後把 App 資料清除或重新安裝再試；
   - 手機時間正確、Chrome 是最新版。
5. 未簽章的 `*-unsigned.apk` 無法安裝（Android 會拒絕），請務必用簽章後的檔案。

## 常見問題

- **建置失敗在「Generate TWA project」**：多半是網站圖示下載失敗
  （`https://s70680.github.io/sky/icon-512.png` 要能打開、Content-Type 是 image/png）。
- **Gradle 錯誤 `compileSdkVersion`／`build-tools` 找不到**：工作流程會從產生出來的
  `app/build.gradle` 讀 compileSdk，自動安裝對應的 `platforms;android-<版本>`；
  `build-tools;36.0.0` 則是寫死在 `android.yml`，Gradle 要求更新版本時改那一行。
- **Google Play 要求更高的 targetSdk**：改 `generate.mjs` 的 `TARGET_SDK`、`COMPILE_SDK`
  和 `android.yml` 的 `build-tools;<版本>`，必要時升級 `@bubblewrap/core`
  （`npm install @bubblewrap/core@latest` 後 commit `package-lock.json`）。
- **想關掉「網站設定」捷徑或改啟動畫面淡出時間**：改 `twa-manifest.json` 的
  `enableSiteSettingsShortcut`、`splashScreenFadeOutDuration`。
