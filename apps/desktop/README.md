# VERA-MMU Desktop

Cette application Tauri rend le parcours VERA lisible pour une personne : sélection native d’un dossier, scan sans écriture, preview, confirmation explicite puis intégration MCP project-local. Le WebView React ne reçoit ni API filesystem, ni API shell, ni accès Git direct. Toutes les opérations passent par le sidecar `vmmu-desktop-bridge` en `stdin`/`stdout` et les contrats Core VERA existants.

## Développement local

Depuis la racine du dépôt VERA, installer les dépendances Python de développement, puis construire le sidecar **sur le système cible**. Sous Windows, utiliser PowerShell ; sous Linux, le script POSIX historique délègue au même builder Python cross-platform.

```text
python -m pip install pyinstaller .
python scripts/build_desktop_sidecar.py
cd apps/desktop
corepack enable
pnpm install --frozen-lockfile
pnpm tauri dev
```

Le builder refuse un target différent du système hôte. Les sidecars Windows et Linux sont donc produits dans leur runner natif respectif et portent le suffixe target requis par Tauri.

**L’ordre ci-dessus est obligatoire.** Tauri déclare le sidecar comme ressource externe : lancer `cargo` ou `tauri build` avant d’avoir construit le binaire échoue sur `resource path binaries/vmmu-desktop-bridge-<target> doesn't exist`. Le message ne désigne pas un défaut du code Rust, seulement une étape manquante.

Sous Linux, la compilation exige en outre les bibliothèques de développement GTK et WebKit, absentes d’une image minimale. Sur base Debian/Ubuntu :

```bash
sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.1-dev \
  libayatana-appindicator3-dev librsvg2-dev libsoup-3.0-dev pkg-config
```

Leur absence se manifeste par `The system library gdk-3.0 required by crate gdk-sys was not found`, bien avant que le code du projet ne soit compilé.

## Artefacts de vérification

La matrice GitHub Actions `.github/workflows/desktop-packaging.yml` produit, sans créer de release, les artefacts suivants :

| Système | Target | Bundles vérifiés |
|---|---|---|
| Linux x64 | `x86_64-unknown-linux-gnu` | AppImage et Debian |
| Windows x64 | `x86_64-pc-windows-msvc` | NSIS (`.exe`) et MSI |

Les artefacts CI sont destinés à la vérification. Une release signée, ses hashes publiés et ses notes ne sont créés que dans le lot de release dédié. Le viewer GitHub Pages, lorsqu’il sera livré, ne pourra qu’importer/exporter des contrats VERA : il ne distribue ni ne lance le sidecar local.
