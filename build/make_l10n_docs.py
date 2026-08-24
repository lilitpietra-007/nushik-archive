"""Write the proofreading documents: an editable Markdown file and a web page."""
import io, json, re, html

rows = json.load(open('strings.json', encoding='utf-8'))
CODE = {'Home': 'HOME', 'Lace & Doilies': 'DOILY', 'The Armenian Alphabet': 'ALPHA',
        'Lace to Wear': 'WEAR', 'Crosses & Small Pieces': 'CROSS'}
PAGES = list(CODE)

for r in rows:
    r['placeholder'] = bool(re.search(r'\[.+\]', r['en'] + r['hy']))

n = 0
for r in rows:
    n += 1
    r['id'] = f"{CODE[r['page']]}-{sum(1 for x in rows[:n] if x['page'] == r['page']):02d}"

paired = [r for r in rows if r['en'] and r['hy']]
gaps = [r for r in rows if not (r['en'] and r['hy'])]
todo = [r for r in rows if r['placeholder']]

# ---------------------------------------------------------------- Markdown
m = ['# Nushik Malkhasyan Archive — Armenian / English text',
     '',
     f'{len(rows)} strings across five pages. {len(paired)} exist in both languages; '
     f'{len(gaps)} are deliberately one-language only.',
     '',
     '## How to use this',
     '',
     'Every string has an ID like `CROSS-07`. Write your corrected Armenian on the '
     '`fix:` line underneath — leave it blank where the Armenian is already right. '
     'Add a comment after `note:` if the English needs changing too. Send the file '
     'back however is easiest; the IDs are what I match on, so nothing else has to '
     'stay tidy.',
     '',
     '**Please look especially at:** the grammatical case endings, which are the '
     'likeliest thing to be wrong; whether the register sounds like a museum label '
     'rather than a translation; and the craft vocabulary — I chose Armenian terms '
     'for *doily*, *filet lace*, *picot*, *hook* and *thread count* without knowing '
     'which words are actually used in Dilijan.',
     '']

if todo:
    m += [f'## Still needs your facts ({len(todo)})', '',
          'These carry square-bracket placeholders. They are written into both '
          'languages, so a fact given once needs the Armenian rewritten too.', '']
    for r in todo:
        m += [f"- **{r['id']}** ({r['page']} · {r['section']}) — {r['en'] or r['hy']}"]
    m += ['']

for page in PAGES:
    pr = [r for r in rows if r['page'] == page]
    m += [f'## {page}', '', f'{len(pr)} strings.', '']
    sec = None
    for r in pr:
        if r['section'] != sec:
            sec = r['section']
            m += [f'### {sec}', '']
        m += [f"**{r['id']}** · {r['kind']}" + ('  ⟵ placeholder' if r['placeholder'] else ''),
              '',
              f"- **EN** {r['en'] or '—'}",
              f"- **HY** {r['hy'] or '—'}",
              '- fix: ',
              '- note: ',
              '']

io.open('nushik-archive-localization.md', 'w', encoding='utf-8').write('\n'.join(m))
print('markdown:', len('\n'.join(m).encode()) // 1024, 'KB')

# ---------------------------------------------------------------- web page
e = html.escape
cards = []
for page in PAGES:
    pr = [r for r in rows if r['page'] == page]
    body, sec = [], None
    for r in pr:
        if r['section'] != sec:
            sec = r['section']
            body.append(f'<h3>{e(sec)}</h3>')
        flag = '<span class="ph">needs a fact</span>' if r['placeholder'] else ''
        body.append(
            f'<div class="row{" is-ph" if r["placeholder"] else ""}">'
            f'<div class="meta"><code>{r["id"]}</code><span>{e(r["kind"])}</span>{flag}</div>'
            f'<div class="pair">'
            f'<p class="en">{e(r["en"]) or "<em>—</em>"}</p>'
            f'<p class="hy" lang="hy">{e(r["hy"]) or "<em>—</em>"}</p>'
            f'</div></div>')
    cards.append(f'<section id="{CODE[page]}"><h2>{e(page)}</h2>'
                 f'<p class="count">{len(pr)} strings</p>{"".join(body)}</section>')

nav = ''.join(f'<a href="#{CODE[p]}">{e(p)}</a>' for p in PAGES)
todo_list = ''.join(
    f'<li><code>{r["id"]}</code> {e(r["en"] or r["hy"])}</li>' for r in todo)

page_html = f'''<title>Archive Text for Proofing</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Manrope:wght@400;500;600&family=Noto+Sans+Armenian:wght@400;500;600&family=Noto+Serif+Armenian:wght@600&display=swap">
<style>
  :root{{
    --bg:#fbf8f2; --panel:#ffffff; --line:#e2dbcb; --ink:#231d14; --soft:#6d6353;
    --accent:#8a6a2f; --ph-bg:#f6edd8; --ph-line:#d9c48c;
    --display:'Fraunces',Georgia,serif; --body:'Manrope',system-ui,sans-serif;
    --arm:'Noto Sans Armenian','Noto Serif Armenian',sans-serif;
  }}
  @media (prefers-color-scheme:dark){{
    :root:not([data-theme="light"]){{
      --bg:#16130e; --panel:#1f1a13; --line:#332b1f; --ink:#f2ece0; --soft:#a4998a;
      --accent:#d9bd7a; --ph-bg:#2a2214; --ph-line:#5a4a26;
    }}
  }}
  :root[data-theme="dark"]{{
    --bg:#16130e; --panel:#1f1a13; --line:#332b1f; --ink:#f2ece0; --soft:#a4998a;
    --accent:#d9bd7a; --ph-bg:#2a2214; --ph-line:#5a4a26;
  }}
  *{{box-sizing:border-box;}}
  body{{margin:0; background:var(--bg); color:var(--ink);
       font-family:var(--body); line-height:1.6;}}
  .wrap{{max-width:62rem; margin:0 auto; padding:3rem 1.25rem 5rem;}}
  header h1{{font-family:var(--display); font-weight:600; font-size:clamp(1.8rem,4vw,2.6rem);
             margin:0 0 .4rem; text-wrap:balance;}}
  .lede{{color:var(--soft); max-width:44rem; margin:0 0 1.6rem;}}
  .how{{background:var(--panel); border:1px solid var(--line); border-radius:.5rem;
        padding:1.1rem 1.3rem; margin:0 0 2rem;}}
  .how h2{{font-family:var(--display); font-size:1.05rem; margin:0 0 .5rem;}}
  .how p{{margin:.5rem 0; max-width:46rem;}}
  .how code{{background:var(--ph-bg); padding:.1em .35em; border-radius:.2rem;}}
  nav.jump{{display:flex; flex-wrap:wrap; gap:.5rem; margin:0 0 2.5rem;}}
  nav.jump a{{font-size:.8rem; letter-spacing:.02em; text-decoration:none;
              color:var(--ink); border:1px solid var(--line); border-radius:2rem;
              padding:.35rem .85rem; background:var(--panel);}}
  nav.jump a:hover{{border-color:var(--accent); color:var(--accent);}}
  section{{margin:0 0 3rem;}}
  section h2{{font-family:var(--display); font-size:1.5rem; margin:0 0 .15rem;
              padding-top:1rem; border-top:1px solid var(--line);}}
  .count{{color:var(--soft); font-size:.82rem; margin:0 0 1.4rem;}}
  h3{{font-size:.72rem; text-transform:uppercase; letter-spacing:.16em;
      color:var(--accent); margin:1.8rem 0 .7rem; font-weight:600;}}
  .row{{background:var(--panel); border:1px solid var(--line); border-radius:.45rem;
        padding:.85rem 1rem; margin:0 0 .6rem;}}
  .row.is-ph{{background:var(--ph-bg); border-color:var(--ph-line);}}
  .meta{{display:flex; align-items:center; gap:.6rem; flex-wrap:wrap;
         margin:0 0 .5rem; font-size:.7rem; color:var(--soft);}}
  .meta code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
              font-size:.72rem; color:var(--accent); font-weight:600;}}
  .ph{{border:1px solid var(--ph-line); border-radius:2rem; padding:.05rem .5rem;
       font-size:.65rem; letter-spacing:.04em;}}
  .pair{{display:grid; grid-template-columns:1fr; gap:.35rem;}}
  @media (min-width:720px){{ .pair{{grid-template-columns:1fr 1fr; gap:1.5rem;}} }}
  .pair p{{margin:0;}}
  .en{{font-size:.94rem;}}
  .hy{{font-family:var(--arm); font-size:.94rem;}}
  @media (min-width:720px){{ .hy{{border-left:1px solid var(--line); padding-left:1.5rem;}} }}
  footer{{margin-top:3rem; padding-top:1.5rem; border-top:1px solid var(--line);
          color:var(--soft); font-size:.85rem;}}
  ul{{padding-left:1.1rem;}} li{{margin:.3rem 0;}}
  li code{{color:var(--accent); font-weight:600;
           font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.78rem;}}
</style>
<div class="wrap">
  <header>
    <h1>Archive Text for Proofing</h1>
    <p class="lede">Every word on the Nushik Malkhasyan archive, English beside Armenian.
      {len(rows)} strings across five pages &mdash; {len(paired)} in both languages,
      {len(gaps)} deliberately in one.</p>
  </header>

  <div class="how">
    <h2>How to send corrections back</h2>
    <p>Each string has an ID like <code>CROSS-07</code>. Quote the ID and give me the
      corrected Armenian &mdash; a list, a voice note, marks on a printout, whatever is
      easiest. The IDs are what I match on.</p>
    <p><strong>Worth a hard look:</strong> the case endings, which are the likeliest thing
      to be wrong; whether the register reads like a museum label rather than a
      translation; and the craft vocabulary &mdash; I picked Armenian words for
      <em>doily</em>, <em>filet lace</em>, <em>picot</em>, <em>hook</em> and
      <em>thread count</em> without knowing which ones are actually used in Dilijan.</p>
    <p>The {len(todo)} highlighted rows are not translation problems &mdash; they are
      placeholders waiting on facts only you have. A fact given once needs writing in
      both languages.</p>
  </div>

  <nav class="jump">{nav}</nav>

  <section id="TODO">
    <h2>Still needs your facts</h2>
    <p class="count">{len(todo)} placeholders</p>
    <ul>{todo_list}</ul>
  </section>

  {''.join(cards)}

  <footer>
    <p>Armenian throughout is a first draft written for this archive and has not yet been
      read by a native speaker. Nothing here is final.</p>
  </footer>
</div>'''

io.open('l10n.html', 'w', encoding='utf-8').write(page_html)
print('html:', len(page_html.encode()) // 1024, 'KB |', len(todo), 'placeholders')
