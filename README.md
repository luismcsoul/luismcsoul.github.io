# luismcsoul.github.io
Luis Alberto Mejia Clavijo develops a unified vision of cognitive aesthetics of systems through poetry, music, image‑text art, audiovisual essays, and theory. Each discipline functions as a Cartesian axis of a single inquiry into perception, responsibility, ecology, and the future of human systems.

# URL & page map (stable, indexable)

/                              → Landing (bio + radial fan)
/about/                        → Extended bio
/projects/the-sustainable-republic/        → Project context (North #1)
/philosophy/pantheism/                     → Meta-philosophy (North #2)

/poetry/                                   → Category hub
/poetry/neo-haiku-of-dawn/                 → Work page
/songs/                                    → Category hub
/sculpture/                                → Category hub
/image-text/                               → Category hub
/theory/                                   → Category hub

/references/                               → Global reference index
/references/[id-or-slug]/                  → Single reference (optional canonical)
/search/                                   → Local search (optional)


# Jekyll structure (collections‑first, GitHub Pages–friendly)


.
├─ _config.yml
├─ _layouts/
│  ├─ base.html
│  ├─ home.html            # landing + radial fan
│  ├─ category.html        # hub listing (Poems, Songs, etc.)
│  ├─ work.html            # a single poem/song/sculpture/image-text item
│  ├─ context.html         # Sustainable Republic / Philosophy
│  └─ reference.html       # individual reference display
├─ _includes/
│  ├─ head-meta.html       # SEO, OpenGraph, JSON-LD blocks
│  ├─ nav-compass.html     # up/down/left/right control
│  ├─ radial-fan.html      # home fan markup
│  └─ breadcrumbs.html
├─ assets/
│  ├─ css/ (site.css)
│  ├─ js/  (compass.js, radial.js, keyboard.js)
│  └─ img/
├─ _data/
│  ├─ contexts.yml         # ids, titles, abstracts for north pages
│  ├─ categories.yml       # labels/colors/icons for radial fan
│  └─ references.yml       # central bibliography/media notes
├─ poetry/                 # collection content (Markdown)
├─ songs/
├─ sculpture/
├─ image-text/
├─ theory/
├─ references/
├─ projects/
│  └─ the-sustainable-republic.md
├─ philosophy/
│  └─ pantheism.md
├─ index.md                # uses layout: home
└─ about.md
``

# _config.yml (core collections & permalinks)

title: "Luis Alberto Mejia Clavijo — Cognitive Aesthetics of Systems"
url: "https://luismcsoul.github.io"
permalink: /:collection/:title/

# Enable sitemap & feed (both safe on GitHub Pages)
plugins:
  - jekyll-sitemap
  - jekyll-feed

collections:
  poetry:
    output: true
    permalink: /poetry/:slug/
  songs:
    output: true
    permalink: /songs/:slug/
  sculpture:
    output: true
    permalink: /sculpture/:slug/
  image-text:
    output: true
    permalink: /image-text/:slug/
  theory:
    output: true
    permalink: /theory/:slug/
  references:
    output: true
    permalink: /references/:slug/

defaults:
  - scope: {path: "", type: poetry}
    values: {layout: work, category_key: "poetry"}
  - scope: {path: "", type: songs}
    values: {layout: work, category_key: "songs"}
  - scope: {path: "", type: sculpture}
    values: {layout: work, category_key: "sculpture"}
  - scope: {path: "", type: image-text}
    values: {layout: work, category_key: "image-text"}
  - scope: {path: "", type: theory}
    values: {layout: work, category_key: "theory"}
  - scope: {path: "", type: references}
    values: {layout: reference}

# Simple navigation ordering inside categories
# you can override per item with 'order' in front matter

# Front matter models (consistent metadata)


---
title: "Neo‑Haiku of Dawn"
date: 2026-01-20
excerpt: "A brief threshold between cognition and light."
order: 12                   # controls left/right within category
media:
  hero: /assets/img/poetry/neo-haiku-dawn.jpg
  alt: "Minimal image evoking light gradients at daybreak"
context:
  project: the-sustainable-republic  # up (North #1)
  philosophy: pantheism              # up (North #2)
references:
  - ref: merleau-ponty-phenomenology
  - ref: gregory-bateson-steps
  - ref: zen-kokinshu
keywords: [neo-haiku, perception, ecology]
schema_type: "Poem"
---
*(Poem body in Markdown)*


# Reference item — references/merleau-ponty-phenomenology.md:


---
title: "Maurice Merleau‑Ponty — Phenomenology of Perception"
author: "Maurice Merleau-Ponty"
year: 1945
type: book
publisher: "Gallimard"
url: "https://..."     # if applicable
tags: [phenomenology, perception, body]
---
Short note on how this text informs the piece.


# The “compass” (up/down/left/right) logic in Liquid
(_includes/nav-compass.html)


<nav class="compass" aria-label="Work navigation">
  {% assign coll = site[page.collection] %}
  {% assign sorted = coll | sort: "order" %}
  {% assign index = sorted | index_of: page %}

  <!-- Left / Right within category -->
  {% assign prev = sorted | where_exp:"i","i.order < page.order" | last %}
  {% assign next = sorted | where_exp:"i","i.order > page.order" | first %}

  <a class="nav-left"  {% if prev %} href="{{ prev.url | relative_url }}"{% else %} aria-disabled="true"{% endif %} title="Previous"></a>
  <a class="nav-right" {% if next %} href="{{ next.url | relative_url }}"{% else %} aria-disabled="true"{% endif %} title="Next"></a>

  <!-- Up: project then philosophy -->
  {% if page.context.project %}
    <a class="nav-up" href="/projects/{{ page.context.project }}/" title="Context: Project"></a>
  {% elsif page.context.philosophy %}
    <a class="nav-up" href="/philosophy/{{ page.context.philosophy }}/" title="Context: Philosophy"></a>
  {% else %}
    <a class="nav-up" href="/about/" title="About"></a>
  {% endif %}

  <!-- Down: references -->
  {% if page.references and page.references.size > 0 %}
    <a class="nav-down" href="#references" title="References"></a>
  {% else %}
    <a class="nav-down" href="/references/" title="Reference Index"></a>
  {% endif %}
</nav>
``

# Keyboard JS (optional enhancement) — assets/js/keyboard.js


document.addEventListener('keydown', (e) => {
  const go = (sel) => {
    const a = document.querySelector(sel);
    if (a && a.getAttribute('href')) window.location = a.getAttribute('href');
  };
  switch (e.key) {
    case 'ArrowLeft':  go('.nav-left');  break;
    case 'ArrowRight': go('.nav-right'); break;
    case 'ArrowUp':    go('.nav-up');    break;
    case 'ArrowDown':  go('.nav-down');  break;
    case 'Escape':     window.location = '/'; break;
  }
});



# Radial fan for categories (CSS‑only first, JS optional)
(Include — _includes/radial-fan.html)


<section class="radial" aria-label="Categories">
  {% assign cats = site.data.categories %}
  <ul class="fan">
    {% for c in cats %}
      <li style="--i:{{ forloop.index0 }}; --n:{{ cats.size }}; --color:{{ c.color }}">
        <a href="{{ c.href }}" aria-label="{{ c.label }}">
          <span class="icon">{{ c.icon }}</span>
          <span class="label">{{ c.label }}</span>
        </a>
      </li>
    {% endfor %}
  </ul>
</section>


# Data — _data/categories.yml


- key: poetry
  label: Poems
  href: /poetry/
  color: "#E85D75"
  icon: "✶"
- key: songs
  label: Songs
  href: /songs/
  color: "#5D9BE8"
  icon: "♪"
- key: image-text
  label: Image‑Text
  href: /image-text/
  color: "#F0A202"
  icon: "▣"
- key: sculpture
  label: Sculpture
  href: /sculpture/
  color: "#7EB26D"
  icon: "▦"
- key: theory
  label: Contemporary Art Theory
  href: /theory/
  color: "#8A7DBE"
  icon: "∴"
``


# CSS (excerpt) — assets/css/site.css


.radial .fan {
  --radius: 10rem;
  list-style: none; margin: 4rem auto; padding: 0;
  position: relative; width: 0; height: 0;
}
.radial .fan > li {
  position: absolute; left: 0; top: 0;
  transform:
    rotate(calc(360deg * var(--i) / var(--n)))
    translate(var(--radius))
    rotate(calc(-360deg * var(--i) / var(--n)));
}
.radial .fan > li a {
  display: grid; place-items: center;
  width: 8rem; height: 8rem; border-radius: 50%;
  background: var(--color); color: #fff; text-decoration: none;
  box-shadow: 0 0.5rem 1rem rgba(0,0,0,.15);
}
.radial .fan .label { font-size: .85rem; margin-top: .25rem }
@media (max-width: 700px) {
  .radial .fan { --radius: 7rem; }
  .radial .fan > li a { width: 6rem; height: 6rem; }
}


# Work page layout scaffold (context up, references down)
_layouts/work.html (excerpt)


---
layout: base
---
<article class="work" itemscope itemtype="https://schema.org/{{ page.schema_type | default: 'CreativeWork' }}">
  <header>
    <h1 itemprop="name">{{ page.title }}</h1>
    {% if page.excerpt %}<p class="lede" itemprop="abstract">{{ page.excerpt }}</p>{% endif %}
  </header>

  {% include nav-compass.html %}

  {% if page.media.hero %}
    <figure class="hero">
      <img src="{{ page.media.hero | relative_url }}" alt="{{ page.media.alt | default: page.title }}">
    </figure>
  {% endif %}

  <div class="content" itemprop="text">
    {{ content }}
  </div>

  <section id="references" aria-label="References">
    <h2>References</h2>
    <ul>
      {% for r in page.references %}
        {% assign ref = site.references | where: "slug", r.ref | first %}
        <li>
          {% if ref %}<a href="{{ ref.url | default: ref.url | relative_url }}">{{ ref.title }}</a>
          {% else %}{{ r.ref }}{% endif %}
        </li>
      {% endfor %}
    </ul>
  </section>
</article>

