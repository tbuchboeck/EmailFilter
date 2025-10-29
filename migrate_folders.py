#!/usr/bin/env python3
"""
Migrates emails from root-level folders to INBOX subfolders
Merges newly created folders with existing INBOX subfolders
"""

import os
import sys
from imapclient import IMAPClient

# Konfiguration
imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
email_user = os.getenv('EMAIL_USER')
email_pass = os.getenv('EMAIL_PASS')

if not email_user or not email_pass:
    print("❌ Fehlende Credentials! Bitte setze EMAIL_USER und EMAIL_PASS")
    sys.exit(1)

# Mapping: source (root level) → target (INBOX subfolder)
FOLDER_MIGRATIONS = {
    'Shopping/Ofenersatzteileshop': 'INBOX/Shopping/Ofenersatzteileshop',
    'Shopping/SchuhSki': 'INBOX/Shopping/SchuhSki',
    'Shopping/Zalando': 'INBOX/Shopping/Zalando',
    'Shopping/Penoblo': 'INBOX/Shopping/Penoblo',
    'Shopping/E9': 'INBOX/Shopping/E9',
    'Shopping/Zooplus': 'INBOX/Shopping/Zooplus',
    'Contracts/Kreditkarte': 'INBOX/Contracts/Kreditkarte',
    'Contracts/EasyName': 'INBOX/Contracts/EasyName',
    'Career/WerLiefertWas': 'INBOX/Career/WerLiefertWas',
    'Sport/Outdooractive': 'INBOX/Sport/Outdooractive',
    'Games/Stardock': 'INBOX/Games/Stardock',
    'Finanzen/Wikifolio': 'INBOX/Finanzen/Wikifolio',
    'Finanzen/Etrade': 'INBOX/Finanzen/Etrade',
    'Hotel_Travel/Aminess': 'INBOX/Hotel_Travel/Aminess',
    'Newsletter/Yahoo_Fantasy': 'INBOX/Newsletter/Yahoo_Fantasy',
    'Newsletter/CodeGym': 'INBOX/Newsletter/CodeGym',
    'Linux_and_IT/Github': 'INBOX/Linux_and_IT/Github',
}

print(f"🔒 Verbinde zu {imap_server}...")

total_moved = 0

for source, target in FOLDER_MIGRATIONS.items():
    try:
        # Create new connection for each folder to avoid disconnection issues
        with IMAPClient(imap_server, ssl=True) as client:
            client.login(email_user, email_pass)
            print(f"\n📂 Migriere: {source} → {target}")

            # Check if source folder exists
            client.select_folder(source)
            messages = client.search(['ALL'])

            if not messages:
                print(f"   ℹ️  Keine E-Mails in {source}")
                continue

            print(f"   📧 {len(messages)} E-Mails gefunden")

            # Create target folder if it doesn't exist
            try:
                client.select_folder(target)
            except:
                print(f"   🔨 Erstelle Zielordner: {target}")
                # Create parent folders
                parts = target.split('/')
                for i in range(len(parts)):
                    partial = '/'.join(parts[:i+1])
                    try:
                        client.create_folder(partial)
                        client.subscribe_folder(partial)
                    except:
                        pass  # Folder might already exist

            # Move all emails
            client.select_folder(source)
            client.copy(messages, target)
            client.delete_messages(messages)
            client.expunge()

            total_moved += len(messages)
            print(f"   ✅ {len(messages)} E-Mails verschoben")

            # Don't delete source folders - let them be cleaned up manually
            # Deleting folders can cause IMAP disconnections

    except Exception as e:
        print(f"   ⚠️  Übersprungen: {e}")

print(f"\n" + "="*60)
print(f"✅ Migration abgeschlossen!")
print(f"📊 Gesamt verschoben: {total_moved} E-Mails")
print(f"💡 Hinweis: Leere Quellordner können Sie manuell löschen")
print("="*60)
