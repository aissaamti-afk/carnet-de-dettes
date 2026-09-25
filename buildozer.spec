[app]

# Application
title = Carnet de dettes
package.name = carnetdettes
package.domain = org.carnetdettes

# Source
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,txt,json
source.exclude_dirs = .git,.github,bin,.buildozer,venv,__pycache__

# Python requirements
requirements = python3,kivy,reportlab

# Display
orientation = portrait
fullscreen = 0

# Version
version = 1.0.0

# Android
android.api = 36
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.enable_androidx = True
android.debug_artifact = apk

# Permissions used by sharing/backups if needed by Android version
android.permissions = android.permission.INTERNET

# Keep the app private to its own storage by default
android.private_storage = True

# Python-for-Android
p4a.bootstrap = sdl2
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
