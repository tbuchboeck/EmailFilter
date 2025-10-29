#!/usr/bin/env python3
"""
Zeigt alle IMAP-Ordner und den verwendeten Separator
"""

import os
import sys
from imapclient import IMAPClient

# Konfiguration aus Umgebungsvariablen
imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
email_user = os.getenv('EMAIL_USER')
email_pass = os.getenv('EMAIL_PASS')

if not email_user or not email_pass:
    print("❌ Fehlende Credentials! Bitte setze EMAIL_USER und EMAIL_PASS")
    sys.exit(1)

print(f"🔒 Verbinde zu {imap_server}...")

try:
    with IMAPClient(imap_server, ssl=True) as client:
        client.login(email_user, email_pass)
        print("✅ Erfolgreich eingeloggt\n")

        # Liste alle Ordner
        folders = client.list_folders()

        print("📁 ALLE ORDNER:")
        print("="*80)

        separators = set()
        folder_list = []

        for folder_info in folders:
            flags, separator, name = folder_info

            # Decode name wenn nötig
            if isinstance(name, bytes):
                name = name.decode('utf-8', errors='ignore')

            if isinstance(separator, bytes):
                separator = separator.decode('utf-8', errors='ignore')

            separators.add(separator)
            folder_list.append((name, separator, flags))

        # Sortiere und zeige Ordner
        folder_list.sort(key=lambda x: x[0])

        for name, separator, flags in folder_list:
            print(f"  {name}")
            if separator:
                print(f"    └─ Separator: '{separator}'")

        print(f"\n📊 Gesamt: {len(folder_list)} Ordner")
        print(f"🔧 Verwendete Separatoren: {separators}")

        # Suche nach Newsletter-Ordnern
        print("\n📮 NEWSLETTER-ORDNER:")
        print("="*80)
        newsletter_folders = [f for f in folder_list if 'newsletter' in f[0].lower()]

        if newsletter_folders:
            for name, separator, flags in newsletter_folders:
                print(f"  ✓ {name}")
        else:
            print("  ⚠️  Keine Newsletter-Ordner gefunden!")

        # Suche nach Career-Ordnern (für Xing)
        print("\n💼 CAREER-ORDNER:")
        print("="*80)
        career_folders = [f for f in folder_list if 'career' in f[0].lower()]

        if career_folders:
            for name, separator, flags in career_folders:
                print(f"  ✓ {name}")
        else:
            print("  ⚠️  Keine Career-Ordner gefunden!")

except Exception as e:
    print(f"❌ Fehler: {e}")
    sys.exit(1)
