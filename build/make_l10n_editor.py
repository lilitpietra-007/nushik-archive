"""Inject the string table into the editor template."""
import io, json, re

rows = json.load(open('strings.json', encoding='utf-8'))
CODE = {'Home': 'HOME', 'Lace & Doilies': 'DOILY', 'The Armenian Alphabet': 'ALPHA',
        'Lace to Wear': 'WEAR', 'Crosses & Small Pieces': 'CROSS'}

seen = {}
out = []
for r in rows:
    seen[r['page']] = seen.get(r['page'], 0) + 1
    out.append({
        'id': f"{CODE[r['page']]}-{seen[r['page']]:02d}",
        'page': r['page'], 'section': r['section'], 'kind': r['kind'],
        'en': r['en'], 'hy': r['hy'],
        'fix': r['hy'],          # the box starts holding my draft, ready to edit
        'note': '',
        'placeholder': bool(re.search(r'\[.+\]', r['en'] + r['hy'])),
    })

# `<` inside a JSON island would end the script element early
blob = json.dumps(out, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
tpl = io.open('l10n_edit_template.html', encoding='utf-8').read()
assert '__STATE_JSON__' in tpl
io.open('l10n_edit.html', 'w', encoding='utf-8').write(tpl.replace('__STATE_JSON__', blob))

print(f"{len(out)} rows | {sum(1 for r in out if r['placeholder'])} placeholders "
      f"| {len(io.open('l10n_edit.html', encoding='utf-8').read().encode()) // 1024} KB")
