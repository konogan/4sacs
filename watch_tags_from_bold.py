#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import time
import yaml
import unicodedata
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONTENT_DIR = "content"

# --- Expressions régulières pour détecter le gras Markdown ( **...** ou __...__ ) ---
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")

def normalize_text(s: str) -> str:
    """Supprime les accents et normalise les espaces."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip()

def extract_bold_words(text):
    """
    Retourne une liste unique d'expressions trouvées en gras (minuscules, sans accents).
    Exemple : **Food Court** -> ['food court']
    """
    matches = re.findall(BOLD_PATTERN, text)
    words = []
    for m1, m2 in matches:
        val = (m1 or m2).strip()
        # Nettoie les caractères parasites mais garde les espaces et tirets
        val = re.sub(r"[^\wÀ-ÿ'’\- ]+", "", val)
        if len(val) >= 2:
            val = normalize_text(val.lower())
            words.append(val)
    return sorted(set(words))

def deduplicate_tags(existing, new):
    """Fusionne et déduplique les tags, en ignorant la casse et les accents."""
    cleaned_existing = [t for t in existing if isinstance(t, str) and t.strip()]
    cleaned_new = [t for t in new if isinstance(t, str) and t.strip()]

    combined = {normalize_text(t.lower()): t for t in cleaned_existing}  # conserve la casse d'origine
    for t in cleaned_new:
        key = normalize_text(t.lower())
        if key not in combined:
            combined[key] = t
    return sorted(combined.values(), key=str.lower)

def update_tags_in_markdown(path):
    """Met à jour les tags YAML à partir des mots en gras du contenu Markdown."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
    except Exception as e:
        print(f"[Erreur] lecture {path} : {e}")
        return

    if not raw.startswith("---"):
        return  # pas de front-matter YAML

    parts = raw.split("---", 2)
    if len(parts) < 3:
        return

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        print(f"[Erreur] YAML invalide dans {path} : {e}")
        return

    body = parts[2]
    bold_words = extract_bold_words(body)
    if not bold_words:
        return  # rien à ajouter

    existing_tags = meta.get("tags", [])
    if not isinstance(existing_tags, list):
        existing_tags = []
    existing_tags = [t for t in existing_tags if isinstance(t, str) and t.strip()]

    merged_tags = deduplicate_tags(existing_tags, bold_words)

    # Vérifie si une mise à jour est nécessaire
    if set(map(normalize_text, merged_tags)) == set(map(normalize_text, existing_tags)):
        return  # aucune différence, inutile de réécrire

    meta["tags"] = merged_tags

    # Réécriture propre du fichier
    new_front = yaml.dump(meta, sort_keys=False, allow_unicode=True).strip()
    new_body = body if body.startswith("\n") else "\n" + body
    new_content = f"---\n{new_front}\n---{new_body}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[OK] Tags mis à jour pour {os.path.basename(path)} -> {', '.join(merged_tags)}")

# --- Surveillance du dossier content/ ---
class MarkdownWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            update_tags_in_markdown(event.src_path)

def main():
    print(f"Surveillance du dossier : {CONTENT_DIR}")
    event_handler = MarkdownWatcher()
    observer = Observer()
    observer.schedule(event_handler, CONTENT_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()