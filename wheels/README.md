# wheels/ — Offline-Wheelhouse (AlmaLinux/Rocky 9 · Python 3.12 · x86_64)

Vorab heruntergeladene Python-Wheels für die **Offline-Installation** des
Marketplace Portals (`pip install --no-index --find-links=wheels`). Damit braucht
die Ziel-VM **kein Internet**.

Dieses Verzeichnis ist `.gitignore`-d (Binär-Artefakte gehören nicht in die
History) — es wird bei Bedarf neu erzeugt und reist im Release-ZIP, nicht im Repo.

## Neu erzeugen (auf einem Linux-Host mit Python 3.12 + Internet)

```bash
python3.12 -m pip download \
  -r requirements/production.txt \
  --dest wheels --only-binary=:all: \
  --python-version 312 --implementation cp --abi cp312 \
  --platform manylinux2014_x86_64 \
  --platform manylinux_2_17_x86_64 \
  --platform manylinux_2_28_x86_64
python3.12 -m pip download pip setuptools wheel --dest wheels --only-binary=:all:
```

Erwartet: nur `.whl` (keine `.tar.gz`-sdists). Binär-Wheels (`psycopg_binary`,
`PyYAML`) müssen `manylinux…_x86_64` sein → laufen auf AlmaLinux 9 (glibc ≥ 2.17).
