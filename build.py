#!/usr/bin/env python3
"""Собирает сайт: русская версия в корне (index.html, s/<id>/, og/) и английская в en/ (если есть готовые переводы).
Запуск: python3 build.py            (картинки пересобираются, если есть playwright)
        python3 build.py --no-og    (без картинок)
Настройки: site.config.json — site (адрес сайта), contact (mailto:... или https://t.me/...),
           en_statuses (какие статусы перевода публиковать; по умолчанию ["reviewed","approved"]).
Английская версия появляется только если: есть хотя бы одна опубликуемая история И готовы английские интерфейсные
и редакционные тексты (i18n/en/ui.json, i18n/en/editorial.json). Без этого собирается только русская версия."""
import json, os, re, sys, html, shutil, pathlib
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT / 'i18n'))
import i18n as I
cfg = json.load(open(ROOT / 'site.config.json', encoding='utf8'))
SITE = cfg.get('site', '').rstrip('/')
CONTACT = cfg.get('contact', '')
CRYPTO = cfg.get('crypto', [])
EN_STATUSES = cfg.get('en_statuses', ['reviewed', 'approved'])
FIRST = ['putin-2005-pensionny-vozrast', 'rogozin-2014-batut', 'chubays-2012-devalvatsiya', 'mutko-2017-doping',
         'medvedev-2016-deneg-net', 'putin-2011-internet', 'peskov-2022-mobilizatsiya']
stories = json.load(open(ROOT / 'stories.json', encoding='utf8'))
by = {s['id']: s for s in stories}
order = [by[i] for i in FIRST if i in by] + [s for s in stories if s['id'] not in FIRST]
keys = ['id', 'who', 'role', 'date', 'place', 'kind', 'quote', 'qsrc', 'head', 'body', 'odate', 'osrc']
def _ru_rec(s):
    r = {k: s.get(k, '') for k in keys}; dt, num, ctx = I.doctype_of(s.get('place', ''))
    r.update({'mt': dt, 'mn': num or '', 'mc': ctx}); return r
data_ru = [_ru_rec(s) for s in order]
tpl = (ROOT / 'template.html').read_text(encoding='utf8')

# ---------- русские интерфейсные тексты ----------
ui_src = json.load(open(ROOT / 'i18n/source/ui.ru.json', encoding='utf8'))
ed_src = json.load(open(ROOT / 'i18n/source/editorial.ru.json', encoding='utf8'))
T_RU = {k: v['ru'] for k, v in ui_src['strings'].items()}
T_RU.update({k: v['ru'] for k, v in ed_src['strings'].items()})
T_RU.update({'story.not_translated': 'Английской версии этой истории пока нет', 'lang.switch_aria': 'Язык', 'quote.show_original': 'Показать оригинал', 'quote.hide_original': 'Скрыть оригинал'})

# ---------- английская версия ----------
def load_en_ui():
    """Возвращает словарь T для EN или None, если интерфейсные/редакционные тексты неполны."""
    T = {}; missing = []
    for name, src, newkey in (('ui', ui_src, 'new_strings_for_en_architecture'), ('editorial', ed_src, None)):
        f = I.EN / f'{name}.json'
        cur = json.load(open(f, encoding='utf8')) if f.exists() else {'strings': {}, 'new_strings': {}}
        for k in src['strings']:
            v = cur['strings'].get(k)
            if v and v.get('en') not in (None, ''): T[k] = v['en']
            elif k.endswith('.few'): T[k] = ''
            else: missing.append(k)
        if newkey:
            for k in src[newkey]:
                if k == '_readme': continue
                v = cur.get('new_strings', {}).get(k)
                if v and v.get('en'): T[k] = v['en']
                elif k not in ('story.translation_note', 'quote.original_label'): missing.append(k)
    return T, missing

def en_story(s):
    """Опубликуемая английская запись истории или None."""
    e = I.load_en(s['id'])
    if not e or e.get('status') not in EN_STATUSES or e['source_hash'] != I.story_hash(s): return None
    en = e['en']; dt, num, _ = I.doctype_of(s.get('place', '')); ex = e.get('en_extra_sources') or {}
    def srcs(ru, tr, extra):
        out = [{'t': tr[i]['t'], 'u': ru[i]['u'], 'l': 'ru'} for i in range(len(ru))]
        return out + [{'t': x['t'], 'u': x['u'], 'l': x.get('lang', 'en')} for x in extra or []]
    return {'id': s['id'], 'who': en['who'], 'role': en['role'], 'date': s['date'], 'place': '', 'kind': s['kind'],
            'quote': en['quote'], 'qsrc': srcs(s['qsrc'], en['qsrc'], ex.get('quote')), 'head': en['head'], 'body': en['body'],
            'odate': s['odate'], 'osrc': srcs(s['osrc'], en['osrc'], ex.get('outcome')),
            'mt': dt, 'mn': num or '', 'mc': en['meta_context'], 'ru': {'quote': s['quote']}}

data_en = [x for x in (en_story(s) for s in data_ru) if x]
T_EN, miss = load_en_ui() if data_en else (None, [])
if data_en and miss:
    print('Английская версия НЕ собрана: не хватает интерфейсных/редакционных текстов:', ', '.join(miss[:8]) + (' …' if len(miss) > 8 else ''))
    data_en = []
HAS_EN = bool(data_en)

# ---------- общие куски ----------
def absurl(p): return (SITE + '/' + p) if SITE else p

def og_meta(T, loc, title, desc, img, url=None):
    t = html.escape(title, quote=True); d = html.escape(desc, quote=True)
    m = ['<meta property="og:type" content="website">', f'<meta property="og:site_name" content="{html.escape(T["page.title.default"], quote=True)}">',
         f'<meta property="og:locale" content="{loc}">', f'<meta property="og:title" content="{t}">',
         f'<meta property="og:description" content="{d}">', f'<meta property="og:image" content="{img}">',
         '<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">',
         '<meta name="twitter:card" content="summary_large_image">', f'<meta name="twitter:title" content="{t}">',
         f'<meta name="twitter:description" content="{d}">', f'<meta name="twitter:image" content="{img}">']
    if url: m.insert(1, f'<meta property="og:url" content="{url}">')
    return '\n'.join(m)

def alt_links(lang, path_ru, path_en):
    """hreflang и canonical. Нужен адрес сайта (в hreflang только абсолютные ссылки)."""
    if not SITE: return ''
    own = path_ru if lang == 'ru' else path_en
    L = [f'<link rel="canonical" href="{SITE}/{own}">']
    if path_en is not None:
        L += [f'<link rel="alternate" hreflang="ru" href="{SITE}/{path_ru}">', f'<link rel="alternate" hreflang="en" href="{SITE}/{path_en}">',
              f'<link rel="alternate" hreflang="x-default" href="{SITE}/{path_ru}">']
    return '\n'.join(L)

def switch_html(lang):
    if not HAS_EN: return ''
    aria = html.escape((T_EN if lang == 'en' else T_RU)['lang.switch_aria'], quote=True)
    a = lambda l, href: f'<a href="{href}" data-lang="{l}" hreflang="{l}" lang="{l}"' + (' aria-current="true"' if l == lang else '') + f'>{l.upper()}</a>'
    return f'<div class="lg" role="group" aria-label="{aria}" data-ta="lang.switch_aria">{a("ru", "/" if lang == "ru" else "/")}{a("en", "/en/")}</div>'

def render_index(lang, data, T, route):
    """Одна и та же страница-приложение: route='story' (корень языка) или 'about' (/about/)."""
    pre = '' if lang == 'ru' else 'en/'
    loc = 'ru_RU' if lang == 'ru' else 'en_US'
    home, about = '/' + pre, '/' + pre + 'about/'
    ALT = {'ru': '/', 'en': '/en/', 'aboutRu': '/about/', 'aboutEn': '/en/about/', 'enIds': [x['id'] for x in data_en]} if HAS_EN else None
    idx = tpl
    if lang == 'en':
        idx = idx.replace('>Обещали.</a>', '>' + html.escape(T['page.title.default']) + '</a>').replace('pointer-events:none">Обещали.</span>', 'pointer-events:none">' + html.escape(T['page.title.default']) + '</span>')
    title = T['page.title.default'] if route == 'story' else T['page.title.about']
    desc = T['page.description'] if route == 'story' else T['page.description.about']
    own = pre if route == 'story' else pre + 'about/'
    idx = idx.replace('@@LANG@@', lang).replace('@@TITLE@@', html.escape(title)).replace('@@DESC@@', html.escape(desc, quote=True))
    idx = idx.replace('@@ROUTE@@', route).replace('@@HOME@@', home).replace('@@ABOUT@@', about)
    if route == 'about':
        idx = idx.replace('<div id="app" aria-live="off"', '<div id="app" class="ab" aria-live="off"').replace('class="ov about" id="about"', 'class="ov about open" id="about"').replace('data-ta="about.aria" aria-hidden="true"', 'data-ta="about.aria" aria-hidden="false"')
    idx = idx.replace('@@SWITCH@@', switch_html(lang))
    idx = idx.replace('@@ALTLINKS@@', alt_links(lang, '' if route == 'story' else 'about/', ('en/' if route == 'story' else 'en/about/') if HAS_EN else None))
    idx = idx.replace('@@OG@@', og_meta(T, loc, title, desc, absurl(pre + 'og/default.png'), (SITE + '/' + own) if SITE else None))
    idx = idx.replace('@@UI@@', json.dumps(T, ensure_ascii=False)).replace('@@ALT@@', json.dumps(ALT, ensure_ascii=False))
    idx = idx.replace('@@DATA@@', json.dumps(data, ensure_ascii=False)).replace('@@SITE@@', SITE)
    idx = idx.replace('@@NOSCRIPT@@', html.escape(T['noscript']))
    if CRYPTO:
        rows = ''.join('<div class="w"><span class="cn">%s</span><code>%s</code><button type="button" class="cp" data-a="%s" data-t="about.copy">Скопировать</button></div>' % (html.escape(c['name']), html.escape(c['addr']), html.escape(c['addr'], quote=True)) for c in CRYPTO)
        idx = idx.replace('@@SUPPORT@@', rows)
    else:
        idx = re.sub(r'<!--SUP-->.*?<!--/SUP-->|<!--SUPB-->.*?<!--/SUPB-->', '', idx, flags=re.S)
    if CONTACT: idx = idx.replace('@@CONTACT@@', html.escape(CONTACT, quote=True))
    else: idx = re.sub(r'\s*<a class="btn" href="@@CONTACT@@".*?</a>', '', idx, flags=re.S)
    return idx

def build_lang(lang, data, T, outdir):
    """Одна языковая версия: outdir/index.html + outdir/s/<id>/index.html. Возвращает список страниц историй."""
    pre = '' if lang == 'ru' else 'en/'          # префикс адреса
    root_rel = '../../'                           # со страницы истории — к индексу языка
    loc = 'ru_RU' if lang == 'ru' else 'en_US'
    other = 'en/' if lang == 'ru' else '../'
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / 'index.html').write_text(render_index(lang, data, T, 'story'), encoding='utf8')
    (outdir / 'about').mkdir(exist_ok=True); (outdir / 'about' / 'index.html').write_text(render_index(lang, data, T, 'about'), encoding='utf8')
    for s in data:
        q = s['quote'].lstrip('…')
        qq = ('«' + q[:110] + ('…' if len(q) > 110 else '') + '»') if lang == 'ru' else ('“' + q[:110] + ('…' if len(q) > 110 else '') + '”')
        title = f"{s['who']}: {qq}"
        full = T['page.title.story'].replace('{who}', s['who']).replace('{quote}', q[:110] + ('…' if len(q) > 110 else ''))
        desc = T['page.description.story_prefix'] + ' ' + T['page.description']
        other_has = (lang == 'ru' and HAS_EN and s['id'] in {x['id'] for x in data_en}) or lang == 'en'
        links = ''
        if SITE and other_has:
            pr, pe = f"s/{s['id']}/", f"en/s/{s['id']}/"
            links = alt_links(lang, pr, pe)
        elif SITE:
            links = alt_links(lang, f"s/{s['id']}/", None)
        page = f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(full)}</title>
<meta name="description" content="{html.escape(T["page.description"], quote=True)}">{links}
{og_meta(T, loc, title, desc, absurl(pre + 'og/' + s['id'] + '.png'), absurl(pre + 's/' + s['id'] + '/'))}
<meta http-equiv="refresh" content="0;url={root_rel}#{s['id']}">
<script>location.replace('{root_rel}#{s['id']}');</script>
</head><body style="margin:0;background:#E4E0D5;font:18px Onest,system-ui,sans-serif;padding:40px"><a href="{root_rel}#{s['id']}">{html.escape(T['page.story_link'])}</a></body></html>
'''
        d = outdir / 's' / s['id']; d.mkdir(parents=True, exist_ok=True); (d / 'index.html').write_text(page, encoding='utf8')

build_lang('ru', data_ru, T_RU, ROOT)
en_dir = ROOT / 'en'
if HAS_EN:
    if en_dir.exists(): shutil.rmtree(en_dir)
    build_lang('en', data_en, T_EN, en_dir)
elif en_dir.exists() and (en_dir / 'index.html').exists():
    shutil.rmtree(en_dir)   # переводов больше нет — английская версия не должна висеть
print('index.html:', len(data_ru), 'историй;', 'EN:', len(data_en) if HAS_EN else 'нет', ';', 'site =', SITE or '(не задан)', '; contact =', CONTACT or '(не задан)')

# ---------- sitemap и robots (только если известен адрес сайта) ----------
if SITE:
    urls = [(SITE + '/', SITE + '/en/' if HAS_EN else None), (SITE + '/about/', SITE + '/en/about/' if HAS_EN else None)]
    en_ids = {x['id'] for x in data_en}
    for s in data_ru: urls.append((f"{SITE}/s/{s['id']}/", f"{SITE}/en/s/{s['id']}/" if s['id'] in en_ids else None))
    L = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    def ent(u, alt_ru, alt_en):
        r = [f'<url><loc>{u}</loc>']
        if alt_en: r += [f'<xhtml:link rel="alternate" hreflang="ru" href="{alt_ru}"/>', f'<xhtml:link rel="alternate" hreflang="en" href="{alt_en}"/>']
        return ''.join(r) + '</url>'
    for ru_u, en_u in urls:
        L.append(ent(ru_u, ru_u, en_u))
        if en_u: L.append(ent(en_u, ru_u, en_u))
    L.append('</urlset>')
    (ROOT / 'sitemap.xml').write_text('\n'.join(L) + '\n', encoding='utf8')
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n', encoding='utf8')

if '--no-og' not in sys.argv:
    try:
        import og
        og.render(data_ru, ROOT / 'og')
        if HAS_EN:
            U = {'kind': {k: T_EN['kind.' + k] for k in ('promise', 'forecast', 'denial', 'irony')}, 'logo': T_EN['page.title.default'], 'more': T_EN['og.tag_more'],
                 'sub': T_EN['og.default_sub'], 'role': T_EN['og.default_role'], 'open': T_EN['og.default_open']}
            og.render(data_en, en_dir / 'og', U)
    except Exception as e:
        print('Картинки превью не собраны:', e)
