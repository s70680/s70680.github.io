# 頭頂星空

依你的位置與時間，即時畫出頭頂的星空、行星、銀河與 88 個星座，點任何天體就有中文介紹。

**打開 App：** https://s70680.github.io/sky/

## 安裝到手機桌面

- **Android（Chrome）**：打開上面的網址 → 右上角「⋮」→「加到主畫面」或「安裝應用程式」
- **iPhone（Safari）**：打開上面的網址 → 下方「分享」→「加入主畫面」

安裝後可以離線使用（開過一次之後），適合帶到沒有訊號的觀星地點。

## 功能

- 頭頂全天星圖（星座盤式圓形視野），拖曳旋轉、雙指縮放
- **指向模式**：舉起手機對準天空，星圖跟著手機方向轉（需要陀螺儀與指南針）
- GPS 自動定位，也可以手動選城市或輸入座標
- 88 星座（台灣慣用譯名）的神話、由來與觀賞方法，升起、最高與落下時間
- 亮星的中文星名、行星與月相、著名星雲星團
- 時間調整與快轉、夜間紅光模式

## 資料與授權

- 天體位置計算：[Astronomy Engine](https://github.com/cosinekitty/astronomy)（MIT License，© Don Cross）
- 星表、星座連線、星座邊界、名稱位置、銀河輪廓：[d3-celestial](https://github.com/ofrohn/d3-celestial) 整理的資料（BSD 3-Clause License，© Olaf Frohn），原始來源包括 Hipparcos／XHIP 星表（CDS/VizieR）、IAU 星座資料、Davenhall & Leggett 星座邊界、Jose R. Vieira 的銀河輪廓表
- 中國傳統星名：[Stellarium「Chinese」星空文化](https://github.com/Stellarium/stellarium/tree/master/skycultures/chinese)（經 d3-celestial 整理，**CC BY-SA 4.0**），本專案轉為繁體字，這份改作的星名資料同樣以 CC BY-SA 4.0 提供
- 字型：Noto Serif TC、IBM Plex Mono（SIL Open Font License 1.1，透過 Google Fonts 載入）
- 星座、亮星、行星與深空天體的中文介紹為本專案撰寫

App 內的「顯示設定」底部可開啟：

- [資料來源與授權](https://s70680.github.io/sky/licenses.html)（完整授權條文）
- [隱私權政策](https://s70680.github.io/sky/privacy.html)（位置與感測器只在手機上使用，不收集任何個人資料）

詳細授權條文也見 [NOTICE.md](NOTICE.md)。上架 Google Play 的文件在 [store/](store/)。
