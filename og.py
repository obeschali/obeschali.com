"""Картинки превью 1200x630 для ссылок (нужен playwright: pip install playwright && playwright install chromium).
Слева — обещание (светлая половина), справа — что было дальше (тёмная). Срок — мелкая метка."""
import html, pathlib, datetime
HERE = pathlib.Path(__file__).parent
FONTS = (HERE / 'og_fonts').resolve().as_uri()
INK, PAPER, MUTE = '#0C0C0A', '#E4E0D5', '#B8AE95'
NB = '\u00a0'
# Сетка: метка 44 · кавычка 118 · текст 170–470 · подпись 506. Цитата — PT Serif, остальное — Onest.
CSS = f'''
@font-face{{font-family:Onest;src:url({FONTS}/on-cyr.woff2) format("woff2");font-weight:100 900;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:Onest;src:url({FONTS}/on-lat.woff2) format("woff2");font-weight:100 900;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
@font-face{{font-family:PTS;src:url({FONTS}/pts700-cyr.woff2) format("woff2");font-weight:700;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:PTS;src:url({FONTS}/pts700-lat.woff2) format("woff2");font-weight:700;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
@font-face{{font-family:JB;src:url({FONTS}/jb600-cyr.woff2) format("woff2");font-weight:600;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:JB;src:url({FONTS}/jb600-lat.woff2) format("woff2");font-weight:600;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:1200px;height:630px;font-family:Onest,sans-serif;color:{INK};background:{PAPER};position:relative;overflow:hidden;-webkit-font-smoothing:antialiased}}
.dark{{position:absolute;left:600px;top:0;width:600px;height:630px;background:{INK}}}
.a{{position:absolute;width:480px}}
.mono{{font:600 19px/24px JB,monospace;letter-spacing:.08em;text-transform:uppercase}}
.lab{{top:44px;display:flex;justify-content:space-between;white-space:nowrap}}
.l{{left:64px}}.r{{left:656px}}.r.lab{{color:{MUTE}}}
.mark{{position:absolute;left:64px;top:118px;height:32px;width:auto;fill:{INK}}}
.fit{{top:170px;margin:0;text-wrap:balance;hyphens:none;overflow-wrap:normal}}
.qs{{font-family:PTS,Georgia,serif;font-weight:700;letter-spacing:-.015em;line-height:1.04}}
.rs{{font-family:Onest,sans-serif;font-weight:760;letter-spacing:-.05em;line-height:.98;color:{PAPER}}}
.who{{top:506px;font-weight:700;font-size:28px;line-height:31px;letter-spacing:-.02em}}
.role{{top:538px;font-size:20px;line-height:24px;opacity:.78;text-wrap:balance}}
.logo{{top:506px;font-weight:800;font-size:28px;line-height:31px;letter-spacing:-.04em;color:{PAPER}}}
.site{{top:538px;font-size:20px;line-height:24px;opacity:.78;color:{PAPER}}}
.big{{left:64px;top:164px;width:auto;font-weight:800;font-size:96px;line-height:1;letter-spacing:-.055em;white-space:nowrap}}
.sub{{left:64px;top:276px;font-family:PTS,Georgia,serif;font-weight:700;font-size:36px;line-height:1.04;letter-spacing:-.015em;text-wrap:balance}}
.rt{{left:656px;top:170px;font-weight:760;font-size:50px;line-height:.98;letter-spacing:-.05em;color:{PAPER};text-wrap:balance}}
.bt{{left:656px;top:510px;color:{MUTE}}}.url{{left:64px;top:510px;opacity:.6}}
'''
# Кегль: от 72 вниз с шагом 2 до 24; берём первый, при котором текст целиком в колонке 480 × 300 и ни одно слово не шире колонки.
FIT = '''<script>Promise.all([['700 40px PTS','Яя«»'],['700 40px PTS','Aa1'],['760 40px Onest','Яя'],['760 40px Onest','Aa1']].map(f=>document.fonts.load(f[0],f[1]))).then(()=>document.fonts.ready).then(()=>{const H=300;for(const p of document.querySelectorAll('[data-fit]')){let ok=0;for(let f=72;f>=24;f-=2){p.style.fontSize=f+'px';if(p.scrollWidth<=p.clientWidth+1&&p.getBoundingClientRect().height<=H+.5){ok=1;break}}p.dataset.ok=ok}window.__fit=1});</script>'''
MARK = '<svg class="mark" viewBox="0 0 92 64"><polygon points="0,64 0,30 24,0 40,0 40,64"/><polygon points="52,64 52,30 76,0 92,0 92,64"/></svg>'
def glue(t):
    """Неразрывные пробелы: короткие слова и тире не повисают в конце строки."""
    import re
    t = re.sub(r'(\d)-([а-яёa-z])', '\\1-\u2060\\2', t)
    t = t.replace(' — ', NB + '— ').replace(' – ', NB + '– ')
    out = []
    for w in t.split(' '):
        if out and w and not out[-1].endswith(NB):
            pv = re.sub(r'[«»,.:;!?…"“”\[\]]', '', out[-1])
            if re.search(r'(^|[^а-яёa-z])[а-яёa-z]{1,2}$', pv, re.I) and not re.search(r'[.!?…]$', out[-1]) and len(out[-1]) + len(w) < 17:
                out[-1] = out[-1] + NB + w; continue
        out.append(w)
    return ' '.join(out)
E = html.escape

def _date(x):
    x = str(x)
    return datetime.date.fromisoformat((x + '-01-01')[:10] if len(x) == 4 else (x + '-01')[:10] if len(x) == 7 else x[:10])

def _plural(U, n, kind):
    u = U['unit'][kind]
    if U['lang'] == 'en': return u['one'] if n == 1 else u['many']
    m100, m10 = n % 100, n % 10
    if m10 == 1 and m100 != 11: return u['one']
    if 2 <= m10 <= 4 and not 11 <= m100 <= 14: return u['few']
    return u['many']

def after(s, U):
    """Срок между словом и тем, что было дальше — как на сайте: до 100 дней — дни, до 24 месяцев — месяцы, дальше годы."""
    d = (_date(s['odate']) - _date(s['date'])).days
    if d < 100: n, k = max(round(d), 0), 'day'
    elif d / 30.4375 < 24: n, k = int(d // 30.4375), 'month'
    else: n, k = int(d // 365.25), 'year'
    return U['after'].replace('{n}', str(n)).replace('{unit}', _plural(U, n, k))

def card(s, U):
    kind = U['kind'].get(s['kind'], '')
    return f'''<!doctype html><meta charset="utf-8"><style>{CSS}</style><div class="dark"></div>
<div class="a l mono lab"><span>{E(kind)} · {E(s['date'][:4])}</span></div>
<div class="a r mono lab"><span>{E(U['next'])}</span><span>{E(after(s, U))}</span></div>
{MARK}<p class="a l fit qs" data-fit>{E(glue(s['quote']))}</p><p class="a r fit rs" data-fit>{E(glue(s['head']))}</p>
<div class="a l who">{E(s['who'])}</div><div class="a l role">{E(s['role'])}</div>
<div class="a r logo">{E(U['logo'])}</div><div class="a r site">obeschali.com</div>{FIT}'''

def default_card(U):
    return f'''<!doctype html><meta charset="utf-8"><style>{CSS}</style><div class="dark"></div>
<div class="a l mono lab"><span>{E(U['kind'].get('promise', ''))}</span></div><div class="a r mono lab"><span>{E(U['next'])}</span></div>
{MARK}<div class="a big">{E(U['logo'])}</div><div class="a sub">{E(U['sub'])}</div>
<div class="a rt">{E(U['role'])}</div><div class="a mono url">obeschali.com</div><div class="a mono bt">{E(U['open'])}</div>'''

def render(data, out, U):
    from playwright.sync_api import sync_playwright
    out = pathlib.Path(out); out.mkdir(exist_ok=True)
    tmp = HERE / '_og_tmp.html'
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1200, 'height': 630})
        def shot(htm, name, fit):
            tmp.write_text(htm, encoding='utf8'); pg.goto(tmp.resolve().as_uri()); pg.evaluate('document.fonts.ready')
            if fit: pg.wait_for_function('window.__fit===1')
            else: pg.wait_for_timeout(200)
            if fit:
                bad = pg.evaluate("[...document.querySelectorAll('[data-fit]')].filter(p=>p.dataset.ok!=='1').length")
                if bad: print('og: НЕ ПОМЕСТИЛОСЬ', name)
            pg.screenshot(path=str(out / name))
        shot(default_card(U), 'default.png', False)
        for s in data: shot(card(s, U), s['id'] + '.png', True)
        b.close()
    tmp.unlink(missing_ok=True)
    print('og:', len(data) + 1, 'картинок')
