"""Dodaje nove unose i menja postojeće u data/podaci.json, proverava ih i ponovo gradi sajt.

Upotreba:  python scripts/unos.py izmene.json [--proba]

izmene.json (sva polja su opciona):
{
  "vesti":    [ {datum, red, izvor, kategorija, naslov, sazetak, url}, ... ],
  "hronika":  [ {datum, red, tip, status, naslov, opis, osobe?, iznos?, izvori:[...]}, ... ],
  "obecanja": [ {datum, status, naslov, opis, napomena?, url}, ... ],
  "izmene":   { "h10": {"status": "zvanicno", "opis": "..."}, "o08": {"status": "ispunjeno", "napomena": "..."} },
  "stanje":   { "vlada": "...", "skupstina": "...", "procenat": "...", "mandati": 141 }
}
Novi unosi dobijaju sledeći slobodan id (v135, h42, o15 ...). Vest čiji url već postoji se preskače.
Ako nešto nije ispravno, skripta ispisuje greške i NE menja ništa. --proba samo proverava.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import ROOT, write  # noqa: E402

KATEGORIJE = {"korupcija", "hapsenje", "institucije", "program", "izbori", "mediji", "bezbednost"}
TIPOVI = {"hapsenje", "prijava", "otkrice", "ostavka", "korak", "izbori", "incident"}
STATUS_H = {"zvanicno", "navod", "najavljeno"}
STATUS_O = {"najavljeno", "u_toku", "delimicno", "ispunjeno", "odstupljeno"}
POLJA = {
    "vesti": {"datum", "red", "izvor", "kategorija", "naslov", "sazetak", "url"},
    "hronika": {"datum", "red", "tip", "status", "naslov", "opis", "osobe", "iznos", "izvori"},
    "obecanja": {"datum", "status", "naslov", "opis", "napomena", "url", "azurirano"},
}
OBAVEZNA = {
    "vesti": {"datum", "izvor", "kategorija", "naslov", "sazetak", "url"},
    "hronika": {"datum", "tip", "status", "naslov", "opis", "izvori"},
    "obecanja": {"datum", "status", "naslov", "opis"},
}
PREFIKS = {"vesti": "v", "hronika": "h", "obecanja": "o"}
DATUM = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL = re.compile(r"^https?://\S+$")


def proveri(kol: str, r: dict, gde: str, novo: bool) -> list[str]:
    err = []
    visak = set(r) - POLJA[kol]
    if visak:
        err.append(f"{gde}: nepoznata polja {sorted(visak)}")
    if novo:
        nema = OBAVEZNA[kol] - {k for k, v in r.items() if v not in (None, "", [])}
        if nema:
            err.append(f"{gde}: nedostaju polja {sorted(nema)}")
    for k in ("datum", "azurirano"):
        if k in r and not DATUM.match(str(r[k])):
            err.append(f"{gde}: {k} mora biti YYYY-MM-DD")
    if "red" in r and not (isinstance(r["red"], int) and 1 <= r["red"] <= 99):
        err.append(f"{gde}: red mora biti ceo broj 1-99")
    if "url" in r and r["url"] and not URL.match(r["url"]):
        err.append(f"{gde}: neispravan url")
    if kol == "vesti" and "kategorija" in r and r["kategorija"] not in KATEGORIJE:
        err.append(f"{gde}: kategorija mora biti jedna od {sorted(KATEGORIJE)}")
    if kol == "hronika":
        if "tip" in r and r["tip"] not in TIPOVI:
            err.append(f"{gde}: tip mora biti jedan od {sorted(TIPOVI)}")
        if "status" in r and r["status"] not in STATUS_H:
            err.append(f"{gde}: status mora biti jedan od {sorted(STATUS_H)}")
        if "izvori" in r and (not isinstance(r["izvori"], list) or not all(URL.match(str(u)) for u in r["izvori"])):
            err.append(f"{gde}: izvori mora biti lista URL-ova")
    if kol == "obecanja" and "status" in r and r["status"] not in STATUS_O:
        err.append(f"{gde}: status mora biti jedan od {sorted(STATUS_O)}")
    return err


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--proba"]
    if len(args) != 1:
        sys.exit("Upotreba: python scripts/unos.py izmene.json [--proba]")
    izm = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    d = json.loads((ROOT / "data" / "podaci.json").read_text(encoding="utf-8"))
    danas = date.today().isoformat()
    err, log = [], []

    def sledeci(kol: str) -> int:
        return max([int(r["id"][1:]) for r in d[kol] if r["id"][1:].isdigit()] + [0]) + 1

    for kol in ("vesti", "hronika", "obecanja"):
        urls = {r.get("url") for r in d[kol] if r.get("url")}
        for i, r in enumerate(izm.get(kol, [])):
            gde = f"{kol}[{i}]"
            if kol == "vesti" and r.get("url") in urls:
                log.append(f"preskočeno (url već postoji): {r.get('naslov', '')[:70]}")
                continue
            e = proveri(kol, r, gde, novo=True)
            if e:
                err += e
                continue
            r = dict(r)
            if kol == "obecanja":
                r.setdefault("azurirano", danas)
            else:
                r.setdefault("red", 50)
            if kol == "hronika":
                isti = [h["id"] for h in d["hronika"] if set(h.get("izvori", [])) & set(r["izvori"])]
                if isti:
                    log.append(f"PAŽNJA: isti izvor kao {', '.join(isti)} — proveri da nije duplikat")
            r["id"] = f"{PREFIKS[kol]}{sledeci(kol)}"
            d[kol].append(r)
            urls.add(r.get("url"))
            log.append(f"dodato {r['id']}: {r['naslov'][:70]}")

    po_id = {r["id"]: (kol, r) for kol in ("vesti", "hronika", "obecanja") for r in d[kol]}
    for rid, polja in (izm.get("izmene") or {}).items():
        if rid not in po_id:
            err.append(f"izmene.{rid}: ne postoji unos sa tim id")
            continue
        kol, r = po_id[rid]
        e = proveri(kol, polja, f"izmene.{rid}", novo=False)
        if e:
            err += e
            continue
        r.update(polja)
        if kol == "obecanja" and "azurirano" not in polja:
            r["azurirano"] = danas
        log.append(f"izmenjeno {rid}: {', '.join(polja)}")

    if izm.get("stanje"):
        dozvoljeno = {"vlada", "skupstina", "procenat", "mandati", "izbori"}
        visak = set(izm["stanje"]) - dozvoljeno
        if visak:
            err.append(f"stanje: nepoznata polja {sorted(visak)}")
        else:
            d["stanje"].update(izm["stanje"])
            d["stanje"]["azurirano"] = danas
            log.append(f"stanje: {', '.join(izm['stanje'])}")

    if err:
        print("GREŠKE, ništa nije upisano:\n  " + "\n  ".join(err))
        return 1
    print("\n".join(log) or "Nema izmena.")
    if "--proba" not in sys.argv:
        write(d["stanje"], d["vesti"], d["hronika"], d["obecanja"], d.get("funkcije", []), d.get("sednice", []))
    return 0


if __name__ == "__main__":
    sys.exit(main())
