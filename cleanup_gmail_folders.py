#!/usr/bin/env python3
"""
Bereinigt Gmail-Ordnerstruktur basierend auf Analyse-Ergebnissen:
- Löscht leere Ordner
- Führt Duplikate zusammen
- Konsolidiert Ordner-Hierarchien

WICHTIG: Führe zuerst analyze_gmail_folders.py aus!
"""

import os
import sys
import json
from imapclient import IMAPClient

# Dry-Run Modus (auf True setzen zum Testen ohne Änderungen)
DRY_RUN = os.getenv('DRY_RUN', 'true').lower() in ['true', '1', 'yes']

def load_gmail_config():
    """Lade Gmail-Konfiguration aus accounts.json"""
    with open('accounts.json', 'r', encoding='utf-8') as f:
        accounts = json.load(f)

    for account in accounts['accounts']:
        if account['id'] == 'gmail':
            return account

    raise ValueError("Gmail account nicht in accounts.json gefunden!")

def move_emails(client, source_folder, target_folder):
    """Verschiebt alle Emails von source nach target"""
    try:
        # Wähle Quell-Ordner
        client.select_folder(source_folder, readonly=False)
        messages = client.search(['ALL'])

        if len(messages) == 0:
            print(f"      ℹ️  Keine Emails zu verschieben")
            return 0

        if DRY_RUN:
            print(f"      🔄 [DRY RUN] Würde {len(messages)} Emails verschieben")
            return len(messages)

        # Verschiebe Emails
        client.move(messages, target_folder)
        print(f"      ✅ {len(messages)} Emails verschoben")
        return len(messages)

    except Exception as e:
        print(f"      ❌ Fehler beim Verschieben: {e}")
        return 0

def delete_folder(client, folder_name):
    """Löscht einen Ordner"""
    try:
        if DRY_RUN:
            print(f"      🗑️  [DRY RUN] Würde Ordner löschen: {folder_name}")
            return True

        client.delete_folder(folder_name)
        print(f"      ✅ Ordner gelöscht: {folder_name}")
        return True

    except Exception as e:
        print(f"      ❌ Fehler beim Löschen von {folder_name}: {e}")
        return False

def cleanup_empty_folders(client, empty_folders):
    """Löscht alle leeren Ordner"""
    print("\n🗑️  LEERE ORDNER LÖSCHEN")
    print("="*80)

    # Filtere System-Ordner aus
    skip_folders = [
        '[Google Mail]/Spam',
        '[Google Mail]/Papierkorb',
        '[Google Mail]/Entwürfe',
        '[Google Mail]/Gesendet',
        '[Google Mail]/Markiert',
        'Trash',
        'Junk',
        'INBOX'
    ]

    # Sortiere nach Tiefe (tiefste zuerst), damit wir von unten nach oben löschen
    empty_folders.sort(key=lambda x: x.count('/'), reverse=True)

    deleted = 0
    skipped = 0

    for folder in empty_folders:
        # Skip System-Ordner
        if folder in skip_folders or any(folder.startswith(skip) for skip in skip_folders):
            print(f"  ⏭️  Überspringe System-Ordner: {folder}")
            skipped += 1
            continue

        print(f"\n  📁 {folder}")
        if delete_folder(client, folder):
            deleted += 1

    print(f"\n📊 Zusammenfassung:")
    print(f"  ✅ Gelöscht: {deleted}")
    print(f"  ⏭️  Übersprungen: {skipped}")

def merge_duplicates(client, duplicates):
    """Führt Duplikate zusammen"""
    print("\n🔀 DUPLIKATE ZUSAMMENFÜHREN")
    print("="*80)

    # Definiere welche Duplikate wie behandelt werden sollen
    merge_plan = {
        'shopping': {
            'source': 'Shopping',
            'target': 'INBOX/Shopping',
            'action': 'move_and_delete'
        },
        'google': {
            'folders': ['Google', 'INBOX/Google'],
            'action': 'delete_all'  # beide sind leer
        }
    }

    for key, plan in merge_plan.items():
        print(f"\n  📦 Behandle Duplikat: {key}")

        if plan['action'] == 'move_and_delete':
            source = plan['source']
            target = plan['target']

            print(f"    📁 Quelle: {source}")
            print(f"    📁 Ziel: {target}")

            moved = move_emails(client, source, target)

            if moved >= 0:  # Auch bei 0 Emails löschen wir den Ordner
                delete_folder(client, source)

        elif plan['action'] == 'delete_all':
            for folder in plan['folders']:
                print(f"    📁 {folder}")
                delete_folder(client, folder)

def consolidate_gaming_folders(client):
    """Konsolidiert INBOX/Gamez und INBOX/Gaming"""
    print("\n🎮 GAMING-ORDNER KONSOLIDIEREN")
    print("="*80)

    # Beide Ordner-Bäume sind leer, aber es gibt Duplikate
    # Entscheide: Behalte "INBOX/Gaming", lösche "INBOX/Gamez"

    folders_to_delete = [
        'INBOX/Gamez/Blizzard',
        'INBOX/Gamez/RockstarGames',
        'INBOX/Gamez/Smite',
        'INBOX/Gamez/Steam',
        'INBOX/Gamez/Ubisoft',
        'INBOX/Gamez'
    ]

    print("  ℹ️  Lösche INBOX/Gamez Struktur (leer, Duplikat von INBOX/Gaming)")

    for folder in folders_to_delete:
        print(f"\n  📁 {folder}")
        delete_folder(client, folder)

def cleanup_trash_subfolders(client):
    """Löscht alle Unterordner im Papierkorb"""
    print("\n🗑️  PAPIERKORB-UNTERORDNER LÖSCHEN")
    print("="*80)

    trash_folders = [
        '[Google Mail]/Papierkorb/0_Searches',
        '[Google Mail]/Papierkorb/Bing+MS',
        '[Google Mail]/Papierkorb/Ebay',
        '[Google Mail]/Papierkorb/Gitlab',
        '[Google Mail]/Papierkorb/Google',
        '[Google Mail]/Papierkorb/GoogleCal',
        '[Google Mail]/Papierkorb/Harry',
        '[Google Mail]/Papierkorb/HashiCorp',
        '[Google Mail]/Papierkorb/IMDB',
        '[Google Mail]/Papierkorb/Nintento',
        '[Google Mail]/Papierkorb/Pinterest',
        '[Google Mail]/Papierkorb/Tripadvisor',
        '[Google Mail]/Papierkorb/Twitch',
        '[Google Mail]/Papierkorb/Twitter'
    ]

    print("  ℹ️  Lösche unnötige Unterordner im Papierkorb")

    for folder in trash_folders:
        print(f"\n  📁 {folder}")
        delete_folder(client, folder)

def move_pierre_to_inbox(client):
    """Verschiebt Pierre-Ordner nach INBOX/Personal"""
    print("\n👤 PIERRE-ORDNER VERSCHIEBEN")
    print("="*80)

    source = 'Pierre'
    target = 'INBOX/Personal/Pierre'

    print(f"  📁 Quelle: {source}")
    print(f"  📁 Ziel: {target}")

    # Erstelle Ziel-Ordner falls nicht vorhanden
    try:
        if not DRY_RUN:
            client.create_folder(target)
            print(f"      ✅ Ziel-Ordner erstellt")
    except Exception as e:
        print(f"      ℹ️  Ziel-Ordner existiert bereits oder konnte nicht erstellt werden: {e}")

    # Verschiebe Emails
    moved = move_emails(client, source, target)

    # Lösche Quell-Ordner
    if moved >= 0:
        delete_folder(client, source)

def main():
    print("🧹 Gmail Ordner-Bereinigung")
    print("="*80)

    if DRY_RUN:
        print("⚠️  DRY RUN MODUS - Es werden KEINE Änderungen vorgenommen!")
        print("    Setze DRY_RUN=false um tatsächlich zu bereinigen\n")
    else:
        print("⚠️  WARNUNG: Dies wird Ordner löschen und Emails verschieben!")
        print("    Stelle sicher, dass du ein Backup hast!\n")

        # Skip confirmation in CI environment (GitHub Actions)
        is_ci = os.getenv('CI') or os.getenv('GITHUB_ACTIONS')

        if not is_ci:
            response = input("Fortfahren? (yes/no): ")
            if response.lower() != 'yes':
                print("Abgebrochen.")
                sys.exit(0)
        else:
            print("⚠️  CI-Modus erkannt - führe Bereinigung automatisch aus\n")

    # Lade Gmail-Konfiguration
    try:
        config = load_gmail_config()
        gmail_user = os.getenv(config['email_user_secret'])
        gmail_pass = os.getenv(config['email_pass_secret'])

        if not gmail_user or not gmail_pass:
            print(f"❌ Fehlende Credentials! Bitte setze {config['email_user_secret']} und {config['email_pass_secret']}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        sys.exit(1)

    print(f"🔒 Verbinde zu {config['imap_server']}...")

    try:
        with IMAPClient(config['imap_server'], ssl=True) as client:
            client.login(gmail_user, gmail_pass)
            print(f"✅ Erfolgreich eingeloggt als {gmail_user}\n")

            # Sammle leere Ordner aus vorheriger Analyse
            # Diese Liste basiert auf den Ergebnissen von analyze_gmail_folders.py
            empty_folders = [
                'Archives',
                'Google',
                'INBOX/Auto',
                'INBOX/Auto/INSTADRIVE',
                'INBOX/Gamez',
                'INBOX/Gamez/Blizzard',
                'INBOX/Gamez/RockstarGames',
                'INBOX/Gamez/Smite',
                'INBOX/Gamez/Steam',
                'INBOX/Gamez/Ubisoft',
                'INBOX/Gaming',
                'INBOX/Gaming/Blizzard',
                'INBOX/Gaming/Nintendo',
                'INBOX/Gaming/Steam',
                'INBOX/Gaming/Ubisoft',
                'INBOX/Google',
                'INBOX/Google/Accounts',
                'INBOX/Google/Cloud',
                'INBOX/Google/Maps',
                'INBOX/Google/Other',
                'INBOX/Microsoft',
                'INBOX/Microsoft/Bing',
                'INBOX/News',
                'INBOX/News/Microsoft-Start',
                'INBOX/Newsletter',
                'INBOX/Newsletter/Medium',
                'INBOX/Newsletter/RottenTomatoes',
                'INBOX/Personal',
                'INBOX/Pets',
                'INBOX/Shopping',
                'INBOX/Shopping/Blinkist',
                'INBOX/Sport',
                'INBOX/Tech',
                'INBOX/Tech/8x8',
                'INBOX/Tech/HashiCorp',
                'INBOX/Tech/IconScout',
                'INBOX/Travel',
                'INBOX/Travel/Komoot',
                'Mailspring',
                'Mailspring/Snoozed',
                'Notes'
            ]

            # Führe Bereinigungen durch
            print("\n" + "="*80)
            print("SCHRITT 1: Duplikate zusammenführen")
            print("="*80)
            merge_duplicates(client, {})

            print("\n" + "="*80)
            print("SCHRITT 2: Gaming-Ordner konsolidieren")
            print("="*80)
            consolidate_gaming_folders(client)

            print("\n" + "="*80)
            print("SCHRITT 3: Pierre-Ordner verschieben")
            print("="*80)
            move_pierre_to_inbox(client)

            print("\n" + "="*80)
            print("SCHRITT 4: Papierkorb-Unterordner löschen")
            print("="*80)
            cleanup_trash_subfolders(client)

            print("\n" + "="*80)
            print("SCHRITT 5: Leere Ordner löschen")
            print("="*80)
            cleanup_empty_folders(client, empty_folders)

            print("\n\n" + "="*80)
            print("✅ BEREINIGUNG ABGESCHLOSSEN!")
            print("="*80)

            if DRY_RUN:
                print("\nDies war ein DRY RUN. Keine Änderungen wurden vorgenommen.")
                print("Setze DRY_RUN=false um tatsächlich zu bereinigen:")
                print("  export DRY_RUN=false")
                print("  python cleanup_gmail_folders.py")
            else:
                print("\nDeine Gmail-Ordnerstruktur wurde bereinigt!")
                print("Führe 'python analyze_gmail_folders.py' erneut aus um das Ergebnis zu sehen.")

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
