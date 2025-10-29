# GitHub Workflow manuell hinzufügen

Aufgrund von GitHub-Sicherheitsrichtlinien muss die Workflow-Datei manuell hinzugefügt werden.

## Option 1: Über GitHub Web-Interface (Einfachste Methode)

1. Gehe zu deinem Repository auf GitHub
2. Klicke auf "Add file" → "Create new file"
3. Als Dateiname eingeben: `.github/workflows/sort-emails.yml`
4. Füge folgenden Inhalt ein:

```yaml
name: Email Sorter

on:
  # Zeitgesteuerte Ausführung - alle 30 Minuten
  schedule:
    - cron: '*/30 * * * *'

  # Manuelles Auslösen über GitHub UI
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (no actual moving of emails)'
        required: false
        default: 'false'
        type: choice
        options:
          - 'true'
          - 'false'

jobs:
  sort-emails:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run email sorter
        env:
          IMAP_SERVER: ${{ secrets.IMAP_SERVER }}
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          DRY_RUN: ${{ github.event.inputs.dry_run || 'false' }}
        run: python sort_emails.py

      - name: Upload logs (on failure)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: email-sorter-logs
          path: |
            *.log
          retention-days: 7
```

5. Klicke auf "Commit new file"

## Option 2: Lokal mit Git

1. Stelle sicher, dass du die neuesten Änderungen hast:
   ```bash
   git pull origin claude/github-actions-email-sorter-011CUbR5yYCqY7z1ztoe7AtY
   ```

2. Die Workflow-Datei existiert bereits lokal unter `.github/workflows/sort-emails.yml`

3. Füge sie manuell über GitHub Web hinzu (siehe Option 1) oder:
   ```bash
   git add .github/workflows/sort-emails.yml
   git commit -m "Add GitHub Actions workflow"
   git push
   ```

## Nach dem Hinzufügen

1. Gehe zum "Actions" Tab in deinem Repository
2. Du solltest den "Email Sorter" Workflow sehen
3. Konfiguriere die Secrets (siehe README.md)
4. Teste den Workflow mit "Run workflow" und aktiviere "dry_run"

## Troubleshooting

Falls der Workflow nicht erscheint:
- Überprüfe, ob Actions in den Repository-Einstellungen aktiviert sind
- Stelle sicher, dass die Datei genau unter `.github/workflows/sort-emails.yml` liegt
- Die Datei muss `.yml` Endung haben (nicht `.yaml`)
