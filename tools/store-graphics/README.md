# 上架圖片產生工具

`build_store_graphics.py` 直接從 App（`sky/index.html`）截圖，重新產生 Google Play 上架圖片與連結分享預覽圖。App 畫面有改的時候（例如 2026-10-05 換成 ESO 照片產生的銀河）重跑一次即可，版面、場景與標題文字都和 2026-09-29 第一次上架的圖相同。

## 產生的檔案

| 檔案 | 尺寸（px） | 內容 |
|---|---|---|
| `store/graphics/phone/01～08-*.png` | 1080 × 1920 | 標題文字＋加框的 App 畫面，共 8 張（Google Play 上限） |
| `store/graphics/phone/raw/` | 1080 × 1920 | 沒有標題的原始截圖（手機 360 × 640 CSS px，3 倍） |
| `store/graphics/tablet-7in/01、02-*.png`（含 `raw/`） | 1200 × 1920 | 7 吋平板（600 × 960 CSS px，2 倍） |
| `store/graphics/tablet-10in/01、02-*.png`（含 `raw/`） | 1920 × 1200 | 10 吋平板（1280 × 800 CSS px，1.5 倍） |
| `store/graphics/feature-graphic.png` | 1024 × 500 | 主題圖片：左邊名稱與說明，右邊星空圓盤 |
| `store/graphics/preview.png` | 1560 × 2332 | 以上全部的總覽，只給人檢查用，不上傳 |
| `sky/og-image.png` | 1200 × 630 | LINE、Facebook 等的連結預覽圖（`index.html` 與 `sky/index.html` 的 `og:image`） |

`store/graphics/icon-512.png` 不會動到。

## 使用方式

```bash
pip install playwright pillow numpy        # Python 3.9 以上
python -m playwright install chromium      # 已經裝過 Playwright 的 Chromium 就跳過
python3 tools/store-graphics/build_store_graphics.py                  # 全部重做，直接寫回 repo
python3 tools/store-graphics/build_store_graphics.py --only phone,og   # 只做其中幾項
python3 tools/store-graphics/build_store_graphics.py --out /tmp/gfx --compare-ref main --compare-out /tmp/cmp
                                                                      # 寫到別的資料夾，並輸出和 main 的新舊對照圖
```

| 選項 | 說明 |
|---|---|
| `--only` | `phone`、`tablet-7in`、`tablet-10in`、`feature`、`og`、`preview`，用逗號分隔；選 `preview` 時會全部重做（總覽要用到所有圖） |
| `--out` | 輸出的根資料夾，預設是 repo 本身 |
| `--app` | 要截圖的網站資料夾（裡面要有 `sky/index.html`），預設是 repo 本身；可以指定另一個 checkout 來拍舊版 App |
| `--canvas-dpr` | 星圖畫布的解析度倍數，預設 3（見下面「怎麼拍」） |
| `--compare-ref`、`--compare-out` | 和某個 git 版本的圖並排比較：舊、新、差異放大 4 倍，並列出差超過 32/255 的像素比例 |

第一次執行會把字型下載到 `tools/store-graphics/.cache/`（下載約 42 MB，解開後約 60 MB，不進 git），之後重複使用。在 2 vCPU 的雲端機器上全部重做約 1.5～2 分鐘。

結束時會逐檔檢查 Google Play 的規格（24 位元 PNG、不可有透明、尺寸正確、長邊不超過短邊 2 倍、8 MB 以內、手機截圖 2～8 張）；任何一張不合格，或某個場景的畫面不對，就以非 0 結束。

只在 Linux（Chromium 141.0.7390.37、Playwright 1.56.0、Pillow 12.3.0）上驗證過：同一台機器重跑，27 個檔案逐位元組相同。Windows、macOS 用的字型檔相同，但文字反鋸齒的方式不同，像素可能有些微差異。Windows 上把 `python3` 換成 `python` 或 `py`。

## 場景

| 檔名 | 畫面 | 怎麼進入 |
|---|---|---|
| 01-sky-now | 頭頂全天星圖 | 開啟 App |
| 02-constellation-orion | 獵戶座介紹卡 | 星座清單 → 搜尋「獵戶」→ 點獵戶座 |
| 03-planet-jupiter | 木星介紹卡 | 星座清單 → 點木星 |
| 04-star-sirius | 天狼星介紹卡 | 星座清單 → 搜尋「大犬」→ 大犬座 → 天狼星 →「在星空中置中」 |
| 05-constellation-list | 星座清單 | 點「星座」 |
| 06-time-fastforward | 時間面板快轉中 | 點「時間」→ 快轉剛好 30 個畫格（每格 1 分鐘，21:00 → 21:30） |
| 07-location | 觀測地點面板 | 點地點 → 選「合歡山」 |
| 08-red-night-mode | 紅光模式 | 點「紅光」 |

- 上架截圖與主題圖片：**2027-02-06（週六）21:00 台北時間**、地點台北。這天是新月，冬季銀河在頭頂，火星、木星都在天上；2026-09 第一次上架的圖也用這個時間。
- 連結預覽圖：**2026-09-29 21:00**（第一次做預覽圖的那個晚上），圖層用 App 預設值。
- 主題圖片的星空圓盤只開星座連線、星座名稱與銀河，不顯示亮星名稱、星雲星團、黃道與網格。
- 標題文字（每張上方的小標、大標、副標）寫在腳本的 `SHOTS`，是從 2026-09 的圖抄下來的；要改文字就改那裡。

## 怎麼拍

- 在本機 127.0.0.1 開一個網站伺服器，用無頭 Chromium 開 `sky/`。頁面的時鐘固定在場景時間（`new Date()` 一律回傳那個時間）。localStorage 先寫好「回訪使用者」的狀態：手動選的地點、已看過操作提示、已關掉安裝卡。另外模擬觸控螢幕、深色模式、減少動態效果，並封鎖 service worker。
- 每個場景都是點真的介面（清單、搜尋框、按鈕）進去，不直接改 App 內部狀態，所以截到的就是使用者會看到的畫面。
- 截圖前會檢查：時間膠囊（例如「2/6 週六 21:00」）、開著的是哪一種卡片與標題、卡片捲到最上面（選地點的場景另外檢查地點、快轉場景檢查停在 21:30），而且畫面上沒有操作提示、toast 訊息或安裝卡。任何一項不對就中止，不會產生錯的圖。
- 字型：App 向 Google Fonts 要的 Noto Serif TC、IBM Plex Mono，由本機的同名字型檔回應（fontsource 打包的 Google Fonts 版本，同樣依 unicode-range 切片）。App 的介面字型清單第一個是「PingFang TC」，Android 手機上實際會用 Roboto（英數）＋ Noto Sans CJK TC（中文）；腳本把這一組放在「PingFang TC」這個名字底下，所以不管在哪台電腦跑，用的字都和 Android 手機一樣。
- 星圖畫布以 3 倍解析度繪製。App 為了省電把畫布上限設在 2 倍，腳本只在截圖時把上限改成 3 倍（不改 repo 裡的檔案），星點和細線比較清楚；2026-09 的圖也是這樣做的。要完全照手機實際畫面，加 `--canvas-dpr 2`。
- App 啟動時會先排一次版面，有時字型還沒載入完；腳本等字型載入後再送一次 resize（和手機轉向時一樣），確保每次結果相同。
- 快轉場景攔截 `requestAnimationFrame` 計算畫格數，讓快轉剛好前進 30 分鐘。
- 加標題、外框、背景漸層與總覽圖用 Pillow 合成；連結預覽圖的文字版面是 HTML，由同一個 Chromium 以 1 倍渲染。

## 字型來源與授權

全部字型都是第一次執行時下載，核對檔案大小與 SHA-256 才使用，不進 git。

| 字型 | 版本與來源 | 授權 | 用途 |
|---|---|---|---|
| Noto Serif TC（可變字重） | npm `@fontsource-variable/noto-serif-tc` 5.3.0 | SIL OFL 1.1 | App 標題、星圖標籤 |
| IBM Plex Mono 400／500 | npm `@fontsource/ibm-plex-mono` 5.3.0 | SIL OFL 1.1 | App 的時間與數字 |
| Roboto | npm `@fontsource/roboto` 5.3.0 | SIL OFL 1.1 | 模擬 Android 系統字（英數） |
| Noto Sans TC Regular／Medium／Bold | GitHub `notofonts/noto-cjk` Sans2.004（SubsetOTF/TC） | SIL OFL 1.1 | 模擬 Android 系統字（中文）、上架圖的小標與副標 |
| Noto Serif TC Bold | GitHub `notofonts/noto-cjk` Serif2.002（SubsetOTF/TC） | SIL OFL 1.1 | 上架圖與預覽圖的大標 |
| DejaVu Sans Mono | npm `dejavu-fonts-ttf` 2.37.3 | Bitstream Vera 授權（DejaVu 的修改為公眾領域） | 預覽圖上的網址 |

OFL 與 Bitstream Vera 授權只規範字型檔本身；用字型做出來的圖片可以自由使用，不需要另外標示。

## 2026-10-05 重做紀錄

用這個腳本產生目前 repo 裡的圖，取代 2026-09-29 的版本（`--compare-ref` 的對照圖不進 git）。和舊圖逐一比對後，差異來源有三種：

1. **銀河**（這次重做的目的）：全部的圖都有，換成 ESO 照片產生的資料（見 [`tools/milkyway/`](../milkyway/)）。銀河很淡，任一像素任一色版最多差 32/255。
2. **獵戶座、天狼星介紹卡的「接下來」時間**：差 1～4 分鐘，獵戶座最高高度從 71° 變成 72°。原因是 2026-10-04 的修正（commit 1862107：恆星與星座的升落時間改用當日的赤經赤緯（加入歲差與章動），並採用 −34′ 的標準大氣折射），舊圖拍的是修正前的 App。用修正前、後兩版 App 分別重拍確認過，只有出現這兩張卡的 4 張圖（手機 02、04，7 吋與 10 吋平板 02）受影響；新圖是現行 App 的正確數字。
3. **截圖工具不同**：2026-09 的圖不是用這個腳本做的。用同一版 App 重拍和舊圖比，星星、標籤、文字的內容與位置都相同，只有文字反鋸齒與不到 1 像素的位置差：多數圖 0.1～0.6% 的像素差超過 32/255；紅光模式（紅字黑底對比高）、7 吋平板的全天星圖與連結預覽圖是 1.9～3.6%。

連結預覽圖換新後，LINE、Facebook 可能還會顯示快取的舊圖一段時間。要馬上更新：LINE 用 [Page Poker](https://poker.line.naver.jp/)（貼上網址、勾選清除快取後送出），Facebook 用[分享偵錯工具](https://developers.facebook.com/tools/debug/)貼上網址後按「Scrape Again」（重新抓取）。
