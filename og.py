"""Картинки превью 1200x630 для ссылок (нужен playwright: pip install playwright && playwright install chromium).
Слева — обещание (светлая половина), справа — что было дальше (тёмная). Срок — мелкая метка."""
import html, pathlib, datetime
HERE = pathlib.Path(__file__).parent
FONTS = (HERE / 'og_fonts').resolve().as_uri()
INK, PAPER, MUTE = '#0C0C0A', '#E4E0D5', '#B8AE95'
CSS = f'''
@font-face{{font-family:Onest;src:url({FONTS}/on-cyr.woff2) format("woff2");font-weight:100 900;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:Onest;src:url({FONTS}/on-lat.woff2) format("woff2");font-weight:100 900;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
@font-face{{font-family:JB;src:url({FONTS}/jb600-cyr.woff2) format("woff2");font-weight:600;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:JB;src:url({FONTS}/jb600-lat.woff2) format("woff2");font-weight:600;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:1200px;height:630px;font-family:Onest,sans-serif;color:{INK};background:{PAPER};position:relative;overflow:hidden}}
.mono{{font:600 19px JB,monospace;letter-spacing:.08em;text-transform:uppercase}}
.p{{position:absolute;top:0;bottom:0;width:600px;padding:44px 52px 40px 64px;display:flex;flex-direction:column}}
.l{{left:0}}.r{{right:0;background:{INK};color:{PAPER};padding:44px 64px 40px 56px}}
.lab{{display:flex;flex-wrap:wrap;justify-content:space-between;column-gap:20px;row-gap:6px;white-space:nowrap}}.r .lab{{color:{MUTE}}}
.q{{flex:1;margin:26px 0;display:flex;flex-direction:column;align-items:flex-start;justify-content:center}}
.mark,.mk2{{display:block;width:auto}}.mark{{fill:{INK}}}
.fit{{margin:0;font-weight:700;line-height:.98;letter-spacing:-.045em;text-wrap:balance}}
.r .fit{{font-weight:760;letter-spacing:-.05em}}
.who{{font-weight:700;font-size:30px;letter-spacing:-.03em}}.role{{font-size:21px;opacity:.78;margin-top:2px}}
.logo{{font-weight:800;font-size:30px;letter-spacing:-.04em;text-align:right}}
.big{{position:absolute;left:60px;top:190px;z-index:5;font-weight:800;font-size:108px;letter-spacing:-.055em;line-height:1;white-space:nowrap}}
.sub{{position:absolute;left:64px;top:350px;width:480px;font-weight:700;font-size:36px;line-height:1.06;letter-spacing:-.03em}}
.rt{{position:absolute;left:656px;top:230px;width:480px;font-weight:760;font-size:56px;line-height:1.02;letter-spacing:-.05em;color:{PAPER}}}
.bt{{position:absolute;left:656px;bottom:40px;color:{MUTE}}}
'''
FIT = '''<script>document.fonts.load('700 40px Onest','Яя').then(()=>document.fonts.ready).then(()=>{const ps=[...document.querySelectorAll('[data-fit]')],mk=document.querySelector('.mark');for(let f=64;f>=28;f-=2){ps.forEach(p=>p.style.fontSize=f+'px');mk.style.height=Math.round(f*.5)+'px';mk.style.marginBottom=Math.round(f*.16)+'px';document.querySelectorAll('.mk2').forEach(m=>{m.style.height=mk.style.height;m.style.marginBottom=mk.style.marginBottom});if(ps.every(p=>p.parentElement.scrollHeight<=p.parentElement.clientHeight+1&&p.scrollWidth<=p.parentElement.clientWidth+1))break;}window.__fit=1});</script>'''
MARK = '<svg class="mark" viewBox="0 0 92 64"><polygon points="0,64 0,30 24,0 40,0 40,64"/><polygon points="52,64 52,30 76,0 92,0 92,64"/></svg>'
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
    return f'''<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="p l"><div class="mono lab"><span>{E(kind)} · {E(s['date'][:4])}</span></div>
<div class="q">{MARK}<p class="fit" data-fit>{E(s['quote'])}</p></div>
<div><div class="who">{E(s['who'])}</div><div class="role">{E(s['role'])}</div></div></div>
<div class="p r"><div class="mono lab"><span>{E(U['next'])} · {E(s['odate'][:4])}</span><span>{E(after(s, U))}</span></div>
<div class="q"><div class="mk2"></div><p class="fit" data-fit>{E(s['head'])}</p></div>
<div class="logo">{E(U['logo'])}</div></div>{FIT}'''

def default_card(U):
    return f'''<!doctype html><meta charset="utf-8"><style>{CSS}</style>
<div class="p l"><div class="mono lab"><span>{E(U['kind'].get('promise', ''))}</span></div></div>
<div class="big">{E(U['logo'])}</div><div class="sub">{E(U['sub'])}</div>
<div class="p r"><div class="mono lab"><span>{E(U['next'])}</span></div></div>
<div class="rt">{E(U['role'])}</div><div class="mono bt">{E(U['open'])}</div>'''

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
            pg.screenshot(path=str(out / name))
        shot(default_card(U), 'default.png', False)
        for s in data: shot(card(s, U), s['id'] + '.png', True)
        b.close()
    tmp.unlink(missing_ok=True)
    print('og:', len(data) + 1, 'картинок')
