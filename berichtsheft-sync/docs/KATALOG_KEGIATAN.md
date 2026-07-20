# Katalog kegiatan per Abteilung

> File sumber (edit di sini): [`data/katalog_abteilung.json`](../data/katalog_abteilung.json)

Sumber kebenaran kegiatan per Abteilung. Edit di sini → jalankan: python3 -m berichtsheft catalog --reload

Setelah edit JSON:

```bash
python3 -m berichtsheft catalog --reload
python3 -m berichtsheft catalog --write-md   # regenerasi file ini
```

## Service

Service / F&B (Frühstück, Restaurant, BAF)

### `BRF` — Frühstück / Restaurant

| Field | Nilai |
|-------|-------|
| Department | F&B |
| Lernfeld | Gästeservice und Kommunikation |
| Keywords | buffet, frühstück, breakfast, gäste begrüßen, brf, getränke |

**Default activities**

- Frühstücksservice und Buffetbetreuung

**Template teks Jerman (pool generator)**

- Unterstützung beim Frühstücksservice: Gäste begrüßen, Buffet auffüllen und Getränke nachfüllen.
- Mithilfe bei der Vorbereitung und dem Abbau des Frühstücksbuffets sowie Abstimmung mit der Küche.
- Gästewünsche am Frühstück entgegennehmen und bei Sonderwünschen die Kolleg:innen informieren.
- Kontrolle der Buffetqualität (Frische, Vollständigkeit) und Nachfüllen der Stationen während des Betriebs.

### `BAF` — BAF / Servicebereich

| Field | Nilai |
|-------|-------|
| Department | F&B |
| Lernfeld | Gästeservice und Kommunikation |
| Keywords | baf, service, restaurant, gästebetreuung |

**Default activities**

- Service und Vorbereitung im BAF-Bereich

**Template teks Jerman (pool generator)**

- Mithilfe im BAF-Bereich: Service und Vorbereitung gemäß Dienstplan.
- Unterstützung bei Gästebetreuung und Abläufen im Frühstücks-/Servicebereich BAF.
- Abstimmung mit dem Team zu Arbeitsabläufen und Übergabe am Schichtende.

## Housekeeping

Housekeeping / Zimmerreinigung

### `Housekeeping` — Housekeeping · alias: `HK`

| Field | Nilai |
|-------|-------|
| Department | Housekeeping |
| Lernfeld | Wirtschafts- und Sozialprozesse |
| Keywords | zimmer, housekeeping, hk, bett, reinigung, wäsche |

**Default activities**

- Zimmerreinigung nach Hotelstandard

**Template teks Jerman (pool generator)**

- Zimmerreinigung und Kontrolle der Zimmerausstattung nach Hotelstandard.
- Unterstützung bei der Bettenaufbereitung und Nachfüllen der Verbrauchsmaterialien.
- Gemeinsame Kontrolle von Störungen und Meldung an die Rezeption.
- Sortierung und Vorbereitung von Wäsche sowie Unterstützung bei der Etagenorganisation.

## Tagungen

Tagung / Veranstaltung / MEP

### `Tagungen` — Tagungsbetreuung

| Field | Nilai |
|-------|-------|
| Department | Tagung |
| Lernfeld | Veranstaltungen und Tagungsbetreuung |
| Keywords | tagung, coffee, konferenz, mep, pausen, coffee-break |

**Default activities**

- Tagungsbetreuung und Pausenversorgung

**Template teks Jerman (pool generator)**

- Betreuung der Tagungsteilnehmer: Getränke, Pausenversorgung und technische Rückmeldungen.
- Nachbereitung der Tagungsräume nach Veranstaltungsende.
- Unterstützung bei Coffee-Breaks und Umräumen der Säle.
- Kontrolle der Tagungsausstattung (Blöcke, Stifte, Wasser) während der Veranstaltung.

### `BRE+TG MEP` — Frühstück & Tagungsvorbereitung MEP

| Field | Nilai |
|-------|-------|
| Department | Tagung / F&B |
| Lernfeld | Veranstaltungen und Tagungsbetreuung |
| Keywords | bre, mep, tagungsvorbereitung, frühstück, bestuhlung |

**Default activities**

- Vorbereitung Frühstück und Tagungsräume (MEP)

**Template teks Jerman (pool generator)**

- Vorbereitung des Frühstücks und der Tagungsräume (MEP) inkl. Bestuhlung und Grundausstattung.
- Aufbau und Dekoration der Tagungstische sowie Bereitstellung von Getränken für die Teilnehmer.
- Abstimmung mit dem Tagungsteam zu Beginn und während der Veranstaltung.

### `FS2` — Frühschicht Frühstück & Tagung

| Field | Nilai |
|-------|-------|
| Department | F&B / Tagung |
| Lernfeld | Veranstaltungen und Tagungsbetreuung |
| Keywords | fs2, frühschicht, tagung, frühstück |

**Default activities**

- Frühschicht im Bereich Frühstück und Tagung

**Template teks Jerman (pool generator)**

- Frühschicht im Bereich Frühstück und Tagung mit wechselnden Einsätzen nach Dienstplan.
- Unterstützung bei der Übergabe zwischen Frühstücks- und Tagungsteam während der Schicht.

## Berufsschule

Berufsschule / schulischer Lernort

### `Schule` — Berufsschule

| Field | Nilai |
|-------|-------|
| Department | Berufsschule |
| Lernfeld | Lernfeld Berufsschule |
| Keywords | schule, unterricht, berufsschule, klassenarbeit |

**Default activities**

- Berufsschulunterricht

**Template teks Jerman (pool generator)**

- Unterricht in der Berufsschule: Theorie zu Hotelfachmann/-frau, Rechnungswesen und Fachkunde.
- Bearbeitung von Übungsaufgaben und Vorbereitung auf anstehende Klassenarbeiten.
- Fachpraktische Übungen und Projektarbeit im schulischen Lernfeld.

## (tanpa Abteilung / skip BLok)

Frei / Ausgang — tidak diisi ke BLok

**Tidak diisi ke BLok.**

### `frei` — Frei / Ausgang · alias: `Ausgang`

| Field | Nilai |
|-------|-------|
| Department | - |
| Lernfeld | - |
| Keywords | frei, ausgang, libur |

**Default activities**

- Frei / Ausgang laut Dienstplan

**Template teks Jerman (pool generator)**

- Frei / Ausgang laut Dienstplan — kein betrieblicher Ausbildungsnachweis.
