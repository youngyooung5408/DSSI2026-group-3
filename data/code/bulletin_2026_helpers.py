"""Helpers for extracting 2026 CEC election-bulletin candidate cards.

The 2026 bulletins share one card template: a header row (號次‧姓名 | 學歷 | 經歷),
a left column (number, name, photo, 基本資料, 推薦之政黨, 具結情形), 學歷/經歷 cells,
and a 政見 box spanning the 學歷+經歷 columns. Vector grid lines are drawn
inconsistently across counties, so the grid is detected from the rendered page
image instead; text is then taken from the PDF text layer, with Windows OCR for
regions that are images (designed platform graphics, scanned pages).
"""
import re
import numpy as np

HEADER_MIN_W = 600      # a card spans ~690-705 pt; the 政見 title row ~500-520 pt
PLATFORM_W = (430, 600)
CARD_MIN_H = 150
DARK = 180              # light grey / red grid lines in some counties need a lenient threshold


def segments(dark, axis, min_len):
    """Runs of dark pixels along `axis` (0 = vertical runs per column)."""
    a = dark if axis == 0 else dark.T
    pad = np.zeros((1, a.shape[1]), bool)
    d = np.diff(np.vstack([pad, a, pad]).astype(np.int8), axis=0)
    starts = np.argwhere(d == 1)
    ends = np.argwhere(d == -1)
    order_s = np.lexsort((starts[:, 0], starts[:, 1]))
    order_e = np.lexsort((ends[:, 0], ends[:, 1]))
    s, e = starts[order_s], ends[order_e]
    keep = (e[:, 0] - s[:, 0]) >= min_len
    # (line position, run start, run end)
    return [(int(c), int(r0), int(r1)) for (r0, c), (r1, _) in zip(s[keep], e[keep])]


def merge_lines(segs, tol=3):
    """Collapse lines drawn as several adjacent pixel rows/columns into one."""
    out = []
    for p, a, b in sorted(segs):
        if any(p - q <= tol and abs(a - qa) <= 12 and abs(b - qb) <= 12 for q, qa, qb in out[-12:]):
            continue
        out.append((p, a, b))
    return out


def detect_cards(gray):
    """Return card geometry dicts (page points, rendered at scale 1)."""
    dark = gray < DARK
    hs = merge_lines(segments(dark, 1, 400))
    vs = merge_lines(segments(dark, 0, 20))
    # Some counties draw one horizontal line across both card columns; split such
    # lines at long vertical lines near the page centre so each card is found alone.
    w = gray.shape[1]
    mids = sorted({x for x, a, b in vs if 0.4 * w < x < 0.6 * w and b - a > 300})
    split = []
    for y, a, b in hs:
        cuts = [x for x in mids if a + 300 < x < b - 300 and any(abs(x - vx) <= 2 and va - 4 <= y <= vb + 4 for vx, va, vb in vs)]
        if b - a > 1.6 * HEADER_MIN_W and cuts:
            edges = [a, *cuts, b]
            split += [(y, l, r) for l, r in zip(edges, edges[1:]) if r - l >= 400]
        else:
            split.append((y, a, b))
    hs = merge_lines(split)
    cards = []
    wide = [h for h in hs if h[2] - h[1] >= HEADER_MIN_W]
    taken = []
    for y1, a1, b1 in wide:
        # A card top is a card-wide line with the column lines starting at it. The header
        # row's bottom line is sometimes too light to detect; then assume the usual 23 pt.
        if any(abs(y1 - t) < CARD_MIN_H and abs(a1 - ta) <= 12 for t, ta in taken):
            continue
        starting = [x for x, a, b in vs if abs(a - y1) <= 4 and b - y1 >= 16 and a1 - 6 <= x <= b1 + 6]
        if len(starting) < 3:
            continue
        y2 = next((y for y, a, b in wide if 16 <= y - y1 <= 32 and abs(a - a1) <= 8 and abs(b - b1) <= 8), y1 + 23)
        bottom = next((y for y, a, b in wide if y > y2 + CARD_MIN_H and abs(a - a1) <= 12 and abs(b - b1) <= 12), None)
        if bottom is None:
            continue
        # column boundaries: vertical lines crossing the header row inside the card
        xs = sorted({x for x, a, b in vs if a <= y1 + 4 and b >= y1 + 16 and a1 - 6 <= x <= b1 + 6})
        cols = []
        for x in xs:
            if not cols or x - cols[-1] > 8:
                cols.append(x)
        if len(cols) < 4:
            continue
        x0, x1 = cols[0], cols[-1]
        inner = cols[1:-1]
        plat = [(y, a, b) for y, a, b in hs if y2 + 20 < y < bottom - 20 and a1 - 6 <= a and b <= b1 + 6
                and PLATFORM_W[0] <= b - a <= PLATFORM_W[1] and abs(b - x1) <= 12]
        if not plat:
            continue
        p_top = plat[0][0]
        c1 = min(inner, key=lambda c: abs(c - plat[0][1]))
        c2 = max(inner)
        p_body = next((y for y, a, b in plat if 16 <= y - p_top <= 32), p_top + 23)
        cards.append(dict(x0=x0, x1=x1, c1=c1, c2=c2, top=y1, header_bottom=y2, platform_title=p_top,
                          platform_top=p_body, bottom=bottom))
        taken.append((y1, a1))
    return cards


def regions(card):
    c = card
    return {
        'left': (c['x0'], c['header_bottom'], c['c1'], c['bottom']),
        'education': (c['c1'], c['header_bottom'], c['c2'], c['platform_title']),
        'experience': (c['c2'], c['header_bottom'], c['x1'], c['platform_title']),
        'platform': (c['c1'], c['platform_top'], c['x1'], c['bottom']),
    }


def words_in(words, box, pad=1):
    x0, t, x1, b = box
    sel = [w for w in words if x0 - pad <= (w['x0'] + w['x1']) / 2 <= x1 + pad and t - pad <= (w['top'] + w['bottom']) / 2 <= b + pad]
    return sel


def words_to_text(sel):
    """Order words into lines (top-to-bottom, left-to-right)."""
    lines = []
    for w in sorted(sel, key=lambda w: (round(w['top']), w['x0'])):
        if lines and abs(w['top'] - lines[-1][0]) <= 3:
            lines[-1][1].append(w)
        else:
            lines.append([w['top'], [w]])
    return '\n'.join(' '.join(x['text'] for x in sorted(ws, key=lambda w: w['x0'])) for _, ws in lines).strip()


def image_share(images, box):
    x0, t, x1, b = box
    area = max((x1 - x0) * (b - t), 1)
    cover = sum(max(0, min(i['x1'], x1) - max(i['x0'], x0)) * max(0, min(i['bottom'], b) - max(i['top'], t))
                for i in images)
    return min(cover / area, 1.0)


def ocr_join(lines):
    text = '\n'.join(l['text'] for l in sorted(lines, key=lambda l: (l['y'], l['x'])))
    return re.sub(r'(?<=[㐀-鿿，。、：；）（「」]) (?=[㐀-鿿，。、：；）（「」])', '', text)


def core_name(s):
    return re.sub(r'[^㐀-鿿]', '', s)


LABELS = ['號次', '姓名', '基本資料', '推薦之政黨', '候選人之具結情形', '學歷', '經歷', '政見']


def parse_left(text):
    """Number, name, birth date (ROC), sex, birthplace and party from the left column."""
    flat = re.sub(r'\s+', '', text)
    out = {}
    m = re.search(r'出生年月日[：:]?(\d{1,3})年?(\d{1,2})月?(\d{1,2})日?', flat)
    if not m:
        nums = re.findall(r'\d+', flat.split('出生年月日')[1] if '出生年月日' in flat else '')
        m = nums[:3] if len(nums) >= 3 else None
        out['birth_roc'] = '-'.join(m) if m else ''
    else:
        out['birth_roc'] = '-'.join(m.groups())
    s = re.search(r'性別[：:]?([男女])', flat)
    out['sex'] = s.group(1) if s else ''
    bp = re.search(r'出生地[：:]?(.+?)(?:推薦之政黨|候選人之具結|$)', flat)
    out['birthplace'] = bp.group(1) if bp else ''
    party = re.search(r'推薦之政黨(.+?)(?:候選人之具結|候選人聲明|$)', flat)
    out['party_bulletin'] = party.group(1) if party and party.group(1) not in LABELS else ''
    head = re.split(r'基本資料|出生年月日', flat)[0]
    head = re.sub('|'.join(LABELS), '', head)
    num = re.match(r'\D*?(\d{1,2})', head)
    out['ballot_number'] = num.group(1) if num else ''
    out['name_bulletin'] = re.sub(r'\d+', '', head).strip('·‧．.')
    return out


# Cards whose grid cannot be detected from the image (花蓮縣: thick decorative frame and
# broken light lines). Boundaries measured by eye from a 1-pt ruler render on 2026-11-18;
# all four regions of these cards are read with OCR.
MANUAL_CARDS = {
    ('15花蓮縣/01縣長/花蓮縣縣長.pdf', 1): [
        dict(x0=62, top=470, c1=255, c2=515, x1=770, header_bottom=492, platform_title=540, platform_top=562, bottom=850),
        dict(x0=790, top=470, c1=985, c2=1210, x1=1490, header_bottom=492, platform_title=540, platform_top=562, bottom=850),
        dict(x0=62, top=857, c1=255, c2=515, x1=770, header_bottom=880, platform_title=1023, platform_top=1045, bottom=1300),
        dict(x0=790, top=857, c1=985, c2=1210, x1=1490, header_bottom=880, platform_title=1023, platform_top=1045, bottom=1300),
    ],
}


def cjk_count(s):
    return len(re.findall(r'[\u3400-\u9fff]', s or ''))


def choose_text(layer, ocr, img_share, force_ocr=False):
    """Prefer the PDF text layer unless it is missing, garbled, or the region is an image."""
    if force_ocr or '�' in (layer or ''):  # replacement characters: glyphs lost in the text layer
        return ocr, 'ocr'
    lc, oc = cjk_count(layer), cjk_count(ocr)
    if lc == 0 and oc == 0:
        return '', 'empty'
    if img_share >= 0.3 and oc > lc:
        return ocr, 'ocr'
    if lc >= 0.6 * oc:
        return layer, 'text_layer'
    return ocr, 'ocr'


def match_candidate(flat_left, name_text, pool):
    """pool: list of (candidate_key, core name). Exact core name first, then containment."""
    n = core_name(name_text)
    exact = [k for k, c in pool if c == n]
    if len(exact) == 1:
        return exact[0], 'exact_name'
    flat = core_name(flat_left)
    contained = [k for k, c in pool if c and c in flat]
    if len(contained) == 1:
        return contained[0], 'name_in_left_column'
    return None, 'unmatched' if not contained else 'ambiguous'


# Card names that neither the text layer nor OCR could read (large vertical name text).
# Read by eye from the rendered bulletin page on 2026-11-18 (Claude Code, checked against
# the ballot number, birth date and party printed on the same card).
# key: (file relative to data/raw/cec_bulletin_2026/, page, card x0, card top) -> name
MANUAL_NAMES = {
    ('05高雄市/02市議員/高雄市第03選舉區.pdf', 1, 778, 814): '蔣黃女',   # 4號, 32年10月10日, 無（楊喬茵指出後複查）
    ('05高雄市/02市議員/高雄市第03選舉區.pdf', 2, 56, 150): '黃韻涵',   # 7號, 女
    ('05高雄市/02市議員/高雄市第08選舉區.pdf', 1, 778, 1302): '黃鈺婷',  # 6號, 60年5月2日, 中國國民黨
    ('05高雄市/02市議員/高雄市第08選舉區.pdf', 2, 56, 150): '陳雅敏',    # 7號, 54年6月13日, 無
}


def manual_name(rel, page, x0, top, tol=6):
    for (f, p, x, t), name in MANUAL_NAMES.items():
        if f == rel and p == page and abs(x - x0) <= tol and abs(t - top) <= tol:
            return name
    return None
