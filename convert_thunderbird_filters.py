#!/usr/bin/env python3
"""
Konvertiert Thunderbird Filter-Export in email_rules.json Format
"""

import json
import sys
from urllib.parse import unquote

def extract_folder_name(folder_uri):
    """Extrahiert Ordnernamen aus IMAP URI"""
    # Format: imap://user@server/INBOX/Folder/Subfolder
    if not folder_uri:
        return None

    parts = folder_uri.split('/')
    if len(parts) < 4:
        return None

    # Alles nach dem Server-Teil nehmen
    folder_path = '/'.join(parts[3:])

    # URL-Dekodierung
    folder_path = unquote(folder_path)

    # INBOX/ entfernen, da wir direkt in Ordner verschieben
    if folder_path.startswith('INBOX/'):
        folder_path = folder_path[6:]
    elif folder_path == 'INBOX':
        return 'INBOX'
    elif folder_path.startswith('Trash'):
        return None  # Trash-Regeln ignorieren
    elif folder_path.startswith('Junk'):
        return None  # Junk-Regeln ignorieren

    return folder_path

def convert_filters(tb_data):
    """Konvertiert Thunderbird-Filter in unser Format"""
    rules = []

    for tb_filter in tb_data.get('filters', []):
        # Nur enabled Filter
        if not tb_filter.get('enabled', False):
            continue

        # Action-Typ prüfen
        actions = tb_filter.get('actionList', [])
        if not actions:
            continue

        # Nur Move-Actions (type: 1)
        move_action = None
        for action in actions:
            if action.get('type') == 1:
                move_action = action
                break

        if not move_action:
            continue  # Keine Move-Action, überspringen

        # Ordnername extrahieren
        folder = extract_folder_name(move_action.get('targetFolderUri', ''))
        if not folder:
            continue

        # Search Terms durchgehen
        from_contains = []
        subject_contains = []

        for term in tb_filter.get('searchTerms', []):
            attrib = term.get('attrib')
            value_obj = term.get('value', {})
            value_str = value_obj.get('str', '')

            if not value_str:
                continue

            # attrib 1 = From, attrib 6 = To/CC (auch als From behandeln)
            if attrib == 1 or attrib == 6:
                if value_str not in from_contains:
                    from_contains.append(value_str)
            # attrib 0 = Subject
            elif attrib == 0:
                if value_str not in subject_contains:
                    subject_contains.append(value_str)

        # Nur wenn Bedingungen vorhanden sind
        if not from_contains and not subject_contains:
            continue

        # Regel erstellen
        rule = {
            'name': tb_filter.get('filterName', folder),
            'folder': folder,
            'conditions': {}
        }

        if from_contains:
            rule['conditions']['from_contains'] = from_contains
        if subject_contains:
            rule['conditions']['subject_contains'] = subject_contains

        rules.append(rule)

    # Nach Ordnername sortieren für bessere Übersicht
    rules.sort(key=lambda r: r['folder'])

    return {'rules': rules}

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.json> <output.json>")
        return 1

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Thunderbird-Filter laden
    with open(input_file, 'r', encoding='utf-8') as f:
        tb_data = json.load(f)

    # Konvertieren
    converted = convert_filters(tb_data)

    print(f"Konvertiert: {len(converted['rules'])} Regeln")

    # Speichern
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)

    print(f"Gespeichert in: {output_file}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
