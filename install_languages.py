import argostranslate.package
import argostranslate.translate

available_packages = argostranslate.package.get_available_packages()

packages = [
    next(p for p in available_packages if p.from_code == "hi" and p.to_code == "en"),
    next(p for p in available_packages if p.from_code == "en" and p.to_code == "hi")
]

for pkg in packages:
    download_path = pkg.download()
    argostranslate.package.install_from_path(download_path)

print("Hindi-English packages installed")
