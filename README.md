# Studenti su pobedili

_Pratimo promenu_

Javna evidencija vesti, hapšenja, krivičnih prijava, otkrivenih zloupotreba i obećanja Studentske liste od izbora 25. oktobra 2026.

**Sajt:** https://pretender3969.github.io/Studenti-su-pobedili/
**RSS pretplata:** https://pretender3969.github.io/Studenti-su-pobedili/feed.xml

## Kako radi

- `index.html` prikazuje podatke iz `data/podaci.json`.
- `feed.xml` je RSS sa poslednjih 60 vesti i događaja.
- Podaci se svakog jutra osvežavaju: izvoz iz baze platforme se pretvara skriptom
  `python scripts/build.py <folder_izvoza>`, a promene se šalju u ovaj repozitorijum.

Svaki unos ima izvor. **Navod** je tvrdnja koju nadležni organ još nije potvrdio, **Zvanično** je odluka suda, tužilaštva, MUP-a ili RIK-a. Krivična prijava nije presuda.
