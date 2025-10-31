# 4sacs — Générateur de site statique

## Présentation

**4sacs** est un générateur de site statique écrit en **Python**, conçu pour transformer des articles rédigés en **Markdown** en un site HTML complet, clair et rapide à héberger (par exemple sur un serveur Nginx, une Freebox, ou GitHub Pages).

Le projet permet désormais d’écrire et de gérer les articles **directement en Markdown**, sans base de données SQL, tout en conservant la structure, la navigation et les fonctionnalités de l’ancien site WordPress.

---

## Objectif

- Écrire des articles de voyage en Markdown.
- Structurer les catégories et les images simplement.
- Générer un site complet avec :
  - Pages d’articles.
  - Index de catégories.
  - Pages de tags.
  - Navigation précédente / suivante.
  - Menu du jour et géolocalisation.
- Produire une hiérarchie d’URL lisible :

  ```
  /categorie/index.html
  /categorie/2024-07-13-mysore.html
  /tags/fort/index.html
  /tags/index.html
  /index.html
  ```

---

## Structure du projet

```
4sacs/
├── assets/                   # Fichiers statiques (CSS, JS, polices, etc.)
│   └── style.css
│
├── content/                  # Contenu source (Markdown)
│   ├── inde/                 
│   │   ├── images/           # Images propres à cette catégorie
│   │   │   ├── photo1.jpg
│   │   │   └── photo2.jpg
│   │   ├── 2024-07-10-delhi.md
│   │   ├── 2024-07-11-taj-mahal.md
│   │   └── ...
│   │
│   ├── karnataka/
│   │   ├── images/
│   │   ├── 2024-07-12-bangalore.md
│   │   └── ...
│   │
│   └── ...
│
├── site_static/              # Dossier généré automatiquement
│   ├── static/               # Copie automatique de `assets/`
│   ├── inde/
│   │   ├── index.html
│   │   ├── 2024-07-10-delhi.html
│   │   └── ...
│   ├── tags/
│   │   ├── fort/index.html
│   │   └── index.html
│   └── index.html
│
├── generate_site_from_md.py  # Générateur principal
└── README.md
```

---

## Format des articles Markdown

Chaque article est un fichier `.md` contenant un **front matter YAML** suivi du contenu.

Exemple :

```markdown
---
title: "Bangalore"
date: "2024-07-12"
author: "Konogan"
categories: ["Karnataka"]
tags: ["fort", "marché"]
lat: 12.981726
lng: 77.614632
menu:
  - Dosa
  - Chai
  - Poha
---

Une journée animée à **Bangalore**, capitale du Karnataka.  
Nous avons visité le marché, puis le fort en fin d’après-midi.

![Fort de Bangalore](images/fort.jpg)
```

### Champs disponibles

| Champ | Type | Description |
|--------|------|-------------|
| `title` | string | Titre de l’article |
| `date` | string (YYYY-MM-DD) | Date de publication |
| `author` | string | Nom de l’auteur |
| `categories` | list | Catégories principales (la première = dossier) |
| `tags` | list | Mots-clés pour indexation |
| `lat`, `lng` | float | Coordonnées géographiques |
| `menu` | list | “Menu du jour” affiché dans la colonne latérale |

---

## Génération du site

### Préparer l'environnement

Créer un environnement virtuel Python :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Contenu minimal de `requirements.txt` :

```
markdown
pyyaml
beautifulsoup4
```

---

### Lancer la génération

#### Mode par défaut (incrémental)

Génère uniquement les articles modifiés ou nouveaux :

```bash
python3 generate_site_from_md.py
```

#### Mode complet

Force la régénération de tout le site :

```bash
python3 generate_site_from_md.py --full
```

---

### Fonctionnement du mode incrémental

Le générateur conserve un cache (`.build_cache.json`) contenant le hash de chaque fichier Markdown.  
Lors du prochain lancement :
- Les fichiers non modifiés sont ignorés.
- Les fichiers supprimés sont retirés du site.
- Les nouveaux fichiers sont ajoutés automatiquement.

Cela permet des reconstructions beaucoup plus rapides.

---

### Résultat

Le site complet est généré dans :

```
site_static/
```

Prévisualisation locale :

```bash
python3 -m http.server --directory site_static
```

Puis ouvrir : [http://localhost:8000](http://localhost:8000)

---

## Règles d’organisation

- Chaque dossier dans `content/` correspond à une **catégorie**.
- Chaque `.md` correspond à un article.
- Les images doivent être placées dans `content/<categorie>/images/`.
- Le script copie automatiquement ces images dans `site_static/<categorie>/images/`.
- Les tags sont regroupés dans `site_static/tags/<tag>/index.html`.

---

## Accessibilité et SEO

Le générateur applique automatiquement :
- Un attribut `alt` à chaque image (nom de fichier si manquant).
- Des rôles ARIA cohérents (`role="main"`, `role="navigation"`, `role="contentinfo"`...).
- Une structure sémantique claire : `<article>`, `<header>`, `<footer>`, `<aside>`.

---

## À venir

- Génération d’une carte interactive à partir des coordonnées (`lat` / `lng`).
- Thèmes CSS alternatifs.
- Pagination et flux RSS.
- Support de génération partielle par tag ou catégorie.
- Option de déploiement automatisé.

---

## Auteur

**Konogan**  
© 2025
