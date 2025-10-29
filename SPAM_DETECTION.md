# Spam-Erkennung

Das Email-Sortier-System enthält eine intelligente **Hybrid Spam-Erkennung**, die mehrere Methoden kombiniert.

## Features

### 1. **SpamAssassin Header-Analyse**
Nutzt vorhandene SpamAssassin-Bewertungen vom Mail-Server:
- `X-Spam-Flag: YES` → Automatisch als Spam markiert
- `X-Spam-Score` > Threshold → Als Spam erkannt

### 2. **Regelbasierte Erkennung**
- **Blacklist Domains**: Bekannte Spam-Domains (z.B. `*.ru`, `*.cn`)
- **Blacklist Keywords**: Spam-Begriffe im Betreff (GEWINN, VIAGRA, etc.)
- **Verdächtige Patterns**:
  - Nur Großbuchstaben im Betreff
  - Viele Ausrufezeichen `!!!`
  - Viele Dollarzeichen `$$$`
  - Mehrfache RE:/FW: Chains

### 3. **Whitelist-System** (Verhindert False Positives!)
- **Automatische Whitelist**: Alle Absender aus `email_rules.json` werden NIE als Spam markiert
- **Manuelle Whitelist**: Zusätzliche vertrauenswürdige Domains in `spam_rules.json`

### 4. **Header-Validierung**
Prüft auf fehlende wichtige Email-Header (Message-ID, Date)

## Konfiguration

### `spam_rules.json`

```json
{
  "enabled": true,                    // Spam-Erkennung aktivieren/deaktivieren
  "spam_folder": "Junk",              // Zielordner für Spam
  "spam_score_threshold": 5.0,        // SpamAssassin Score Threshold
  "check_spamassassin_headers": true, // SpamAssassin Headers prüfen

  "blacklist_domains": [
    "*.ru",                           // Wildcard: Alle .ru Domains
    "*.cn",
    "tempmail.com"
  ],

  "blacklist_keywords_subject": [
    "GEWINN",
    "VIAGRA",
    "Sie haben gewonnen"
  ],

  "suspicious_subject_patterns": [
    "^[A-ZÄÖÜ\\s!?]+$",               // Nur Großbuchstaben
    "!!!+",                            // Viele Ausrufezeichen
    "\\$\\$\\$+"                       // Viele Dollarzeichen
  ],

  "whitelist_domains": [
    "amazon.com",
    "paypal.com",
    "google.com"
  ]
}
```

## Wie es funktioniert

1. **Whitelist-Check** (ZUERST!):
   - Alle Absender aus `email_rules.json` → KEIN Spam
   - Alle Domains aus `whitelist_domains` → KEIN Spam

2. **SpamAssassin-Check**:
   - Falls Server SpamAssassin nutzt, werden die Header ausgewertet

3. **Regelbasierte Checks**:
   - Domain-Blacklist
   - Keyword-Blacklist
   - Pattern-Matching
   - Header-Validierung

4. **Ergebnis**:
   - **Spam erkannt** → In `Junk` Ordner verschieben
   - **Kein Spam** → Normale Regeln anwenden

## Statistiken

Die Logs zeigen detaillierte Spam-Statistiken:

```
Email Sorting Statistics:
  Processed: 42
  Moved: 15
  Spam detected: 3       ← Anzahl erkannter Spam-Emails
  Errors: 0
  By folder:
    Junk: 3              ← Spam-Emails
    Shopping/Amazon: 5
    ...
```

## Anpassung

### Neue Spam-Keywords hinzufügen:

```json
{
  "blacklist_keywords_subject": [
    "GEWINN",
    "DEIN_NEUES_KEYWORD"
  ]
}
```

### Domains zur Whitelist hinzufügen:

```json
{
  "whitelist_domains": [
    "vertrauenswuerdige-domain.com"
  ]
}
```

### Spam-Erkennung temporär deaktivieren:

```json
{
  "enabled": false
}
```

## False Positives vermeiden

**Automatischer Schutz:**
- Alle Absender aus deinen `email_rules.json` sind automatisch whitelisted
- Amazon, Ebay, LinkedIn, etc. werden NIE als Spam markiert

**Manueller Schutz:**
Füge vertrauenswürdige Domains zur `whitelist_domains` hinzu.

## SpamAssassin auf dem Server

Falls dein Mail-Server SpamAssassin nutzt:
- Das System erkennt und nutzt die SpamAssassin-Header automatisch
- Sehr genau und keine zusätzliche Konfiguration nötig

**Prüfen ob SpamAssassin aktiv ist:**
- Schau dir eine Email im Header an
- Suche nach `X-Spam-Score` oder `X-Spam-Flag`
- Falls vorhanden → SpamAssassin ist aktiv

## Performance

Die Spam-Erkennung ist sehr schnell:
- Keine externe API-Calls
- Keine ML-Modelle (keine lange Ladezeit)
- Läuft komplett lokal
- Minimal zusätzliche Rechenzeit

## Logs

Spam-Erkennungen werden detailliert geloggt:

```
SPAM DETECTED: From: scammer@spam-domain.ru, Subject: YOU WON $$$,
Reason: Blacklisted domain: spam-domain.ru -> Moving to Junk
```

## Testen

**Dry-Run Modus:**
```bash
export DRY_RUN=true
python sort_emails.py
```

Zeigt, welche Emails als Spam erkannt würden, ohne sie zu verschieben.
