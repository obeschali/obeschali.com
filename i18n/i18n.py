#!/usr/bin/env python3
"""Локализация «Обещали.»: выгрузка текстов для перевода, проверка и приём готовых английских версий.

  python3 i18n/i18n.py export [--all] [--size 10]   выгрузить в i18n/handoff/ то, что ещё не переведено или изменилось
  python3 i18n/i18n.py import ФАЙЛ.json [...]        принять готовый перевод (истории, ui или editorial)
  python3 i18n/i18n.py status                       что переведено, что устарело, что ждёт проверки
  python3 i18n/i18n.py approve ID [ID ...]          пометить переводы историй как проверенные (reviewed)

Русские тексты никогда не меняются. Принятые переводы лежат в i18n/en/. Если русский оригинал изменился,
у перевода меняется статус на stale, сам перевод не удаляется и не перезаписывается."""
import json, re, sys, hashlib, datetime, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
I18N = ROOT / 'i18n'
EN = I18N / 'en'
STORIES = json.load(open(ROOT / 'stories.json', encoding='utf8'))
BY = {s['id']: s for s in STORIES}
T_FIELDS = ['who', 'role', 'quote', 'head', 'body', 'meta_context']  # + qsrc[].t, osrc[].t
STATUSES = ['draft', 'reviewed', 'approved']
today = lambda: datetime.date.today().isoformat()

def sha(obj):
    return hashlib.sha1(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode('utf8')).hexdigest()[:12]

def doctype_of(place):
    """Тип материала по русскому полю place. Ключ метки в ui + номер + остаток контекста. Совпадает с логикой сайта."""
    p = (place or '').strip(); m = None
    def num(g): return re.sub(r'№\s*', '', g).strip() if g else None
    if (m := re.match(r'^указ\s*(№\s*\S+)?\s*(.*)$', p, re.I)): return 'decree', num(m.group(1)), m.group(2)
    if (m := re.match(r'^распоряжение правительства\s*(№\s*\S+)?\s*(.*)$', p, re.I)): return 'government_order', num(m.group(1)), m.group(2)
    if (m := re.match(r'^(.*?),?\s*предвыборная программа$', p, re.I)): return 'election_program', None, m.group(1)
    if (m := re.match(r'^программное заявление\s*(.*)$', p, re.I)): return 'program_statement', None, m.group(1)
    if (m := re.match(r'^послание\s*(.*)$', p, re.I)): return 'address', None, m.group(1)
    if (m := re.match(r'^официальное заявление\s*(.*)$', p, re.I)): return 'official_statement', None, m.group(1)
    if (m := re.match(r'^поручение\s*(.*)$', p, re.I)): return 'instruction', None, m.group(1)
    if (m := re.match(r'^(законопроект|законодательная инициатива)\s*(.*)$', p, re.I)): return 'legislative_initiative', None, m.group(2)
    return 'quote', None, p

def ru_fields(s):
    """Русские тексты истории, которые подлежат переводу (то, от чего считается хеш)."""
    dt, number, ctx = doctype_of(s.get('place', ''))
    return {'who': s['who'], 'role': s['role'], 'quote': s['quote'], 'head': s['head'], 'body': s['body'],
            'meta_context': ctx, 'qsrc': [x['t'] for x in s['qsrc']], 'osrc': [x['t'] for x in s['osrc']]}

def story_hash(s): return sha(ru_fields(s))

def empty_en(s):
    return {'who': '', 'role': '', 'quote': '', 'head': '', 'body': '', 'meta_context': '',
            'qsrc': [{'i': i, 't': ''} for i in range(len(s['qsrc']))],
            'osrc': [{'i': i, 't': ''} for i in range(len(s['osrc']))]}

def load_en(sid):
    f = EN / 'stories' / f'{sid}.json'
    return json.load(open(f, encoding='utf8')) if f.exists() else None

def state(s):
    e = load_en(s['id'])
    if not e: return 'new', None
    return ('current' if e['source_hash'] == story_hash(s) else 'stale'), e

def story_item(s, reason, prev=None):
    dt, number, ctx = doctype_of(s.get('place', ''))
    it = {'id': s['id'], 'reason': reason, 'source_hash': story_hash(s),
          'ru': {k: s[k] for k in ['id', 'cat', 'kind', 'w', 'who', 'role', 'date', 'place', 'quote', 'qsrc', 'head', 'body', 'odate', 'osrc']},
          'ru_derived': {'doctype': dt, 'doctype_number': number, 'meta_context': ctx,
                         'note': 'Тип материала и номер код определяет сам по полю place. Переводить нужно только meta_context.'},
          'en': empty_en(s),
          'en_extra_sources': {'quote': [], 'outcome': [], 'note': 'Необязательно. Англоязычные источники: {"t": "название", "u": "https://…"}. Не выдумывайте ссылки: только те, что вы реально проверили.'},
          'notes': ''}
    if prev: it['previous_en'] = {'en': prev['en'], 'was_for_source_hash': prev['source_hash'], 'status': prev.get('status')}
    return it

def cmd_export(a):
    out = I18N / 'handoff'; out.mkdir(exist_ok=True)
    for f in out.glob('*.json'): f.unlink()
    items = []
    for s in STORIES:
        st, e = state(s)
        if st == 'new' or a.all: items.append(story_item(s, 'new' if st == 'new' else ('changed' if st == 'stale' else 'all'), e if st != 'new' else None))
        elif st == 'stale': items.append(story_item(s, 'changed', e))
    n = 0
    for i in range(0, len(items), a.size):
        n += 1; chunk = items[i:i + a.size]
        json.dump({'format': 'obeschali-stories/1', 'batch': n, 'count': len(chunk), 'stories': chunk}, open(out / f'stories-batch-{n:02d}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    for name in ('ui', 'editorial'):
        src = json.load(open(I18N / 'source' / f'{name}.ru.json', encoding='utf8'))
        en = json.load(open(EN / f'{name}.json', encoding='utf8')) if (EN / f'{name}.json').exists() else {'strings': {}}
        pend = {}
        for k, v in src['strings'].items():
            h = sha(v['ru']); cur = en['strings'].get(k)
            if a.all or not cur or cur.get('source_hash') != h:
                pend[k] = {'source_hash': h, 'ru': v['ru'], 'note': v.get('note', ''), 'en': '', **({'previous_en': cur['en']} if cur else {})}
        doc = {'format': f'obeschali-{name}/1', 'readme': src['_readme'], 'strings': pend}
        if name == 'ui':
            doc['new_strings'] = {k: {'source_hash': sha(v['intent']), 'intent': v['intent'], 'en': ''} for k, v in src['new_strings_for_en_architecture'].items() if k != '_readme'
                                  if a.all or not en.get('new_strings', {}).get(k) or en['new_strings'][k].get('source_hash') != sha(v['intent'])}
            doc['new_strings_readme'] = src['new_strings_for_en_architecture']['_readme']
        if name == 'editorial': doc['methodology'] = src['methodology']
        if pend or doc.get('new_strings') or a.all: json.dump(doc, open(out / f'{name}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    import shutil, collections
    shutil.copy(I18N / 'source' / 'INSTRUCTIONS.md', out / 'INSTRUCTIONS.md')
    cnt = lambda it: {k: {'count': v, 'en': ''} for k, v in sorted(collections.Counter(it).items())}
    gl = EN / 'glossary.json'
    json.dump({'format': 'obeschali-glossary/1', 'readme': 'Справочник повторяющихся значений для единообразия. Заполните en один раз и держитесь этих форм во всех историях. Вспомогательный файл: при импорте не читается.',
               'who': cnt(s['who'] for s in STORIES), 'role': cnt(s['role'] for s in STORIES), 'source_titles': cnt(x['t'] for s in STORIES for x in s['qsrc'] + s['osrc'])},
              open(out / 'glossary.json', 'w', encoding='utf8'), ensure_ascii=False, indent=2)
    print(f'выгружено историй: {len(items)} в {n} файлах; файлы в {out}')

def err(m): print('  ОШИБКА:', m); return 1

def cmd_import(a):
    bad = 0
    for path in a.files:
        d = json.load(open(path, encoding='utf8')); fmt = d.get('format', '')
        print(path, fmt)
        if fmt.startswith('obeschali-stories/'):
            for it in d['stories']:
                sid = it.get('id'); s = BY.get(sid)
                if not s: bad += err(f'{sid}: такой истории нет'); continue
                if it.get('source_hash') != story_hash(s): bad += err(f'{sid}: русский оригинал изменился после выгрузки (source_hash не совпадает). Выгрузите заново'); continue
                en = it.get('en') or {}; probs = []
                for k in T_FIELDS:
                    if not isinstance(en.get(k), str) or (not en[k].strip() and not (k == 'meta_context' and not ru_fields(s)['meta_context'])): probs.append(f'пусто поле {k}')
                for k, ref in (('qsrc', s['qsrc']), ('osrc', s['osrc'])):
                    L = en.get(k) or []
                    if len(L) != len(ref) or [x.get('i') for x in L] != list(range(len(ref))): probs.append(f'{k}: должно быть {len(ref)} элементов с i=0..{len(ref)-1}')
                    else:
                        for x in L:
                            if not str(x.get('t', '')).strip(): probs.append(f'{k}[{x["i"]}].t пусто')
                for k in ('quote', 'head', 'body', 'who', 'role'):
                    if re.search('[А-Яа-яЁё]', en.get(k) or ''): probs.append(f'в поле {k} остались кириллические буквы')
                ex = it.get('en_extra_sources') or {}
                for k in ('quote', 'outcome'):
                    for x in ex.get(k) or []:
                        if not str(x.get('u', '')).startswith('https://') or not x.get('t'): probs.append(f'en_extra_sources.{k}: нужны t и https-ссылка u')
                if probs: bad += err(f'{sid}: ' + '; '.join(probs)); continue
                old = load_en(sid)
                if old and old.get('status') in ('reviewed', 'approved') and old['source_hash'] == it['source_hash'] and not a.force:
                    print(f'  пропущено {sid}: уже {old["status"]} для этого оригинала (используйте --force)'); continue
                rec = {'id': sid, 'lang': 'en', 'source_hash': it['source_hash'], 'status': 'draft',
                       'provenance': {'translator': a.translator, 'imported_at': today(), 'file': pathlib.Path(path).name, 'reason': it.get('reason', '')},
                       'en': {k: en[k] for k in T_FIELDS} | {'qsrc': [{'i': x['i'], 't': x['t']} for x in en['qsrc']], 'osrc': [{'i': x['i'], 't': x['t']} for x in en['osrc']]},
                       'en_extra_sources': {'quote': [{'t': x['t'], 'u': x['u'], 'lang': 'en'} for x in ex.get('quote') or []], 'outcome': [{'t': x['t'], 'u': x['u'], 'lang': 'en'} for x in ex.get('outcome') or []]},
                       'notes': it.get('notes', '')}
                (EN / 'stories').mkdir(parents=True, exist_ok=True)
                json.dump(rec, open(EN / 'stories' / f'{sid}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=2)
                print(f'  принято {sid} (draft)')
        elif fmt.startswith(('obeschali-ui/', 'obeschali-editorial/')):
            name = 'ui' if 'ui' in fmt else 'editorial'
            src = json.load(open(I18N / 'source' / f'{name}.ru.json', encoding='utf8'))
            f = EN / f'{name}.json'; cur = json.load(open(f, encoding='utf8')) if f.exists() else {'format': f'obeschali-{name}-en/1', 'strings': {}, 'new_strings': {}}
            for k, v in d.get('strings', {}).items():
                if k not in src['strings']: bad += err(f'{k}: нет такого ключа'); continue
                if v.get('source_hash') != sha(src['strings'][k]['ru']): bad += err(f'{k}: русский оригинал изменился'); continue
                if not isinstance(v.get('en'), (str, dict)) or (not v['en'] and not k.endswith('.few')): bad += err(f'{k}: пустой перевод'); continue
                cur['strings'][k] = {'source_hash': v['source_hash'], 'en': v['en'], 'status': 'draft', 'imported_at': today(), 'translator': a.translator}
            for k, v in d.get('new_strings', {}).items():
                if k not in src.get('new_strings_for_en_architecture', {}) or k == '_readme': bad += err(f'{k}: нет такого ключа'); continue
                if not v.get('en'): bad += err(f'{k}: пустой перевод'); continue
                cur.setdefault('new_strings', {})[k] = {'source_hash': v['source_hash'], 'en': v['en'], 'status': 'draft', 'imported_at': today(), 'translator': a.translator}
            json.dump(cur, open(f, 'w', encoding='utf8'), ensure_ascii=False, indent=2); print(f'  обновлён {f.name}')
        else: bad += err('неизвестный формат файла')
    sys.exit(1 if bad else 0)

def cmd_status(a):
    c = {'new': 0, 'current': 0, 'stale': 0}; st = {}
    for s in STORIES:
        k, e = state(s); c[k] += 1
        if e and k == 'current': st[e.get('status', 'draft')] = st.get(e.get('status', 'draft'), 0) + 1
    print(f'историй: {len(STORIES)}; без перевода: {c["new"]}; перевод актуален: {c["current"]} {st}; русский изменился после перевода: {c["stale"]}')
    for name in ('ui', 'editorial'):
        src = json.load(open(I18N / 'source' / f'{name}.ru.json', encoding='utf8'))['strings']
        f = EN / f'{name}.json'; cur = json.load(open(f, encoding='utf8'))['strings'] if f.exists() else {}
        ok = sum(1 for k, v in src.items() if k in cur and cur[k]['source_hash'] == sha(v['ru']))
        print(f'{name}: {ok} из {len(src)} актуально')

def cmd_approve(a):
    for sid in a.ids:
        e = load_en(sid)
        if not e: print(sid, 'нет перевода'); continue
        e['status'] = a.status; e.setdefault('provenance', {})['reviewed_at'] = today()
        json.dump(e, open(EN / 'stories' / f'{sid}.json', 'w', encoding='utf8'), ensure_ascii=False, indent=2); print(sid, '→', a.status)

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('export'); p.add_argument('--all', action='store_true'); p.add_argument('--size', type=int, default=10); p.set_defaults(f=cmd_export)
    p = sub.add_parser('import'); p.add_argument('files', nargs='+'); p.add_argument('--translator', default='ChatGPT'); p.add_argument('--force', action='store_true'); p.set_defaults(f=cmd_import)
    p = sub.add_parser('status'); p.set_defaults(f=cmd_status)
    p = sub.add_parser('approve'); p.add_argument('ids', nargs='+'); p.add_argument('--status', default='reviewed', choices=STATUSES[1:]); p.set_defaults(f=cmd_approve)
    a = ap.parse_args(); a.f(a)

if __name__ == '__main__': main()
