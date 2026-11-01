"""
Desktop pokretač aplikacije.

Ovo NIJE Electron - koristi puno lakši pristup za Python aplikacije:
1. Pokrene Streamlit server u pozadini (kao podproces), lokalno na
   127.0.0.1, bez pristupa izvana.
2. Otvori nativni macOS prozor (pywebview, koristi ugrađeni WKWebView)
   koji prikazuje tu lokalnu adresu - izgleda i ponaša se kao desktop
   aplikacija, bez trake preglednika.

Zahtijeva dodatni paket: pip install pywebview
(vidi requirements-desktop.txt)

Pokretanje za testiranje: python desktop_launcher.py
Pakiranje u .app: vidi upute u README.md (odjeljak "Pakiranje u desktop app").
"""

import subprocess
import sys
import time
import webview

STREAMLIT_PORT = 8501


def start_streamlit_server():
    return subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", str(STREAMLIT_PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
    )


def main():
    server_process = start_streamlit_server()
    try:
        # Kratka pauza da se Streamlit server stigne podići prije
        # otvaranja prozora
        time.sleep(2.5)
        webview.create_window(
            "Jyotish",
            f"http://127.0.0.1:{STREAMLIT_PORT}",
            width=1200,
            height=850,
        )
        webview.start()
    finally:
        server_process.terminate()


if __name__ == "__main__":
    main()
