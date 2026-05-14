# Essora Store — Paquete de actualización completo

Paquete con todos los archivos del proyecto, listos para reemplazar en
`/usr/local/essora-store/`.

## Archivos modificados en esta entrega

- **ui_widgets.py** — Multi-select DEB + badge `not_available` para AppImages sin URL
- **essora_core.py** — `install_many_deb()` para batch DEB + cascada de resolución AppImage + validación ELF post-descarga
- **appimage** (script) — Resolución batch de URLs en 3 fuentes (data/ → GitHub API → HTML scrape)

## Archivos sin cambios (incluidos por completitud)

- essora-store.py
- essora_about_dialog.py
- essora-repo-update.py
- essora-fix-broken.py
- essora-deb-db
- translations.py

## Instalación

```bash
sudo cp ui_widgets.py        /usr/local/essora-store/
sudo cp essora_core.py       /usr/local/essora-store/
sudo cp essora-store.py      /usr/local/essora-store/
sudo cp essora_about_dialog.py /usr/local/essora-store/
sudo cp essora-repo-update.py  /usr/local/essora-store/
sudo cp essora-fix-broken.py   /usr/local/essora-store/
sudo cp translations.py        /usr/local/essora-store/
sudo cp appimage               /usr/local/essora-store/
sudo cp essora-deb-db          /usr/local/essora-store/

sudo chmod +x /usr/local/essora-store/appimage
sudo chmod +x /usr/local/essora-store/essora-deb-db
sudo chmod +x /usr/local/essora-store/essora-repo-update.py
sudo chmod +x /usr/local/essora-store/essora-fix-broken.py

# Forzar regeneración del catálogo AppImage con la nueva cascada
sudo rm -f /usr/local/essora-store/last-update.txt

# Recomendado: con GitHub token (sube rate limit a 5000 req/h)
# Crear token en: https://github.com/settings/tokens (fine-grained, sin permisos especiales)
export GITHUB_TOKEN="github_pat_..."
sudo -E /usr/local/essora-store/appimage
```

## Requisitos

- Imagen `not_available.png` en `/usr/local/essora-store/icons/not_available.png`
- `jq` instalado: `sudo apt-get install jq`

## Features incluidos

1. **Multi-select DEB**: checkboxes en cada paquete DEB para instalación batch.
2. **Badge AppImage not available**: apps sin URL ni `github_path` muestran tu imagen en lugar del botón Install.
3. **Cascada de resolución AppImage en el generador**: el JSON siempre tiene URL directa al `.appimage` o vacía.
4. **Validación ELF al instalar**: si el download devuelve HTML por error, se detecta y borra antes de dejar archivo corrupto.
