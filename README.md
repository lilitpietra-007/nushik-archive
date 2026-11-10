# Nushik Malkhasyan — needlework archive

A bilingual (Armenian / English) archive of the hand needlework of Nushik
Malkhasyan of Dilijan, Armenia — twenty-seven pieces so far, in four
collections, with a page about her life. More are still to be photographed.

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
python3 optimize_images.py   # only after adding or replacing an image
python3 build_static.py      # writes ../dist
python3 check_site.py        # the pre-flight checks, see below
```

Needs Python with Pillow — and Pillow with AVIF support, which not every
install has. On this machine `/usr/bin/python3` has it and a bare `python3` may
not; if `optimize_images.py` cannot write an AVIF, that is why.

`build_static.py` reads the page bodies (`_home_body.html`, `body2.html`,
`template_alpha.html`, `template_wear.html`, `_small_body.html`,
`_life_body.html`), inlines the stylesheets, points every image at a real file,
and writes the six pages, a 404 page, `robots.txt`, `sitemap.xml`, `_headers`,
the icons and the share card.

`optimize_images.py` is the image pipeline and only needs running when an image
changes. For each WebP it encodes an AVIF and keeps it only where it saves at
least ten per cent — on some of the cutouts it does not, because their weight
is mostly alpha channel and AVIF has no advantage there. It also writes the two
kinds of derived copy the pages ask for: a phone-sized `_sm` copy of each
painted backdrop, sized on the shorter side because `cover` on a tall phone
scales a landscape painting by its height; and a `_card` copy of the four
images the home page shows on its collection cards, which are also gallery
thumbnails on their own pages and so cannot simply be made smaller. Where a
derived copy would not actually be lighter it is not written, and the build
falls back to the original on its own.

The seal in the footer is drawn by `make_seal.py` into `seal.svg`, wrapped as
`seal.html`, and injected into every page's footer by the build. It was once
pasted into the doilies page by hand, which is why it appeared on one page only.

## The address, and search engines

Two settings at the top of `build_static.py` decide both:

`SITE_URL` is the address the site is served from. It is currently
`https://lilitpietra-007.github.io/nushik-archive`. It feeds the canonical
link, `sitemap.xml`, `robots.txt` and the absolute share-image URL, and nothing
else — every link between pages is relative, so the site runs unchanged at a
domain root or in a subdirectory. **Change it the day the domain changes and
rebuild**, or the canonical links will keep pointing at the old address and
search engines will go on treating that as the real one.

`INDEXABLE` is `True`, so pages carry no `noindex` and `robots.txt` allows
everything. It was `False` while the Armenian was an unread draft; the family
has since read the home page, the alphabet page, the About Nushik page and the
wearables prologue. The rest is still a draft (see **Still open**), but it is
hers and it is accurate enough to be found.

## Deploying

The whole site is static, so "deploy" means "copy `dist/` somewhere". It is
154 files and 19 MB, the largest of them 0.4 MB — comfortably inside every
free tier's limits.

### Cloudflare Pages (the intended home)

In the Cloudflare dashboard: **Workers & Pages → Create → Pages → Connect to
Git**, pick this repository, and set

| | |
|---|---|
| Production branch | `main` |
| Framework preset | None |
| Build command | *leave empty* |
| Build output directory | `dist` |
| Root directory | *leave empty* |

Nothing is compiled on the host — the site is committed already built, so
Cloudflare only has to publish the folder. There are no environment variables
and no build image to pin.

Then **Custom domains → Set up a domain**. If the domain is registered at
Cloudflare the DNS is written for you; if it is elsewhere, Cloudflare gives you
the CNAME to add. The certificate is issued automatically either way. Once the
domain answers, change `SITE_URL` (above) and rebuild.

Cloudflare reads `dist/_headers` as configuration, which is the reason to
prefer it: the fonts, stylesheet and script are cached for a year as
`immutable`, the images for a month, and the pages not at all. Every one of
those filenames carries a content hash, so a rebuild invalidates them by
itself and a visitor never has to be told to refresh.

### GitHub Pages (where it is now)

`.github/workflows/deploy.yml` publishes `dist/` on every push to `main` that
touches it. It needs Pages enabled with **Source: GitHub Actions**
(Settings → Pages), and Pages on a private repository needs a paid plan — on a
free account the repository has to be public. Pages ignores directories
beginning with `_`, which is why `dist/.nojekyll` exists — keep it.

Pages ignores `_headers` entirely, and that is its real cost here. Without it
Pages caches each page for ten minutes with no way to purge, which is what
broke the site once: a rebuild renamed the stylesheet and deleted the old one
while browsers were still being served a cached page asking for it, so the
site came back unstyled for ten minutes. `KEEP_ASSETS = 5` in
`build_static.py` is the guard against that — it keeps the last five
stylesheets and scripts instead of deleting them, so a cached page always
finds the file it asks for. **Leave it alone until the move to Cloudflare is
live**; afterwards it is merely harmless, and the five stale files can go.

Keep this workflow running until the Cloudflare domain is answering. There is
no harm in both being live, and it is the easy way to compare them.

## Weight

Measured in Chromium against a local server, cold cache, counting every file
the page actually fetches:

| page | desktop | phone |
|---|---|---|
| home | 0.71 MB | 0.66 MB |
| doilies | 1.90 MB | 1.84 MB |
| alphabet | 0.78 MB | 0.76 MB |
| wearables | 0.90 MB | 0.86 MB |
| small pieces | 1.22 MB | 1.19 MB |
| About Nushik | 0.38 MB | 0.34 MB |

A first visit costs about 190 KB before any photograph: 56 KB of stylesheet,
9 KB of script, and four fonts at 123 KB. All of it is cached for a year, so
the second page a visitor opens costs only its own images — walking the whole
site, all six pages, comes to 4.5 MB.

The doilies page is the heaviest and the only one where scrolling still
fetches: it loads 1.2 MB above the fold and the rest as the visitor goes down.
The high-resolution versions behind the zoom viewer are separate again, and
are fetched only when someone actually opens one.

## Checking before you publish

```sh
cd build
python3 check_site.py
```

It needs Playwright and a Chromium; it finds the browser by searching
`/opt/pw-browsers`, so it does not break when the version changes.

It reads the built pages first — dead links, in-page anchors, duplicate ids,
missing `alt` text, one `h1` per page and no skipped heading levels, the title
and description and share image and favicon and `lang`, a WebP fallback inside
every `<picture>`, and files in `dist/` that nothing references. Then it opens
each of the 7 pages in both languages at 4 widths and checks for console
errors, responses of 400 or worse, images that did not decode, sideways
scrolling, text of the wrong language showing through, and tap targets under
24px. Then it opens all 27 pieces in the zoom viewer at two sizes and checks
each one loads, is not cropped, and has a caption. Then a keyboard pass.
Finally it screenshots each page and measures the real contrast of the text
against the pixels behind it, which is the only way to tell on this site —
every page sets its text over a photograph under a veil.

It has caught, among others: a blank lightbox caption on three pages, two
contrast failures at 4.2:1 and 4.3:1, and language buttons 37×19px on a phone.

## Still open

- The Armenian on the home page, the alphabet page, the About Nushik page and
  the wearables prologue is the family's own. Everything else — the doilies
  and small-pieces prologues, the piece titles, the footer lines — is still a
  draft and wants a native reader.
  `localization/nushik-archive-localization.md` lists every string with an ID
  for marking up corrections.
- More of her work is still to be photographed. When it is added, the counts
  on the home page (the hero line and the four card counts) and the meta
  description of each collection page have to be updated by hand.
