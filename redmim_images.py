#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from PIL import Image
import glob
import hashlib

CONTENT_DIR = "content"
MAX_SIZE = 1024
CACHE_FILE = ".image_cache.json"

def get_image_hash(image_path):
    """Calcule le hash MD5 d'une image."""
    try:
        with open(image_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

def load_cache():
    """Charge le cache des images traitées."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache):
    """Sauvegarde le cache des images traitées."""
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

def needs_resize(image_path, cache):
    """
    Vérifie si une image a besoin d'être redimensionnée.
    Retourne True si l'image n'est pas dans le cache ou a été modifiée.
    """
    current_hash = get_image_hash(image_path)
    if not current_hash:
        return False

    cached_info = cache.get(image_path)
    if not cached_info:
        return True

    # Vérifier si le hash a changé (fichier modifié)
    if cached_info.get('hash') != current_hash:
        return True

    # Vérifier si l'image respecte déjà la taille max
    try:
        with Image.open(image_path) as img:
            return max(img.size) > MAX_SIZE
    except Exception:
        return False

def resize_image(image_path, cache):
    """
    Redimensionne une image si nécessaire et met à jour le cache.
    """
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            original_filesize = os.path.getsize(image_path)

            # Vérifier si le redimensionnement est nécessaire
            if max(original_size) <= MAX_SIZE:
                # Mettre à jour le cache même si pas de redimensionnement
                cache[image_path] = {
                    'hash': get_image_hash(image_path),
                    'original_size': original_size,
                    'resized': False,
                    'timestamp': os.path.getmtime(image_path)
                }
                print(f"  ✓ {os.path.basename(image_path)} : taille correcte ({original_size[0]}x{original_size[1]})")
                return False

            # Calculer les nouvelles dimensions
            ratio = MAX_SIZE / max(original_size)
            new_width = int(original_size[0] * ratio)
            new_height = int(original_size[1] * ratio)
            new_size = (new_width, new_height)

            # Redimensionner
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)

            # Sauvegarder en optimisant la qualité
            if image_path.lower().endswith(('.png', '.webp')):
                resized_img.save(image_path, optimize=True)
            else:
                resized_img.save(image_path, optimize=True, quality=85)

            # Calculer les statistiques
            new_filesize = os.path.getsize(image_path)
            reduction = ((original_filesize - new_filesize) / original_filesize) * 100

            # Mettre à jour le cache
            cache[image_path] = {
                'hash': get_image_hash(image_path),
                'original_size': original_size,
                'new_size': new_size,
                'original_filesize_kb': round(original_filesize / 1024, 1),
                'new_filesize_kb': round(new_filesize / 1024, 1),
                'reduction_percent': round(reduction, 1),
                'resized': True,
                'timestamp': os.path.getmtime(image_path)
            }

            print(f"  ✅ {os.path.basename(image_path)} : {original_size[0]}x{original_size[1]} → {new_size[0]}x{new_size[1]} "
                  f"({cache[image_path]['original_filesize_kb']}Ko → {cache[image_path]['new_filesize_kb']}Ko, -{reduction:.1f}%)")

            return True

    except Exception as e:
        print(f"  ❌ Erreur avec {os.path.basename(image_path)} : {e}")
        return False

def process_category_images(category_dir, cache):
    """
    Traite toutes les images d'une catégorie qui nécessitent un redimensionnement.
    """
    images_dir = os.path.join(category_dir, "images")

    if not os.path.exists(images_dir):
        return 0, 0, 0  # ← CORRECTION ICI : retourner 3 valeurs

    # Trouver toutes les images
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG']:
        image_files.extend(glob.glob(os.path.join(images_dir, ext)))

    if not image_files:
        return 0, 0, 0  # ← CORRECTION ICI : retourner 3 valeurs

    print(f"\n📁 {os.path.basename(category_dir)}/")

    resized_count = 0
    skipped_count = 0
    error_count = 0

    for image_path in image_files:
        if needs_resize(image_path, cache):
            if resize_image(image_path, cache):
                resized_count += 1
            else:
                error_count += 1
        else:
            # Image déjà traitée et à la bonne taille
            cached_info = cache.get(image_path, {})
            if cached_info.get('resized'):
                status = "redimensionnée"
            else:
                status = "déjà optimale"

            print(f"  ⏭️  {os.path.basename(image_path)} : {status} ({cached_info.get('original_size', '?')})")
            skipped_count += 1

    return resized_count, skipped_count, error_count

def cleanup_cache(cache):
    """
    Nettoie le cache des images qui n'existent plus.
    """
    cleaned_cache = {}
    for image_path, info in cache.items():
        if os.path.exists(image_path):
            # Vérifier si le fichier a été modifié depuis le cache
            current_hash = get_image_hash(image_path)
            if current_hash and info.get('hash') == current_hash:
                cleaned_cache[image_path] = info
    return cleaned_cache

def main():
    """
    Script principal avec cache intelligent.
    """
    print("🖼️  Redimensionnement intelligent des images")
    print(f"📏 Taille maximale : {MAX_SIZE}px")
    print("🔍 Utilisation du cache pour éviter les retraitements")
    print("=" * 50)

    if not os.path.exists(CONTENT_DIR):
        print(f"❌ Le dossier {CONTENT_DIR} n'existe pas !")
        sys.exit(1)

    # Charger et nettoyer le cache
    cache = load_cache()
    initial_cache_size = len(cache)
    cache = cleanup_cache(cache)
    if len(cache) < initial_cache_size:
        print(f"🧹 Cache nettoyé : {initial_cache_size - len(cache)} entrées supprimées")

    # Options en ligne de commande
    force_refresh = "--refresh" in sys.argv
    if force_refresh:
        print("🔄 Forcer le rafraîchissement de toutes les images")
        cache = {}  # Vider le cache pour tout retraiter

    total_resized = 0
    total_skipped = 0
    total_errors = 0
    categories_processed = 0

    # Parcourir toutes les catégories
    for category in sorted(os.listdir(CONTENT_DIR)):
        category_path = os.path.join(CONTENT_DIR, category)

        if os.path.isdir(category_path):
            resized, skipped, errors = process_category_images(category_path, cache)
            total_resized += resized
            total_skipped += skipped
            total_errors += errors
            if resized > 0 or errors > 0 or skipped > 0:  # ← CORRECTION ICI : inclure skipped
                categories_processed += 1

    # Sauvegarder le cache
    save_cache(cache)

    print("\n" + "=" * 50)
    print("📊 RÉSULTATS :")
    print(f"   • Catégories traitées : {categories_processed}")
    print(f"   • Images redimensionnées : {total_resized}")
    print(f"   • Images déjà optimisées : {total_skipped}")
    print(f"   • Erreurs : {total_errors}")
    print(f"   • Entrées dans le cache : {len(cache)}")

    if total_resized == 0 and total_errors == 0:
        print("\n🎉 Toutes les images sont déjà optimisées !")

    print("✅ Opération terminée !")

if __name__ == "__main__":
    main()