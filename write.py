#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import textwrap

CONTENT_DIR = "content"


def slugify(text):
    import re
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text.strip("-")


def list_categories():
    """Retourne la liste des catégories existantes"""
    if not os.path.exists(CONTENT_DIR):
        return []
    return [d for d in os.listdir(CONTENT_DIR) if os.path.isdir(os.path.join(CONTENT_DIR, d))]


def choose_category():
    """Permet de choisir ou créer une catégorie"""
    cats = list_categories()
    print("\n=== Catégories existantes ===")
    if cats:
        for i, c in enumerate(cats, 1):
            print(f"{i}. {c}")
    else:
        print("(Aucune catégorie trouvée)")

    choice = input("\nNuméro de catégorie (ou nom pour en créer une) : ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(cats):
        return cats[int(choice) - 1]
    return choice  # nouvelle catégorie


def get_date():
    """Demande une date (format FR ou ISO) ou prend aujourd’hui"""
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    raw = input(f"Date (par défaut {today.strftime('%d/%m/%Y')}) : ").strip()

    if not raw:
        return today_str

    # Essaye format français JJ/MM/AAAA
    try:
        dt = datetime.datetime.strptime(raw, "%d/%m/%Y").date()
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass

    # Essaye format ISO AAAA-MM-JJ
    try:
        dt = datetime.datetime.strptime(raw, "%Y-%m-%d").date()
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        print("⚠Format de date non reconnu. Utilise JJ/MM/AAAA ou AAAA-MM-JJ.")
        return today_str


def create_post(cat, title, date):
    """Crée le fichier Markdown prérempli"""
    slug = slugify(title)
    cat_dir = os.path.join(CONTENT_DIR, cat)
    os.makedirs(os.path.join(cat_dir, "images"), exist_ok=True)

    filename = f"{date}-{slug}.md"
    path = os.path.join(cat_dir, filename)

    front_matter = textwrap.dedent(f"""\
    ---
    title: {title}
    date: '{date}'
    author: konogan
    categories:
    - {cat}
    tags:
    -
    lat: ''
    lng: ''
    menu:
    - 'Le midi :'
    -
    - 'Le soir :'
    -
    ---
    """)

    body = textwrap.dedent("""\
    ![](images/nom.jpg)
    """)

    with open(path, "w", encoding="utf-8") as f:
        f.write(front_matter + "\n" + body)

    print(f"\nArticle créé : {path}")
    print("Tu peux maintenant le modifier et y ajouter ton texte.")


def main():
    print("=== Créateur d'article 4sacs ===")

    cat = choose_category()
    title = input("Titre de l’article : ").strip()
    if not title:
        print("Titre obligatoire.")
        return

    date = get_date()
    create_post(cat, title, date)


if __name__ == "__main__":
    main()