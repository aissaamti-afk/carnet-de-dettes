# Carnet de dettes - Android APK

## Build depuis GitHub

1. Créez un dépôt GitHub.
2. Ajoutez `main.py`, `buildozer.spec` et le dossier `.github/workflows/`.
3. Poussez les fichiers sur la branche `main`.
4. Ouvrez l'onglet **Actions**.
5. Ouvrez **Build Android APK**.
6. Une fois le build terminé, ouvrez l'exécution réussie.
7. Dans **Artifacts**, téléchargez `carnet-de-dettes-apk`.
8. Décompressez l'archive et installez le fichier `.apk` sur Android.

Le workflow utilise l'action Buildozer recommandée par la documentation Buildozer pour les builds Android GitHub Actions.
