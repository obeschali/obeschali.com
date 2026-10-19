"""Картинки превью 1200x630 для ссылок (нужен playwright: pip install playwright && playwright install chromium)."""
import json, html, pathlib
COLS = ['#E4E0D5', '#A79D84', '#9DB0BF', '#C9C2AE']
UI_RU = {'kind': {'promise': 'Обещание', 'forecast': 'Прогноз', 'denial': 'Заверение', 'irony': 'Ирония'}, 'logo': 'Обещали.', 'more': 'Что было дальше →', 'sub': 'Публичные слова и то, что было дальше.', 'role': 'Документальный архив заявлений и их последствий', 'open': 'Открыть →'}
HERE = pathlib.Path(__file__).parent
FONTS = (HERE / 'og_fonts').resolve().as_uri()
CSS = f'''
@font-face{{font-family:Onest;src:url({FONTS}/on-cyr.woff2) format("woff2");font-weight:100 900;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:Onest;src:url({FONTS}/on-lat.woff2) format("woff2");font-weight:100 900;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
@font-face{{font-family:JB;src:url({FONTS}/jb600-cyr.woff2) format("woff2");font-weight:600;unicode-range:U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116}}
@font-face{{font-family:JB;src:url({FONTS}/jb600-lat.woff2) format("woff2");font-weight:600;unicode-range:U+0000-00FF,U+0131,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215}}
*{{box-sizing:border-box}}html,body{{margin:0}}
body{{width:1200px;height:630px;font-family:Onest,sans-serif;color:#0C0C0A;position:relative;overflow:hidden}}
.logo{{position:absolute;left:64px;top:48px;font-weight:800;font-size:40px;letter-spacing:-.04em;line-height:1}}
.tag{{position:absolute;right:64px;top:56px;font:600 15px JB,monospace;letter-spacing:.14em;text-transform:uppercase}}
.line{{position:absolute;left:0;right:0;top:120px;border-top:2px solid #0C0C0A}}
.q{{position:absolute;left:64px;right:64px;top:150px;height:290px;display:flex;align-items:center}}
.q p{{margin:0;font-weight:700;line-height:.98;letter-spacing:-.045em;text-wrap:balance}}
.by{{position:absolute;left:64px;right:64px;bottom:44px;border-top:2px solid #0C0C0A;padding-top:22px;display:flex;justify-content:space-between;align-items:flex-end}}
.who{{font-weight:700;font-size:44px;letter-spacing:-.035em;line-height:1.05}}
.role{{font-size:22px;opacity:.85;margin-top:4px}}
.more{{font:600 16px JB,monospace;letter-spacing:.14em;text-transform:uppercase;display:flex;align-items:center;gap:12px;white-space:nowrap}}
.more i{{display:block;width:12px;height:12px;background:#0C0C0A}}
'''
def card(s, col, U=None):
    U = U or UI_RU; KIND = U['kind']; q = s['quote']
    return f'''<!doctype html><meta charset="utf-8"><style>{CSS}body{{background:{col}}}</style>
<div class="logo">{html.escape(U["logo"])}</div><div class="tag">{html.escape(KIND.get(s['kind'], ''))} · {html.escape(s['date'][:4])}</div><div class="line"></div>
<div class="q"><p id="p">{html.escape(q)}</p></div>
<div class="by"><div><div class="who">{html.escape(s['who'])}</div><div class="role">{html.escape(s['role'])}</div></div><div class="more"><i></i>{html.escape(U["more"])}</div></div>
<script>
const p=document.getElementById('p'),box=p.parentElement;
for(let f=84;f>=30;f-=2){{p.style.fontSize=f+'px';if(box.scrollHeight<=box.clientHeight+1&&p.scrollWidth<=box.clientWidth+1)break;}}
</script>'''
def default_card(U=None):
    U = U or UI_RU
    return f'''<!doctype html><meta charset="utf-8"><style>{CSS}body{{background:#E4E0D5}}
.big{{position:absolute;left:64px;top:150px;font-weight:800;font-size:150px;letter-spacing:-.05em;line-height:1}}
.sub{{position:absolute;left:64px;top:340px;width:900px;font-weight:700;font-size:54px;line-height:1.05;letter-spacing:-.04em}}</style>
<div class="logo" style="opacity:0">{html.escape(U["logo"])}</div><div class="line"></div>
<div class="big">{html.escape(U["logo"])}</div><div class="sub">{html.escape(U["sub"])}</div>
<div class="by"><div class="role" style="font-size:24px">{html.escape(U["role"])}</div><div class="more"><i></i>{html.escape(U["open"])}</div></div>'''
def render(data, out, U=None):
    U = U or UI_RU
    from playwright.sync_api import sync_playwright
    out = pathlib.Path(out); out.mkdir(exist_ok=True)
    tmp = HERE / '_og_tmp.html'
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1200, 'height': 630})
        def shot(htm, name):
            tmp.write_text(htm, encoding='utf8'); pg.goto(tmp.resolve().as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(120)
            pg.screenshot(path=str(out / name))
        shot(default_card(U), 'default.png')
        for i, s in enumerate(data):
            shot(card(s, COLS[i % 4], U), s['id'] + '.png')
        b.close()
    tmp.unlink(missing_ok=True)
    print('og:', len(data) + 1, 'картинок')
