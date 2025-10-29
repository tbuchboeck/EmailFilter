# Inbox-Analyse ausführen

## Via GitHub Actions (EMPFOHLEN)

1. **Workflow-Datei hinzufügen** (nur einmalig):
   - Gehe zu: https://github.com/tbuchboeck/EmailFilter
   - Klicke auf `.github/workflows/` Ordner (oder erstelle ihn)
   - Klicke auf "Add file" → "Create new file"
   - Dateiname: `analyze-inbox.yml`
   - Kopiere den Inhalt aus `.github/workflows/analyze-inbox.yml` (in diesem Repo)
   - Klicke "Commit new file"

2. **Analyse starten**:
   - Gehe zu: https://github.com/tbuchboeck/EmailFilter/actions
   - Klicke auf "Analyze Inbox" Workflow
   - Klicke "Run workflow" → "Run workflow"
   - Warte ca. 1-2 Minuten
   - Klicke auf den Run um die Ergebnisse zu sehen

## Lokal ausführen

```bash
# 1. Credentials setzen
export IMAP_SERVER="imap.example.com"
export EMAIL_USER="deine@email.com"
export EMAIL_PASS="dein-passwort"

# 2. Script ausführen
python analyze_inbox.py
```

## Was zeigt die Analyse?

Die Analyse gibt dir:

### 📊 Statistiken
- Wie viele E-Mails werden gefiltert
- Wie viele werden als Spam erkannt
- Wie viele bleiben ungefiltert

### 📁 Top Zielordner
- Shopping/Amazon: 45 E-Mails
- Newsletter/Tech: 23 E-Mails
- etc.

### ❓ Ungefilterte E-Mails
Zeigt alle E-Mails, die KEINE Regel haben:
- Gruppiert nach Domain
- Mit Beispiel-Subjects
- **Automatische Regelvorschläge!**

### 💡 Regelvorschläge
Das Script schlägt automatisch neue Regeln vor:

```json
{
  "name": "Newsletter » Medium",
  "folder": "Newsletter/Medium",
  "conditions": {
    "from_contains": ["medium.com"]
  }
}
```

Diese kannst du direkt in deine `email_rules.json` kopieren!

## Beispiel-Output

```
📊 ANALYSE ERGEBNISSE
================================================================================

📧 Gesamt:              156 E-Mails
✅ Gefiltert:          89 E-Mails (57.1%)
🗑️  Als Spam erkannt:   12 E-Mails (7.7%)
❓ Ungefiltert:        55 E-Mails (35.3%)

📁 TOP 10 ZIELORDNER:
    18x → Shopping/Amazon
    12x → Newsletter/Tech
     9x → Career/LinkedIn
     ...

❓ UNGEFILTERTE E-MAILS:

📮 medium.com (8 E-Mails):
   From: Medium Daily Digest <noreply@medium.com>
   Subject: Your daily digest from Medium

   From: Medium Writers <writers@medium.com>
   Subject: New story recommendations

💡 VORSCHLÄGE FÜR NEUE REGELN:

# medium.com (8 E-Mails)
# Beispiel: Medium Daily Digest <noreply@medium.com>
{
  "name": "Newsletter » Medium",
  "folder": "Newsletter/Medium",
  "conditions": {
    "from_contains": ["medium.com"]
  }
},
```

## Nächste Schritte

1. **Analyse ausführen** (siehe oben)
2. **Regelvorschläge prüfen**
3. **Gewünschte Regeln in `email_rules.json` einfügen**
4. **Commit & Push**
5. **Fertig!** Die neuen Regeln werden beim nächsten Run angewendet
