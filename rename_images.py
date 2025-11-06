#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from PIL import Image
from PIL.ExifTags import TAGS
import glob
from datetime import datetime

def get_image_date_taken(image_path):
    """
    Récupère la date de prise de vue depuis les métadonnées EXIF.
    Retourne None si non trouvée.
    """
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                        try:
                            # Format: "2023:10:25 14:30:45"
                            return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                        except (ValueError, TypeError):
                            continue
    except Exception:
        pass

    # Si pas de date EXIF, utiliser la date de modification du fichier
    try:
        timestamp = os.path.getmtime(image_path)
        return datetime.fromtimestamp(timestamp)
    except Exception:
        return None

def rename_images_in_directory(directory, dry_run=False):
    """
    Renomme toutes les images du répertoire selon le format YYYY-MM-DD_NNN.ext
    """
    print(f"\n📁 Traitement du dossier : {directory}")

    # Formats d'images supportés
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.JPG', '*.JPEG', '*.PNG', '*.HEIC', '*.heic']

    # Collecter toutes les images
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(directory, ext)))

    if not image_files:
        print("  Aucune image trouvée.")
        return 0, 0

    print(f"  {len(image_files)} image(s) trouvée(s)")

    # Grouper les images par date
    date_groups = {}

    for image_path in image_files:
        date_taken = get_image_date_taken(image_path)

        if date_taken:
            date_key = date_taken.strftime('%Y-%m-%d')
        else:
            # Si pas de date, utiliser "unknown"
            date_key = "unknown"

        if date_key not in date_groups:
            date_groups[date_key] = []

        date_groups[date_key].append(image_path)

    # Renommer les images
    renamed_count = 0
    error_count = 0

    for date_key, images in date_groups.items():
        print(f"  📅 Date : {date_key} ({len(images)} image(s))")

        # Trier les images par heure de prise de vue (ou par nom si pas d'heure)
        sorted_images = []
        for img_path in images:
            date_taken = get_image_date_taken(img_path)
            if date_taken:
                sort_key = date_taken
            else:
                sort_key = datetime.fromtimestamp(os.path.getctime(img_path))
            sorted_images.append((sort_key, img_path))

        sorted_images.sort(key=lambda x: x[0])

        # Renuméroter
        for idx, (sort_key, old_path) in enumerate(sorted_images, 1):
            # Extension du fichier
            _, ext = os.path.splitext(old_path)
            ext = ext.lower()

            # Nouveau nom
            if date_key == "unknown":
                new_filename = f"unknown_{idx:03d}{ext}"
            else:
                new_filename = f"{date_key}_{idx:03d}{ext}"

            new_path = os.path.join(directory, new_filename)

            # Vérifier si le fichier de destination existe déjà
            counter = 1
            original_new_path = new_path
            while os.path.exists(new_path) and new_path != old_path:
                if date_key == "unknown":
                    new_filename = f"unknown_{idx:03d}_{counter:02d}{ext}"
                else:
                    new_filename = f"{date_key}_{idx:03d}_{counter:02d}{ext}"
                new_path = os.path.join(directory, new_filename)
                counter += 1

            if old_path != new_path:
                if dry_run:
                    print(f"    🔄 [SIMULATION] {os.path.basename(old_path)} → {os.path.basename(new_path)}")
                else:
                    try:
                        os.rename(old_path, new_path)
                        print(f"    ✅ {os.path.basename(old_path)} → {os.path.basename(new_path)}")
                        renamed_count += 1
                    except Exception as e:
                        print(f"    ❌ Erreur avec {os.path.basename(old_path)} : {e}")
                        error_count += 1
            else:
                print(f"    ⏭️  {os.path.basename(old_path)} (déjà correct)")

    return renamed_count, error_count

def main():
    """
    Script principal de renommage des images.
    """
    print("🖼️  Renommage des images par date de prise de vue")
    print("📝 Format : YYYY-MM-DD_NNN.ext")
    print("=" * 50)

    # Déterminer le répertoire cible
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        target_dir = input("Entrez le chemin du répertoire à traiter : ").strip()

    if not target_dir:
        target_dir = "."  # Répertoire courant

    target_dir = os.path.abspath(target_dir)

    if not os.path.exists(target_dir):
        print(f"❌ Le répertoire {target_dir} n'existe pas !")
        sys.exit(1)

    # Vérifier le mode simulation
    dry_run = "--dry-run" in sys.argv or "--simulate" in sys.argv

    if dry_run:
        print("🔍 MODE SIMULATION - Aucun fichier ne sera modifié")

    # Demander confirmation
    if not dry_run:
        print(f"\n⚠️  Ce script va renommer les images dans : {target_dir}")
        print("   Format : YYYY-MM-DD_NNN.ext (ex: 2023-10-25_001.jpg)")
        response = input("   Voulez-vous continuer ? (o/N) : ")
        if response.lower() not in ['o', 'oui', 'y', 'yes']:
            print("❌ Opération annulée.")
            return

    # Traiter le répertoire
    renamed, errors = rename_images_in_directory(target_dir, dry_run=dry_run)

    print("\n" + "=" * 50)
    print("📊 RÉSULTATS :")
    print(f"   • Images renommées : {renamed}")
    print(f"   • Erreurs : {errors}")

    if dry_run:
        print("\n💡 Pour appliquer les changements, relancez le script sans --dry-run")
    else:
        print("✅ Opération terminée !")

def batch_process_content_directory():
    """
    Version alternative pour traiter tous les dossiers d'images du répertoire content/
    """
    content_dir = "content"

    if not os.path.exists(content_dir):
        print(f"❌ Le répertoire {content_dir} n'existe pas !")
        return

    total_renamed = 0
    total_errors = 0

    print("🖼️  Renommage en lot des images dans content/")
    print("=" * 50)

    # Parcourir toutes les catégories
    for category in sorted(os.listdir(content_dir)):
        category_path = os.path.join(content_dir, category)
        images_dir = os.path.join(category_path, "images")

        if os.path.isdir(category_path) and os.path.exists(images_dir):
            renamed, errors = rename_images_in_directory(images_dir, dry_run=False)
            total_renamed += renamed
            total_errors += errors

    print("\n" + "=" * 50)
    print("📊 RÉSULTATS TOTAUX :")
    print(f"   • Images renommées : {total_renamed}")
    print(f"   • Erreurs : {total_errors}")
    print("✅ Opération terminée !")

if __name__ == "__main__":
    # Si lancé sans argument, proposer les deux modes
    if len(sys.argv) == 1:
        print("Choisissez le mode :")
        print("1 - Répertoire spécifique")
        print("2 - Tous les dossiers images de content/")
        choice = input("Votre choix (1 ou 2) : ").strip()

        if choice == "2":
            batch_process_content_directory()
        else:
            main()
    else:
        main()