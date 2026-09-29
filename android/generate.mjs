// 產生「頭頂星空」的 Android Trusted Web Activity（TWA）專案。
//
// 用法：
//   cd android && npm ci && node generate.mjs [輸出目錄]
//
// 讀取 twa-manifest.json（由 @bubblewrap/core 的 TwaManifest.fromWebManifestJson 產生後
// 固定套件 id、名稱、顏色、版本等欄位），呼叫 TwaGenerator.createTwaProject() 產出可用
// Gradle 建置的 Android 專案，再視需要把 compileSdk / targetSdk 調成 Google Play 目前
// 對新上架 App 的要求（見 TARGET_SDK）。
//
// 環境變數：
//   TWA_ICON_BASE   測試用：把 iconUrl / maskableIconUrl / webManifestUrl 的網域改成這個
//                   位址（例如 http://localhost:8000/sky/），方便在沒有對外網路的環境驗證。
//   TWA_OUT_DIR     輸出目錄（預設為第一個參數，再預設為 ./build/twa）。
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { TwaGenerator, TwaManifest, ConsoleLog, fetchUtils } from '@bubblewrap/core';

const here = path.dirname(fileURLToPath(import.meta.url));
const manifestPath = path.join(here, 'twa-manifest.json');

// Google Play 對新上架與更新 App 的 targetSdk 要求（2026-08-31 起為 Android 16 / API 36）。
export const TARGET_SDK = 36;
export const COMPILE_SDK = 36;

const outDir = path.resolve(process.env.TWA_OUT_DIR || process.argv[2] || path.join(here, 'build', 'twa'));
const log = new ConsoleLog('generate');

function rewriteBase(url, base) {
  if (!url || !base) return url;
  const u = new URL(url);
  const b = new URL(base);
  return new URL(u.pathname.replace(/^\/sky\//, ''), b).toString();
}

async function main() {
  const json = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));

  const iconBase = process.env.TWA_ICON_BASE;
  if (iconBase) {
    json.iconUrl = rewriteBase(json.iconUrl, iconBase);
    json.maskableIconUrl = rewriteBase(json.maskableIconUrl, iconBase);
    json.monochromeIconUrl = rewriteBase(json.monochromeIconUrl, iconBase);
    json.webManifestUrl = rewriteBase(json.webManifestUrl, iconBase);
    // 本機的 http.server 不支援 HTTP/2，改用 node-fetch。
    fetchUtils.setFetchEngine('node-fetch');
  } else {
    // GitHub Pages 走 HTTP/2 沒問題，但 node-fetch 較單純、錯誤訊息較清楚。
    fetchUtils.setFetchEngine('node-fetch');
  }

  // TwaManifest 建構子讀的是舊欄位 appVersion；以 appVersionName 為準，避免兩個欄位不同步。
  if (json.appVersionName) json.appVersion = json.appVersionName;

  const twaManifest = new TwaManifest(json);
  const error = twaManifest.validate();
  if (error) throw new Error(`twa-manifest.json 無效：${error}`);

  if (fs.existsSync(outDir)) fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });

  log.info(`輸出目錄：${outDir}`);
  const generator = new TwaGenerator();
  await generator.createTwaProject(outDir, twaManifest, log, (done, total) => {
    log.info(`進度 ${done}/${total}`);
  });

  // 確保 compileSdk / targetSdk 符合 Google Play 要求（bubblewrap 樣板若已相同則不變）。
  const appGradle = path.join(outDir, 'app', 'build.gradle');
  let gradle = fs.readFileSync(appGradle, 'utf8');
  gradle = gradle.replace(/compileSdkVersion\s+\d+/, `compileSdkVersion ${COMPILE_SDK}`);
  gradle = gradle.replace(/targetSdkVersion\s+\d+/, `targetSdkVersion ${TARGET_SDK}`);
  fs.writeFileSync(appGradle, gradle);

  // 移除已停用的 jcenter()（2021 年起唯讀、常逾時），只保留 google() 與 mavenCentral()。
  const rootGradle = path.join(outDir, 'build.gradle');
  let root = fs.readFileSync(rootGradle, 'utf8');
  root = root.replace(/jcenter\(\)/g, 'mavenCentral()');
  fs.writeFileSync(rootGradle, root);

  // 摘要，方便在 CI log 中核對。
  const summary = {
    packageId: twaManifest.packageId,
    name: twaManifest.name,
    launcherName: twaManifest.launcherName,
    host: twaManifest.host,
    startUrl: twaManifest.startUrl,
    versionCode: twaManifest.appVersionCode,
    versionName: twaManifest.appVersionName,
    minSdk: twaManifest.minSdkVersion,
    targetSdk: TARGET_SDK,
    compileSdk: COMPILE_SDK,
    enableNotifications: twaManifest.enableNotifications,
    features: twaManifest.features,
  };
  log.info('專案摘要：\n' + JSON.stringify(summary, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
