import argostranslate.package

argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()

required_pairs = [
    ("en", "hi"),
    ("en", "ta"),
    ("en", "te"),
    ("en", "kn"),
    ("en", "ml"),
    ("en", "ur")
]

for package in available_packages:
    if (package.from_code, package.to_code) in required_pairs:
        print(f"Installing {package.from_code} → {package.to_code}")
        argostranslate.package.install_from_path(package.download())

print("✅ Offline packages installed successfully!")