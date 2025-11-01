#!/usr/bin/env python3
"""
Analysiert die Gmail-Ordnerstruktur und findet:
- Duplikate (ähnliche Namen)
- Leere Ordner
- Ordner mit wenig Emails
- Vorschläge zur Konsolidierung
"""

import os
import sys
import json
from imapclient import IMAPClient
from collections import defaultdict
import re

# Konfiguration aus accounts.json
def load_gmail_config():
    with open('accounts.json', 'r', encoding='utf-8') as f:
        accounts = json.load(f)

    for account in accounts['accounts']:
        if account['id'] == 'gmail':
            return account

    raise ValueError("Gmail account nicht in accounts.json gefunden!")

def normalize_folder_name(name):
    """Normalisiert Ordnernamen für Duplikat-Erkennung"""
    # Entferne INBOX/ prefix
    name = name.replace('INBOX/', '')
    # Kleinbuchstaben
    name = name.lower()
    # Entferne Leerzeichen, Bindestriche, Unterstriche
    name = re.sub(r'[\s\-_]+', '', name)
    return name

def find_similar_folders(folders):
    """Findet Ordner mit ähnlichen Namen"""
    normalized = {}
    for folder in folders:
        norm = normalize_folder_name(folder['name'])
        if norm not in normalized:
            normalized[norm] = []
        normalized[norm].append(folder['name'])

    # Finde Duplikate
    duplicates = {k: v for k, v in normalized.items() if len(v) > 1}
    return duplicates

def get_folder_hierarchy(folders):
    """Erstellt eine Hierarchie-Darstellung"""
    hierarchy = defaultdict(list)

    for folder in folders:
        name = folder['name']
        if '/' in name:
            parts = name.split('/')
            parent = '/'.join(parts[:-1])
            child = parts[-1]
            hierarchy[parent].append({'name': name, 'child': child, 'count': folder['count']})
        else:
            hierarchy['ROOT'].append({'name': name, 'child': name, 'count': folder['count']})

    return hierarchy

def suggest_consolidation(folders):
    """Schlägt Konsolidierungen vor"""
    suggestions = []

    # Finde Ordner mit nur einem Unterordner
    hierarchy = get_folder_hierarchy(folders)

    for parent, children in hierarchy.items():
        if parent != 'ROOT' and len(children) == 1 and children[0]['count'] < 50:
            suggestions.append({
                'type': 'single_child',
                'parent': parent,
                'child': children[0]['name'],
                'reason': f'Ordner "{parent}" hat nur einen Unterordner mit {children[0]["count"]} Emails',
                'suggestion': f'Verschiebe Emails direkt nach "{parent}" und lösche Unterordner'
            })

    # Finde leere oder fast leere Ordner
    for folder in folders:
        if folder['count'] == 0:
            suggestions.append({
                'type': 'empty',
                'folder': folder['name'],
                'reason': 'Ordner ist leer',
                'suggestion': 'Ordner löschen'
            })
        elif folder['count'] < 5 and '/' in folder['name']:
            suggestions.append({
                'type': 'almost_empty',
                'folder': folder['name'],
                'count': folder['count'],
                'reason': f'Ordner hat nur {folder["count"]} Emails',
                'suggestion': 'Überlege Zusammenführung mit übergeordnetem Ordner'
            })

    return suggestions

def main():
    print("🔍 Gmail Ordner-Analyse")
    print("="*80 + "\n")

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

            # Liste alle Ordner und zähle Emails
            folder_data = []
            all_folders = client.list_folders()

            print("📊 Analysiere Ordner (das kann etwas dauern)...\n")

            for folder_info in all_folders:
                flags, separator, name = folder_info

                # Decode name
                if isinstance(name, bytes):
                    name = name.decode('utf-8', errors='ignore')

                # Skip bestimmte System-Ordner
                if name in ['[Gmail]', '[Google Mail]']:
                    continue

                try:
                    # Wähle Ordner aus und zähle Emails
                    client.select_folder(name, readonly=True)
                    messages = client.search(['ALL'])
                    count = len(messages)

                    folder_data.append({
                        'name': name,
                        'count': count,
                        'flags': flags
                    })
                except Exception as e:
                    folder_data.append({
                        'name': name,
                        'count': 0,
                        'flags': flags,
                        'error': str(e)
                    })

            # Sortiere nach Anzahl (absteigend)
            folder_data.sort(key=lambda x: x['count'], reverse=True)

            # === AUSGABE ===

            print("📁 ALLE ORDNER (sortiert nach Anzahl):")
            print("="*80)
            total_emails = 0
            for folder in folder_data:
                if 'error' in folder:
                    print(f"  ⚠️  {folder['name']}: ERROR - {folder['error']}")
                else:
                    print(f"  📧 {folder['name']}: {folder['count']} Emails")
                    total_emails += folder['count']

            print(f"\n📊 Gesamt: {len(folder_data)} Ordner mit {total_emails} Emails")

            # Finde Duplikate
            print("\n\n🔍 MÖGLICHE DUPLIKATE:")
            print("="*80)
            duplicates = find_similar_folders(folder_data)

            if duplicates:
                for normalized, originals in duplicates.items():
                    counts = []
                    for orig in originals:
                        folder = next((f for f in folder_data if f['name'] == orig), None)
                        if folder:
                            counts.append(f"{orig} ({folder['count']} Emails)")
                    print(f"  ⚠️  Ähnlich: {', '.join(counts)}")
            else:
                print("  ✅ Keine offensichtlichen Duplikate gefunden")

            # Leere Ordner
            print("\n\n📭 LEERE ODER FAST LEERE ORDNER:")
            print("="*80)
            empty_folders = [f for f in folder_data if f['count'] < 5 and 'error' not in f]

            if empty_folders:
                for folder in empty_folders:
                    if folder['count'] == 0:
                        print(f"  🗑️  {folder['name']}: LEER")
                    else:
                        print(f"  ⚠️  {folder['name']}: {folder['count']} Emails")
            else:
                print("  ✅ Alle Ordner haben mindestens 5 Emails")

            # Konsolidierungs-Vorschläge
            print("\n\n💡 KONSOLIDIERUNGS-VORSCHLÄGE:")
            print("="*80)
            suggestions = suggest_consolidation(folder_data)

            if suggestions:
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"\n{i}. {suggestion['reason']}")
                    print(f"   → {suggestion['suggestion']}")
                    if suggestion['type'] != 'empty':
                        print(f"   📁 {suggestion.get('folder', suggestion.get('child', ''))}")
            else:
                print("  ✅ Keine Konsolidierungs-Vorschläge")

            # Speichere Ergebnis in JSON
            output = {
                'total_folders': len(folder_data),
                'total_emails': total_emails,
                'folders': folder_data,
                'duplicates': duplicates,
                'empty_folders': [f['name'] for f in folder_data if f['count'] == 0],
                'suggestions': suggestions
            }

            with open('gmail_folder_analysis.json', 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"\n\n💾 Detaillierte Analyse gespeichert in: gmail_folder_analysis.json")
            print("\nNächste Schritte:")
            print("  1. Schaue dir die Vorschläge an")
            print("  2. Führe python cleanup_gmail_folders.py aus um automatisch aufzuräumen")

    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
