#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import shutil
import yaml
import markdown
import hashlib
from bs4 import BeautifulSoup
from collections import defaultdict
import glob
from dotenv import load_dotenv
import locale
from datetime import datetime

# --- Localisation française ---
try:
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
except locale.Error:
    print("⚠️ Locale fr_FR.UTF-8 non disponible, utilisation du format ISO.")

# Charger les variables d’environnement (.env)
load_dotenv()

# === CONFIGURATION ===
CONTENT_DIR = "content"
OUTPUT_DIR = "site_static"
ASSETS_DIR = "assets"
CSS_URL = "static/style.css"
SITE_TITLE = "4sacs"
CACHE_FILE = ".build_cache.json"
GA_TRACKING_ID = os.getenv("GA_TRACKING_ID", "")
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"

# --- UTILS ---
def slugify(text):
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")

def format_date_fr(date_str):
    """Convertit une date 'YYYY-MM-DD' en '22 juillet 2024'."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%-d %B %Y")  # Linux/macOS
    except ValueError:
        return date_str

def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_markdown_article(path):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        meta = yaml.safe_load(parts[1])
        body_md = parts[2].strip()
    else:
        meta = {}
        body_md = raw
    body_html = markdown.markdown(body_md, extensions=["extra", "smarty", "sane_lists"])
    soup = BeautifulSoup(body_html, "html.parser")
    for img in soup.find_all("img"):
        if not img.get("alt"):
            src = img.get("src", "")
            img["alt"] = os.path.splitext(os.path.basename(src))[0].replace("-", " ")
        img["role"] = "img"
    return meta, str(soup)

def copy_static_assets():
    static_dir = os.path.join(OUTPUT_DIR, "static")
    if os.path.exists(static_dir):
        shutil.rmtree(static_dir)
    shutil.copytree(ASSETS_DIR, static_dir)
    print("Dossier static mis à jour.")

def copy_category_images(category_dir, cat_output_dir):
    src_img_dir = os.path.join(category_dir, "images")
    dst_img_dir = os.path.join(cat_output_dir, "images")
    if os.path.exists(src_img_dir):
        shutil.copytree(src_img_dir, dst_img_dir, dirs_exist_ok=True)

def get_favicon_html():
    favicon_path = "static/4sacs.png"
    return f"""
  <link rel="icon" type="image/png" href="/{favicon_path}">
  <link rel="shortcut icon" type="image/png" href="/{favicon_path}">
"""

def get_head_html():
    return f"""
   <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
   <link rel="stylesheet" href="https://unpkg.com/leaflet.fullscreen@1.6.0/Control.FullScreen.css" />
   <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
   <script src="https://unpkg.com/leaflet.fullscreen@1.6.0/Control.FullScreen.js"></script>
   <script src="../static/4sacs.js" defer></script>
"""

def get_ga_script():
    if not ENABLE_ANALYTICS or not GA_TRACKING_ID or GA_TRACKING_ID.startswith("G-XXXX"):
        return ""
    return f"""
  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_TRACKING_ID}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{GA_TRACKING_ID}');
  </script>"""

# === GÉNÉRATION DES ARTICLES ===
def render_article(meta, content_html, categories_map):
    title = meta.get("title", "Sans titre")
    date = meta.get("date", "")
    author = meta.get("author", "Inconnu")
    categories = meta.get("categories", [])
    tags = meta.get("tags", [])
    lat, lng = meta.get("lat"), meta.get("lng")
    menu_items = meta.get("menu", [])
    main_cat = categories[0] if categories else "Divers"
    formatted_date = format_date_fr(date)

    side_html = ""
    if menu_items or (lat and lng):
        side_html = "<aside class='side' role='complementary'>"
        if menu_items:
            side_html += "<div class='menu-jour'><h3>Menu du jour</h3><ul>" + "".join(
                f"<li>{i}</li>" for i in menu_items
            ) + "</ul></div>"
        if lat and lng:
            side_html += f"<pre class='geo' data-lat='{lat}' data-lng='{lng}'>{lat}, {lng}</pre>"
        side_html += "</aside>"

    nav_html = ""
    posts_in_cat = categories_map.get(main_cat, [])
    if posts_in_cat:
        idx = next((i for i, p in enumerate(posts_in_cat) if p["title"] == title), None)
        if idx is not None:
            prev_link = "<span class='prev-empty'></span>"
            next_link = "<span class='next-empty'></span>"
            if idx > 0:
                prev = posts_in_cat[idx - 1]
                prev_link = f"<a href='{prev['filename']}' class='prev'>← {prev['title']}</a>"
            if idx < len(posts_in_cat) - 1:
                nxt = posts_in_cat[idx + 1]
                next_link = f"<a href='{nxt['filename']}' class='next'>{nxt['title']} →</a>"
            nav_html = f"<nav class='post-nav'>{prev_link}{next_link}</nav>"

    tag_links = " ".join(
        f"<span class='tag'><a href='../tags/{slugify(str(t))}/'>#{t}</a></span>"
        for t in tags if t and isinstance(t, str)
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
 <meta charset="utf-8">
 <title>{title}</title>
 <link rel="stylesheet" href="../{CSS_URL}">
 {get_favicon_html()}
 {get_head_html()}
 {get_ga_script()}
</head>
<body>
 <article data-lat="{lat or ''}" data-lng="{lng or ''}">
   <header class="article-header">
     <div class="meta">
       <span class="cat"><a href="./">{main_cat}</a></span>
       <time datetime="{date}" class="date">{formatted_date}</time>
     </div>
     <h1 id="article-title"><span class="sep">/</span> {title}</h1>
   </header>
   {nav_html}
   <main class="article-layout">
     <div class="content">{content_html}</div>{side_html}
   </main>
   <footer>{tag_links}<p><em>Publié le {formatted_date} par {author}</em></p></footer>
 </article>
</body>
</html>"""

# === GÉNÉRATION COMPLÈTE ===
def main():
    force_full = "--full" in sys.argv
    cache = load_cache() if not force_full else {}
    incremental = not force_full

    print("=== 4sacs – Génération du site statique ===")
    print(f"Mode : {'Incrémental' if incremental else 'Complet'}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    copy_static_assets()

    articles = []
    categories_map = defaultdict(list)
    tags_map = defaultdict(list)
    new_cache = {}

    # --- Lecture Markdown ---
    for cat_dir in sorted(os.listdir(CONTENT_DIR)):
        full_cat_dir = os.path.join(CONTENT_DIR, cat_dir)
        if not os.path.isdir(full_cat_dir):
            continue

        cat_slug = slugify(cat_dir)
        cat_output_dir = os.path.join(OUTPUT_DIR, cat_slug)
        os.makedirs(cat_output_dir, exist_ok=True)
        copy_category_images(full_cat_dir, cat_output_dir)

        for md_file in sorted(glob.glob(os.path.join(full_cat_dir, "*.md"))):
            meta, body_html = load_markdown_article(md_file)
            title = meta.get("title", os.path.basename(md_file))
            date = meta.get("date", "")
            filename = f"{date}-{slugify(title)}.html"
            article = {**meta, "filename": filename, "html": body_html, "category": cat_dir, "source": md_file}
            articles.append(article)
            for cat in meta.get("categories", [cat_dir]):
                categories_map[cat].append(article)
            for tag in meta.get("tags", []):
                if tag:
                    tags_map[tag].append(article)
            h = file_hash(md_file)
            new_cache[md_file] = {"hash": h, "output": os.path.join(cat_output_dir, filename)}

    for c in categories_map:
        categories_map[c].sort(key=lambda x: x.get("date", ""))

    # --- Génération des articles ---
    for cat, items in categories_map.items():
        cat_slug = slugify(cat)
        cat_output_dir = os.path.join(OUTPUT_DIR, cat_slug)
        for art in items:
            md_file = art["source"]
            h = file_hash(md_file)
            unchanged = incremental and md_file in cache and cache[md_file]["hash"] == h
            if not unchanged:
                html = render_article(art, art["html"], categories_map)
                with open(os.path.join(cat_output_dir, art["filename"]), "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"Généré : {art['filename']}")

    # --- Suppression fichiers supprimés ---
    if incremental:
        for old_path, old_data in cache.items():
            if old_path not in new_cache and os.path.exists(old_data["output"]):
                os.remove(old_data["output"])
                print(f"Supprimé : {old_data['output']}")
                
    # --- Pages catégories ---
    for cat, items in categories_map.items():
        cat_slug = slugify(cat)
        cat_output_dir = os.path.join(OUTPUT_DIR, cat_slug)
        if items:
            first_date = format_date_fr(items[0].get("date", ""))
            last_date = format_date_fr(items[-1].get("date", ""))
            date_range = first_date if first_date == last_date else f"{first_date} – {last_date}"
        else:
            date_range = ""
        items_html = "\n".join(
            (
                "<li class='category' "
                f"data-lat='{(it.get('lat') or '')}' "
                f"data-lng='{(it.get('lng') or '')}'>"
                f"<a href='{it['filename']}' "
                f"aria-label='Ouvrir : {it.get('title','')}'>"
                f"{it.get('title','Sans titre')}</a> "
                f"<em>({format_date_fr(it.get('date',''))})</em>"
                "</li>"
            )
            for it in items
        )
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{cat}</title>
  <link rel="stylesheet" href="../{CSS_URL}">
  {get_favicon_html()}
  {get_head_html()}
  {get_ga_script()}
</head>
<body>
  <article>
    <header class="article-header">
      <div class="meta">
        <span class="cat"><a href="../index.html">{SITE_TITLE}</a></span>
        <time class="date">{date_range}</time>
      </div>
      <h1 id="article-title"><span class="sep">/</span> {cat}</h1>
    </header>
    <main><ul>{items_html}</ul></main>
    <footer><p><a href="../index.html">← Retour</a></p></footer>
  </article>
</body>
</html>"""
        with open(os.path.join(cat_output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

    # --- Pages tags ---
    tags_map = {t: v for t, v in tags_map.items() if t and isinstance(t, str) and t.strip()}
    tags_root = os.path.join(OUTPUT_DIR, "tags")
    os.makedirs(tags_root, exist_ok=True)

    for tag, items in sorted(tags_map.items(), key=lambda kv: kv[0].lower()):
        tag_slug = slugify(tag)
        tag_dir = os.path.join(tags_root, tag_slug)
        os.makedirs(tag_dir, exist_ok=True)
        grouped = defaultdict(list)
        for it in items:
            cat = it["categories"][0] if it["categories"] else "Divers"
            grouped[cat].append(it)
        count_items = len(items)
        blocks = []
        for cat, posts in sorted(grouped.items()):
            cat_html = f"<h2><a href='../../{slugify(cat)}/'>{cat}</a></h2><ul>"
            for p in posts:
                cat_html += f"<li><a href='../../{slugify(cat)}/{p['filename']}'>{p['title']}</a></li>"
            cat_html += "</ul>"
            blocks.append(cat_html)
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>#{tag}</title>
  <link rel="stylesheet" href="../../{CSS_URL}">
  {get_favicon_html()}
  {get_head_html()}
  {get_ga_script()}
</head>
<body>
  <article>
    <header class="article-header">
      <div class="meta">
        <span class="cat"><a href="../index.html">Tags</a></span>
        <time class="date">{count_items} article{'s' if count_items > 1 else ''}</time>
      </div>
      <h1 id="article-title"><span class="sep">/</span> #{tag}</h1>
    </header>
    <main>{''.join(blocks)}</main>
    <footer><p><a href="../index.html">← Retour</a></p></footer>
  </article>
</body></html>"""
        with open(os.path.join(tag_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

    total_tags = len(tags_map)
    tags_blocks = "\n".join(
        f"<a href='{slugify(tag)}/' class='tag-cloud'>#{tag}</a><span class='count'>({len(items)})</span>"
        for tag, items in sorted(tags_map.items())
    )
    html_tags = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>Tags</title>
  <link rel="stylesheet" href="../{CSS_URL}">
  {get_favicon_html()}
  {get_head_html()}
  {get_ga_script()}
</head>
<body>
  <article>
    <header class="article-header">
      <div class="meta">
        <span class="cat"><a href="../index.html">{SITE_TITLE}</a></span>
        <time class="date">{total_tags} tags</time>
      </div>
      <h1 id="article-title"><span class="sep">/</span> Tags</h1>
    </header>
    <main><div class="tags-cloud">{tags_blocks}</div></main>
    <footer><p><a href="../index.html">← Retour aux catégories</a></p></footer>
  </article>
</body></html>"""
    with open(os.path.join(tags_root, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_tags)

    # --- Accueil principale ---
    index_items = []
    for c, items in sorted(categories_map.items(), key=lambda kv: kv[1][0].get("date", "")):
        first_date = format_date_fr(items[0].get("date", "")) if items else ""
        last_date = format_date_fr(items[-1].get("date", "")) if len(items) > 1 else first_date
        date_range = first_date if first_date == last_date else f"{first_date} – {last_date}"
        index_items.append(f"<li><a href='{slugify(c)}/'>{c}</a> <em>{date_range} ({len(items)} articles)</em></li>")

    html_index = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{SITE_TITLE}</title>
  <link rel="stylesheet" href="{CSS_URL}">
  {get_favicon_html()}
  {get_ga_script()}
</head>
<body class="home">
  <article>
    <header class="article-header">
      <div class="meta">
        <span class="cat">{SITE_TITLE}</span>
        <time class="date">Carnets de route et notes de voyage</time>
      </div>
      <h1 id="article-title"><span class="sep">/</span> Accueil</h1>
    </header>
    <main><ul class="category-list">{''.join(index_items)}</ul></main>
    <footer class="home-footer"><p><a href="tags/">Voir les tags →</a></p></footer>
  </article>
</body>
</html>"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_index)

    save_cache(new_cache)
    print("Cache mis à jour.")
    print("Génération terminée.")

if __name__ == "__main__":
    main()