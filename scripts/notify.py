"""Šalje push obaveštenje (OneSignal) kad se na sajtu pojave novi unosi.

Upotreba:  python scripts/notify.py [--od HEAD~1] [--proba]
Poredi data/podaci.json sa verzijom iz git-a (--od, podrazumevano prethodni commit) i za nove
vesti i događaje iz hronike šalje jedno obaveštenje svim pretplatnicima. --proba samo ispisuje poruku.

Ključevi se čuvaju VAN repozitorijuma, u ../onesignal.json:
  {"app_id": "...", "rest_api_key": "..."}
Ako tog fajla nema, skripta ne radi ništa.
"""
import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SITE_URL = "https://pretender3969.github.io/Studenti-su-pobedili/"
ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT.parent / "onesignal.json"
API = "https://api.onesignal.com/notifications?c=push"


def stari_podaci(ref: str) -> dict:
    try:
        out = subprocess.run(["git", "show", f"{ref}:data/podaci.json"], cwd=ROOT,
                             capture_output=True, check=True).stdout
        return json.loads(out.decode("utf-8"))
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return {}


def novi_unosi(staro: dict, novo: dict) -> list[dict]:
    rows = []
    for kolekcija, sidro in (("vesti", "vest"), ("hronika", "hronika")):
        bilo = {r.get("id") for r in staro.get(kolekcija, [])}
        for r in novo.get(kolekcija, []):
            if r.get("id") not in bilo:
                rows.append({**r, "_sidro": f"{sidro}-{r['id']}"})
    # najnoviji i najvažniji prvi; najavljeni događaji iz budućnosti ne idu na vrh
    rows.sort(key=lambda r: (r.get("status") != "najavljeno", r.get("datum", ""), r.get("red", 0)), reverse=True)
    return rows


def poruka(rows: list[dict]) -> dict:
    glavni = rows[0]
    n = len(rows)
    naslov = "Pratimo promenu: nova vest" if n == 1 else f"Pratimo promenu: {n} novih unosa"
    tekst = glavni["naslov"] + ("" if n == 1 else f" i još {n - 1}")
    return {"naslov": naslov, "tekst": tekst[:240], "url": f"{SITE_URL}#{glavni['_sidro']}"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--od", default="HEAD~1", help="git verzija sa kojom se poredi")
    p.add_argument("--proba", action="store_true", help="samo ispiši poruku, ne šalji")
    args = p.parse_args()

    novo = json.loads((ROOT / "data" / "podaci.json").read_text(encoding="utf-8"))
    rows = novi_unosi(stari_podaci(args.od), novo)
    if not rows:
        print("Nema novih unosa, obaveštenje nije poslato.")
        return 0
    msg = poruka(rows)
    print(f"{msg['naslov']}\n{msg['tekst']}\n{msg['url']}")
    if args.proba:
        return 0

    if not CONFIG.is_file():
        print(f"Nije podešeno ({CONFIG} ne postoji), obaveštenje nije poslato.")
        return 0
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    body = {
        "app_id": cfg["app_id"],
        "target_channel": "push",
        "included_segments": ["Total Subscriptions"],
        "headings": {"en": msg["naslov"]},
        "contents": {"en": msg["tekst"]},
        "url": msg["url"],
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"), method="POST", headers={
        "Authorization": f"Key {cfg['rest_api_key']}",
        "Content-Type": "application/json; charset=utf-8",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("Poslato:", r.read().decode("utf-8"))
        return 0
    except urllib.error.HTTPError as e:
        print("OneSignal greška", e.code, e.read().decode("utf-8", "replace"))
        return 1
    except urllib.error.URLError as e:
        print("Mreža nedostupna:", e.reason)
        return 1


if __name__ == "__main__":
    sys.exit(main())
