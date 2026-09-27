[app]

title = Carnet de dettes
package.name = carnetdettes
package.domain = org.carnetdettes

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,txt,json
source.exclude_dirs = .git,.github,bin,.buildozer,venv,__pycache__

requirements = python3,kivy

orientation = portrait
fullscreen = 0

version = 1.0.0

android.api = 36
android.minapi = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.enable_androidx = True
android.debug_artifact = apk

android.permissions = android.permission.INTERNET

android.private_storage = True

p4a.bootstrap = sdl2
p4a.branch = develop

[buildozer]

log_level = 2
warn_on_root = 1
