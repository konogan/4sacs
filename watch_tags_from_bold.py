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
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")

def normalize_text(s: str) -> str:
    """Supprime les accents, normalise les espaces et la casse."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()

def extract_bold_words(text: str) -> list[str]:
    """Retourne une liste unique de mots en gras (minuscules, sans accents)."""
    words = {
        normalize_text(re.sub(r"[^\wÀ-ÿ'’\- ]+", "", (m1 or m2).strip()))
        for m1, m2 in re.findall(BOLD_PATTERN, text)
        if (m1 or m2).strip()
    }
    return sorted(w for w in words if len(w) >= 2)

def deduplicate_tags(existing: list[str], new: list[str]) -> list[str]:
    """Fusionne et déduplique les tags, en ignorant la casse et les accents."""
    def clean_list(lst):
        return [t for t in lst if isinstance(t, str) and t.strip()]

    existing = clean_list(existing)
    new = clean_list(new)

    combined = {normalize_text(t): t for t in existing}
    combined.update({normalize_text(t): t for t in new})
    return sorted(combined.values(), key=str.lower)

def update_tags_in_markdown(path: str):
    """Met à jour les tags YAML à partir des mots en gras du contenu Markdown."""
    try:
        raw = open(path, "r", encoding="utf-8").read()
    except Exception as e:
        print(f"[Erreur] lecture {path} : {e}")
        return

    if not raw.startswith("---"):
        return

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
        return

    existing_tags = meta.get("tags", [])
    if not isinstance(existing_tags, list):
        existing_tags = []

    merged_tags = deduplicate_tags(existing_tags, bold_words)

    if set(map(normalize_text, merged_tags)) == set(map(normalize_text, existing_tags)):
        return  # pas de changement

    meta["tags"] = merged_tags

    new_front = yaml.dump(meta, sort_keys=False, allow_unicode=True).strip()
    new_content = f"---\n{new_front}\n---\n{body.lstrip()}"

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[OK] {os.path.basename(path)} : tags mis à jour -> {', '.join(merged_tags)}")

class MarkdownWatcher(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(".md"):
            update_tags_in_markdown(event.src_path)

def main():
    print(f"Surveillance du dossier : {CONTENT_DIR}")
    observer = Observer()
    observer.schedule(MarkdownWatcher(), CONTENT_DIR, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()