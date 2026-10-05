#!/usr/bin/env python3
"""Rebuild the Google Play store graphics and the link-preview image of 頭頂星空 from the real app.

Everything that shows the sky is captured from sky/index.html in headless Chromium (Playwright),
then composed with Pillow in the same layout as the graphics first published on 2026-09-29:

  store/graphics/phone/0N-*.png            1080 x 1920, caption + framed screenshot (8 images)
  store/graphics/phone/raw/0N-*.png        1080 x 1920, plain screenshots (360 x 640 CSS px at 3x)
  store/graphics/tablet-7in/0N-*.png       1200 x 1920 (+ raw/, 600 x 960 CSS px at 2x)
  store/graphics/tablet-10in/0N-*.png      1920 x 1200 (+ raw/, 1280 x 800 CSS px at 1.5x)
  store/graphics/feature-graphic.png       1024 x 500, text on the left, sky dome on the right
  store/graphics/preview.png               1560 x 2332 contact sheet of all of the above (for review only)
  sky/og-image.png                         1200 x 630 link preview (og:image in index.html and sky/index.html)

store/graphics/icon-512.png is not touched.

How a capture is made (details and reasons in README.md)
  * The repository is served on 127.0.0.1; the page gets a fixed clock (Date is frozen at the scene time),
    a pre-seeded localStorage (place, "hint already seen", "install card dismissed") and touch emulation.
    Scenes are reached by clicking the real UI (list, search box, buttons), never by editing app state.
  * Fonts: Google Fonts requests are answered locally with the same families the app asks for
    (Noto Serif TC, IBM Plex Mono). The system UI font of an Android phone (Roboto + Noto Sans CJK TC)
    is supplied under the first name of the app's font stack, so every computer uses the same fonts.
    All font files are downloaded once into tools/store-graphics/.cache/ and checked by SHA-256.
    Reruns on the same system give byte-identical files; other operating systems may differ slightly in text
    anti-aliasing.
  * The canvas is drawn at 3x (the app caps it at 2x to save battery). The 2026-09 graphics were made
    that way; --canvas-dpr 2 gives exactly what a phone shows.

Usage (from the repository root)
  pip install playwright pillow numpy        # Python 3.9+
  python -m playwright install chromium      # skip if Chromium is already installed for Playwright
  python3 tools/store-graphics/build_store_graphics.py                # rebuild everything
  python3 tools/store-graphics/build_store_graphics.py --only phone   # phone, tablet-7in, tablet-10in,
                                                                      # feature, og, preview
  python3 tools/store-graphics/build_store_graphics.py --compare-ref HEAD --compare-out /tmp/cmp
                                                                      # also write old-vs-new pictures
"""
import argparse
import base64
import functools
import hashlib
import http.server
import io
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
from datetime import datetime, timedelta, timezone

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
CACHE = os.path.join(HERE, '.cache')

# ----------------------------------------------------------------------------- pinned font downloads
# Every file is checked by SHA-256 and size. All fonts are under the SIL Open Font License 1.1 except
# DejaVu Sans Mono (Bitstream Vera licence, free to use and redistribute). None of them is committed.
DOWNLOADS = {
    # Noto Serif TC as Google Fonts serves it (unicode-range slices, variable weight). App: titles, map labels.
    'noto-serif-tc': dict(
        url='https://registry.npmjs.org/@fontsource-variable/noto-serif-tc/-/noto-serif-tc-5.3.0.tgz',
        sha256='41bcff2b3a286a7a3d60347eaee882c92d59cca5bd19688c8e49d7e96ec908dd', size=5883712, kind='tgz'),
    # IBM Plex Mono 400/500 as Google Fonts serves it. App: times, numbers.
    'ibm-plex-mono': dict(
        url='https://registry.npmjs.org/@fontsource/ibm-plex-mono/-/ibm-plex-mono-5.3.0.tgz',
        sha256='60d3c0cfa549cb06fcb8867ee83f994d78e212abfac3bef3275436acb5c4d029', size=1344435, kind='tgz'),
    # Roboto: the Latin part of an Android phone's system font.
    'roboto': dict(
        url='https://registry.npmjs.org/@fontsource/roboto/-/roboto-5.3.0.tgz',
        sha256='77620f437249772e381698224ea1bddd01c985ecd60267a63ddc96b9eb9348f7', size=4049049, kind='tgz'),
    # Noto Sans / Serif CJK TC (region subset OTFs of the same releases Android and Debian ship):
    # the Chinese part of the phone's system font, and the caption fonts.
    'NotoSansTC-Regular.otf': dict(
        url='https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/SubsetOTF/TC/NotoSansTC-Regular.otf',
        sha256='5bab0cb3c1cf89dde07c4a95a4054b195afbcfe784d69d75c340780712237537', size=5683368, kind='file'),
    'NotoSansTC-Medium.otf': dict(
        url='https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/SubsetOTF/TC/NotoSansTC-Medium.otf',
        sha256='bf206dca0975779bac71cb49a037a364156ca98a0c431b1b7d6b29fb8952ac7e', size=5695744, kind='file'),
    'NotoSansTC-Bold.otf': dict(
        url='https://raw.githubusercontent.com/notofonts/noto-cjk/Sans2.004/Sans/SubsetOTF/TC/NotoSansTC-Bold.otf',
        sha256='55420b259eb119bf5f2a0aadba10cf9d736c12d64ab93e78546d69ef5f43558b', size=5839972, kind='file'),
    'NotoSerifTC-Bold.otf': dict(
        url='https://raw.githubusercontent.com/notofonts/noto-cjk/Serif2.002/Serif/SubsetOTF/TC/NotoSerifTC-Bold.otf',
        sha256='a8a172938babdac9eb69e78d0614c8da50f60e144ffd9f69854ada7de897b300', size=8258456, kind='file'),
    # DejaVu Sans Mono: the web address on the link-preview image.
    'dejavu': dict(
        url='https://registry.npmjs.org/dejavu-fonts-ttf/-/dejavu-fonts-ttf-2.37.3.tgz',
        sha256='b7013ac58f9225250619db82cfb72e99c37ca8195f2b5a06a9e6a95bc5e1c84a', size=5494986, kind='tgz'),
}


def log(*a):
    print(*a, flush=True)


def fetch(name):
    """Download (once) and verify one pinned file; return its local path (a directory for tarballs)."""
    spec = DOWNLOADS[name]
    os.makedirs(CACHE, exist_ok=True)
    raw = os.path.join(CACHE, os.path.basename(spec['url']))
    if not (os.path.exists(raw) and os.path.getsize(raw) == spec['size'] and _sha256(raw) == spec['sha256']):
        log('  download', spec['url'])
        req = urllib.request.Request(spec['url'], headers={'User-Agent': 'toudingxingkong-store-graphics'})
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        if len(data) != spec['size'] or hashlib.sha256(data).hexdigest() != spec['sha256']:
            sys.exit('downloaded %s does not match the pinned size/SHA-256; refusing to use it' % spec['url'])
        with open(raw + '.part', 'wb') as f:
            f.write(data)
        os.replace(raw + '.part', raw)
    if spec['kind'] == 'file':
        return raw
    out = os.path.join(CACHE, name)
    stamp = os.path.join(out, '.sha256')
    if not (os.path.exists(stamp) and open(stamp).read() == spec['sha256']):
        shutil.rmtree(out, ignore_errors=True)
        with tarfile.open(raw) as t:
            for m in t.getmembers():
                if not m.isfile() or '..' in m.name or m.name.startswith('/'):
                    continue
                if not re.search(r'\.(woff2|ttf|css|json)$|/LICENSE$', m.name):
                    continue
                dst = os.path.join(out, m.name)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                with t.extractfile(m) as src, open(dst, 'wb') as f:
                    f.write(src.read())
        with open(stamp, 'w') as f:
            f.write(spec['sha256'])
    return os.path.join(out, 'package')


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


class Fonts:
    """Local font files: the CSS that answers the app's Google Fonts request, and Pillow fonts for captions."""

    # Unicode ranges handled by the CJK faces (Han, CJK punctuation, Bopomofo, full-width forms).
    CJK = ('U+2E80-2FDF,U+3000-303F,U+3100-312F,U+3190-33FF,U+3400-4DBF,U+4E00-9FFF,U+F900-FAFF,'
           'U+FE10-FE1F,U+FE30-FE4F,U+FF00-FFEF,U+20000-2FA1F')
    ROBOTO_SUBSETS = ('latin', 'latin-ext', 'greek', 'greek-ext', 'cyrillic', 'cyrillic-ext', 'vietnamese')

    def __init__(self):
        log('fonts')
        self.nst = fetch('noto-serif-tc')
        self.ipm = fetch('ibm-plex-mono')
        self.rob = fetch('roboto')
        self.dejavu = fetch('dejavu')
        self.otf = {k: fetch(k) for k in ('NotoSansTC-Regular.otf', 'NotoSansTC-Medium.otf',
                                          'NotoSansTC-Bold.otf', 'NotoSerifTC-Bold.otf')}
        self.files = {}  # served file name -> local path
        self.css = self._google_css()

    def _faces(self, css_path, files_dir, family, weight, keep=None, fmt='woff2'):
        out = []
        for m in re.finditer(r'@font-face\s*{(.*?)}', open(css_path, encoding='utf-8').read(), re.S):
            body = m.group(1)
            fn = re.search(r'url\(\./files/([^)]+\.woff2)\)', body).group(1)
            if keep and not keep(fn):
                continue
            ur = re.search(r'unicode-range:\s*([^;]+);', body).group(1)
            self.files[fn] = os.path.join(files_dir, fn)
            out.append("@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
                       "src:url(https://fonts.gstatic.com/local/%s) format('%s');unicode-range:%s;}"
                       % (family, weight, fn, fmt, ur))
        return out

    def _otf_face(self, family, weight, key):
        fn = os.path.basename(self.otf[key])
        self.files[fn] = self.otf[key]
        return ("@font-face{font-family:'%s';font-style:normal;font-weight:%s;font-display:swap;"
                "src:url(https://fonts.gstatic.com/local/%s) format('opentype');unicode-range:%s;}"
                % (family, weight, fn, self.CJK))

    def _google_css(self):
        css = []
        # What fonts.googleapis.com returns for the app's request (Noto Serif TC 500/700, IBM Plex Mono 400/500).
        css += self._faces(os.path.join(self.nst, 'wght.css'), os.path.join(self.nst, 'files'), 'Noto Serif TC', '200 900')
        for w in ('400', '500'):
            css += self._faces(os.path.join(self.ipm, '%s.css' % w), os.path.join(self.ipm, 'files'), 'IBM Plex Mono', w)
        # The phone's system UI font. The app asks for "PingFang TC", "Noto Sans TC", ..., system-ui; on Android
        # none of the named fonts exists and the text ends up in Roboto (Latin) + Noto Sans CJK TC (Chinese).
        # Defining that pair under the first name makes Windows, macOS and Linux all render the same thing.
        # Like an Android phone, weight 500 uses the Regular Chinese face and 600 the Bold one.
        for w in ('400', '500', '700'):
            css += self._faces(os.path.join(self.rob, '%s.css' % w), os.path.join(self.rob, 'files'), 'PingFang TC', w,
                               keep=lambda fn: re.search(r'roboto-(%s)-\d00-normal' % '|'.join(self.ROBOTO_SUBSETS), fn))
        for w, key in (('400', 'NotoSansTC-Regular.otf'), ('500', 'NotoSansTC-Regular.otf'), ('700', 'NotoSansTC-Bold.otf')):
            css.append(self._otf_face('PingFang TC', w, key))
            # Chinese characters inside IBM Plex Mono text (e.g. "2/6 週六 21:00") fall back to the same font.
            css.append(self._otf_face('IBM Plex Mono', w, key))
        return '\n'.join(css)

    def pil(self, kind, size):
        path = {'sans': self.otf['NotoSansTC-Regular.otf'], 'sans-medium': self.otf['NotoSansTC-Medium.otf'],
                'serif-bold': self.otf['NotoSerifTC-Bold.otf']}[kind]
        return ImageFont.truetype(path, size)


# ----------------------------------------------------------------------------- scenes
TPE = timezone(timedelta(hours=8))
STORE_TIME = datetime(2027, 2, 6, 21, 0, tzinfo=TPE)   # Sat: new moon, winter Milky Way overhead, Mars and Jupiter up
OG_TIME = datetime(2026, 9, 29, 21, 0, tzinfo=TPE)     # the evening the link preview was first made
TAIPEI = {'name': '台北', 'lat': 25.033, 'lon': 121.565}
CLEAN_LAYERS = {'lines': True, 'conNames': True, 'starNames': False, 'mw': True, 'dso': False, 'ecl': False, 'grid': False}

DEVICES = {
    'phone': dict(viewport={'width': 360, 'height': 640}, device_scale_factor=3, is_mobile=True, has_touch=True),
    'tablet-7in': dict(viewport={'width': 600, 'height': 960}, device_scale_factor=2, is_mobile=True, has_touch=True),
    'tablet-10in': dict(viewport={'width': 1280, 'height': 800}, device_scale_factor=1.5, is_mobile=True, has_touch=True),
}

# (folder, file stem, scene, kicker, title, subtitle). Captions copied from the 2026-09-29 graphics.
SHOTS = [
    ('phone', '01-sky-now', 'sky-now', '即時星空', '你頭頂的星空，一眼看懂', '依你的位置與時間，即時畫出星星、行星與銀河'),
    ('phone', '02-constellation-orion', 'orion', '星座介紹', '點一下星座，就有中文介紹', '88 星座的神話由來、亮星與最佳觀賞時間'),
    ('phone', '03-planet-jupiter', 'jupiter', '行星位置', '行星在哪裡，一點就知道', '即時計算方位、高度、亮度與升落時間'),
    ('phone', '04-star-sirius', 'sirius', '亮星資料', '認識夜空中的亮星', '中文星名、亮度、顏色與升落時間'),
    ('phone', '05-constellation-list', 'list', '星座清單', '現在天上有哪些星座？', '由高到低排好，也能搜尋全部 88 星座'),
    ('phone', '06-time-fastforward', 'fastforward', '時間控制', '快轉時間，看星星轉動', '查看今晚 9 點、午夜或任何日期的星空'),
    ('phone', '07-location', 'location', '觀測地點', '選城市，或用 GPS 定位', '台灣各縣市、觀星景點與海外城市'),
    ('phone', '08-red-night-mode', 'red', '紅光模式', '觀星時保護夜間視力', '一鍵切換紅色畫面，眼睛維持暗適應'),
    ('tablet-7in', '01-sky-now', 'sky-now', '即時星空', '你頭頂的星空，一眼看懂', '依你的位置與時間，即時畫出星星、行星與銀河'),
    ('tablet-7in', '02-constellation-orion', 'orion', '星座介紹', '點一下星座，就有中文介紹', '88 星座的神話由來、亮星與最佳觀賞時間'),
    ('tablet-10in', '01-sky-now', 'sky-now', '即時星空', '你頭頂的星空，一眼看懂', '依你的位置與時間，即時畫出星星、行星與銀河'),
    ('tablet-10in', '02-constellation-orion', 'orion', '星座介紹', '點一下星座，就有中文介紹', '88 星座的神話由來、亮星與最佳觀賞時間'),
]

INIT_JS = r"""
(() => {
  // Fixed clock: every `new Date()` / Date.now() returns the scene time.
  const FIXED = %(fixed)d;
  const RealDate = Date;
  class FixedDate extends RealDate {
    constructor(...a) { if (a.length === 0) super(FIXED); else super(...a); }
    static now() { return FIXED; }
  }
  FixedDate.UTC = RealDate.UTC; FixedDate.parse = RealDate.parse;
  window.Date = FixedDate;
  // The state a returning user has: place chosen by hand, first-run hint seen, install card dismissed.
  try {
    const K = 'toudingxingkong.';
    localStorage.clear();
    localStorage.setItem(K + 'hint', '1');
    localStorage.setItem(K + 'installSeen', '1');
    localStorage.setItem(K + 'locMode', JSON.stringify('manual'));
    localStorage.setItem(K + 'loc', JSON.stringify(%(loc)s));
    const layers = %(layers)s;
    if (layers) localStorage.setItem(K + 'layers', JSON.stringify(layers));
  } catch (e) {}
  // Frame gate: lets the build count animation frames (the fast-forward adds one minute per frame).
  const realRAF = window.requestAnimationFrame.bind(window);
  let budget = Infinity, pending = 0;
  const held = [];
  window.requestAnimationFrame = (cb) => {
    pending++;
    return realRAF((t) => {
      pending--;
      if (budget <= 0) { held.push(cb); return; }
      if (budget !== Infinity) budget--;
      cb(t);
    });
  };
  window.__storeShots = {
    pending: () => pending,
    held: () => held.length,
    budget: (n) => { budget = n; if (n > 0) held.splice(0).forEach((cb) => window.requestAnimationFrame(cb)); },
  };
})();
"""

HIDE_UI_CSS = '.topbar,.dock,.summary,.zoom,.hint,.toast,#loading{display:none!important}'


def serve(root):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=root))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class Capturer:
    def __init__(self, pw, fonts, app_root, canvas_dpr, work):
        self.fonts = fonts
        self.work = work
        self.canvas_dpr = canvas_dpr
        self.srv = serve(app_root)
        self.base = 'http://127.0.0.1:%d/' % self.srv.server_address[1]
        if not os.path.exists(os.path.join(app_root, 'sky', 'index.html')):
            sys.exit('no sky/index.html under %s' % app_root)
        env = dict(os.environ, LANG='zh_TW.UTF-8', LANGUAGE='zh_TW:zh', LC_ALL='zh_TW.UTF-8')  # date field: 2027/02/06
        self.browser = pw.chromium.launch(args=['--lang=zh-TW'], env=env)
        log('browser: Chromium', self.browser.version)

    def close(self):
        self.browser.close()
        self.srv.shutdown()

    # -- page setup
    def _route_fonts(self, ctx):
        def css(route):
            route.fulfill(status=200, body=self.fonts.css,
                          headers={'content-type': 'text/css; charset=utf-8', 'access-control-allow-origin': '*'})

        def font(route):
            p = self.fonts.files.get(route.request.url.rsplit('/', 1)[-1])
            if not p:
                route.fulfill(status=404, body='')
                return
            with open(p, 'rb') as f:
                body = f.read()
            route.fulfill(status=200, body=body, headers={
                'content-type': 'font/otf' if p.endswith('.otf') else 'font/woff2', 'access-control-allow-origin': '*'})
        ctx.route('https://fonts.googleapis.com/**', css)
        ctx.route('https://fonts.gstatic.com/**', font)

    def _route_app(self, ctx):
        """Serve sky/index.html with the canvas resolution cap raised (only in these screenshots)."""
        if self.canvas_dpr == 2:
            return
        pat = 'dpr = Math.min(window.devicePixelRatio || 1, 2);'

        def page(route):
            resp = route.fetch()
            body = resp.text()
            if pat not in body:
                log('  WARNING: canvas resolution cap not found in sky/index.html; drawing the map at the app default')
            body = body.replace(pat, 'dpr = Math.min(window.devicePixelRatio || 1, %s);' % self.canvas_dpr)
            headers = {k: v for k, v in resp.headers.items() if k.lower() not in ('content-length', 'content-encoding')}
            headers['content-type'] = 'text/html; charset=utf-8'
            route.fulfill(status=resp.status, body=body, headers=headers)
        ctx.route(re.compile(r'^%ssky/(index\.html)?(\?.*)?$' % re.escape(self.base)), page)

    def open(self, device_opts, when, loc=TAIPEI, layers=None):
        ctx = self.browser.new_context(**device_opts, locale='zh-TW', timezone_id='Asia/Taipei', color_scheme='dark',
                                       reduced_motion='reduce', service_workers='block')
        self._route_fonts(ctx)
        self._route_app(ctx)
        ctx.add_init_script(INIT_JS % {'fixed': int(when.timestamp() * 1000), 'loc': json.dumps(loc, ensure_ascii=False),
                                       'layers': json.dumps(layers) if layers else 'null'})
        page = ctx.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.goto(self.base + 'sky/', wait_until='load')
        page.wait_for_function("() => document.querySelector('#loading').hidden", polling=50)
        self.settle(page)
        # The app lays the map out once at start-up, sometimes before the web fonts arrive. A resize event
        # (as when a phone rotates) lays it out again with the final fonts, so every run gives the same picture.
        page.evaluate("() => window.dispatchEvent(new Event('resize'))")
        self.settle(page)
        return ctx, page, errors

    @staticmethod
    def settle(page, ms=350):
        """Wait until web fonts are loaded and the app has no animation frame pending."""
        for _ in range(2):
            page.evaluate('() => document.fonts.ready.then(() => true)')
            page.wait_for_function('() => window.__storeShots.pending() === 0', polling=40, timeout=30000)
            page.wait_for_timeout(ms)

    # -- scenes: each one clicks through the real interface
    def scene(self, page, name):
        if name == 'sky-now':
            pass
        elif name == 'orion':
            page.click('#btnCons')
            self.settle(page)
            page.fill('#conSearch', '獵戶')
            page.click('#listRows [data-act=con-go][data-id=Ori]')     # opens the card and centres the figure
        elif name == 'jupiter':
            page.click('#btnCons')
            self.settle(page)
            page.click('#listRows [data-act=body-go][data-id=Jupiter]')
        elif name == 'sirius':
            page.click('#btnCons')
            self.settle(page)
            page.fill('#conSearch', '大犬')
            page.click('#listRows [data-act=con-go][data-id=CMa]')
            self.settle(page)
            page.click('#sheetBody [data-act=star] >> text=天狼星')       # bright-star link on the 大犬座 card
            self.settle(page)
            page.click('#sheetBody [data-act=center]')                  # 「在星空中置中」
            self.settle(page)
            page.evaluate("() => { document.querySelector('#sheetBody').scrollTop = 0; }")  # back to the top of the card
        elif name == 'list':
            page.click('#btnCons')
        elif name == 'fastforward':
            page.click('#btnTime')
            self.settle(page)
            # 「快轉看星星轉動」 advances the clock one minute per animation frame: let exactly 30 frames run.
            page.evaluate("() => { window.__storeShots.budget(30); document.querySelector('#playBtn').click(); }")
            page.wait_for_function('() => window.__storeShots.held() > 0', polling=40, timeout=30000)
        elif name == 'location':
            page.click('#placeBtn')
            self.settle(page)
            page.click('#sheetBody [data-act=city] >> text=合歡山')
            page.wait_for_function("() => document.querySelector('#toast').hidden", polling=100, timeout=10000)
            page.evaluate("() => { document.querySelector('#sheetBody').scrollTop = 0; }")
        elif name == 'red':
            page.click('#btnRed')
        else:
            raise ValueError(name)
        if name == 'fastforward':
            page.evaluate('() => document.fonts.ready.then(() => true)')
            page.wait_for_timeout(400)
        else:
            self.settle(page)

    @staticmethod
    def check_scene(page, name, when):
        """Fail loudly if the screen is not what the caption promises (or shows a hint, toast or install card)."""
        st = page.evaluate("""() => ({
            time: document.querySelector('#timeText').textContent,
            place: document.querySelector('#placeName').textContent,
            kicker: document.querySelector('#sheet').hidden ? null : document.querySelector('#sheetKicker').textContent,
            title: (document.querySelector('#sheetBody .title') || {}).textContent || null,
            clock: (document.querySelector('#clockText') || {}).textContent || null,
            play: (document.querySelector('#playBtn') || {}).textContent || null,
            scroll: document.querySelector('#sheetBody').scrollTop,
            hint: !document.querySelector('#hint').hidden,
            toast: !document.querySelector('#toast').hidden,
            install: !document.querySelector('#installCard').hidden,
            red: !document.querySelector('#red').hidden })""")
        want_time = '%d/%d 週%s %s' % (when.month, when.day, '日一二三四五六'[(when.weekday() + 1) % 7],
                                      (when + timedelta(minutes=30) if name == 'fastforward' else when).strftime('%H:%M'))
        problems = []
        if st['time'] != want_time:
            problems.append('time chip %r, expected %r' % (st['time'], want_time))
        if st['hint'] or st['toast'] or st['install']:
            problems.append('hint/toast/install card visible: %r' % st)
        expect = {'orion': ('星座', '獵戶座'), 'jupiter': ('太陽系', '木星'), 'sirius': ('恆星', '天狼星'),
                  'list': ('星座清單', None), 'fastforward': ('觀測時間', None), 'location': ('觀測地點', None)}
        if name in expect:
            k, t = expect[name]
            if st['kicker'] != k or (t and st['title'] != t) or st['scroll'] != 0:
                problems.append('sheet %r / %r / scroll %r, expected %r / %r / 0' % (st['kicker'], st['title'], st['scroll'], k, t))
        elif st['kicker'] is not None:
            problems.append('a sheet is open: %r' % st['kicker'])
        if name == 'location' and st['place'] != '合歡山':
            problems.append('place %r' % st['place'])
        if name == 'fastforward' and (st['play'] != '停止快轉' or not (st['clock'] or '').endswith('21:30')):
            problems.append('fast-forward state %r / %r' % (st['play'], st['clock']))
        if name == 'red' and not st['red']:
            problems.append('red mode is off')
        if problems:
            raise RuntimeError('scene %s: %s' % (name, '; '.join(problems)))
        return st

    def shot(self, device, scene, when, path):
        ctx, page, errors = self.open(DEVICES[device], when)
        try:
            self.scene(page, scene)
            st = self.check_scene(page, scene, when)
            page.screenshot(path=path)
        finally:
            ctx.close()
        if errors:
            raise RuntimeError('page errors in %s/%s: %s' % (device, scene, errors))
        return st

    def dome(self, size, dsf, when, layers, path):
        """The bare sky dome (all controls hidden), for the feature graphic and the link preview."""
        ctx, page, errors = self.open(dict(viewport={'width': size, 'height': size}, device_scale_factor=dsf), when, layers=layers)
        try:
            page.add_style_tag(content=HIDE_UI_CSS)
            page.evaluate("() => window.dispatchEvent(new Event('resize'))")
            self.settle(page)
            page.screenshot(path=path)
        finally:
            ctx.close()
        if errors:
            raise RuntimeError('page errors in dome capture: %s' % errors)

    def html(self, html, size, path, files):
        """Render an HTML card (used for the link preview, which was designed in HTML) at 1x."""
        ctx = self.browser.new_context(viewport={'width': size[0], 'height': size[1]}, device_scale_factor=1)
        local = dict(files)

        def handler(route):
            name = route.request.url.split('/local/', 1)[-1]
            if name == 'card.html':
                route.fulfill(status=200, body=html, headers={'content-type': 'text/html; charset=utf-8'})
            elif name in local:
                with open(local[name], 'rb') as f:
                    route.fulfill(status=200, body=f.read(), headers={'content-type': _mime(name)})
            else:
                route.fulfill(status=404, body='')
        ctx.route('https://store-graphics.invalid/local/**', handler)
        page = ctx.new_page()
        page.goto('https://store-graphics.invalid/local/card.html', wait_until='load')
        page.evaluate('() => document.fonts.ready.then(() => true)')
        page.wait_for_timeout(300)
        page.locator('#card').screenshot(path=path)
        ctx.close()


def _mime(name):
    return {'.png': 'image/png', '.otf': 'font/otf', '.ttf': 'font/ttf', '.woff2': 'font/woff2'}.get(os.path.splitext(name)[1], 'application/octet-stream')


# ----------------------------------------------------------------------------- composition (Pillow)
NIGHT = (8, 12, 31)        # --night  #080C1F
TOP = (15, 21, 50)         # #0F1532
LEFT = (13, 20, 47)        # feature graphic, left edge
BRASS = (217, 178, 106)    # --brass  #D9B26A
TEXT = (236, 232, 221)     # --text   #ECE8DD
MUTED = (154, 163, 191)    # --muted  #9AA3BF

# Caption layouts measured from the 2026-09 images: (font size, y) for kicker, title and subtitle; frame box.
LAYOUT = {
    'portrait': dict(kicker=(34, 92), spacing=9, title=(76, 160), sub=(38, 272), frame_top=372, frame_h=1500),
    'landscape': dict(kicker=(30, 40), spacing=9, title=(64, 80), sub=(32, 170), frame_top=236, frame_h=928),
}
FRAME_RADIUS = 44


def _to_img(arr):
    return Image.fromarray(np.clip(np.round(arr), 0, 255).astype(np.uint8), 'RGB')


def _blend(base, color, mask_img):
    a = np.asarray(mask_img).astype(np.float64)[..., None] / 255.0
    return base * (1 - a) + np.array(color, np.float64) * a


def store_background(w, h):
    """Navy vertical gradient with a soft brass glow at the top centre."""
    t = (np.arange(h, dtype=np.float64) / (h - 1))[:, None, None]
    base = np.array(TOP, np.float64) + (np.array(NIGHT, np.float64) - np.array(TOP, np.float64)) * t
    base = np.broadcast_to(base, (h, w, 3)).copy()
    glow = Image.new('L', (w, h), 0)
    ImageDraw.Draw(glow).ellipse((0.1 * w, -0.1 * h, 0.9 * w, 0.2 * h), fill=27)
    glow = glow.filter(ImageFilter.GaussianBlur(0.05 * max(w, h)))
    return _blend(base, BRASS, glow)


def draw_text(draw, xy, text, font, fill, spacing=0):
    if not spacing:
        draw.text(xy, text, font=font, fill=fill)
        return
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + spacing


def text_width(draw, text, font, spacing=0):
    if not spacing:
        return draw.textlength(text, font=font)
    return sum(draw.textlength(ch, font=font) for ch in text) + spacing * (len(text) - 1)


def compose_store(raw, kicker, title, sub, fonts):
    """A store screenshot: kicker, headline and subtitle above the app screenshot in a rounded brass frame."""
    W, H = raw.size
    lay = LAYOUT['portrait' if H > W else 'landscape']
    fh = lay['frame_h']
    fw = round(fh * W / H)
    fx, fy = (W - fw) // 2, lay['frame_top']
    bg = store_background(W, H)
    shadow = Image.new('L', (W, H), 0)
    ImageDraw.Draw(shadow).rounded_rectangle((fx - 10, fy - 10 + 18, fx + fw - 1 + 10, fy + fh - 1 + 10 + 18),
                                             radius=FRAME_RADIUS, fill=136)
    bg = bg * (1 - np.asarray(shadow.filter(ImageFilter.GaussianBlur(17))).astype(np.float64)[..., None] / 255.0)
    img = _to_img(bg)
    mask = Image.new('L', (fw, fh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, fw - 1, fh - 1), radius=FRAME_RADIUS, fill=255)
    img.paste(raw.convert('RGB').resize((fw, fh), Image.LANCZOS), (fx, fy), mask)
    over = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(over).rounded_rectangle((fx + 1, fy + 1, fx + fw - 2, fy + fh - 2), radius=FRAME_RADIUS,
                                           outline=BRASS + (110,), width=3)
    img = Image.alpha_composite(img.convert('RGBA'), over).convert('RGB')
    d = ImageDraw.Draw(img)
    size, y = lay['kicker']
    f = fonts.pil('sans-medium', size)
    draw_text(d, ((W - text_width(d, kicker, f, lay['spacing'])) / 2, y), kicker, f, BRASS, lay['spacing'])
    for text, (size, y), kind, color in ((title, lay['title'], 'serif-bold', TEXT), (sub, lay['sub'], 'sans', MUTED)):
        d.text((W / 2, y), text, font=fonts.pil(kind, size), fill=color, anchor='ma')
    return img


def compose_feature(dome, fonts):
    """1024 x 500 feature graphic: name and tagline on the left, the sky dome on the right."""
    W, H = 1024, 500
    x = (np.arange(W, dtype=np.float64) / (W - 1))[None, :, None]
    base = np.array(LEFT, np.float64) + (np.array(NIGHT, np.float64) - np.array(LEFT, np.float64)) * x
    base = np.broadcast_to(base, (H, W, 3)).copy()
    halo = Image.new('L', (W, H), 0)
    ImageDraw.Draw(halo).ellipse((762 - 218, 250 - 218, 762 + 218, 250 + 218), fill=64)
    img = _to_img(_blend(base, BRASS, halo.filter(ImageFilter.GaussianBlur(23))))
    mask = Image.new('L', (434, 434), 0)
    ImageDraw.Draw(mask).ellipse((10, 10, 424, 424), fill=255)
    img.paste(dome.convert('RGB').resize((434, 434), Image.LANCZOS), (545, 33), mask.filter(ImageFilter.GaussianBlur(1.5)))
    d = ImageDraw.Draw(img)
    draw_text(d, (72, 112), '即時星空圖', fonts.pil('sans-medium', 22), BRASS, spacing=8)
    draw_text(d, (68, 149), '頭頂星空', fonts.pil('serif-bold', 104), TEXT)
    d.rectangle((72, 295, 136, 297), fill=BRASS)
    body = fonts.pil('sans', 28)
    draw_text(d, (72, 322), '依你的位置與時間，即時畫出', body, TEXT)
    draw_text(d, (72, 364), '頭頂的星星、行星、銀河與 88 星座', body, TEXT)
    draw_text(d, (72, 414), '點一下，就有中文介紹', fonts.pil('sans', 24), MUTED)
    return img


OG_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Noto Serif CJK TC';font-weight:700;src:url(NotoSerifTC-Bold.otf) format('opentype');}
@font-face{font-family:'Noto Sans CJK TC';font-weight:400;src:url(NotoSansTC-Regular.otf) format('opentype');}
@font-face{font-family:'DejaVu Sans Mono';font-weight:400;src:url(DejaVuSansMono.ttf) format('truetype');}
html,body{margin:0}
.serif{font-family:"Noto Serif CJK TC",serif}.sans{font-family:"Noto Sans CJK TC",sans-serif}.mono{font-family:"DejaVu Sans Mono",monospace}
.card{width:1200px;height:630px;position:relative;overflow:hidden;background:radial-gradient(ellipse 60% 80% at 26% 50%,#0E1433 0%,#050810 70%)}
.dome{position:absolute;left:18px;top:15px;width:600px;height:600px}
.txt{position:absolute;left:668px;top:0;bottom:0;width:490px;display:flex;flex-direction:column;justify-content:center;gap:22px}
.kick{color:#D9B26A;font-size:26px;letter-spacing:.18em}
h1{margin:0;color:#ECE8DD;font-size:104px;line-height:1.05;letter-spacing:.06em;font-weight:700}
.sub{color:#C9CFE3;font-size:30px;line-height:1.55}
.feat{color:#9AA3BF;font-size:24px;line-height:1.6}
.url{color:#D9B26A;font-size:24px;margin-top:10px}
</style></head><body><div class="card" id="card">
<img class="dome" src="dome.png">
<div class="txt">
<div class="kick sans">免費 · 不用下載</div>
<h1 class="serif">頭頂星空</h1>
<div class="sub sans">打開就能看到你頭頂<br>此刻的星空與星座</div>
<div class="feat sans">88 星座中文介紹、行星與銀河<br>舉起手機對準天空，星圖跟著轉</div>
<div class="url mono">s70680.github.io/sky</div>
</div></div></body></html>"""


def compose_preview(paths, fonts):
    """Contact sheet for a quick look (not uploaded to Google Play)."""
    W, H = 1560, 2332
    img = Image.new('RGB', (W, H), NIGHT)
    d = ImageDraw.Draw(img)
    label = fonts.pil('sans', 18)
    img.paste(Image.open(paths['feature']).convert('RGB'), ((W - 1024) // 2, 24))
    for i, stem in enumerate(s for f, s, *_ in SHOTS if f == 'phone'):
        x, y = 24 + (i % 4) * 384, 564 if i < 4 else 1248
        img.paste(Image.open(paths['phone/' + stem]).convert('RGB').resize((360, 640), Image.LANCZOS), (x, y))
        name = stem + '.png'
        d.text((x + (360 - d.textlength(name, font=label)) / 2, y + 650), name, font=label, fill=MUTED)
    x = 24
    for folder, stem, size in (('tablet-7in', '01-sky-now', (200, 320)), ('tablet-7in', '02-constellation-orion', (200, 320)),
                               ('tablet-10in', '01-sky-now', (512, 320)), ('tablet-10in', '02-constellation-orion', (512, 320))):
        img.paste(Image.open(paths[folder + '/' + stem]).convert('RGB').resize(size, Image.LANCZOS), (x, 1952))
        name = '%s · %s' % (folder.split('-')[1], stem[:2])
        d.text((x + (size[0] - d.textlength(name, font=label)) / 2, 1952 + 330), name, font=label, fill=MUTED)
        x += size[0] + 24
    return img


# ----------------------------------------------------------------------------- checks and comparisons
def check_outputs(written, root):
    """Google Play rules: 24-bit PNG without alpha, exact sizes, 2-8 phone screenshots, long side <= 2x short side."""
    problems, rows = [], []
    phone = [p for p in written if '/phone/' in p and '/raw/' not in p]
    if written and any('/phone/' in p for p in written) and not 2 <= len(phone) <= 8:
        problems.append('phone screenshots: %d (Google Play allows 2-8)' % len(phone))
    for p in sorted(written):
        im = Image.open(p)
        w, h = im.size
        ok = im.mode == 'RGB' and 'transparency' not in im.info
        if '/tablet-' in p or '/phone/' in p:  # screenshot rules
            ok &= 320 <= min(w, h) and max(w, h) <= 3840 and max(w, h) <= 2 * min(w, h)
        size_ok = os.path.getsize(p) <= 8 * 1024 * 1024
        exp = None
        if p.endswith('feature-graphic.png'):
            exp = (1024, 500)
        elif p.endswith('og-image.png'):
            exp = (1200, 630)
        elif '/phone/' in p:
            exp = (1080, 1920)
        elif '/tablet-7in/' in p:
            exp = (1200, 1920)
        elif '/tablet-10in/' in p:
            exp = (1920, 1200)
        elif p.endswith('preview.png'):
            exp = (1560, 2332)
        if exp and (w, h) != exp:
            ok = False
        rows.append('%-52s %4dx%-4d %-4s %5d KB %s' % (os.path.relpath(p, root), w, h, im.mode, os.path.getsize(p) // 1024,
                                                      'ok' if ok and size_ok else 'PROBLEM'))
        if not (ok and size_ok):
            problems.append(os.path.relpath(p, root))
    return rows, problems


def compare(written, ref, out_dir, root):
    """Old (git ref) vs new side by side, with the absolute difference amplified 4x on the right."""
    os.makedirs(out_dir, exist_ok=True)
    made = []
    for p in sorted(written):
        rel = os.path.relpath(p, root).replace(os.sep, '/')  # path inside the repository, as git spells it
        try:
            old_bytes = subprocess.run(['git', '-C', REPO, 'show', '%s:%s' % (ref, rel)], check=True,
                                       capture_output=True).stdout
        except subprocess.CalledProcessError:
            continue
        old = Image.open(io.BytesIO(old_bytes)).convert('RGB')
        new = Image.open(p).convert('RGB')
        if old.size != new.size:
            continue
        diff = np.abs(np.asarray(old).astype(np.int16) - np.asarray(new).astype(np.int16)).max(axis=2)
        dimg = Image.fromarray(np.clip(diff * 4, 0, 255).astype(np.uint8)).convert('RGB')
        w, h = old.size
        k = min(1.0, 900.0 / h)
        tw, th = round(w * k), round(h * k)
        head = 40
        sheet = Image.new('RGB', (tw * 3 + 40, th + head), (24, 26, 38))
        dd = ImageDraw.Draw(sheet)
        try:
            f = ImageFont.truetype(fetch('NotoSansTC-Regular.otf'), 22)
        except Exception:
            f = ImageFont.load_default()
        for i, (im, cap) in enumerate(((old, '舊（%s）' % ref), (new, '新'), (dimg, '差異 ×4'))):
            sheet.paste(im.resize((tw, th), Image.LANCZOS), (i * (tw + 20), head))
            dd.text((i * (tw + 20) + 6, 8), cap, font=f, fill=(236, 232, 221))
        name = rel.replace('/', '__')
        dst = os.path.join(out_dir, name)
        sheet.save(dst, optimize=True)
        made.append((dst, float((diff > 32).mean() * 100)))
    return made


# ----------------------------------------------------------------------------- main
TARGETS = ('phone', 'tablet-7in', 'tablet-10in', 'feature', 'og', 'preview')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--only', default=','.join(TARGETS), help='comma list of: ' + ', '.join(TARGETS))
    ap.add_argument('--out', default=REPO, help='write store/graphics/... and sky/og-image.png under this folder (default: the repository)')
    ap.add_argument('--app', default=REPO, help='folder served as the web site (must contain sky/index.html)')
    ap.add_argument('--canvas-dpr', type=float, default=3, help='star-map canvas resolution in the screenshots (app default: 2)')
    ap.add_argument('--compare-ref', help='git ref of the graphics to compare with, e.g. HEAD or origin/main')
    ap.add_argument('--compare-out', default=os.path.join(CACHE, 'compare'), help='where the comparison pictures go')
    args = ap.parse_args()
    only = [t.strip() for t in args.only.split(',') if t.strip()]
    for t in only:
        if t not in TARGETS:
            sys.exit('unknown target %r' % t)
    if 'preview' in only:  # the contact sheet needs everything else
        only = list(TARGETS)
    from playwright.sync_api import sync_playwright

    fonts = Fonts()
    work = os.path.join(CACHE, 'work')
    os.makedirs(work, exist_ok=True)
    out = lambda rel: os.path.join(args.out, rel)
    written, paths = [], {}
    t0 = time.time()
    with sync_playwright() as pw:
        cap = Capturer(pw, fonts, os.path.abspath(args.app), args.canvas_dpr, work)
        try:
            for folder, stem, scene, kicker, title, sub in SHOTS:
                if folder not in only:
                    continue
                raw_path = out('store/graphics/%s/raw/%s.png' % (folder, stem))
                os.makedirs(os.path.dirname(raw_path), exist_ok=True)
                st = cap.shot(folder, scene, STORE_TIME, raw_path)
                raw = Image.open(raw_path).convert('RGB')
                raw.save(raw_path, optimize=True)
                comp = compose_store(raw, kicker, title, sub, fonts)
                comp_path = out('store/graphics/%s/%s.png' % (folder, stem))
                comp.save(comp_path, optimize=True)
                written += [raw_path, comp_path]
                paths['%s/%s' % (folder, stem)] = comp_path
                log('  %-12s %-24s %s  %s' % (folder, stem, st['place'], st['time']))
            if 'feature' in only:
                dome_path = os.path.join(work, 'feature-dome.png')
                cap.dome(460, 2, STORE_TIME, CLEAN_LAYERS, dome_path)
                p = out('store/graphics/feature-graphic.png')
                compose_feature(Image.open(dome_path), fonts).save(p, optimize=True)
                written.append(p)
                paths['feature'] = p
                log('  feature graphic')
            if 'og' in only:
                dome_path = os.path.join(work, 'og-dome.png')
                cap.dome(640, 2, OG_TIME, None, dome_path)
                p = out('sky/og-image.png')
                os.makedirs(os.path.dirname(p), exist_ok=True)
                cap.html(OG_HTML, (1200, 630), p, {
                    'dome.png': dome_path, 'NotoSerifTC-Bold.otf': fonts.otf['NotoSerifTC-Bold.otf'],
                    'NotoSansTC-Regular.otf': fonts.otf['NotoSansTC-Regular.otf'],
                    'DejaVuSansMono.ttf': os.path.join(fonts.dejavu, 'ttf', 'DejaVuSansMono.ttf')})
                Image.open(p).convert('RGB').save(p, optimize=True)
                written.append(p)
                log('  link preview (og-image)')
        finally:
            cap.close()
    if 'preview' in only:
        p = out('store/graphics/preview.png')
        compose_preview(paths, fonts).save(p, optimize=True)
        written.append(p)
        log('  preview')
    rows, problems = check_outputs(written, args.out)
    log('\nchecks (Google Play: 24-bit PNG without alpha, exact size, long side <= 2x short side, <= 8 MB):')
    for r in rows:
        log('  ' + r)
    if args.compare_ref:
        made = compare(written, args.compare_ref, args.compare_out, args.out)
        log('\ncomparison pictures in %s:' % args.compare_out)
        for dst, pct in made:
            log('  %-60s %5.2f%% of pixels differ by more than 32/255' % (os.path.basename(dst), pct))
    log('\ndone in %.0f s' % (time.time() - t0))
    if problems:
        sys.exit('problems: ' + ', '.join(problems))


if __name__ == '__main__':
    main()
