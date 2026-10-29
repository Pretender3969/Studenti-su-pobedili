"""Gradi podatke za javni sajt iz izvoza baze platforme "Pratimo promenu".

Upotreba:  python scripts/build.py <export_dir>
<export_dir> sadrži podfoldere vesti/, hronika/, obecanja/, stanje/ sa po jednim JSON fajlom po unosu.
Izlaz:  data/podaci.json  i  feed.xml  u korenu repozitorijuma.
"""
import json
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

SITE_URL = "https://pretender3969.github.io/Studenti-su-pobedili/"
ROOT = Path(__file__).resolve().parent.parent

TIPOVI = {
    "hapsenje": "Hapšenje", "prijava": "Krivična prijava", "otkrice": "Otkrivena zloupotreba",
    "ostavka": "Ostavka / smena", "korak": "Korak ka promeni", "izbori": "Izbori", "incident": "Incident / pritisak",
}


def load(export: Path, name: str) -> list[dict]:
    folder = export / name
    if not folder.is_dir():
        return []
    rows = []
    for f in sorted(folder.glob("*.json")):
        row = json.loads(f.read_text(encoding="utf-8"))
        row["id"] = f.stem
        rows.append(row)
    return rows


def sort_key(row: dict):
    return (row.get("datum", ""), row.get("red", 0))


def rss_date(datum: str, red: int) -> str:
    d = datetime.strptime(datum, "%Y-%m-%d").replace(hour=6, tzinfo=timezone.utc)
    # red (1-99) razdvaja unose istog dana da bi čitači zadržali redosled
    return format_datetime(d.replace(minute=min(int(red or 0), 59)))


def build_feed(vesti: list[dict], hronika: list[dict]) -> str:
    items = []
    for e in hronika:
        if e.get("status") == "najavljeno":
            continue
        link = (e.get("izvori") or [SITE_URL])[0]
        naslov = f"[{TIPOVI.get(e.get('tip'), 'Događaj')}] {e['naslov']}"
        opis = " ".join(x for x in [e.get("opis", ""), e.get("iznos", ""), e.get("osobe", "")] if x)
        items.append((sort_key(e), naslov, link, opis, f"{SITE_URL}#hronika-{e['id']}", e))
    for v in vesti:
        link = v.get("url") or SITE_URL
        items.append((sort_key(v), f"{v['naslov']} ({v.get('izvor', '')})", link, v.get("sazetak", ""), f"{SITE_URL}#vest-{v['id']}", v))
    items.sort(key=lambda x: x[0], reverse=True)
    out = []
    for _, naslov, link, opis, guid, row in items[:60]:
        out.append(
            "<item>"
            f"<title>{escape(naslov)}</title>"
            f"<link>{escape(link)}</link>"
            f"<description>{escape(opis)}</description>"
            f"<guid isPermaLink=\"false\">{escape(guid)}</guid>"
            f"<pubDate>{rss_date(row['datum'], row.get('red', 0))}</pubDate>"
            "</item>"
        )
    now = format_datetime(datetime.now(timezone.utc))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>'
        "<title>Pratimo promenu</title>"
        f"<link>{SITE_URL}</link>"
        f'<atom:link href="{SITE_URL}feed.xml" rel="self" type="application/rss+xml"/>'
        "<description>Vesti, hapšenja, krivične prijave i obećanja Studentske liste od izbora 25. oktobra 2026.</description>"
        "<language>sr-Latn</language>"
        f"<lastBuildDate>{now}</lastBuildDate>"
        + "".join(out)
        + "</channel></rss>\n"
    )


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("Upotreba: python scripts/build.py <export_dir>")
    export = Path(sys.argv[1])
    vesti = sorted(load(export, "vesti"), key=sort_key, reverse=True)
    hronika = sorted(load(export, "hronika"), key=sort_key, reverse=True)
    obecanja = load(export, "obecanja")
    stanje_rows = load(export, "stanje")
    stanje = next((s for s in stanje_rows if s["id"] == "trenutno"), {})
    stanje.pop("id", None)

    data = {
        "generisano": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "stanje": stanje, "vesti": vesti, "hronika": hronika, "obecanja": obecanja,
    }
    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "podaci.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "feed.xml").write_text(build_feed(vesti, hronika), encoding="utf-8")
    print(f"vesti={len(vesti)} hronika={len(hronika)} obecanja={len(obecanja)}")


if __name__ == "__main__":
    main()
