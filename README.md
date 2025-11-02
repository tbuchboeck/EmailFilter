# Email Sorter - Automatisches Email-Sortier-System

Ein automatisches Email-Sortier-System, das über GitHub Actions läuft und Emails basierend auf definierten Regeln in entsprechende Ordner sortiert.

## Features

- Läuft automatisch alle 30 Minuten auf GitHub Actions (kostenlos!)
- **Multi-Account-Unterstützung** (Gmail, Outlook, Easy Name, etc.)
- Sortiert Emails basierend auf konfigurierbaren Regeln
- **Intelligente Spam-Erkennung** (Hybrid: SpamAssassin + Regelbasiert)
- Unterstützt Filterung nach Absender und Betreff
- **Erhält gelesen/ungelesen-Status** der Emails
- Keine lokale Installation notwendig
- Sichere Speicherung von Credentials über GitHub Secrets
- Dry-Run Modus zum Testen
- Automatische Whitelist für False-Positive-Vermeidung
- **Spam-only-Modus** für Accounts ohne Regel-Sortierung

## Setup

### 1. Repository forken/klonen

Forke dieses Repository oder klone es in deinen eigenen GitHub Account.

### 2. Email-Regeln konfigurieren (optional)

Bearbeite die Datei `email_rules.json` nach deinen Wünschen:

```json
{
  "rules": [
    {
      "name": "Newsletter",
      "folder": "Newsletter",
      "conditions": {
        "from_contains": ["newsletter", "info@"],
        "subject_contains": ["newsletter", "weekly digest"]
      }
    }
  ]
}
```

**Regel-Struktur:**
- `name`: Name der Regel (für Logs)
- `folder`: Ziel-Ordner im Email-Account
- `conditions`: Bedingungen für das Matching
  - `from_contains`: Liste von Begriffen im Absender-Feld
  - `subject_contains`: Liste von Begriffen im Betreff

**Matching-Logik:** Eine Email wird verschoben, wenn **mindestens eine** Bedingung zutrifft (OR-Verknüpfung).

### 3. GitHub Secrets konfigurieren

Gehe zu deinem Repository auf GitHub:

1. `Settings` → `Secrets and variables` → `Actions`
2. Klicke auf `New repository secret`
3. Füge folgende Secrets hinzu:

| Secret Name | Beschreibung | Beispiel |
|-------------|--------------|----------|
| `EMAIL_USER` | Deine Email-Adresse | `deine.email@gmail.com` |
| `EMAIL_PASS` | Email-Passwort oder App-Password | `dein-app-passwort` |
| `IMAP_SERVER` | IMAP-Server (optional, Standard: imap.gmail.com) | `imap.gmail.com` |

### 4. Gmail App-Passwort erstellen (für Gmail-Nutzer)

Wenn du Gmail verwendest:

1. Gehe zu [Google Account Security](https://myaccount.google.com/security)
2. Aktiviere 2-Faktor-Authentifizierung (falls noch nicht aktiv)
3. Suche nach "App-Passwörter" oder gehe zu [App-Passwörter](https://myaccount.google.com/apppasswords)
4. Erstelle ein neues App-Passwort für "Mail"
5. Verwende dieses Passwort als `EMAIL_PASS` Secret

### 5. IMAP-Server für andere Provider

| Provider | IMAP Server |
|----------|-------------|
| Gmail | `imap.gmail.com` |
| Outlook/Hotmail | `outlook.office365.com` |
| Yahoo | `imap.mail.yahoo.com` |
| iCloud | `imap.mail.me.com` |
| GMX | `imap.gmx.net` |
| Web.de | `imap.web.de` |

## Multi-Account Setup (NEU! 🎉)

Du kannst jetzt mehrere Email-Konten gleichzeitig verwalten! Jedes Konto kann seine eigenen Regeln haben oder nur Spam-Filterung verwenden.

### Account-Konfiguration (`accounts.json`)

Alle Accounts werden in `accounts.json` konfiguriert:

```json
{
  "accounts": [
    {
      "id": "easyname",
      "name": "Easy Name Primary Account",
      "enabled": true,
      "imap_server": "imap.easyname.com",
      "email_user_secret": "EMAIL_USER",
      "email_pass_secret": "EMAIL_PASS",
      "rules_file": "email_rules_easyname.json",
      "spam_rules_file": "spam_rules.json",
      "spam_filtering_only": false
    },
    {
      "id": "gmail",
      "name": "Gmail Account",
      "enabled": true,
      "imap_server": "imap.gmail.com",
      "email_user_secret": "GMAIL_USER",
      "email_pass_secret": "GMAIL_PASS",
      "rules_file": "email_rules_gmail.json",
      "spam_rules_file": "spam_rules.json",
      "spam_filtering_only": false
    },
    {
      "id": "wife_account",
      "name": "Wife's Account (Spam Only)",
      "enabled": false,
      "imap_server": "imap.easyname.com",
      "email_user_secret": "WIFE_EMAIL_USER",
      "email_pass_secret": "WIFE_EMAIL_PASS",
      "rules_file": null,
      "spam_rules_file": "spam_rules.json",
      "spam_filtering_only": true
    }
  ]
}
```

### Account-Felder erklärt:

- **id**: Eindeutige ID für den Account (verwendet in Logs und CLI)
- **name**: Beschreibender Name
- **enabled**: `true` = Account wird verarbeitet, `false` = Account wird übersprungen
- **imap_server**: IMAP-Server-Adresse
- **email_user_secret**: Name des GitHub Secrets für den Benutzernamen
- **email_pass_secret**: Name des GitHub Secrets für das Passwort
- **rules_file**: Pfad zur Regeldatei (oder `null` für Spam-only)
- **spam_rules_file**: Pfad zur Spam-Regeldatei
- **spam_filtering_only**: `true` = Nur Spam-Filterung, keine Regel-Sortierung

### GitHub Secrets für Multi-Account

Füge für jeden Account separate Secrets hinzu:

| Account | Secret Name | Beispiel |
|---------|-------------|----------|
| Easy Name | `EMAIL_USER` | `deine@easyname.com` |
| Easy Name | `EMAIL_PASS` | `dein-passwort` |
| Gmail | `GMAIL_USER` | `deine@gmail.com` |
| Gmail | `GMAIL_PASS` | `dein-app-passwort` |
| Wife's Account | `WIFE_EMAIL_USER` | `frau@easyname.com` |
| Wife's Account | `WIFE_EMAIL_PASS` | `frau-passwort` |

### Separate Regeln pro Account

Jedes Konto kann seine eigene Regeldatei haben:

- `email_rules_easyname.json` - Regeln für Easy Name Account
- `email_rules_gmail.json` - Regeln für Gmail Account
- etc.

Du kannst auch die gleiche Regeldatei für mehrere Accounts verwenden!

### Neue Regeln für Gmail lernen

Um Regeln für dein Gmail-Konto zu lernen:

```bash
# Lokal testen (optional)
export GMAIL_USER="deine@gmail.com"
export GMAIL_PASS="dein-app-passwort"
python analyze_inbox.py gmail

# Oder via GitHub Actions:
# Actions → Analyze Inbox → Run workflow → Wähle "gmail" aus
```

Das Script analysiert deine Gmail Inbox und schlägt automatisch Regeln vor, die du in `email_rules_gmail.json` einfügen kannst!

### Spam-Only-Modus

Perfekt für Accounts, bei denen du nur Spam filtern willst:

1. Setze `"spam_filtering_only": true`
2. Setze `"rules_file": null`
3. Der Account verwendet nur Spam-Filterung, keine Regel-Sortierung

## Verwendung

### Automatische Ausführung

Der Email-Sorter läuft automatisch alle 30 Minuten über GitHub Actions. Nach dem Setup musst du nichts weiter tun!

### Manuelles Auslösen

1. Gehe zu `Actions` Tab in deinem Repository
2. Wähle den "Email Sorter" Workflow
3. Klicke auf `Run workflow`
4. Optional: Aktiviere "Dry run" zum Testen (verschiebt keine Emails)

### Logs überprüfen

1. Gehe zum `Actions` Tab
2. Klicke auf einen Workflow-Run
3. Sieh dir die Logs an um zu sehen, welche Emails sortiert wurden

## 🤖 Vollständig Automatisierte Wartung (NEU!)

Das System analysiert **automatisch jeden Sonntag** deine Inbox und erstellt **automatisch Pull Requests** mit neuen Filterregeln!

### Was passiert automatisch:
1. 📊 Inbox wird analysiert
2. 🤖 Neue Regeln werden **automatisch erstellt**
3. 🔀 **Pull Request wird automatisch erstellt**
4. ✅ Du musst nur noch **reviewen & mergen**

**Zero-Touch Email Management!** Das System fügt automatisch neue Regeln hinzu - du musst nur noch auf "Merge" klicken.

**➡️ [Komplette Anleitung in AUTOMATED_RULES.md](AUTOMATED_RULES.md)**
**➡️ [Alte Anleitung (manuell) in AUTOMATION.md](AUTOMATION.md)**

**Quick Setup:**
1. Repository Secrets setzen (EMAIL_USER, EMAIL_PASS, IMAP_SERVER)
2. GitHub Actions aktivieren
3. Fertig! Jede Woche kommen Vorschläge automatisch

## Lokales Testen

Du kannst das Script auch lokal testen:

```bash
# Dependencies installieren
pip install -r requirements.txt

# Umgebungsvariablen für alle konfigurierten Accounts setzen
export EMAIL_USER="deine@easyname.com"
export EMAIL_PASS="dein-passwort"
export GMAIL_USER="deine@gmail.com"
export GMAIL_PASS="dein-app-passwort"
export DRY_RUN="true"  # Optional: Nur simulieren

# Email-Sorter ausführen (alle enabled Accounts)
python sort_emails.py

# Inbox analysieren für spezifischen Account
python analyze_inbox.py gmail
python analyze_inbox.py easyname

# Inbox analysieren für alle enabled Accounts
python analyze_inbox.py
```

## Workflow-Zeitplan anpassen

Bearbeite `.github/workflows/sort-emails.yml` und ändere die Cron-Expression:

```yaml
schedule:
  - cron: '*/30 * * * *'  # Alle 30 Minuten
```

**Beispiele:**
- `'0 * * * *'` - Jede Stunde
- `'0 */6 * * *'` - Alle 6 Stunden
- `'0 9 * * *'` - Täglich um 9:00 Uhr
- `'0 9 * * 1'` - Jeden Montag um 9:00 Uhr

## Fehlerbehebung

### "Login failed"
- Überprüfe EMAIL_USER und EMAIL_PASS Secrets
- Bei Gmail: Verwende ein App-Passwort, kein normales Passwort
- Überprüfe, ob IMAP in deinem Email-Account aktiviert ist

### "Connection refused"
- Überprüfe den IMAP_SERVER
- Stelle sicher, dass IMAP im Email-Provider aktiviert ist

### Ordner werden nicht erstellt
- Manche Email-Provider erlauben keine Ordnererstellung über IMAP
- Erstelle die Ordner manuell in deinem Email-Client

## Sicherheit

- Credentials werden sicher als GitHub Secrets gespeichert
- GitHub Actions verwendet verschlüsselte Umgebungsvariablen
- Das Script läuft auf GitHub-Servern, nicht auf deinem PC
- GitHub Actions hat strikte Sicherheitsrichtlinien

## Kosten

Vollständig kostenlos! GitHub Actions bietet:
- 2.000 Minuten/Monat für private Repositories
- Unbegrenzte Minuten für öffentliche Repositories
- Dieser Workflow benötigt < 1 Minute pro Ausführung

## Erweiterte Konfiguration

### Nur bestimmte Emails verarbeiten

Bearbeite `sort_emails.py` und ändere die Suche:

```python
# Nur ungelesene Emails
messages = client.search(['UNSEEN'])

# Emails der letzten 24 Stunden
from datetime import datetime, timedelta
date = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
messages = client.search(['SINCE', date])
```

### Mehrere Bedingungen (AND-Verknüpfung)

Aktuell werden Bedingungen mit OR verknüpft. Für AND-Verknüpfung ändere in `sort_emails.py`:

```python
def check_rule_match(email_data, rule):
    conditions = rule.get('conditions', {})

    # Beide Bedingungen müssen erfüllt sein
    from_match = False
    subject_match = False

    from_contains = conditions.get('from_contains', [])
    if from_contains:
        email_from = email_data.get('from', '').lower()
        from_match = any(term.lower() in email_from for term in from_contains)

    subject_contains = conditions.get('subject_contains', [])
    if subject_contains:
        email_subject = email_data.get('subject', '').lower()
        subject_match = any(term.lower() in email_subject for term in subject_contains)

    return from_match and subject_match
```

## Spam-Erkennung

Das System enthält eine **intelligente Hybrid Spam-Erkennung**:

- SpamAssassin Header-Analyse (wenn vorhanden)
- Regelbasierte Erkennung (Blacklists, Keywords, Patterns)
- Automatische Whitelist für bekannte Absender
- Konfigurierbar über `spam_rules.json`

**Siehe [SPAM_DETECTION.md](SPAM_DETECTION.md) für Details!**

### Spam-Erkennung aktivieren/deaktivieren:

```json
{
  "enabled": true,
  "spam_folder": "Junk"
}
```

## Lizenz

MIT License - Frei verwendbar!

## Support

Bei Problemen:
1. Überprüfe die Workflow-Logs im Actions Tab
2. Teste lokal mit `DRY_RUN=true`
3. Erstelle ein GitHub Issue

## Beispiel-Output

```
2025-10-29 10:30:15 - INFO - Connecting to imap.gmail.com...
2025-10-29 10:30:16 - INFO - Successfully logged in
2025-10-29 10:30:16 - INFO - Selected INBOX
2025-10-29 10:30:17 - INFO - Found 42 emails to process
2025-10-29 10:30:17 - INFO - Email matches rule 'Newsletter': From: newsletter@example.com, Subject: Weekly Update -> Moving to Newsletter
2025-10-29 10:30:18 - INFO - Email matches rule 'Shopping': From: amazon.com, Subject: Your order has shipped -> Moving to Shopping
...
2025-10-29 10:30:17 - INFO - SPAM DETECTED: From: scammer@spam.ru, Subject: YOU WON $$$, Reason: Blacklisted domain: spam.ru -> Moving to Junk
...
2025-10-29 10:30:25 - INFO - ==================================================
2025-10-29 10:30:25 - INFO - Email Sorting Statistics:
2025-10-29 10:30:25 - INFO -   Processed: 42
2025-10-29 10:30:25 - INFO -   Moved: 15
2025-10-29 10:30:25 - INFO -   Spam detected: 3
2025-10-29 10:30:25 - INFO -   Errors: 0
2025-10-29 10:30:25 - INFO -   By folder:
2025-10-29 10:30:25 - INFO -     Newsletter: 8
2025-10-29 10:30:25 - INFO -     Shopping: 4
2025-10-29 10:30:25 - INFO -     Junk: 3
2025-10-29 10:30:25 - INFO -     Social: 3
2025-10-29 10:30:25 - INFO - ==================================================
```
