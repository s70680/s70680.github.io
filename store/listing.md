# Google Play 商店資訊（頭頂星空）

> 直接複製到 Play Console →「發布商品資訊（Store presence）」→「主要商品詳情」。字數以 Play Console 的計算方式（每個中英文字、標點、空白都算 1 個字元）用程式實際計算。

## 基本設定

| 欄位 | 內容 |
|---|---|
| 套件名稱 | `io.github.s70680.sky` |
| 預設語言 | 中文（台灣）– zh-TW |
| 應用程式或遊戲 | 應用程式 |
| 免費或付費 | 免費 |
| 應用程式類別 | **教育**（替代方案：書籍與參考資源） |
| 標記（Tags） | 天文、教育、科學（在 Play Console「商店設定 → 標記」從清單中挑選最接近的最多 5 個，清單內沒有的就跳過） |
| 聯絡電子郵件 | Play Console 規定必填（會公開顯示）。建議另開一個專用 Gmail，不要用私人或公司信箱 |
| 網站 | https://s70680.github.io/sky/ |
| 隱私權政策網址 | https://s70680.github.io/sky/privacy.html |

為什麼選「教育」：App 的核心是認識星座與天體（中文介紹、神話與觀賞方法），與 Google Play「教育」類別最相符；manifest 也已宣告 `education`。

## 繁體中文（zh-TW，預設語言）

### 應用程式名稱（11 / 30 字元）

```
頭頂星空：星座盤與星圖
```

### 簡短說明（40 / 80 字元）

```
依你的位置與時間，畫出頭頂的星空、行星、銀河與 88 星座，點一下就有中文介紹。
```

### 完整說明（944 / 4000 字元）

```
抬頭看到一顆很亮的星，想知道它叫什麼？頭頂星空依照你所在的位置與現在的時間，即時畫出此刻天上的星星、行星、月亮與銀河，點一下星座或星星，就有淺顯易懂的中文介紹。

【主要功能】
• 頭頂全天星圖：像星座盤一樣的圓形視野，單指拖曳旋轉、雙指縮放。
• 指向模式：把手機舉向天空，星圖會跟著手機方向轉動，對照實際星空找星座（需要手機有陀螺儀與電子羅盤）。
• 88 個星座：使用台灣慣用譯名，介紹神話由來、如何辨認與觀賞重點，並列出今天的升起、最高與落下時間。
• 亮星與中國傳統星名：天狼星、織女星、牛郎星、北極星等常見亮星的中文介紹，以及兩千多顆恆星的中國傳統星名（例如參宿七、河鼓二）。
• 太陽、月亮與八大行星：即時計算位置，並顯示月相。
• 著名深空天體：仙女座星系、獵戶座大星雲、昴宿星團、大小麥哲倫雲等，附中文說明。
• 時間調整與快轉：查看今晚 9 點或任何時刻的星空，也能快轉看星星東升西落。
• 地點：可使用手機定位，也能選擇台灣各縣市、合歡山、阿里山、鹿林天文台等觀星景點與海外城市，或自行輸入經緯度。
• 圖層開關：星座連線、星座名稱、亮星名稱、銀河、星雲星團、黃道、方位高度網格。
• 夜間紅光模式：整個畫面變成紅色，保護暗適應，觀星時眼睛不會被螢幕光刺激。
• 離線使用：開啟過一次之後，到山上沒有訊號的觀星地點也能使用。

【適合誰】
• 第一次想認識星座的人
• 喜歡觀星、露營、上山看星空的人
• 想快速查「那顆亮星是什麼」的人

【隱私】
不需要註冊，沒有廣告，也沒有任何分析或追蹤工具。位置與方向感測資料只在手機上用來計算星空，不會傳送給開發者。

【資料來源】
天體位置以開源的 Astronomy Engine 計算；星表與星座連線資料來自 d3-celestial（依巴谷星表等），銀河依歐洲南方天文台（ESO）的銀河全景照片產生（ESO/S. Brunier，CC BY 4.0），中國傳統星名來自 Stellarium 星空文化資料。完整授權說明可在 App 內「圖層」→「資料來源與授權」查看。

有任何問題或建議，歡迎到 GitHub 留言：https://github.com/s70680/s70680.github.io/issues
```

## 英文（en-US，選填的翻譯）

在 Play Console「商品詳情 → 管理翻譯 → 新增自己的翻譯」加入 English (United States)。因為 App 介面只有中文，說明中已明白寫出「介面與介紹為繁體中文」，避免外國使用者誤會。

### App name（29 / 30）

```
Sky Above: Star Map (Chinese)
```

### Short description（78 / 80）

```
See the stars, planets, Milky Way and 88 constellations above you, in Chinese.
```

### Full description（1880 / 4000）

```
Wondering what that bright star is? 頭頂星空 (Sky Above) draws the sky for your location and the current time: stars, planets, the Moon and the Milky Way. Tap any constellation or star to read a short introduction. The app's interface and descriptions are in Traditional Chinese (Taiwan).

FEATURES
• All-sky dome view like a planisphere: drag to rotate, pinch to zoom.
• Pointing mode: hold your phone up to the sky and the chart follows it (requires a gyroscope and compass).
• All 88 constellations with their myths, how to find them, and today's rise, transit and set times.
• Bright stars with Chinese descriptions, plus traditional Chinese names for more than 2,000 stars.
• Sun, Moon and the eight planets computed in real time, with the lunar phase.
• Famous deep-sky objects such as the Andromeda Galaxy, the Orion Nebula, the Pleiades and the Magellanic Clouds.
• Time controls: jump to 9 pm tonight or any moment, or fast-forward to watch the sky turn.
• Location from your phone, from a list of places in Taiwan and abroad, or entered as coordinates.
• Layer switches: constellation lines and names, star names, Milky Way, deep-sky objects, ecliptic, alt-azimuth grid.
• Night red mode to protect your dark adaptation.
• Works offline after the first launch.

PRIVACY
No sign-up, no ads, no analytics or tracking. Location and motion-sensor data are used only on your device to draw the sky and are never sent to the developer.

DATA SOURCES
Positions are computed with the open-source Astronomy Engine. Star and constellation data come from d3-celestial (Hipparcos and other catalogues); the Milky Way is generated from ESO's Milky Way panorama (credit: ESO/S. Brunier, CC BY 4.0); traditional Chinese star names come from the Stellarium sky-culture data. Full notices are available in the app.

Questions or suggestions: https://github.com/s70680/s70680.github.io/issues
```

## 圖像素材（由圖像製作流程產出，路徑不要改）

| 欄位 | 檔案 | 規格（Google 規定） |
|---|---|---|
| 應用程式圖示 | `store/graphics/icon-512.png` | 512×512 px，32 位元 PNG（含 alpha），≤ 1 MB |
| 主題圖片（Feature graphic） | `store/graphics/feature-graphic.png` | 1024×500 px，JPEG 或 24 位元 PNG（不可有透明） |
| 手機螢幕截圖 | `store/graphics/phone/` 內的檔案 | 至少 2 張、最多 8 張；JPEG 或 24 位元 PNG（不可有透明）；最短邊 ≥ 320 px、最長邊 ≤ 3840 px，長邊不可超過短邊 2 倍 |

平板截圖不是必填，但圖像流程已提供：`store/graphics/tablet-7in/`（7 吋平板）與 `store/graphics/tablet-10in/`（10 吋平板），建議一併上傳。各資料夾內的 `raw/` 是原始截圖，上傳時使用資料夾第一層的檔案。

圖示以外的圖（含連結預覽圖 `sky/og-image.png`）都由 `tools/store-graphics/build_store_graphics.py` 從 App 截圖產生，App 畫面有改時重跑一次即可（說明見 [`tools/store-graphics/README.md`](../tools/store-graphics/README.md)）。2026-10-05 已用新的銀河資料重新產生。

## 撰寫原則（已遵守，日後修改時也請注意）

- 目標年齡層選 13 歲以上時，商店文字不要寫「適合小朋友／兒童」，以免被認定「無意間吸引兒童」而套用家庭政策。
- 只寫 App 真的有的功能；例如沒有推播通知、沒有 AR 相機畫面，就不要寫。
- 不堆疊關鍵字、不寫「最好」「第一名」「免費」等促銷字眼在名稱中（違反 [Google Play 中繼資料政策](https://support.google.com/googleplay/android-developer/answer/9898842)）。
- 不用別人的商標當關鍵字（例如不要寫「比 Stellarium／Star Walk 更好」）。
