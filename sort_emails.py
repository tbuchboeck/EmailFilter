#!/usr/bin/env python3
"""
Automatisches Email-Sortier-System
Sortiert Emails basierend auf definierten Regeln in entsprechende Ordner
"""

import os
import json
import logging
from datetime import datetime
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def decode_email_header(header):
    """Dekodiert Email-Header (Subject, From, etc.)"""
    if header is None:
        return ""

    decoded_parts = decode_header(header)
    decoded_string = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(encoding or 'utf-8', errors='replace')
        else:
            decoded_string += part

    return decoded_string


def load_rules(rules_file='email_rules.json'):
    """Lädt Email-Sortier-Regeln aus JSON-Datei"""
    if not os.path.exists(rules_file):
        logger.warning(f"Rules file {rules_file} not found. Using default rules.")
        return {
            "rules": [
                {
                    "name": "Newsletter",
                    "folder": "Newsletter",
                    "conditions": {
                        "from_contains": ["newsletter", "info@"],
                        "subject_contains": ["newsletter", "weekly digest"]
                    }
                },
                {
                    "name": "Social Media",
                    "folder": "Social",
                    "conditions": {
                        "from_contains": ["facebook.com", "twitter.com", "linkedin.com", "instagram.com"]
                    }
                },
                {
                    "name": "Shopping",
                    "folder": "Shopping",
                    "conditions": {
                        "from_contains": ["amazon", "ebay", "shop"],
                        "subject_contains": ["order", "shipped", "delivery"]
                    }
                }
            ]
        }

    with open(rules_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def check_rule_match(email_data, rule):
    """Prüft, ob eine Email einer Regel entspricht"""
    conditions = rule.get('conditions', {})

    # From-Bedingungen prüfen
    from_contains = conditions.get('from_contains', [])
    if from_contains:
        email_from = email_data.get('from', '').lower()
        if any(term.lower() in email_from for term in from_contains):
            return True

    # Subject-Bedingungen prüfen
    subject_contains = conditions.get('subject_contains', [])
    if subject_contains:
        email_subject = email_data.get('subject', '').lower()
        if any(term.lower() in email_subject for term in subject_contains):
            return True

    return False


def create_folder_if_not_exists(client, folder_name):
    """Erstellt einen IMAP-Ordner, falls er nicht existiert"""
    try:
        folders = client.list_folders()
        folder_exists = any(folder_name.encode() in folder[2] or folder_name in str(folder[2])
                          for folder in folders)

        if not folder_exists:
            logger.info(f"Creating folder: {folder_name}")
            client.create_folder(folder_name)

        return True
    except Exception as e:
        logger.error(f"Error creating folder {folder_name}: {e}")
        return False


def sort_emails(imap_server, email_user, email_pass, rules_config, dry_run=False):
    """
    Hauptfunktion zum Sortieren von Emails

    WICHTIG: Verwendet BODY.PEEK[] um den gelesen/ungelesen-Status zu erhalten!

    Args:
        imap_server: IMAP Server-Adresse
        email_user: Email-Benutzername
        email_pass: Email-Passwort
        rules_config: Dictionary mit Sortier-Regeln
        dry_run: Wenn True, werden keine Emails verschoben (nur Simulation)
    """
    stats = {
        'processed': 0,
        'moved': 0,
        'errors': 0,
        'by_folder': {}
    }

    try:
        # Verbindung zum IMAP-Server
        logger.info(f"Connecting to {imap_server}...")
        with IMAPClient(imap_server, ssl=True) as client:
            client.login(email_user, email_pass)
            logger.info("Successfully logged in")

            # INBOX auswählen
            client.select_folder('INBOX')
            logger.info("Selected INBOX")

            # Alle ungelesenen Emails abrufen (oder alle neueren Emails)
            # Hier: Emails der letzten 7 Tage
            messages = client.search(['NOT', 'DELETED'])
            logger.info(f"Found {len(messages)} emails to process")

            if not messages:
                logger.info("No emails to process")
                return stats

            # Emails abrufen und verarbeiten
            for msg_id in messages:
                try:
                    stats['processed'] += 1

                    # Email-Daten abrufen (PEEK um Flags nicht zu ändern!)
                    # FLAGS holen für späteren Restore
                    fetch_data = client.fetch([msg_id], ['FLAGS', 'BODY.PEEK[]'])

                    if msg_id not in fetch_data:
                        continue

                    # Flags speichern für später
                    msg_flags = fetch_data[msg_id].get(b'FLAGS', ())
                    raw_email = fetch_data[msg_id].get(b'BODY[]')

                    if not raw_email:
                        continue

                    # Email parsen
                    email_msg = message_from_bytes(raw_email)

                    email_data = {
                        'from': decode_email_header(email_msg.get('From', '')),
                        'subject': decode_email_header(email_msg.get('Subject', '')),
                        'date': email_msg.get('Date', '')
                    }

                    # Regeln durchgehen
                    matched_rule = None
                    for rule in rules_config.get('rules', []):
                        if check_rule_match(email_data, rule):
                            matched_rule = rule
                            break

                    if matched_rule:
                        target_folder = matched_rule['folder']
                        logger.info(
                            f"Email matches rule '{matched_rule['name']}': "
                            f"From: {email_data['from'][:50]}, "
                            f"Subject: {email_data['subject'][:50]} "
                            f"-> Moving to {target_folder}"
                        )

                        if not dry_run:
                            # Zielordner erstellen falls nötig
                            create_folder_if_not_exists(client, target_folder)

                            # Email verschieben
                            # copy() übernimmt automatisch die Flags
                            result = client.copy([msg_id], target_folder)

                            # Original aus INBOX löschen
                            client.delete_messages([msg_id])
                            client.expunge()

                            stats['moved'] += 1
                            stats['by_folder'][target_folder] = stats['by_folder'].get(target_folder, 0) + 1
                        else:
                            logger.info(f"[DRY RUN] Would move to {target_folder}")
                            stats['moved'] += 1
                            stats['by_folder'][target_folder] = stats['by_folder'].get(target_folder, 0) + 1

                except Exception as e:
                    logger.error(f"Error processing email {msg_id}: {e}")
                    stats['errors'] += 1
                    continue

            logger.info("Email sorting completed")

    except Exception as e:
        logger.error(f"IMAP connection error: {e}")
        raise

    return stats


def main():
    """Hauptfunktion"""
    # Konfiguration aus Umgebungsvariablen
    imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    # Validierung
    if not email_user or not email_pass:
        logger.error("EMAIL_USER and EMAIL_PASS environment variables must be set")
        return 1

    # Regeln laden
    rules_config = load_rules()
    logger.info(f"Loaded {len(rules_config.get('rules', []))} sorting rules")

    # Email-Sortierung durchführen
    try:
        stats = sort_emails(imap_server, email_user, email_pass, rules_config, dry_run)

        # Statistiken ausgeben
        logger.info("=" * 50)
        logger.info("Email Sorting Statistics:")
        logger.info(f"  Processed: {stats['processed']}")
        logger.info(f"  Moved: {stats['moved']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info("  By folder:")
        for folder, count in stats['by_folder'].items():
            logger.info(f"    {folder}: {count}")
        logger.info("=" * 50)

        return 0

    except Exception as e:
        logger.error(f"Email sorting failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
