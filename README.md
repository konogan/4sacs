# 4sacs – Générateur de site statique

## Présentation générale

**4sacs** est un ensemble d’outils Python permettant de générer un site statique complet à partir de fichiers **Markdown**.  
Le système repose sur trois scripts principaux :

1. **`generate_site_from_md.py`** — Générateur principal du site HTML.
2. **`write.py`** — Outil d’écriture et de conversion Markdown → HTML (avec gestion de YAML front matter).
3. **`watch_tags_from_bold.py`** — Observateur et synchroniseur automatique des **tags** et métadonnées des fichiers Markdown (utile pour surveiller les modifications dans les fichiers sources).

Ce système ne nécessite **aucune base de données** ni CMS : tous les contenus sont stockés localement, dans des fichiers `.md`, organisés par catégories.

---

## 1. `generate_site_from_md.py` — Génération du site

### Rôle
Ce script constitue le **cœur du générateur**. Il parcourt les fichiers Markdown du répertoire `content/`, lit leurs métadonnées YAML, et construit un site statique dans `site_static/`.

### Fonctionnalités principales
- **Lecture du front matter YAML** pour extraire : `title`, `date`, `author`, `categories`, `tags`, `menu`, `lat/lng`.
- **Conversion Markdown → HTML** via `markdown` et `BeautifulSoup`.
- **Copie automatique** des images et fichiers statiques (`assets/ → site_static/static/`).
- **Création des pages** :
    - Articles individuels.
    - Index de catégories (`/categorie/index.html`).
    - Pages de tags (`/tags/<nom>/index.html`).
    - Page d’accueil (`/index.html`).
    - Page des tags (`/tags/index.html`).
- **Mise en cache** des fichiers Markdown avec `hash MD5` pour les générations **incrémentales**.
- **Regénération automatique des tags et catégories** à chaque exécution, même en mode incrémental.
- **Support Google Analytics** (via variables d’environnement `.env`).
- **Structure ARIA et sémantique HTML propre**.

### Mode d’exécution

#### Mode par défaut (incrémental)
```bash
python3 generate_site_from_md.py
```
Seuls les fichiers Markdown modifiés sont régénérés, mais **les tags, catégories et l’index global sont toujours mis à jour**.

#### Mode complet
```bash
python3 generate_site_from_md.py --full
```
Force la régénération de **tous les fichiers** et le recalcul du cache (`.build_cache.json`).

### Cache
Le fichier `.build_cache.json` contient le hash MD5 de chaque article.  
Lors de chaque génération :
- Si le hash n’a pas changé → pas de régénération HTML.
- Si le fichier est supprimé → le HTML correspondant est supprimé.
- Si le fichier est nouveau ou modifié → il est régénéré.

---

## 2. `write.py` — Outil d’écriture et de conversion

### Rôle
Ce script gère la **création et modification des fichiers Markdown** à partir d’un modèle, avec validation du front matter YAML.

### Fonctionnalités
- Création de nouveaux articles Markdown avec métadonnées standardisées.
- Conversion bidirectionnelle : édition du contenu ou génération du HTML brut pour prévisualisation.
- Gestion automatique du front matter YAML :
    - `title`, `date`, `author`
    - `categories`, `tags`, `menu`, `lat`, `lng`
- Vérification du format de date et du nom de fichier.
- Peut être utilisé en ligne de commande ou intégré à un outil de rédaction.

### Exemple d’utilisation
```bash
python3 write.py "inde" "2025-07-20-mysore" --title "Mysore Palace" --tags fort marché
```

Crée automatiquement :  
`content/inde/2025-07-20-mysore.md`  
avec le YAML prérempli et un contenu de base.

---

## 3. `watch_tags_from_bold.py` — Surveillance des modifications

### Rôle
Ce script est un **observateur** (watcher) des fichiers Markdown.  
Il analyse les fichiers `.md` pour détecter les **tags**, **titres** et **catégories**, et peut déclencher automatiquement la régénération partielle du site ou la mise à jour du cache.

### Fonctionnalités
- Surveillance des répertoires `content/*`.
- Extraction automatique des `tags:` depuis les fichiers Markdown.
- Peut afficher les statistiques de tags (fréquence, cooccurrence).
- Peut déclencher une commande système (`generate_site_from_md.py`) dès qu’un fichier est modifié.
- Détection des erreurs YAML ou syntaxiques.

### Exemple d’usage
```bash
python3 watch_tags_from_bold.py --watch
```
ou en mode diagnostic :
```bash
python3 watch_tags_from_bold.py --stats
```

---

## 4. Organisation du projet

```
4sacs/
├── assets/                # Fichiers CSS/JS/images partagés
├── content/               # Contenu Markdown classé par catégories
│   ├── inde/
│   │   ├── images/
│   │   ├── 2025-07-10-delhi.md
│   │   └── 2025-07-11-taj-mahal.md
│   └── ...
│
├── site_static/           # Dossier généré automatiquement
│   ├── static/
│   ├── inde/
│   │   ├── index.html
│   │   └── 2025-07-10-delhi.html
│   ├── tags/
│   │   ├── fort/index.html
│   │   └── index.html
│   └── index.html
│
├── generate_site_from_md.py
├── write.py
├── watch_tags_from_bold.py
├── .env
└── .build_cache.json
```

---

## 5. Dépendances

Fichier `requirements.txt` minimal :

```
markdown
pyyaml
beautifulsoup4
python-dotenv
watchdog
```

Installation :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 6. Déploiement et prévisualisation

Génération du site :
```bash
python3 generate_site_from_md.py
```

Prévisualisation locale :
```bash
python3 -m http.server --directory site_static
```
→ [http://localhost:8000](http://localhost:8000)

Déploiement possible sur :
- **GitHub Pages**
- **Freebox / NAS local**
- **Serveur Nginx / Apache**
- **Cloud S3 / Netlify**

---

## 7. Avantages et philosophie

- 100 % **statique et autonome**
- **Aucune base de données**
- **Incrémental et rapide**
- **Lisible et extensible**
- Compatible **SEO** et **accessibilité**
- Idéal pour un carnet de route, un blog minimaliste, ou une collection d’articles organisés.

---

## Auteur

**Konogan Cossec**  
© 2025 — *4sacs Project*
