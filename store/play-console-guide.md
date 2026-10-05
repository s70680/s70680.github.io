# 頭頂星空 上架 Google Play 完整步驟（個人開發者帳號・台灣）

> 對象：第一次申請 Google Play 開發者帳號的**個人帳號**。內容已於 2026-09-29 對照 Google 官方說明查核，連結都附在各節；Play Console 介面文字偶爾會改，以實際畫面為準。
> 相關檔案：商店文案 [`store/listing.md`](listing.md)、測試邀請 [`store/tester-invite.md`](tester-invite.md)、圖像 `store/graphics/`、Android 建置與 assetlinks 說明 [`android/README.md`](../android/README.md)。
> 本文件不是法律意見。

---

## 0. 先知道的三件事

1. **新個人帳號必須先做「封閉測試」**：至少 **12 位測試人員**、**連續加入至少 14 天**，才能申請正式版（Production）。這是最花時間的一段，請盡早開始找人。來源：[新個人開發人員帳戶的應用程式測試規定](https://support.google.com/googleplay/android-developer/answer/14151465)
2. **要有一支實體 Android 手機**（Android 10 以上、未 root）用來完成裝置驗證。來源：[裝置驗證規定](https://support.google.com/googleplay/android-developer/answer/14316361)
3. **個人帳號會公開顯示你的法定姓名、國家與開發人員電子郵件**；若日後開始收費（應用程式內購），Google 還會公開你的**完整地址**。來源：[Play 管理中心規定](https://support.google.com/googleplay/android-developer/answer/10788890)

---

## 1. 註冊開發者帳號

來源：[開始使用 Play 管理中心](https://support.google.com/googleplay/android-developer/answer/6112435)、[驗證開發人員身分](https://support.google.com/googleplay/android-developer/answer/10841920)

1. 準備：一個 Google 帳號（建議專門用來當開發者的新 Gmail）、身分證（或護照）、一張以本人姓名申請的信用卡／簽帳金融卡、手機號碼。必須年滿 18 歲。
2. 前往 https://play.google.com/console/signup ，帳戶類型選 **個人（Personal）**。
3. 填寫：
   - 開發人員名稱（會顯示在商店，可與本名不同，例如「s70680」或你想要的品牌名）
   - 法定姓名、法定地址（與證件一致）
   - 聯絡電子郵件、聯絡電話（給 Google 聯絡你用，不公開）
   - 開發人員電子郵件（**會公開顯示**）
   - 以上電子郵件與電話都要用一次性驗證碼驗證。
4. 回答幾個關於開發經驗、預計上架數量的問題（照實回答即可，不影響審核）。
5. 支付 **一次性註冊費 US$25**。
6. **身分驗證**：依畫面上傳證件照片，姓名必須與付款卡片一致。審核通常幾天內完成，會以電子郵件通知。
7. **裝置驗證**：身分驗證通過後，Play Console 首頁會出現「驗證你可以存取 Android 行動裝置」工作項目 → 用手機掃 QR code 安裝「Google Play Console」App → 用同一個帳號登入 → 選開發人員帳戶 → 點「驗證」。約 1 分鐘完成。

> **Android 開發人員驗證／套件名稱註冊（2026 新制）**：在 Play Console 建立應用程式時，Google 會**自動**註冊套件名稱並綁定你的帳號，新 App 不需額外動作；只要到首頁或「Android developer verification」頁確認狀態為已註冊。來源：[在 Google Play 管理中心註冊](https://developer.android.com/developer-verification/guides/google-play-console)、[註冊 Play 套件名稱](https://support.google.com/googleplay/android-developer/answer/16984799)

---

## 2. 建立應用程式

Play Console →「所有應用程式」→「建立應用程式」：

| 欄位 | 選擇 |
|---|---|
| 應用程式名稱 | 頭頂星空：星座盤與星圖（可之後再改，見 listing.md） |
| 預設語言 | **中文（台灣）– zh-TW** |
| 應用程式或遊戲 | **應用程式** |
| 免費或付費 | **免費**（⚠️ 一旦發布為免費就不能改成付費；日後要收費請用應用程式內購，見第 10 節） |
| 聲明 | 勾選「開發人員計畫政策」與「美國出口法規」 |

套件名稱不是在這裡填，而是**第一次上傳 .aab 時**由檔案決定：`io.github.s70680.sky`，之後永遠不能改。

---

## 3. Play 應用程式簽署與上傳 .aab

來源：[使用 Play 應用程式簽署](https://support.google.com/googleplay/android-developer/answer/9842756)

1. 取得 `.aab`：依 [`android/README.md`](../android/README.md) 的說明，從 GitHub Actions 工作流程下載建置好的 `app-release.aab`（versionName 1.0.0）。上傳金鑰（upload key）的保管方式也寫在那份文件，**金鑰與密碼務必備份**。
2. 目前規定：新 App 與更新必須 **target Android 16（API 36）以上**（2026-08-31 起）。Android 專案已照此設定；若上傳時出現 target API 錯誤，請 Android 流程更新後重新建置。來源：[目標 API 級別規定](https://support.google.com/googleplay/android-developer/answer/11926878)
3. 第一次上傳建議放在**封閉測試**軌道（第 6 節），上傳時 Play Console 會詢問 Play 應用程式簽署：選 **使用 Google 產生的應用程式簽署金鑰**（預設，最省事，也最安全）。

### 上傳後立刻做：更新 assetlinks.json（非常重要）

Trusted Web Activity 要靠 Digital Asset Links 證明 App 與網站是同一個擁有者，否則 App 上方會出現網址列。**Google Play 重新簽署後的憑證和你的上傳金鑰不同**，所以：

1. Play Console →「測試與發布」→「設定」→「應用程式完整性」→「應用程式簽署」。
2. 複製「**應用程式簽署金鑰憑證**」的 **SHA-256 憑證指紋**（不是「上傳金鑰憑證」那一個）。
3. 依 [`android/README.md`](../android/README.md) 的步驟，把它加進 repo 根目錄的 `.well-known/assetlinks.json`（可同時保留上傳金鑰的指紋），推送到 main。
4. 確認 https://s70680.github.io/.well-known/assetlinks.json 能打開並含有新指紋；可用 Google 的 [Statement List Generator and Tester](https://developers.google.com/digital-asset-links/tools/generator) 檢查。
5. 從 Play 安裝測試版 → 開啟 App → 上方**不應該**出現網址列。若出現，通常是指紋貼錯或網站快取未更新（等幾分鐘、清除 Chrome 資料後再試）。

---

## 4. 商店資訊與圖像

Play Console →「發布商品資訊」→「主要商品詳情」：文字全部複製 [`listing.md`](listing.md)。

| 素材 | 檔案 | 規格 |
|---|---|---|
| 應用程式圖示 | `store/graphics/icon-512.png` | 512×512 PNG（32 位元含 alpha），≤ 1 MB |
| 主題圖片 | `store/graphics/feature-graphic.png` | 1024×500，JPEG 或 24 位元 PNG（無透明） |
| 手機螢幕截圖 | `store/graphics/phone/` | 2～8 張，JPEG 或 24 位元 PNG，邊長 320～3840 px，長邊 ≤ 短邊 2 倍 |

來源：[新增預覽素材](https://support.google.com/googleplay/android-developer/answer/9866151)

「商店設定」：類別選 **教育**；聯絡資訊填電子郵件（必填、會公開）與網站 https://s70680.github.io/sky/ 。

---

## 5. 「應用程式內容」逐項填寫（Policy → App content）

所有項目都要完成，否則無法送審。以下是每一題的建議答案與理由（依 2026-09-29 查核的 App 實際行為：只在手機上計算；沒有帳號、廣告、分析或追蹤；只有 GitHub Pages 與 Google Fonts 傳送檔案）。

### 5.1 隱私權政策
- 網址：**https://s70680.github.io/sky/privacy.html**（App 內「圖層」→「隱私權政策」也能開啟）。

### 5.2 廣告
- **否，我的應用程式不含廣告。**

### 5.3 應用程式存取權
- **所有功能都不需要特殊存取權即可使用**（沒有登入、沒有付費牆）。
- 注意：位置權限拒絕後仍可手動選城市，所以不需要提供測試帳號或說明。

### 5.4 內容分級（IARC 問卷）
來源：[內容分級](https://support.google.com/googleplay/android-developer/answer/9898843)
1. 電子郵件填開發者信箱。
2. 類別選 **「所有其他應用程式類型」**（本 App 不是遊戲、社群或通訊軟體；若選項中有「參考資料、新聞或教育」，選那一項亦可）。
3. 各題答案：
   - 暴力、恐怖、性、裸露、髒話、粗俗幽默、毒品／酒精／菸草、賭博或模擬賭博：**全部「否」**。（星座神話介紹是文字敘述，沒有暴力或性的描寫。）
   - 使用者之間能否互動或交流（聊天、分享內容）：**否**
   - 是否會將使用者的實際位置分享給其他使用者：**否**（位置只在手機上使用）
   - 是否可購買數位商品：**否**（目前沒有內購；日後加入時要重新填寫問卷）
   - 是否是網頁瀏覽器或搜尋引擎：**否**
   - 是否含有使用者產生的內容：**否**
4. 預期結果：各地區最低分級（例如「3 歲以上」「普遍級」）。

### 5.5 目標對象和內容（Target audience）
來源：[Google Play 家庭政策](https://support.google.com/googleplay/android-developer/answer/9893335)
- 建議勾選：**13–15 歲、16–17 歲、18 歲以上**（不要勾 12 歲以下）。
- 「App 是否可能無意間吸引兒童？」→ **否**（商店文案與圖像已避免以兒童為訴求）。
- 為什麼不選 12 歲以下？一旦目標對象包含兒童，就要遵守「家庭政策」：Google 可能要求加入中立的年齡篩選、所有 SDK 必須是家庭認證、送審更嚴格；而且**專門以兒童為對象的 App 不得要求位置權限**，會直接衝突本 App 的定位功能。選 13 歲以上不妨礙小朋友在家長陪同下使用，但可避免這些限制。
- 取捨：選 13+ 就**不能**申請「老師認可」或在兒童專區曝光。若將來想做兒童版，應另外設計（例如完全不要求定位、只手動選城市）。

### 5.6 資料安全性（Data safety）
來源：[提供資料安全性部分的資訊](https://support.google.com/googleplay/android-developer/answer/10787469)

Google 的定義：
- 「**收集**」＝把資料從使用者裝置傳出去。
- 「**只在裝置上本機處理、不會傳出裝置的使用者資料，不需要揭露。**」

本 App 的位置、方向感測資料都只在手機上計算、存在手機的 localStorage，從未傳出裝置；字型與 App 檔案的下載只是一般網頁請求（GitHub／Google 會看到 IP，但開發者沒有收集或取得這些資料，也沒有加入任何 SDK）。因此：

1. 「您的應用程式是否會收集或分享任何必要的使用者資料類型？」→ **否**
2. 系統會顯示摘要「沒有收集資料」「沒有與第三方分享資料」→ 儲存。
3. 若後續頁面問到安全性作法：資料傳輸是否加密 → 本 App 所有連線都是 HTTPS；因為沒有收集資料，「使用者可要求刪除資料」可視畫面選項選不適用。

> ⚠️ 何時要改：如果日後加入分析工具（例如 Google Analytics、Firebase）、當機回報、廣告、帳號或內購驗證伺服器，就會開始「收集」資料，必須在上線前更新 Data safety 與 privacy.html。

### 5.7 廣告 ID
- 「您的應用程式是否使用廣告 ID？」→ **否**。
- 如果 Play Console 顯示「宣告中未使用廣告 ID，但資訊清單含有 `com.google.android.gms.permission.AD_ID`」的警告，請 Android 流程在 manifest 移除該權限（`tools:node="remove"`）再重新建置；本 App 本身不使用它。

### 5.8 政府應用程式
- **否**（不是由政府機關開發或代表政府）。

### 5.9 金融功能
- 選 **「我的應用程式不提供任何金融功能」**。

### 5.10 健康
- **否／不含健康功能**（沒有健身、醫療、健康資料等功能）。

### 5.11 新聞應用程式
- **否**，不是新聞或雜誌應用程式。

### 5.12 其他可能出現的項目
- **COVID-19 接觸追蹤或狀態應用程式**：否。
- **權限宣告（敏感權限）**：目前的 Android 外殼（見 `android/twa-manifest.json`）**沒有開啟定位委派**，App 本身不宣告任何位置權限；定位是由 Chrome 以網站權限向使用者詢問。所以一般不會出現位置權限宣告。Google 公告將於 **2026 年 11 月**推出前景「精確位置」宣告工具、**2027-01-27** 起全面執行「最小範圍」規定；若日後改為開啟定位委派，請只宣告 `ACCESS_COARSE_LOCATION`（約 1 公里精度就夠畫星空）。來源：[前景位置存取的最小範圍](https://support.google.com/googleplay/android-developer/answer/17033915)
- **相片與影片權限、全螢幕通知、前景服務、精確鬧鐘**：本 App 都沒有使用；若 Console 詢問，回答未使用。

---

## 6. 封閉測試（必經：12 人 × 連續 14 天）

來源：[新個人開發人員帳戶的應用程式測試規定](https://support.google.com/googleplay/android-developer/answer/14151465)、[設定開放、封閉或內部測試](https://support.google.com/googleplay/android-developer/answer/9845334)

### 6.1 建立測試人員名單（建議用 Google 群組）
1. 到 https://groups.google.com 建立群組，例如「頭頂星空測試」，群組電子郵件如 `toudingxingkong-testers@googlegroups.com`。
2. 設定「誰可以加入群組」→ **任何人都可以要求加入**或由你邀請；「誰可以查看成員」→ 僅限管理員（保護測試者隱私）。
3. 把親友的 **Gmail（手機上 Play 商店登入的帳號）** 加入群組，或請他們自行申請加入。

### 6.2 建立封閉測試軌道
1. Play Console →「測試與發布」→「測試」→「封閉測試」→ 預設軌道「Closed testing - Alpha」→「管理軌道」。
2. 「測試人員」分頁 → 選 **Google 群組** → 填群組電子郵件 → 儲存。
3. 「意見回饋網址或電子郵件」填 GitHub Issues：https://github.com/s70680/s70680.github.io/issues
4. 「國家／地區」至少選 **台灣**（有海外親友就一起勾）。
5. 建立版本 → 上傳 `.aab`（第 3 節）→ 版本名稱 1.0.0 → 版本資訊（繁中）例如「第一個測試版：全天星圖、指向模式、88 星座中文介紹」→ 送審。
6. 審核通過後（通常數小時到數天），在「測試人員」分頁複製 **「加入測試」網址**（opt-in URL，格式類似 `https://play.google.com/apps/testing/io.github.s70680.sky`）。

### 6.3 測試人員要做的事
把 [`tester-invite.md`](tester-invite.md) 的訊息貼到 LINE：
1. 用手機的 Gmail 加入 Google 群組（或回覆你他的 Gmail 由你加入）。
2. 用**同一個 Gmail** 在手機瀏覽器開啟「加入測試」網址 → 按「成為測試人員」。
3. 點「在 Google Play 下載」安裝。
4. **14 天內不要退出測試、不要解除安裝**；有空打開用一用並回報問題。

### 6.4 14 天怎麼算、要注意什麼
- 計算的是「**同時處於已加入狀態**」的測試人員至少 12 位、**連續** 14 天。中途退出再加入的人，天數要重新連續計算。
- **建議邀請 15～20 人**，預留有人忘記加入或誤退出的緩衝。
- Play Console 的「資訊主頁」會顯示「已加入測試的人數／天數」進度。
- 測試期間可以上傳更新版（例如修正問題），**不會**重置 14 天。每次修正都記下來，申請正式版時要寫。

---

## 7. 申請正式版存取權（Production access）

條件達成後，Play Console 首頁 →「申請正式版存取權」。表單分三部分，以下是可直接參考改寫的草稿（請依實際測試情形修改）：

**第一部分：關於封閉測試**
- 你如何招募測試人員？
  > 邀請家人、朋友與同事（共約 N 位）透過 Google 群組加入封閉測試，請他們在日常生活與晚上觀星時使用。
- 測試人員的參與情形？
  > 測試期間多數測試人員每週開啟數次，主要使用全天星圖、指向模式與星座介紹；也有人在戶外無網路環境測試離線功能。
- 意見回饋摘要？
  > 收到的回饋包括：（例）指向模式剛開啟時方向需要幾秒校正、希望星座介紹字體更大、部分機型第一次開啟定位較慢。

**第二部分：關於你的應用程式**
- 目標對象？
  > 對星空有興趣、想認識星座的一般大眾（13 歲以上），特別是台灣使用者，介面為繁體中文。
- 應用程式的價值？
  > 依使用者位置與時間即時顯示頭頂星空，提供 88 星座與亮星的繁體中文介紹、台灣慣用譯名、夜間紅光模式與離線使用，適合在山上觀星時使用。
- 預估第一年安裝數？
  > 選最低一級（例如 0–10,000）即可，照實估計。

**第三部分：關於正式版準備**
- 根據測試做了哪些修改？
  > （例）修正某些機型指向模式方向偏差、調整字體大小、改善定位失敗時的提示。（沒有修改也要說明測試確認了哪些功能運作正常。）
- 你如何判斷已準備好正式發布？
  > 所有測試人員都能正常安裝與開啟，主要功能（星圖、定位、指向模式、星座介紹、離線）在多種 Android 機型上測試通過，沒有未解決的當機問題。

審核通常 **7 天內**完成，結果以電子郵件通知。被拒絕時，信中會說明原因；通常是測試人數或天數不足、或回答太簡略，補足後可再申請。

---

## 8. 正式發布

1. 取得正式版存取權後：「測試與發布」→「正式版」→「建立新版本」→ 可直接從封閉測試**升級**同一個版本（不必重新上傳）。
2. 國家／地區：先選 **台灣**（之後可再增加）。
3. 發布方式：可選**分階段發布**，例如先 20%，觀察幾天沒問題再調到 100%。
4. 送審：首次正式版審核可能需要數天，最長可達一週以上。
5. 上架後：到商店頁確認文字、圖片、隱私權政策連結都正確；從商店安裝一次，確認上方**沒有網址列**。

---

## 9. 日後更新

- 網頁內容（`sky/` 裡的檔案）更新後推到 GitHub Pages，**App 會自動拿到新內容**，不用重新上架。
- 只有改 Android 外殼（圖示、名稱、權限、target API 等）才需要重新建置 `.aab`，並把 versionCode 加 1 後上傳。
- 每年留意 Google 的 target API 規定（通常每年 8 月底提高一級）。
- 改變資料處理方式時，先更新 privacy.html 與 Data safety。

---

## 10. 未來想收費：Play 結帳（Play Billing）

- Google Play 上的數位內容（例如解鎖進階功能）必須使用 **Google Play 結帳系統**。
- TWA 的做法：網頁透過 **Digital Goods API**（查商品與購買狀態）＋ **Payment Request API**（以 Google Play 為付款方式）。需求：Chrome 101 以上、Bubblewrap 1.8.2 以上並在 `twa-manifest.json` 開啟 `playBilling`（及 `alphaDependencies`）、有效的 Google 付款商家帳戶、App 已在任一測試軌道上架。來源：[在 TWA 使用 Play 結帳收款](https://developer.chrome.com/docs/android/trusted-web-activity/receive-payments-play-billing)
- 購買後必須由**後端伺服器**確認（acknowledge），否則 3 天後會自動退款——這代表需要一個伺服器，屬於「收集資料」，要同步更新 privacy.html 與 Data safety。
- App 本身維持**免費**，用內購解鎖功能；開始營利後，Google 會公開你的**完整地址**（見第 0 節）。
- 授權面：原本授權不明的銀河輪廓資料已在 2026-10-05 換成由 ESO 銀河全景照片（CC BY 4.0）產生的資料（見第 13 節）；收費後仍要保留 ESO/S. Brunier 的出處標示與 CC BY-SA 星名資料的標示。

---

## 11. 檢查清單

- [ ] 開發者帳號：個人、US$25、身分驗證通過
- [ ] 裝置驗證完成（Play Console App）
- [ ] 建立應用程式：zh-TW、應用程式、免費
- [ ] `.aab` 上傳到封閉測試；選 Google 產生的應用程式簽署金鑰
- [ ] 應用程式簽署金鑰 SHA-256 → `.well-known/assetlinks.json` → 推送 → 驗證無網址列
- [ ] 商店資訊：名稱、簡短說明、完整說明（zh-TW＋en-US）、圖示、主題圖片、≥2 張手機截圖、類別「教育」、聯絡信箱、網站
- [ ] 隱私權政策網址
- [ ] 廣告：否
- [ ] 應用程式存取權：全部功能可直接使用
- [ ] 內容分級問卷完成
- [ ] 目標對象：13–15、16–17、18+；不會吸引兒童
- [ ] Data safety：不收集、不分享
- [ ] 廣告 ID：否（manifest 無 AD_ID 權限）
- [ ] 政府／金融／健康／新聞：否
- [ ] 確認 App 沒有宣告精確位置權限（目前 TWA 不宣告任何位置權限）
- [ ] Google 群組建立、封閉測試軌道審核通過、取得 opt-in 網址
- [ ] 邀請 15～20 位測試人員，確認 ≥12 人加入
- [ ] 連續 14 天（期間持續修正與記錄回饋）
- [ ] 申請正式版存取權（第 7 節草稿）
- [ ] 通過後建立正式版、選台灣、（可選）分階段發布

## 12. 實際時程預估

| 時間 | 事項 |
|---|---|
| 第 0～3 天 | 註冊帳號、付費、身分驗證（可能 1～3 天）、裝置驗證 |
| 第 1～4 天 | 建立 App、上傳 .aab、填完所有「應用程式內容」、商店資訊；封閉測試送審（數小時～數天） |
| 第 3～5 天 | 更新 assetlinks.json；發 LINE 邀請，湊滿 12 人以上 |
| 第 5～19 天 | 連續 14 天封閉測試（期間可更新版本） |
| 第 19 天 | 申請正式版存取權 |
| 第 19～26 天 | Google 審核（通常 7 天內） |
| 第 26～30 天 | 建立正式版、審核、上架 |

**合計約 4～6 週**。最常見的延誤是測試人員沒有真的按下「成為測試人員」，或用了和 Play 商店不同的 Gmail——開始 14 天計時前，務必在 Play Console 確認人數已達 12 人以上。

---

## 13. 內嵌資料的授權稽核（2026-09-29；銀河資料 2026-10-05 更新）

> 不是法律意見；依各來源公開的授權文字整理。

| 元件 | App 內用途 | 上游來源 | 授權條款 | 可用於 Play 商業發布？ | 需要的動作 |
|---|---|---|---|---|---|
| Astronomy Engine | `astronomy.browser.min.js`，計算太陽、月亮、行星位置與星座判定 | [cosinekitty/astronomy](https://github.com/cosinekitty/astronomy) | MIT | ✅ 可以 | 保留授權文字（檔案開頭已有；licenses.html 已附全文） |
| 恆星位置／星等／色指數 `STAR_DATA`（5,045 顆） | 星圖上的星點 | d3-celestial `stars.6.json` ← XHIP（[VizieR V/137D](https://cdsarc.cds.unistra.fr/viz-bin/cat/V/137D)）／Hipparcos | d3-celestial：[BSD-3-Clause](https://github.com/ofrohn/d3-celestial/blob/master/LICENSE)；CDS 資料以開放授權發布並要求註明出處（[CDS Legals](https://cds.unistra.fr/legals/)） | ✅ 可以 | 保留 BSD 聲明與 CDS/Hipparcos 出處（已加入） |
| 星名、Bayer 編號 `STAR_INFO` 的英文名與編號 | 點星星時顯示的名稱 | d3-celestial `starnames.json`（Kostjuk 2002 交叉索引、IAU 星名） | BSD-3-Clause（d3-celestial）；星名為事實資料 | ✅ 可以 | 無 |
| **中國傳統星名** `STAR_INFO` 第 4 欄（2,513 筆，如「參宿七」） | 星名標籤與介紹 | d3-celestial `starnames.cn.json` ← [Stellarium「Chinese」星空文化](https://github.com/Stellarium/stellarium/tree/master/skycultures/chinese) | **CC BY-SA 4.0**（Stellarium 官方 description.md／info.ini 明載） | ✅ 可以（CC BY-SA 允許商業使用） | 必須**姓名標示**＋**相同方式分享**：已在 licenses.html、NOTICE.md 標示作者與授權，並聲明這份改作星名表以 CC BY-SA 4.0 提供。比對結果：2,468／2,513 筆與 Stellarium 現行資料一致，其餘為簡繁轉換差異（斗／鬥）。 |
| 星座連線 `CON_LINES`、名稱位置 `CON_LABELS`、等級 `CON_RANK` | 星座連線與標籤 | d3-celestial `constellations*.json` ← IAU 星座資料，經 Olaf Frohn 修改 | BSD-3-Clause | ✅ 可以 | 無（已標示） |
| 星座邊界 `CON_BOUNDS` | 星座範圍（點選判定與邊界線） | Davenhall & Leggett 1989（[VizieR VI/49](https://cdsarc.cds.unistra.fr/viz-bin/cat/VI/49)），經 d3-celestial | BSD-3-Clause＋CDS 出處 | ✅ 可以 | 無（已標示） |
| **銀河 `MW_DATA`**（3,388 點、5 個亮度等級；2026-10-05 起） | 銀河圖層 | ESO「[The Milky Way panorama](https://www.eso.org/public/images/eso0932a/)」（eso0932a，Credit: ESO/S. Brunier），由 `tools/milkyway/build_milkyway.py` 計算產生（App 內不含照片本身） | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)（[ESO 使用條款](https://www.eso.org/public/copyright/)：網站上的圖片除另有註明外都採 CC BY 4.0） | ✅ 可以（CC BY 允許商業使用） | 必須**姓名標示**、標明有改作、不得暗示 ESO 背書：licenses.html、NOTICE.md 與「圖層」設定的說明文字都已加入 ESO/S. Brunier 與授權連結 |
| ~~銀河輪廓（舊）~~ | 2026-10-05 前的銀河圖層 | d3-celestial `mw.json` ← Jose R. Vieira「Milky Way Outline Catalog」；輪廓 2–5 由 Axel Mellinger 的銀河全景照片描出 | 原作者未聲明任何授權（[issue #160](https://github.com/ofrohn/d3-celestial/issues/160)）；Mellinger 全景照片的[商業使用需付授權費](https://www.milkywaysky.com/licenses.html) | ⚠️ 不確定 | **已移除**，由上一列取代 |
| 深空天體清單 `DSO`（27 筆） | 星雲星團圖層 | 本專案整理（座標為科學事實） | — | ✅ 可以 | 無 |
| 中文介紹（星座、亮星、行星、深空天體） | 介紹文字 | 本專案撰寫 | 作者自有 | ✅ 可以 | 無 |
| 字型 Noto Serif TC、IBM Plex Mono | 介面文字 | Google Fonts | SIL OFL 1.1 | ✅ 可以（執行時從 Google Fonts 載入，未打包） | licenses.html 已附 OFL 全文 |

### 銀河資料的處理結果（2026-10-05）

原本的銀河輪廓權利鏈不完整，已改用**明確允許商業使用**的來源重新產生，渲染程式與資料格式都沒有改：

1. 來源：ESO 的「The Milky Way panorama」（[eso0932a](https://www.eso.org/public/images/eso0932a/)，Credit: ESO/S. Brunier），依 [ESO 使用條款](https://www.eso.org/public/copyright/)採 CC BY 4.0。頁面上「因版權原因無法提供 8 億像素原圖」只是說明原始超大圖要向攝影者索取，ESO 發布的 6000 × 3000 版本本身沒有另外註明例外。
2. 做法：`tools/milkyway/build_milkyway.py` 下載照片（固定版本、核對 SHA-256 與內嵌的 ESO 中繼資料）→ 用 App 自己的星表比對照片中的星點，量出照片座標框與銀河座標差 3.8°，先校正 → 移除星點、平滑 → 取樣在原本的 20,000 點 Fibonacci 格點上，各亮度等級的天空面積和舊資料相同 → 刪除與銀河盤面不相連的區塊（大小麥哲倫雲、M31、昴宿星團、獵戶座大星雲、照片中的行星）。說明與驗證數字在 `tools/milkyway/README.md`。
3. 標示：licenses.html、NOTICE.md、README、「圖層」設定的說明文字與商店完整說明都已加上 ESO/S. Brunier 與 CC BY 4.0。

先前建議的 Gaia DR3 沒有採用：Gaia 檔案庫資料實際採 **CC BY-NC 3.0 IGO**，商業使用前要先向 ESA 申請授權（[Gaia 授權頁](https://www.cosmos.esa.int/web/gaia-users/license)、[ESDC 條款](https://www.cosmos.esa.int/web/esdc/terms-and-conditions)）；ESA 對外發布的 Gaia 全天圖雖標示 CC BY-SA 3.0 IGO，但底層資料的非商業條款容易引起爭議，所以避開。
