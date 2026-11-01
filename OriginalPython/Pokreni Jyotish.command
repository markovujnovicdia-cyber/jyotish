#!/bin/bash
set -e
APPDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APPDIR"
trap 'echo "Ako pokretanje nije uspjelo, pošaljite prikaz poruke iz ovog prozora."; read -p "Pritisnite Enter za zatvaranje..."' ERR
PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
    echo "Za ovu aplikaciju potreban je Python 3. Instalirajte ga s python.org."
    read -p "Pritisnite Enter za zatvaranje..."
    exit 1
fi
APP_ENV="$HOME/.jyotish_app_venv"
if [ ! -x "$APP_ENV/bin/python3" ]; then
    "$PYTHON_BIN" -m venv "$APP_ENV"
fi
if ! "$APP_ENV/bin/python3" -c 'import streamlit, swisseph, geopy, timezonefinder, fpdf' >/dev/null 2>&1; then
    echo "Pripremam aplikaciju. Prvo pokretanje može potrajati nekoliko minuta."
    "$APP_ENV/bin/python3" -m pip install -r requirements.txt
fi
echo "Pokrećem Jyotish. Ostavite ovaj prozor otvoren dok koristite aplikaciju."
"$APP_ENV/bin/python3" -m streamlit run app.py --server.address 127.0.0.1 --server.headless false --browser.gatherUsageStats false
