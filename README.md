# Nushik Malkhasyan — needlework archive

A bilingual (Armenian / English) archive of twenty-seven pieces of hand
needlework by Nushik Malkhasyan of Dilijan, Armenia.

`dist/` is the finished website — plain HTML, CSS, images and one small script.
No build step, no framework, no server code. Any static host will serve it.

## Layout

| | |
|---|---|
| `dist/` | the website, ready to upload |
| `build/` | page sources, stylesheets, fonts, cut-out images, and the scripts that assemble `dist/` |
| `photos/` | the original photographs the cut-outs were made from |
| `localization/` | every string on the site, English beside Armenian |

## Rebuilding

```sh
cd build
python3 build_static.py      # writes ../dist
```

Needs Python with Pillow. `build_static.py` reads the page bodies
(`_home_body.html`, `body2.html`, `template_alpha.html`, `template_wear.html`,
`_small_body.html`), inlines the stylesheets, points every image at a real file,
and writes the five pages, a 404 page, `robots.txt`, the icons and the share card.

The seal in the footer is drawn by `make_seal.py` into `seal.svg`, wrapped as
`seal.html`, and injected into every page's footer by the build. It was once
pasted into the doilies page by hand, which is why it appeared on one page only.

**When you have a domain**, put it in `SITE_URL` at the top of `build_static.py`
and rebuild. That adds the canonical link, the sitemap, and absolute share-image
URLs. It ships empty on purpose: the site works fully without it, and a canonical
link pointing at a domain you do not own is worse than none at all.

## Search engines are turned off

`INDEXABLE` at the top of `build_static.py` is `False`, which puts
`noindex, nofollow` on every page and `Disallow: /` in `robots.txt`. That is
deliberate: the Armenian is an unreviewed draft and twenty-one strings still
show `[square-bracket]` placeholders, and none of that should be findable under
her name. A live site is fine to share by link in that state; being indexed is
not. Flip it to `True` and rebuild once the text is final.

## Deploying

The whole site is static, so "deploy" means "copy `dist/` somewhere".

**Cloudflare Pages / Netlify** — create a project, drag the `dist` folder onto
the upload area. You get an HTTPS address immediately; add a custom domain in
the project settings.

**GitHub Pages** — `.github/workflows/deploy.yml` publishes `dist/`
on every push to `main` that touches it. It needs Pages enabled with **Source:
GitHub Actions** (Settings → Pages), and Pages on a private repository needs a
paid plan — on a free account the repository has to be public. Pages ignores directories beginning with `_`, which
is why `dist/.nojekyll` exists — keep it. Note that Pages ignores `_headers`, so
you lose the caching rules but nothing else.

`dist/_headers` tells Cloudflare Pages and Netlify to cache the fonts and the
stylesheet forever (both carry content hashes in their names, so a rebuild
invalidates them by itself) and never to cache the pages.

Whichever host: point the domain's DNS at it, and let the host issue the
certificate. Nothing here needs a server, a database, or a build pipeline.

## Weight

A first visit to the home page is about 640 KB — HTML, stylesheet, script,
fonts, the painting used as the ground, and the one image above the fold.
Everything else loads as the visitor scrolls, and the browser caches the fonts
and the painting for every later page.

The heaviest page is the doilies at roughly 1.7 MB of photographs, and the
high-resolution versions behind the zoom viewer are only fetched when someone
actually opens one.

## Still open

- The Armenian is a first draft and has not been read by a native speaker.
  `localization/nushik-archive-localization.md` lists every string with an ID
  for marking up corrections.
- Twenty-one strings carry `[square bracket]` placeholders waiting on facts:
  her birth year, who taught her, who wore the collars, and the measurements
  for fifteen pieces.
