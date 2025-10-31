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

# === CONFIGURATION ===
CONTENT_DIR = "content"
OUTPUT_DIR = "site_static"
ASSETS_DIR = "assets"
CSS_URL = "static/style.css"
SITE_TITLE = "4sacs"
CACHE_FILE = ".build_cache.json"


# --- UTILS ---
def slugify(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")

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

    # Ajouter alt et role="img"
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

def render_article(meta, content_html, categories_map):
    title = meta.get("title", "Sans titre")
    date = meta.get("date", "")
    author = meta.get("author", "Inconnu")
    categories = meta.get("categories", [])
    tags = meta.get("tags", [])
    lat, lng = meta.get("lat"), meta.get("lng")
    menu_items = meta.get("menu", [])

    main_cat = categories[0] if categories else "Divers"

    side_html = ""
    if menu_items or (lat and lng):
        side_html = "<aside class='side' role='complementary' aria-label='Informations supplémentaires'>"
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
            prev_link = ""
            next_link = ""
            if idx > 0:
                prev = posts_in_cat[idx - 1]
                prev_link = f"<a href='{prev['filename']}' class='prev' aria-label='Article précédent : {prev['title']}'>← {prev['title']}</a>"
            if idx < len(posts_in_cat) - 1:
                nxt = posts_in_cat[idx + 1]
                next_link = f"<a href='{nxt['filename']}' class='next' aria-label='Article suivant : {nxt['title']}'>{nxt['title']} →</a>"
            nav_html = f"<nav class='post-nav'>{prev_link} {next_link}</nav>"

    tag_links = " ".join(
        f"<span class='tag'><a href='../tags/{slugify(t)}/' aria-label='Voir le tag {t}'>#{t}</a></span>"
        for t in tags
    )
    title_html = f"<span class='cat'><a href='./' aria-label='Retour à la catégorie {main_cat}'>{main_cat}</a></span> / {title}"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="../{CSS_URL}">
</head>
<body>
  <article data-lat="{lat or ''}" data-lng="{lng or ''}" aria-labelledby="article-title">
    <header><h1 id="article-title">{title_html}</h1>{nav_html}</header>
    <main class="article-layout"><div class="content">{content_html}</div>{side_html}</main>
    <footer>{tag_links}<p><em>Publié le {date} par {author}</em></p></footer>
  </article>
</body>
</html>"""
    return html


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

    # --- Lecture des fichiers Markdown ---
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
            article = {**meta, "filename": filename, "html": body_html, "category": cat_dir}
            articles.append(article)

            for cat in meta.get("categories", [cat_dir]):
                categories_map[cat].append(article)
            for tag in meta.get("tags", []):
                tags_map[tag].append(article)

            h = file_hash(md_file)
            new_cache[md_file] = {"hash": h, "output": os.path.join(cat_output_dir, filename)}

            # Vérifie si régénération nécessaire
            if incremental and md_file in cache and cache[md_file]["hash"] == h:
                continue

            html = render_article(meta, body_html, categories_map)
            with open(os.path.join(cat_output_dir, filename), "w", encoding="utf-8") as f:
                f.write(html)
            print(f"Généré : {filename}")

    # Suppression des fichiers supprimés
    if incremental:
        for old_path, old_data in cache.items():
            if old_path not in new_cache and os.path.exists(old_data["output"]):
                os.remove(old_data["output"])
                print(f"Supprimé : {old_data['output']}")

    # Tri des articles
    for c in categories_map:
        categories_map[c].sort(key=lambda x: x.get("date", ""))

    # Index de catégories
    for cat, items in categories_map.items():
        cat_slug = slugify(cat)
        cat_output_dir = os.path.join(OUTPUT_DIR, cat_slug)
        items_html = "\n".join(
            f"<li><a href='{it['filename']}'>{it['title']}</a> <em>({it['date']})</em></li>"
            for it in items
        )
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>{cat}</title>
<link rel="stylesheet" href="../{CSS_URL}"></head>
<body>
  <article><header><h1><span class='cat'><a href="../index.html">{SITE_TITLE}</a></span> / {cat}</h1></header>
  <main><ul>{items_html}</ul></main>
  <footer><p><a href="../index.html">← Retour</a></p></footer></article>
</body></html>"""
        with open(os.path.join(cat_output_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

    # Tags
    tags_root = os.path.join(OUTPUT_DIR, "tags")
    os.makedirs(tags_root, exist_ok=True)
    for tag, items in sorted(tags_map.items()):
        tag_slug = slugify(tag)
        tag_dir = os.path.join(tags_root, tag_slug)
        os.makedirs(tag_dir, exist_ok=True)
        grouped = defaultdict(list)
        for it in items:
            cat = it["categories"][0] if it["categories"] else "Divers"
            grouped[cat].append(it)
        blocks = []
        for cat, posts in sorted(grouped.items()):
            cat_html = f"<h2><a href='../../{slugify(cat)}/'>{cat}</a></h2><ul>"
            for p in posts:
                cat_html += f"<li><a href='../../{slugify(cat)}/{p['filename']}'>{p['title']}</a></li>"
            cat_html += "</ul>"
            blocks.append(cat_html)
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>#{tag}</title>
<link rel="stylesheet" href="../../{CSS_URL}"></head>
<body>
  <article><header><h1><span class='cat'><a href="../index.html">{SITE_TITLE}</a></span> / #{tag}</h1></header>
  <main>{''.join(blocks)}</main>
  <footer><p><a href="../index.html">← Retour</a></p></footer></article>
</body></html>"""
        with open(os.path.join(tag_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)

    # Index principal
    index_html = "\n".join(
        f"<li><a href='{slugify(c)}/'>{c}</a> ({len(items)} articles)</li>"
        for c, items in sorted(categories_map.items(), key=lambda kv: kv[1][0].get("date", ""))
    )
    html_index = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><title>{SITE_TITLE}</title>
<link rel="stylesheet" href="{CSS_URL}"></head>
<body>
  <article><header><h1>{SITE_TITLE}</h1></header>
  <main><ul>{index_html}</ul></main>
  <footer><p><a href="tags/">Voir les tags →</a></p></footer></article>
</body></html>"""
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_index)

    save_cache(new_cache)
    print("Cache mis à jour.")
    print("Génération terminée.")


if __name__ == "__main__":
    main()