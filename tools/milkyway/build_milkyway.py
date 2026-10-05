#!/usr/bin/env python3
"""Build the Milky Way layer (MW_DATA in sky/index.html) from ESO's Milky Way panorama.

Source image
  "The Milky Way panorama" (eso0932a), credit: ESO/S. Brunier
  https://www.eso.org/public/images/eso0932a/
  Licence: Creative Commons Attribution 4.0 International (CC BY 4.0),
  see https://www.eso.org/public/copyright/

What the script does (details and the reasons for each step are in README.md)
  1. Download the image (default: a pinned GitHub copy, checked by SHA-256) and check
     that its embedded AVM metadata identifies eso0932a / ESO/S. Brunier.
  2. Measure how the panorama is oriented: detect stars in the image and fit a 3-D
     rotation against the app's own star catalogue (STAR_DATA in sky/index.html).
     The panorama is an equirectangular map in galactic coordinates, but its frame
     is tilted by about 3.8 degrees from the IAU galactic frame, so this step matters.
  3. Remove stars (median filter), subtract the sky background, smooth on the sphere.
  4. Sample the result on the same 20,000-point Fibonacci lattice the app has always
     used, cut it into 5 brightness levels, drop anything that is not connected to
     the Galactic plane (Magellanic Clouds, M31, planets, Pleiades, ...).
  5. Write `const MW_DATA=[ra,dec,level,...]` (ICRS/J2000 degrees) into sky/index.html.

Usage (from the repository root)
  python3 tools/milkyway/build_milkyway.py                  # build and print the report
  python3 tools/milkyway/build_milkyway.py --write          # also update sky/index.html
  python3 tools/milkyway/build_milkyway.py --check          # compare with the committed MW_DATA
  python3 tools/milkyway/build_milkyway.py --compare-html OLD.html   # IoU against another MW_DATA

Requires Python 3.9+, numpy, scipy (1.6+) and Pillow.
"""
import argparse
import hashlib
import json
import math
import os
import re
import sys
import urllib.request

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
INDEX_HTML = os.path.join(REPO, 'sky', 'index.html')
CACHE_DIR = os.path.join(HERE, '.cache')

# --------------------------------------------------------------------------- source
SOURCES = {
    # A byte-for-byte copy of the ESO image kept in typpo/spacekit (MIT-licensed code; the image
    # itself stays under ESO's licence). Pinned to the commit that added it (2018-11-30), so the
    # URL can never change. 4096 x 2048 px, downscaled from ESO's 6000 x 3000 release; it carries
    # ESO's AVM metadata (avm:ID eso0932a, credit "ESO/S. Brunier").
    'github-copy': {
        'url': 'https://raw.githubusercontent.com/typpo/spacekit/'
               'c90a496d2252702d13e1659101ce0d99b2bea0e5/src/assets/skybox/eso_milkyway.jpg',
        'sha256': '9ed7908d233f98a814a52caba2e525b1849e14592cded3355be1611a8ef14ec7',
        'bytes': 2475382,
    },
    # ESO's own "Large JPEG" (6000 x 3000 px, about 7.8 MB). Not pinned by checksum because it
    # could not be downloaded when this script was written; the result should match the
    # committed data closely (use --check to see how many points differ).
    'eso': {
        'url': 'https://cdn.eso.org/images/large/eso0932a.jpg',
        'sha256': None,
        'bytes': None,
    },
}
EXPECTED_AVM_ID = 'eso0932a'
EXPECTED_CREDIT = 'ESO/S. Brunier'

# --------------------------------------------------------------------------- parameters
WORK_SIZE = (4096, 2048)       # every input is resampled to this (0.0879 deg/px)
STAR_MEDIAN_DEG = 0.8          # median-filter window that removes stars but keeps the glow
SMOOTH_SIGMA_DEG = 1.0         # Gaussian smoothing on the sphere (lattice spacing is 1.37 deg)
BACKGROUND_MIN_B = 40.0        # sky background = median brightness at |b| >= this
LATTICE_N = 20000              # Fibonacci lattice, identical to the one used by the old data
# share of the lattice (= share of the sky) at level >= 1..5. These are the shares of the previous
# Milky Way data (3388, 842, 323, 89 and 25 of 20000 points), so the renderer's alpha per level
# gives the same overall brightness as before; only the shapes come from the new source.
LEVEL_AREA = (0.1694, 0.0421, 0.01615, 0.00445, 0.00125)
PLANE_B = 5.0                  # keep only regions connected to |b| < PLANE_B

# IAU 1958 galactic frame expressed in ICRS (Hipparcos Vol. 1, Sec. 1.5.3): g = AG @ r_icrs
AG = np.array([
    [-0.0548755604162154, -0.8734370902348850, -0.4838350155487132],
    [+0.4941094278755837, -0.4448296299600112, +0.7469822444972189],
    [-0.8676661490190047, -0.1980763734312015, +0.4559837761750669],
])


# --------------------------------------------------------------------------- helpers
def log(*a):
    print(*a, file=sys.stderr, flush=True)


def unit(lon_deg, lat_deg):
    lo, la = np.radians(lon_deg), np.radians(lat_deg)
    c = np.cos(la)
    return np.stack([c * np.cos(lo), c * np.sin(lo), np.sin(la)], -1)


def lonlat(v):
    return (np.degrees(np.arctan2(v[..., 1], v[..., 0])) % 360.0,
            np.degrees(np.arcsin(np.clip(v[..., 2], -1.0, 1.0))))


def fibonacci_lattice(n):
    """Point i: z = 1 - (2i+1)/n, longitude = i * golden angle (ICRS RA/Dec)."""
    i = np.arange(n, dtype=np.float64)
    z = 1.0 - (2.0 * i + 1.0) / n
    ra = np.degrees((i * math.pi * (3.0 - math.sqrt(5.0))) % (2.0 * math.pi))
    dec = np.degrees(np.arcsin(z))
    return ra, dec


def read_js_array(html, name):
    m = re.search(r'const ' + name + r'=\[([^\]]*)\];', html)
    if not m:
        raise SystemExit('could not find const %s=[...] in index.html' % name)
    return np.array([float(x) for x in m.group(1).split(',')])


def read_text(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def read_bytes(path):
    with open(path, 'rb') as f:
        return f.read()


def fmt(x):
    # 0.1 degree is plenty: each point is drawn as a soft sprite about 4 degrees across
    s = '%.1f' % x
    s = s.rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


# --------------------------------------------------------------------------- 1. input
def fetch(source, path):
    if path:
        log('using local file', path)
        return path
    spec = SOURCES[source]
    os.makedirs(CACHE_DIR, exist_ok=True)
    dst = os.path.join(CACHE_DIR, source + '_' + os.path.basename(spec['url']))
    if not os.path.exists(dst):
        log('downloading', spec['url'])
        req = urllib.request.Request(spec['url'], headers={'User-Agent': 'toudingxingkong-milkyway-build'})
        with urllib.request.urlopen(req, timeout=120) as r, open(dst + '.part', 'wb') as f:
            f.write(r.read())
        os.replace(dst + '.part', dst)
    data = read_bytes(dst)
    digest = hashlib.sha256(data).hexdigest()
    if spec['bytes'] and len(data) != spec['bytes']:
        raise SystemExit('unexpected size for %s: %d bytes (expected %d)' % (dst, len(data), spec['bytes']))
    if spec['sha256'] and digest != spec['sha256']:
        raise SystemExit('SHA-256 mismatch for %s: %s (expected %s)' % (dst, digest, spec['sha256']))
    log('input %s  %d bytes  sha256 %s' % (dst, len(data), digest))
    return dst


def check_provenance(path):
    im = Image.open(path)
    xmp = im.info.get('xmp', b'')
    if isinstance(xmp, bytes):
        xmp = xmp.decode('utf-8', 'replace')
    found = {
        'avm_id': (re.search(r'avm:ID="([^"]*)"', xmp) or [None, None])[1],
        'credit': (re.search(r'photoshop:Credit="([^"]*)"', xmp) or [None, None])[1],
        'title': (re.search(r'<dc:title>.*?<rdf:li[^>]*>([^<]*)<', xmp, re.S) or [None, None])[1],
        'size': list(im.size),
    }
    ok = found['avm_id'] == EXPECTED_AVM_ID and found['credit'] == EXPECTED_CREDIT
    if not ok:
        log('WARNING: embedded metadata does not identify %s / %s: %s' % (EXPECTED_AVM_ID, EXPECTED_CREDIT, found))
    if abs(im.size[0] - 2 * im.size[1]) > 2:
        raise SystemExit('expected a 2:1 all-sky panorama, got %s' % (im.size,))
    return found, ok


def load_luma(path):
    im = Image.open(path).convert('L')
    if im.size != WORK_SIZE:
        im = im.resize(WORK_SIZE, Image.LANCZOS)
    return np.asarray(im).astype(np.float32)


# --------------------------------------------------------------------------- 2. orientation
class Frame:
    """Image pixel <-> sky. The image is equirectangular in a frame obtained from the IAU
    galactic frame by the rotation R (v_img = R @ v_gal); longitude grows to the left,
    the image centre is longitude 0. b_off is a small vertical offset in degrees."""

    def __init__(self, w, h, R=None, b_off=0.0):
        self.w, self.h, self.R, self.b_off = w, h, np.eye(3) if R is None else R, b_off
        self.px = w / 360.0

    def pix_to_img_vec(self, x, y):
        lon = (180.0 - (x + 0.5) / self.px) % 360.0
        lat = 90.0 - (y + 0.5) / self.px + self.b_off
        return unit(lon, lat)

    def icrs_to_pix(self, v_icrs):
        vi = (v_icrs @ AG.T) @ self.R.T
        lon, lat = lonlat(vi)
        x = (self.w / 2.0 - lon * self.px - 0.5) % self.w
        y = self.h / 2.0 - (lat - self.b_off) * self.px - 0.5
        return x, y


def detect_stars(luma):
    k = int(round(STAR_MEDIAN_DEG * luma.shape[1] / 360.0)) | 1
    hp = luma - ndimage.median_filter(luma, size=k)
    hp = ndimage.gaussian_filter(hp, 0.7)
    peak = (hp == ndimage.maximum_filter(hp, size=5)) & (hp > np.percentile(hp, 99.9))
    y, x = np.nonzero(peak)
    flux = hp[y, x]
    o = np.argsort(-flux)[:6000]
    return x[o].astype(np.float64), y[o].astype(np.float64), flux[o]


def fit_orientation(luma, stars):
    """Match catalogue stars (mag < 4.5) to image peaks and fit the frame rotation (Kabsch)."""
    h, w = luma.shape
    sx, sy, sflux = detect_stars(luma)
    cat = stars[stars[:, 2] < 4.5]
    g = unit(cat[:, 0], cat[:, 1]) @ AG.T            # catalogue stars in the galactic frame
    frame = Frame(w, h)
    stats = None
    for radius in (5.0, 3.0, 2.0, 1.0, 0.6, 0.4, 0.4):
        p = frame.pix_to_img_vec(sx, sy)              # peaks in the image frame
        pred = g @ frame.R.T
        dots = pred @ p.T
        cosr = math.cos(math.radians(radius))
        pairs = []
        for i in range(len(pred)):
            c = np.nonzero(dots[i] > cosr)[0]
            if len(c):
                pairs.append((i, c[np.argmax(sflux[c])]))
        pairs = np.array(pairs)
        A, B = g[pairs[:, 0]], p[pairs[:, 1]]
        U, _, Vt = np.linalg.svd(A.T @ B)
        d = np.sign(np.linalg.det(Vt.T @ U.T))
        frame.R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
        # small vertical offset (half a pixel or so from resampling): mean latitude residual
        _, lat_pred = lonlat(A @ frame.R.T)
        _, lat_obs = lonlat(B)
        frame.b_off -= float(np.mean(lat_obs - lat_pred))
        obs = frame.pix_to_img_vec(sx[pairs[:, 1]], sy[pairs[:, 1]])
        res = np.degrees(np.arccos(np.clip(np.sum((A @ frame.R.T) * obs, 1), -1, 1)))
        stats = {'matched': int(len(pairs)), 'catalogue_stars': int(len(cat)),
                 'median_residual_deg': round(float(np.median(res)), 3),
                 'p90_residual_deg': round(float(np.percentile(res, 90)), 3)}
    gc_lon, gc_lat = lonlat(frame.R @ np.array([1.0, 0.0, 0.0]))
    stats.update({
        'rotation_deg': round(math.degrees(math.acos(min(1.0, (np.trace(frame.R) - 1) / 2))), 3),
        'galactic_centre_in_image_lon_lat': [round(float((gc_lon + 180) % 360 - 180), 3), round(float(gc_lat), 3)],
        'b_offset_deg': round(frame.b_off, 3),
    })
    if stats['matched'] < 0.7 * stats['catalogue_stars'] or stats['median_residual_deg'] > 0.25:
        raise SystemExit('orientation fit failed: %s' % stats)
    return frame, stats


# --------------------------------------------------------------------------- 3. glow map
def glow_map(luma, frame):
    h = luma.shape[0]
    k = int(round(STAR_MEDIAN_DEG * frame.px)) | 1
    m = ndimage.median_filter(luma, size=k)
    # Gaussian smoothing on the sphere, done in the image frame: per row along longitude
    # (sigma / cos(lat)), then along latitude. The Milky Way lies near the image equator,
    # where this is exact enough; rows near the poles get a capped kernel.
    lat = 90.0 - (np.arange(h) + 0.5) / frame.px
    s = SMOOTH_SIGMA_DEG * frame.px
    out = np.empty_like(m)
    for r in range(h):
        c = max(math.cos(math.radians(lat[r])), 0.05)
        out[r] = ndimage.gaussian_filter1d(m[r], s / c, mode='wrap')
    out = ndimage.gaussian_filter1d(out, s, axis=0, mode='nearest')
    return out


def sample(img, x, y):
    h, w = img.shape
    x0 = np.floor(x).astype(int)
    y0 = np.clip(np.floor(y).astype(int), 0, h - 2)
    fx = x - np.floor(x)
    fy = np.clip(y - y0, 0.0, 1.0)
    x1 = (x0 + 1) % w
    x0 = x0 % w
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy)
            + img[y0 + 1, x0] * (1 - fx) * fy + img[y0 + 1, x1] * fx * fy)


# --------------------------------------------------------------------------- 4. levels
def lattice_neighbours(v):
    tree = cKDTree(v)
    spacing = math.sqrt(4 * math.pi / len(v))
    return tree.query_pairs(1.6 * spacing, output_type='ndarray')


def components(mask, pairs):
    """Connected components of the lattice points in mask (union-find)."""
    parent = np.arange(len(mask))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b in pairs:
        if mask[a] and mask[b]:
            ra_, rb_ = find(a), find(b)
            if ra_ != rb_:
                parent[ra_] = rb_
    return np.array([find(i) for i in range(len(mask))])


def make_levels(value, b, pairs):
    """Cut the lattice values into levels 1..5 by sky share (LEVEL_AREA) and drop every patch that
    is not connected to the Galactic plane. Returns levels, thresholds and the dropped patches."""
    n = len(value)
    counts = [int(round(f * n)) for f in LEVEL_AREA]
    keep = np.ones(n, bool)
    dropped = []
    for _ in range(4):   # thresholds and the off-plane cut depend on each other; converges in 2
        v = np.where(keep, value, -np.inf)
        order = np.argsort(-v, kind='stable')
        thr = [float(v[order[c - 1]]) for c in counts]
        on = v >= thr[0]
        comp = components(on, pairs)
        plane_roots = set(comp[on & (np.abs(b) < PLANE_B)].tolist())
        off = on & ~np.isin(comp, list(plane_roots))
        if not off.any():
            break
        dropped += [np.nonzero(comp == r)[0] for r in np.unique(comp[off])]
        keep &= ~off
    level = np.zeros(n, np.int8)
    for k, t in enumerate(thr):
        level[(v >= t) & keep] = k + 1
    return level, thr, dropped


# --------------------------------------------------------------------------- 5. report
def report_metrics(level, ra, dec, pairs):
    v = unit(ra, dec)
    l, b = lonlat(v @ AG.T)
    rep = {'points': int((level > 0).sum()), 'per_level': {}, 'sky_share_ge': {}}
    for k in range(1, 6):
        rep['per_level'][k] = int((level == k).sum())
        rep['sky_share_ge'][k] = round(float((level >= k).mean()), 5)
    # centroid of the brightest level, galactic coordinates (the Galactic centre is l = 0, b = 0)
    for k in (5, 4):
        c = (v[level >= k] @ AG.T).mean(0)
        cl, cb = lonlat(c / np.linalg.norm(c))
        rep['level%d+_centroid_l_b' % k] = [round(float((cl + 180) % 360 - 180), 2), round(float(cb), 2)]
    # is the band continuous? every 1-degree step of galactic longitude has a level >= 1 point
    # within |b| <= 10; and the share of the exact equator (b = 0, 0.5-degree steps) that is lit
    # (dark nebulae such as the Great Rift and the Coalsack sit right on the equator)
    on = level > 0
    lb = np.zeros(360, bool)
    lb[np.floor(l[on & (np.abs(b) <= 10)]).astype(int) % 360] = True
    rep['band_longitudes_missing'] = np.nonzero(~lb)[0].tolist()
    tree = cKDTree(v)
    _, idx = tree.query(unit(np.arange(0, 360, 0.5), np.zeros(720)) @ AG)     # galactic -> ICRS
    rep['equator_lit_share'] = round(float((level[idx] > 0).mean()), 4)
    rep['connected_patches'] = int(len(np.unique(components(on, pairs)[on])))
    rep['max_abs_b'] = round(float(np.abs(b[on]).max()), 1)
    return rep


def iou(a, o):
    return {k: round(float(((a >= k) & (o >= k)).sum() / max(1, ((a >= k) | (o >= k)).sum())), 3)
            for k in range(1, 6)}


def old_levels_on_lattice(html, ra, dec):
    """Map an existing MW_DATA (points on the same lattice) back to lattice indices."""
    a = read_js_array(html, 'MW_DATA').reshape(-1, 3)
    tree = cKDTree(unit(ra, dec))
    d, idx = tree.query(unit(a[:, 0], a[:, 1]))
    if np.degrees(d.max()) > 0.1:
        raise SystemExit('MW_DATA points are not on the %d-point lattice' % LATTICE_N)
    lev = np.zeros(len(ra), np.int8)
    lev[idx] = a[:, 2].astype(np.int8)
    return lev


NAMED = {'LMC': (80.89, -69.75), 'SMC': (13.16, -72.8), 'M31': (10.685, 41.269), 'M45 Pleiades': (56.75, 24.12),
         'M42 Orion Nebula': (83.82, -5.39), 'NGC 1499 California Nebula': (60.2, 36.4), '47 Tuc': (6.02, -72.08)}


def describe_patch(idx, ra, dec, value):
    c = unit(ra[idx], dec[idx]).mean(0)
    c /= np.linalg.norm(c)
    cra, cdec = lonlat(c)
    cl, cb = lonlat(c @ AG.T)
    near = [k for k, (r, d) in NAMED.items() if math.degrees(math.acos(min(1.0, float(unit(r, d) @ c)))) < 6]
    eps = math.radians(23.4392911)          # ecliptic latitude: planets in the photo sit near 0
    beta = math.degrees(math.asin(-math.sin(eps) * c[1] + math.cos(eps) * c[2]))
    return {'points': int(len(idx)), 'ra_dec': [round(float(cra), 1), round(float(cdec), 1)],
            'l_b': [round(float((cl + 180) % 360 - 180), 1), round(float(cb), 1)],
            'ecliptic_lat': round(beta, 1), 'peak_value': round(float(value[idx].max()), 1), 'near': near}


def js_line(ra, dec, level):
    m = level > 0
    vals = []
    for r, d, k in zip(ra[m], dec[m], level[m]):
        vals += [fmt(r), fmt(d), str(int(k))]
    return 'const MW_DATA=[' + ','.join(vals) + '];'


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', choices=sorted(SOURCES), default='github-copy')
    ap.add_argument('--image', help='use this local copy of eso0932a instead of downloading')
    ap.add_argument('--html', default=INDEX_HTML, help='index.html to read STAR_DATA from / write MW_DATA to')
    ap.add_argument('--write', action='store_true', help='replace MW_DATA in --html')
    ap.add_argument('--check', action='store_true', help='compare with the MW_DATA currently in --html')
    ap.add_argument('--compare-html', help='also report IoU per level against the MW_DATA in this file')
    ap.add_argument('--report', help='write the JSON report here')
    ap.add_argument('--dump', help='save lattice values/levels as .npz (for plots)')
    args = ap.parse_args()

    path = fetch(args.source, args.image)
    meta, meta_ok = check_provenance(path)
    luma = load_luma(path)
    html = read_text(args.html)
    stars = read_js_array(html, 'STAR_DATA').reshape(-1, 4)

    frame, fit = fit_orientation(luma, stars)
    log('orientation:', json.dumps(fit))
    glow = glow_map(luma, frame)

    ra, dec = fibonacci_lattice(LATTICE_N)
    v = unit(ra, dec)
    _, b = lonlat(v @ AG.T)
    x, y = frame.icrs_to_pix(v)
    value = sample(glow, x, y)
    # sky background: median of the high-latitude rows (image frame; it is tilted by only a few degrees)
    row_lat = 90.0 - (np.arange(frame.h) + 0.5) / frame.px + frame.b_off
    bg = float(np.median(glow[np.abs(row_lat) >= BACKGROUND_MIN_B]))
    value = value - bg
    pairs = lattice_neighbours(v)
    level, thr, dropped = make_levels(value, b, pairs)

    rep = {
        'source': {'file': os.path.basename(path), 'sha256': hashlib.sha256(read_bytes(path)).hexdigest(),
                   'metadata': meta, 'metadata_ok': meta_ok},
        'orientation_fit': fit,
        'parameters': {'work_size': WORK_SIZE, 'star_median_deg': STAR_MEDIAN_DEG,
                       'smooth_sigma_deg': SMOOTH_SIGMA_DEG, 'lattice_n': LATTICE_N,
                       'level_area': LEVEL_AREA, 'plane_b_deg': PLANE_B, 'background_min_b_deg': BACKGROUND_MIN_B},
        'background': round(bg, 3),
        'thresholds_above_background': [round(t, 3) for t in thr],
        'dropped_off_plane': [describe_patch(i, ra, dec, value) for i in dropped],
    }
    rep['metrics'] = report_metrics(level, ra, dec, pairs)
    if args.compare_html:
        old = old_levels_on_lattice(read_text(args.compare_html), ra, dec)
        rep['compare'] = {'file': args.compare_html, 'metrics': report_metrics(old, ra, dec, pairs),
                          'iou_per_level': iou(level, old)}
    line = js_line(ra, dec, level)
    rep['mw_data_bytes'] = len(line.encode('utf-8'))

    if args.check:
        cur = old_levels_on_lattice(html, ra, dec)
        d = np.abs(cur.astype(int) - level.astype(int))
        rep['check'] = {'points_differing': int((d > 0).sum()), 'max_level_change': int(d.max())}
        log('check: %d lattice points differ from the MW_DATA in %s (largest change: %d level)'
            % (rep['check']['points_differing'], args.html, rep['check']['max_level_change']))
    if args.dump:
        np.savez_compressed(args.dump, ra=ra, dec=dec, value=value, level=level, thr=np.array(thr))
    out = json.dumps(rep, ensure_ascii=False, indent=2)
    print(out)
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(out + '\n')
    if args.write:
        comment = ('// MW_DATA: Milky Way glow as [RA, Dec (ICRS, degrees), level 1-5] on a 20,000-point '
                   'Fibonacci lattice. Generated by tools/milkyway/build_milkyway.py from '
                   '"The Milky Way panorama", ESO/S. Brunier (CC BY 4.0); see licenses.html.')
        new_html, n = re.subn(r'(?:// MW_DATA: [^\n]*\n)?const MW_DATA=\[[^\]]*\];',
                              lambda _: comment + '\n' + line, html, count=1)
        if n != 1:
            raise SystemExit('MW_DATA not found in ' + args.html)
        with open(args.html, 'w', encoding='utf-8', newline='') as f:
            f.write(new_html)
        log('wrote %d points (%d bytes) to %s' % ((level > 0).sum(), len(line), args.html))
    if args.check and rep['check']['points_differing']:
        sys.exit(1)


if __name__ == '__main__':
    main()
