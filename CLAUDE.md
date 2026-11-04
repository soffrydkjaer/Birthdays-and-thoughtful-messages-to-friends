# Omsorgs-agent: fødselsdage og "jeg tænkte på dig"

Formål: Hjælpe ejeren af dette repo med at være der for dem, de holder af — ved at huske
fødselsdage og jævnligt (hver 4.-6. uge) at række ud med en lille besked.

Agenten **sender ikke selv beskeder**. Den skriver færdige udkast, som ejeren
kan kopiere og sende fra sin telefon (SMS, Messenger, WhatsApp osv.).

## Filer
- `data/contacts.json` — personer: navn, gruppe (familie/venner), relation,
  fødselsdag (`MM-DD`, eller `null` hvis ukendt), `marked` (krydset af med (x)
  i den oprindelige liste), `notes` (fritekst: interesser, hvad der sker i
  deres liv, hvordan I plejer at skrive), evt. `"paused": true`.
- `data/state.json` — hvornår hver person sidst fik en besked og hvornår
  næste check-in er planlagt. Rediger ikke i hånden medmindre nødvendigt.
- `data/messages.jsonl` — log over alle foreslåede beskeder.
- `scripts/omsorg.py` — planlæggeren (se docstring).

## Daglig rutine (når agenten køres)
1. `python3 scripts/omsorg.py plan` (dato i Europe/Copenhagen; giv
   `--date YYYY-MM-DD` hvis containerens dato kan afvige).
2. For hver person i `birthdays_today`: skriv en fødselsdagshilsen.
   For hver i `checkins_due`: skriv en check-in-besked.
3. Log hver besked: `python3 scripts/omsorg.py record <id> birthday|checkin "<tekst>"`.
   Det planlægger automatisk næste check-in om 28-42 dage.
4. Skriv dagens oversigt til `daily/YYYY-MM-DD.md` (se format nedenfor).
5. `git add -A && git commit -m "Dagens beskeder YYYY-MM-DD" && git push`.
6. Send ejeren en push-notifikation med en kort opsummering
   (fx "🎂 Far har fødselsdag i dag · 💬 Sig hej til Rikke og Anker")
   og beskederne, klar til at kopiere. Ingen notifikation hvis der intet er.

`birthdays_upcoming` (inden for 7 dage) nævnes i oversigten som et heads-up,
især for familie (gave/opringning) — der skrives ikke besked til dem endnu.

## Hvem får hvad
- **Fødselsdagshilsen:** alle med en fødselsdag i `contacts.json`.
- **Check-in (hver 4.-6. uge):** alle med `"checkin": true` — som standard
  alle kvinder i familie og vennekreds (ikke mænd). Sæt `"checkin": false` for at stoppe check-ins
  til en person (fødselsdagshilsen fortsætter).

## Sådan skal beskederne lyde
- **Uformel tone, som når man skriver til en ven.** Ikke høfligt eller
  kort-agtigt — ingen "Kære …", "Jeg håber, du har det godt", "Med venlig hilsen".
  Gerne småt og hverdagsagtigt, som en sms.
- På dansk, medmindre `notes` siger andet. Kort: 1-3 sætninger.
- **Check-ins:** start med `checkin_greeting`, hvis den er sat (fx "Hej søde"),
  efterfulgt af komma. Er den `null`, start fx med "Hej [fornavn]" eller "Heey".
- **Fødselsdagshilsner:** brug ALDRIG "Hej søde". Start direkte med tillykke,
  fx "Tillykke med dagen, [fornavn]!".
- **Aldrig samme besked to gange i træk til samme person.** Læs
  `recent_messages` og skift både formulering, åbning (efter hilsenen) og
  vinkel. `record` afviser en tekst, der er identisk med en af de to seneste.
- Variér vinklen på check-ins: "hvordan har du det", "hvordan går det med …",
  "kom til at tænke på dig", et minde, et forslag om at ses/ringe.
  Slut gerne med et spørgsmål, så det er let at svare.
- Max én emoji, og ikke i hver besked. Brug `notes` til at gøre det konkret.

### Eksempler — check-ins
- Hej søde, kom lige til at tænke på dig! Hvordan har du det for tiden? 💛
- Hej søde, hvordan går det med dig? Føler det er alt for længe siden vi har snakket
- Hej søde, jeg sad lige og tænkte på dig. Hvad sker der i dit liv for tiden?
- Hej søde! Hvordan har du det? Skal vi ikke snart finde en dag og ses?
- Hej søde, bare et lille hej herfra 🙂 Hvordan går det med alt?
- Hej søde, har du haft en god uge? Fortæl mig lidt om hvad du går og laver

### Eksempler — fødselsdage
- Tillykke med dagen, Rikke! 🎉 Håber du bliver fejret helt vildt i dag
- Stort tillykke med fødselsdagen! Håber du får en dejlig dag med masser af kage og gode mennesker
- Tillykke med de mange år, Louise! Du fortjener den bedste dag 🥳
- Tillykke far! Håber du får en rigtig god dag. Kh
- Tillykke med dagen! Glæder mig til at fejre dig næste gang vi ses 🎂

## Format for `daily/YYYY-MM-DD.md`
```
# Beskeder YYYY-MM-DD

## 🎂 Fødselsdage i dag
**Navn** — tekst

## 💬 Check-ins
**Navn** — tekst

## 📅 Snart
- Navn: DD/MM (om N dage)
```

## Når ejeren giver besked
- "Jeg har skrevet med X" → `record <id> checkin "(skrevet selv)"`.
- "Sæt X på pause" → `"paused": true` i contacts.json.
- Nye personer/fødselsdage/noter → opdatér contacts.json (id = navn i
  små bogstaver med bindestreger, æ→ae, ø→oe, å→aa).
