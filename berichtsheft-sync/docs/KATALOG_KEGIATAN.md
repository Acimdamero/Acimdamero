# Katalog kegiatan per Abteilung

> File sumber (edit di sini): [`data/katalog_abteilung.json`](../data/katalog_abteilung.json)

Sumber kebenaran kegiatan per Abteilung, termasuk conditions per code. templates_de tetap pool default. Edit conditions di file ini (id, label_de, when, texts_de) → jalankan: python3 -m berichtsheft catalog --reload --write-md

Setelah edit JSON:

```bash
python3 -m berichtsheft catalog --reload
python3 -m berichtsheft catalog --write-md   # regenerasi file ini
```

## Conditions bearbeiten

Conditions (variabel situasi) diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) pada array `conditions` setiap code. Field `templates_de` tetap pool default dan tetap kompatibel dengan generator yang ada.

Matcher `when` (semua opsional, `null` = any):

| Key | Nilai |
|-----|--------|
| day_type | `arbeit`, `schule`, `frei`, atau `null` |
| weekday | `mo`, `di`, `mi`, `do`, `fr`, `sa`, `so`, atau `null` |
| time_band | `frueh`, `spaet`, `nacht`, `any` |
| guest_situation | array tag situasi tamu |
| tags | array tag tugas |

Setiap condition punya `id` (slug), `label_de`, `when`, dan `texts_de` (2–4 kalimat Jerman). Generator nanti memilih teks dari condition yang `when`-nya cocok; sampai saat itu `templates_de` tetap sumber kalimat default.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `buffet-andrang` — Buffetandrang am Morgen
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=buffet, andrang`
  - Während des Frühstücksandrangs Gäste begrüßen, freie Plätze anbieten und das Buffet laufend nachfüllen.
  - Getränkestationen für Kaffee, Tee und Saft im Stoßbetrieb kontrollieren und leere Kannen sofort austauschen.
  - Die Küche über zur Neige gehende Speisen informieren und die Laufwege am Buffet freihalten.
- `buffet-aufbau` — Aufbau und Abbau des Buffets
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=aufbau, abbau, tags=buffet`
  - Das Frühstücksbuffet vor der Öffnung aufbauen und Geschirr, Besteck sowie Speisenstationen nach Hotelstandard platzieren.
  - Die Kühlkette und die Frische leicht verderblicher Speisen beim Aufbau prüfen.
  - Nach Betriebsschluss das Buffet abbauen, Reste fachgerecht entsorgen und die Stationen für die nächste Schicht reinigen.
- `sonderwunsch` — Sonderwünsche am Frühstück
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=sonderwunsch, allergie`
  - Sonderwünsche und Hinweise zu Allergien am Frühstück aufnehmen und an die Küche weitergeben.
  - Alternative Speisen für Gäste mit Unverträglichkeiten anfordern und die Ausgabe kurz erklären.
  - Rückfragen zum Buffetangebot sachlich beantworten und bei Unsicherheit die Serviceleitung hinzuziehen.
- `ruhiges-fruehstueck` — Ruhiger Frühstücksbetrieb
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=ruhig, tags=fruehstueck`
  - Bei geringem Gästeaufkommen Buffetqualität, Tischsauberkeit und Getränkevorrat in Ruhe kontrollieren.
  - Freie Tische abräumen, neu eindecken und die Stationen optisch ordnen.
  - Mise en Place und Restarbeiten für die folgende Frühstücksschicht vorbereiten.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `service-vorbereitung` — Vorbereitung im Service
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=vorbereitung, tags=mise-en-place, service`
  - Den Servicebereich BAF vorbereiten und Gedecke, Getränke sowie Arbeitsplätze gemäß Dienstplan herrichten.
  - Besteck, Gläser und Servietten kontrollieren und fehlende Teile nachlegen.
  - Den Ablauf der Schicht mit dem Team abstimmen, bevor die Gäste eintreffen.
- `gaestebetreuung` — Gästebetreuung im Service
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=service, gast, tags=baf`
  - Gäste im BAF-Bereich begrüßen, Bestellungen aufnehmen und Speisen sowie Getränke servieren.
  - Während des Service auf Nachbestellungen achten und abgeräumtes Geschirr zeitnah abtragen.
  - Bei Fragen zur Speisekarte die Kolleg:innen oder die Küche hinzuziehen.
- `schichtuebergabe` — Übergabe am Schichtende
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=uebergabe, tags=schichtende`
  - Offene Tische, Reservierungen und besondere Gästewünsche für die Folgeschicht notieren.
  - Den Arbeitsplatz übergeben, Belege abstimmen und den Bereich aufräumen.
  - In der Übergabe Störungen und noch offene Aufgaben mit dem Team durchsprechen.

## Rezeption

Rezeption / Empfang (Check-in, Check-out, Reservierung)

**Schwerpunkt:** conditions paling lengkap (Check-in Andrang, Check-out, Telefon, Reservierungsänderung, Beschwerde, Night Audit, ruhige Schicht, Gruppenanreise).

### `Rezeption` — Rezeption / Empfang · alias: `Rez`

| Field | Nilai |
|-------|-------|
| Department | Rezeption |
| Lernfeld | Gästeservice und Kommunikation / Empfang |
| Keywords | rezeption, empfang, check-in, check-out, reservierung, gäste, telefon, rez |

**Default activities**

- Empfangsdienst mit Check-in, Check-out und Reservierungen

**Template teks Jerman (pool generator)**

- Gäste am Empfang begrüßen, den Check-in durchführen und die Schlüsselkarte aushändigen.
- Check-out abwickeln, die Rechnung erläutern und offene Posten sachlich mit dem Gast klären.
- Reservierungen aufnehmen, ändern und im System bestätigen sowie die Verfügbarkeit prüfen.
- Telefonate entgegennehmen, Anliegen notieren und an die zuständige Stelle weiterleiten.
- Gästewünsche entgegennehmen (Weckdienst, Taxi, Zusatzartikel) und an die zuständige Abteilung weitergeben.
- Unterstützung bei leichten Aufgaben des Night Audit: Tagesabschluss kontrollieren und offene Buchungen prüfen.
- Schlüsselkarten programmieren, ausgeben und bei Verlust nach den Hausregeln neu erstellen.
- Beschwerden ruhig und sachlich aufnehmen, eine Lösung anbieten und die Schichtleitung informieren.

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `check-in-rush` — Check-in Andrang
  - when: `day_type=arbeit, weekday=any, time_band=spaet, guest_situation=check-in, andrang, tags=empfang`
  - Im Check-in-Andrang Gäste zügig begrüßen, die Reservierung prüfen und den Check-in im System abschließen.
  - Schlüsselkarten programmieren, den WLAN-Hinweis und die Frühstückszeiten nennen und die Warteschlange freundlich steuern.
  - Ausweise und Zahlungsdaten auch bei vollem Empfang sorgfältig erfassen.
  - Kolleg:innen bei gleichzeitigem Andrang unterstützen und Gäste mit längerer Wartezeit kurz informieren.
- `check-out` — Check-out
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=check-out, rechnung, tags=empfang`
  - Den Check-out durchführen, die Rechnung Position für Position erläutern und die Zahlung verbuchen.
  - Offene Posten wie Minibar oder Spa sachlich mit dem Gast klären und bei Bedarf die Fachabteilung fragen.
  - Die Schlüsselkarte einziehen, den Zimmerstatus auf abgereist setzen und den Gast verabschieden.
  - Bei frühem Check-out die Gepäckaufbewahrung anbieten und die Abreise im System vollständig abschließen.
- `phone` — Telefon
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=telefon, tags=anruf`
  - Anrufe mit der Hotelbegrüßung annehmen, das Anliegen notieren und an die zuständige Stelle weiterleiten.
  - Reservierungsanfragen am Telefon aufnehmen und die Verfügbarkeit im System prüfen.
  - Interne Gespräche mit Housekeeping, Küche oder Technik kurz und nachvollziehbar dokumentieren.
  - Bei gleichzeitigem Andrang am Tresen den Anrufer höflich um einen Moment bitten.
- `reservation-change` — Reservierungsänderung
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=reservierung, aenderung, tags=buchung`
  - Die bestehende Reservierung suchen und den Änderungswunsch zu Datum, Zimmertyp oder Personenzahl aufnehmen.
  - Die Verfügbarkeit prüfen, die Änderung im System speichern und die neue Bestätigung erläutern.
  - Eine Stornierung oder einen No-Show nach Hausregel kennzeichnen und Sonderfälle an die Schichtleitung geben.
  - Gruppen- oder Firmenreservierungen nur nach den hinterlegten Konditionen anpassen.
- `complaint` — Beschwerde
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=beschwerde, tags=reklamation`
  - Die Beschwerde ruhig anhören, den Sachverhalt wiederholen und eine konkrete Lösung anbieten.
  - Housekeeping, Technik oder den Service informieren und den Gast über den nächsten Schritt auf dem Laufenden halten.
  - Den Vorgang im Schichtbericht festhalten und die Schichtleitung einbinden.
  - Nach der Klärung nachfragen, ob das Anliegen für den Gast zufriedenstellend gelöst ist.
- `night-audit` — Night Audit
  - when: `day_type=arbeit, weekday=any, time_band=nacht, guest_situation=night-audit, tagesabschluss, tags=audit`
  - Beim Night Audit offene Buchungen, Zahlungen und den Zimmerstatus vor dem Tagesabschluss prüfen.
  - No-Shows und noch belegte Zimmer mit der Spätschicht abgleichen und im System kennzeichnen.
  - Tagesumsatz und offene Posten kontrollieren und Unstimmigkeiten der Schichtleitung melden.
  - Nach dem Abschluss die Listen für die Frühschicht und das Housekeeping bereitlegen.
- `quiet-shift` — Ruhige Schicht
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=ruhig, tags=vorbereitung`
  - In der ruhigen Phase die An- und Abreisen des Tages vorbereiten und die Gästelisten kontrollieren.
  - Schlüsselkarten, Formulare und Informationsmaterial am Empfang nachfüllen und den Tresen ordnen.
  - Offene E-Mails und Reservierungsanfragen bearbeiten und Rückfragen für die nächste Schicht notieren.
  - Hausinformationen zu Frühstück, Tagung und Technik mit den anderen Abteilungen abgleichen.
- `group-arrival` — Gruppenanreise
  - when: `day_type=arbeit, weekday=any, time_band=spaet, guest_situation=gruppe, anreise, tags=check-in`
  - Die Gruppenanreise vorbereiten und Zimmerliste, Schlüsselkarten sowie Willkommensunterlagen vor dem Eintreffen bereitlegen.
  - Die Reiseleitung begrüßen, die Zimmerverteilung abstimmen und den Check-in der Gruppe zügig durchführen.
  - Hinweise zu Anreisezeit, Gepäck und Frühstück an Housekeeping und den Service weitergeben.
  - Nach der Anreise die Belegung im System prüfen und fehlende Namen oder Zahlungsarten nachtragen.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `abreisezimmer` — Abreisezimmer
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=abreise, checkout-zimmer, tags=reinigung`
  - Abreisezimmer nach dem Check-out vollständig reinigen und die Ausstattung nach Hotelstandard kontrollieren.
  - Minibar, Safe und vergessene Gegenstände prüfen und Fundsachen an die Rezeption melden.
  - Den Zimmerstatus nach der Endkontrolle auf sauber setzen und die Rezeption informieren.
- `stayover` — Bleiberzimmer
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=stayover, bleiber, tags=reinigung`
  - Bleiberzimmer diskret reinigen, die Betten aufbereiten und Verbrauchsmaterialien nachfüllen.
  - Persönliche Gegenstände der Gäste nicht verlegen und den Hinweis Bitte nicht stören beachten.
  - Fehlende Handtücher oder Pflegeprodukte ergänzen und den Zimmerstatus aktualisieren.
- `waesche` — Wäsche und Etage
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=waesche, tags=etage`
  - Schmutzwäsche sortieren, den Wäschewagen bestücken und saubere Wäsche auf die Etage bringen.
  - Den Wäschebestand im Lager kontrollieren und Fehlmengen der Hausdame melden.
  - Das Etagenoffice aufräumen und die Reinigungsmittel nach Schichtplan auffüllen.
- `stoerung` — Störung melden
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=stoerung, tags=technik`
  - Defekte an Licht, Fernseher, Klima oder Sanitär im Zimmer festhalten und an Rezeption oder Technik melden.
  - Das Zimmer bis zur Freigabe kennzeichnen, damit es nicht vorzeitig verkauft wird.
  - Nach der Reparatur eine kurze Nachkontrolle durchführen und den Status an die Rezeption zurückmelden.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `coffee-break` — Coffee-Break
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=coffee-break, pause, tags=tagung`
  - Den Coffee-Break vor der Pause aufbauen und Heißgetränke, Kaltgetränke, Gebäck sowie Geschirr bereitstellen.
  - Während der Pause den Nachschub kontrollieren, Geschirr abräumen und die Station sauber halten.
  - Nach der Pause Reste abziehen und den Raum für den nächsten Programmpunkt herrichten.
- `raum-nachbereitung` — Nachbereitung Tagungsraum
  - when: `day_type=arbeit, weekday=any, time_band=spaet, guest_situation=nachbereitung, tags=tagungsraum`
  - Den Tagungsraum nach Veranstaltungsende abräumen, die Tische reinigen und die Bestuhlung zurückbauen.
  - Beamer, Mikrofon und Flipchart kontrollieren und Auffälligkeiten der Tagungsleitung melden.
  - Die Ausstattung auf Vollständigkeit prüfen und den Raum für die nächste Buchung vorbereiten.
- `saal-umraum` — Umräumen der Säle
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=umraum, bestuhlung, tags=saal`
  - Die Bestuhlung nach Plan auf parlamentarisch, Theater oder U-Form umbauen.
  - Tische, Stühle und Technik mit dem Tagungsteam abstimmen und die Fluchtwege freihalten.
  - Namensschilder, Blöcke und Wasser nach der neuen Ordnung erneut platzieren.
- `ausstattung-kontrolle` — Ausstattung während der Tagung
  - when: `day_type=arbeit, weekday=any, time_band=any, guest_situation=ausstattung, tags=tagung`
  - Während der Tagung Blöcke, Stifte und Wasser auf den Tischen kontrollieren und nachlegen.
  - Technische Rückmeldungen der Teilnehmer aufnehmen und an die zuständige Stelle weitergeben.
  - Raumtemperatur und Beleuchtung bei Bedarf mit der Technik oder der Tagungsleitung abstimmen.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `mep-bestuhlung` — Bestuhlung und Grundausstattung MEP
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=bestuhlung, tags=mep`
  - Die Tagungsräume im MEP nach Plan bestuhlen und Blöcke, Stifte und Wasser auflegen.
  - Technikanschlüsse und die Präsentationsfläche vor Beginn kurz prüfen.
  - Abweichungen vom Bestuhlungsplan mit dem Tagungsteam klären, bevor die Teilnehmer eintreffen.
- `mep-fruehstueck` — Frühstück und Tagungsgetränke
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=fruehstueck, getraenke, tags=mep`
  - Frühstücksbereich und Tagungsgetränke parallel vorbereiten und die Menge an die Teilnehmerzahl anpassen.
  - Kaffee, Tee und Wasser an den Tagungsstationen bereitstellen und rechtzeitig nachfüllen.
  - Offene Punkte zwischen Frühstück und Tagung im Team kurz festhalten.
- `mep-abstimmung` — Abstimmung mit dem Tagungsteam
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=abstimmung, tags=mep, tagung`
  - Zu Schichtbeginn Ablauf, Zeiten und besondere Wünsche mit dem Tagungsteam durchgehen.
  - Änderungen bei Pausenzeit oder Personenzahl aufnehmen und an Küche oder Service weitergeben.
  - Am Ende der Vorbereitung den Raum gemeinsam freigeben und offene Mängel notieren.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `fs2-fruehschicht` — Frühschicht Frühstück und Tagung
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=fruehschicht, tags=fs2`
  - Die Frühschicht FS2 beginnen und den Einsatzort Frühstück oder Tagung laut Dienstplan klären.
  - Je nach Einsatz das Buffet, den Tagungsraum oder beide Bereiche herrichten und die ersten Gäste betreuen.
  - Material und Getränke für den Vormittag bereitstellen und Fehlmengen sofort melden.
- `fs2-uebergabe` — Übergabe Frühstück zu Tagung
  - when: `day_type=arbeit, weekday=any, time_band=frueh, guest_situation=uebergabe, tags=fs2, tagung`
  - Offene Aufgaben, Uhrzeiten und Gästezahlen zwischen Frühstücks- und Tagungsteam übergeben.
  - Nach dem Frühstück in den Tagungsbereich wechseln und die Pausenversorgung unterstützen.
  - Zum Schichtende festhalten, was erledigt ist und was die nächste Schicht übernimmt.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `unterricht-theorie` — Theorieunterricht
  - when: `day_type=schule, weekday=any, time_band=any, tags=unterricht, theorie`
  - Im Theorieunterricht zu Hotelfach, Fachkunde und betrieblichen Abläufen mitarbeiten und mitschreiben.
  - Offene Fragen im Unterricht klären und den Bezug zu Service, Rezeption oder Housekeeping notieren.
  - Die behandelten Lerninhalte für den Ausbildungsnachweis verständlich zusammenfassen.
- `klassenarbeit` — Übung und Klassenarbeit
  - when: `day_type=schule, weekday=any, time_band=any, tags=klassenarbeit, uebung`
  - Übungsaufgaben zu Rechnungswesen und Fachkunde bearbeiten und die Ergebnisse vergleichen.
  - Den Stoff für eine anstehende Klassenarbeit wiederholen und Beispielaufgaben durchrechnen.
  - Die Rückmeldung der Lehrkraft zu Fehlern notieren und die Verbesserung für die nächste Stunde planen.
- `projekt-schule` — Projektarbeit
  - when: `day_type=schule, weekday=any, time_band=any, tags=projekt`
  - Eine fachpraktische Übung oder Projektarbeit im schulischen Lernfeld durchführen.
  - Die Arbeitsschritte dokumentieren und das Ergebnis im Team vorstellen.
  - Den Bezug zum betrieblichen Ausbildungsplan herstellen und offene Punkte für die nächste Schulwoche notieren.

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

**Conditions** — diedit di [`data/katalog_abteilung.json`](../data/katalog_abteilung.json) (`conditions`).

- `freier-tag` — Freier Tag laut Dienstplan
  - when: `day_type=frei, weekday=any, time_band=any, tags=frei`
  - Frei laut Dienstplan — an diesem Tag findet kein betrieblicher Einsatz statt.
  - Es wird kein Ausbildungsnachweis geschrieben und nichts an BLok übergeben.
- `ausgang-samstag` — Ausgang am Samstag
  - when: `day_type=frei, weekday=sa, time_band=any, tags=ausgang, wochenende`
  - Ausgang am Samstag laut Dienstplan, ohne Tätigkeit im Betrieb.
  - Der Tag bleibt frei und wird nicht als Arbeitstag an BLok gemeldet.
