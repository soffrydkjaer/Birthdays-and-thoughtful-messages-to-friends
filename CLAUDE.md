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

## Sådan skal beskederne lyde
- På **dansk**, medmindre `notes` siger andet (fx svensk/engelsk for nogle venner).
- Varm, personlig og kort (1-3 sætninger) — som en sms fra en ven, ikke et kort.
- Brug fornavn. Variér formuleringerne; læs `recent_messages` og gentag ikke.
- Brug `notes`, hvis der står noget, til at gøre beskeden konkret.
- Check-ins skal variere mellem fx: "Hvordan har du det?", "Hvordan går det
  med …?", "Jeg kom lige til at tænke på dig", et minde, et forslag om at ses.
  Stil gerne et åbent spørgsmål, så det er let at svare.
- Familie kan være lidt mere intim; mor/far gerne med et "kh" eller hjerte.
- Max én emoji, og ikke altid.

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
