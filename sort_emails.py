#!/usr/bin/env python3
"""
Automatisches Email-Sortier-System
Sortiert Emails basierend auf definierten Regeln in entsprechende Ordner
"""

import os
import json
import logging
import re
from datetime import datetime
from imapclient import IMAPClient
from email import message_from_bytes
from email.header import decode_header
from email.utils import parseaddr

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


def load_accounts(accounts_file='accounts.json'):
    """Lädt Account-Konfiguration aus JSON-Datei"""
    if not os.path.exists(accounts_file):
        logger.error(f"Accounts file {accounts_file} not found.")
        return {"accounts": []}

    with open(accounts_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_spam_rules(spam_rules_file='spam_rules.json'):
    """Lädt Spam-Erkennungs-Regeln aus JSON-Datei"""
    if not os.path.exists(spam_rules_file):
        logger.warning(f"Spam rules file {spam_rules_file} not found. Spam detection disabled.")
        return {"enabled": False}

    with open(spam_rules_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_whitelist_from_rules(rules_config):
    """
    Erstellt Whitelist aus email_rules.json um False Positives zu vermeiden

    WICHTIG: Ignoriert Regeln, die in Spam/Trash/Junk-Ordner verschieben!
    """
    whitelist = set()

    # Ordner die NICHT auf die Whitelist kommen sollen
    spam_folders = {
        'junk', 'spam', 'trash', 'deleted', 'gelöscht',
        'papierkorb', 'spamverdacht', 'quarantine'
    }

    for rule in rules_config.get('rules', []):
        # Prüfe Zielordner - wenn Spam/Trash/Junk -> NICHT whitelisten!
        target_folder = rule.get('folder', '').lower()

        # Prüfe ob Zielordner ein Spam/Trash-Ordner ist
        is_spam_folder = any(spam_word in target_folder for spam_word in spam_folders)

        if is_spam_folder:
            logger.debug(f"Skipping whitelist for spam/trash folder: {rule.get('folder')}")
            continue  # Diese Absender NICHT whitelisten!

        # Nur "gute" Ordner (Shopping, Newsletter, etc.) whitelisten
        conditions = rule.get('conditions', {})
        from_contains = conditions.get('from_contains', [])

        for email_pattern in from_contains:
            # Extrahiere Domain aus Email-Adressen oder verwende Pattern direkt
            if '@' in email_pattern:
                domain = email_pattern.split('@')[-1]
                whitelist.add(domain.lower())
            else:
                whitelist.add(email_pattern.lower())

    return whitelist


def extract_email_domain(from_address):
    """Extrahiert Domain aus Email-Adresse"""
    if not from_address:
        return ""

    # Parse Email-Adresse
    _, email = parseaddr(from_address)
    if '@' in email:
        return email.split('@')[-1].lower()
    return ""


def check_spamassassin_headers(email_msg, threshold=5.0):
    """Prüft SpamAssassin Headers falls vorhanden"""
    # X-Spam-Flag: YES/NO
    spam_flag = email_msg.get('X-Spam-Flag', '').upper()
    if spam_flag == 'YES':
        return True, "SpamAssassin Flag: YES"

    # X-Spam-Score
    spam_score = email_msg.get('X-Spam-Score', '')
    if spam_score:
        try:
            score = float(spam_score)
            if score >= threshold:
                return True, f"SpamAssassin Score: {score} >= {threshold}"
        except ValueError:
            pass

    return False, None


def is_spam(email_msg, email_data, spam_rules, whitelist):
    """
    Hauptfunktion zur Spam-Erkennung

    Returns:
        (is_spam, reason) - Tuple mit Boolean und Grund
    """
    if not spam_rules.get('enabled', False):
        return False, None

    from_address = email_data.get('from', '')
    subject = email_data.get('subject', '')
    domain = extract_email_domain(from_address)

    # 1. Whitelist-Check: Bekannte Absender sind NIEMALS Spam
    if domain and domain in whitelist:
        return False, None

    # 2. Spam-Rules Whitelist mit Domain-Matching (inkl. Subdomains)
    for pattern in spam_rules.get('whitelist_domains', []):
        pattern = pattern.lower()
        if not domain:
            continue
        # Exakte Domain-Match: paypal.com == paypal.com
        if pattern == domain:
            return False, None
        # Subdomain-Match: email.paypal.com ends with .paypal.com
        if domain.endswith('.' + pattern):
            return False, None

    # 3. SpamAssassin Header-Check
    if spam_rules.get('check_spamassassin_headers', True):
        is_spam_sa, reason = check_spamassassin_headers(
            email_msg,
            spam_rules.get('spam_score_threshold', 5.0)
        )
        if is_spam_sa:
            return True, reason

    # 4. Blacklist Domains
    for blacklist_domain in spam_rules.get('blacklist_domains', []):
        if blacklist_domain.startswith('*.'):
            # Wildcard Domain (z.B. *.ru)
            tld = blacklist_domain[2:]
            if domain.endswith(tld):
                return True, f"Blacklisted domain: {domain}"
        elif blacklist_domain.lower() in domain:
            return True, f"Blacklisted domain: {blacklist_domain}"

    # 5. Blacklist Keywords im Betreff
    subject_upper = subject.upper()
    for keyword in spam_rules.get('blacklist_keywords_subject', []):
        if keyword.upper() in subject_upper:
            return True, f"Spam keyword in subject: {keyword}"

    # 6. Verdächtige Betreff-Patterns
    for pattern in spam_rules.get('suspicious_subject_patterns', []):
        try:
            if re.search(pattern, subject):
                return True, f"Suspicious subject pattern: {pattern}"
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")

    # 7. Verdächtige From-Patterns
    for pattern in spam_rules.get('suspicious_from_patterns', []):
        try:
            if re.search(pattern, from_address):
                return True, f"Suspicious from pattern: {pattern}"
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")

    # 8. Fehlende wichtige Header
    for required_header in spam_rules.get('required_headers_missing', []):
        if not email_msg.get(required_header):
            return True, f"Missing required header: {required_header}"

    return False, None


def create_folder_if_not_exists(client, folder_name):
    """
    Erstellt einen IMAP-Ordner, falls er nicht existiert.
    Erstellt automatisch auch Parent-Ordner falls nötig.
    """
    try:
        folders = client.list_folders()

        # Get the folder separator from the server
        separator = '/'  # Default
        if folders:
            # Extract separator from first folder info
            first_folder = folders[0]
            if len(first_folder) >= 2 and first_folder[1]:
                sep = first_folder[1]
                if isinstance(sep, bytes):
                    sep = sep.decode('utf-8', errors='ignore')
                if sep:  # Only use if not empty
                    separator = sep

        # Extract existing folder names
        existing_folders = set()
        for folder_info in folders:
            name = folder_info[2]
            if isinstance(name, bytes):
                name = name.decode('utf-8', errors='ignore')
            existing_folders.add(name)

        # Check if folder already exists
        if folder_name in existing_folders:
            return True

        # Split folder path and create parent folders first
        parts = folder_name.split('/')

        # Create each level of the hierarchy
        for i in range(len(parts)):
            partial_path = separator.join(parts[:i+1])

            if partial_path not in existing_folders:
                logger.info(f"Creating folder: {partial_path}")
                try:
                    client.create_folder(partial_path)
                    existing_folders.add(partial_path)
                    # Subscribe to folder so it's visible in webmail
                    try:
                        client.subscribe_folder(partial_path)
                        logger.info(f"Subscribed to folder: {partial_path}")
                    except Exception as sub_error:
                        logger.warning(f"Could not subscribe to {partial_path}: {sub_error}")
                except Exception as create_error:
                    logger.warning(f"Could not create folder {partial_path}: {create_error}")
                    # Continue anyway - maybe it exists but wasn't in the list

        return True
    except Exception as e:
        logger.error(f"Error creating folder {folder_name}: {e}")
        return False


def sort_emails(imap_server, email_user, email_pass, rules_config, dry_run=False,
                spam_rules_file='spam_rules.json', spam_filtering_only=False):
    """
    Hauptfunktion zum Sortieren von Emails

    WICHTIG: Verwendet BODY.PEEK[] um den gelesen/ungelesen-Status zu erhalten!

    Args:
        imap_server: IMAP Server-Adresse
        email_user: Email-Benutzername
        email_pass: Email-Passwort
        rules_config: Dictionary mit Sortier-Regeln
        dry_run: Wenn True, werden keine Emails verschoben (nur Simulation)
        spam_rules_file: Pfad zur Spam-Regeln-Datei
        spam_filtering_only: Wenn True, werden nur Spam-Regeln angewendet (keine normalen Regeln)
    """
    # Spam-Regeln laden
    spam_rules = load_spam_rules(spam_rules_file)
    spam_enabled = spam_rules.get('enabled', False)

    # Whitelist aus email_rules.json erstellen
    whitelist = build_whitelist_from_rules(rules_config)
    logger.info(f"Built whitelist with {len(whitelist)} entries")

    if spam_enabled:
        logger.info("Spam detection enabled")
    else:
        logger.info("Spam detection disabled")

    stats = {
        'processed': 0,
        'moved': 0,
        'spam_detected': 0,
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

                    # SPAM-CHECK ZUERST! (vor normalen Regeln)
                    if spam_enabled:
                        spam_detected, spam_reason = is_spam(email_msg, email_data, spam_rules, whitelist)

                        if spam_detected:
                            spam_folder = spam_rules.get('spam_folder', 'Junk')
                            logger.info(
                                f"SPAM DETECTED: "
                                f"From: {email_data['from'][:50]}, "
                                f"Subject: {email_data['subject'][:50]}, "
                                f"Reason: {spam_reason} "
                                f"-> Moving to {spam_folder}"
                            )

                            if not dry_run:
                                create_folder_if_not_exists(client, spam_folder)
                                client.copy([msg_id], spam_folder)
                                client.delete_messages([msg_id])
                                client.expunge()

                                stats['spam_detected'] += 1
                                stats['moved'] += 1
                                stats['by_folder'][spam_folder] = stats['by_folder'].get(spam_folder, 0) + 1
                            else:
                                logger.info(f"[DRY RUN] Would move spam to {spam_folder}")
                                stats['spam_detected'] += 1
                                stats['moved'] += 1
                                stats['by_folder'][spam_folder] = stats['by_folder'].get(spam_folder, 0) + 1

                            continue  # Nächste Email

                    # Normale Regeln durchgehen (nur wenn nicht als Spam erkannt und wenn nicht spam_filtering_only)
                    if not spam_filtering_only:
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
    """Hauptfunktion - verarbeitet alle konfigurierten Accounts"""
    dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'

    # Lade Account-Konfiguration
    accounts_config = load_accounts()
    accounts = accounts_config.get('accounts', [])

    if not accounts:
        logger.error("No accounts configured in accounts.json")
        return 1

    logger.info(f"Found {len(accounts)} configured account(s)")

    overall_stats = {
        'total_processed': 0,
        'total_moved': 0,
        'total_spam_detected': 0,
        'total_errors': 0,
        'accounts_processed': 0,
        'accounts_skipped': 0
    }

    # Verarbeite jeden Account
    for account in accounts:
        account_id = account.get('id', 'unknown')
        account_name = account.get('name', account_id)

        # Überspringe deaktivierte Accounts
        if not account.get('enabled', False):
            logger.info(f"Skipping disabled account: {account_name}")
            overall_stats['accounts_skipped'] += 1
            continue

        logger.info("=" * 70)
        logger.info(f"Processing account: {account_name} ({account_id})")
        logger.info(f"Description: {account.get('description', 'N/A')}")
        logger.info("=" * 70)

        # Hole Credentials aus Environment Variables
        email_user_secret = account.get('email_user_secret')
        email_pass_secret = account.get('email_pass_secret')

        if not email_user_secret or not email_pass_secret:
            logger.error(f"Account {account_id}: Missing credential secret names")
            overall_stats['accounts_skipped'] += 1
            continue

        email_user = os.getenv(email_user_secret)
        email_pass = os.getenv(email_pass_secret)

        if not email_user or not email_pass:
            logger.error(f"Account {account_id}: Credentials not found in environment ({email_user_secret}, {email_pass_secret})")
            overall_stats['accounts_skipped'] += 1
            continue

        # IMAP Server
        imap_server = account.get('imap_server')
        if not imap_server:
            logger.error(f"Account {account_id}: No IMAP server specified")
            overall_stats['accounts_skipped'] += 1
            continue

        # Spam filtering only?
        spam_filtering_only = account.get('spam_filtering_only', False)

        # Regeln laden (nur wenn nicht spam_filtering_only)
        rules_config = {"rules": []}
        if not spam_filtering_only:
            rules_file = account.get('rules_file')
            if rules_file:
                rules_config = load_rules(rules_file)
                logger.info(f"Loaded {len(rules_config.get('rules', []))} sorting rules from {rules_file}")
            else:
                logger.warning(f"Account {account_id}: No rules file specified, only spam filtering will be performed")
        else:
            logger.info(f"Account {account_id}: Spam filtering only mode")

        # Spam rules file
        spam_rules_file = account.get('spam_rules_file', 'spam_rules.json')

        # Email-Sortierung durchführen
        try:
            stats = sort_emails(
                imap_server=imap_server,
                email_user=email_user,
                email_pass=email_pass,
                rules_config=rules_config,
                dry_run=dry_run,
                spam_rules_file=spam_rules_file,
                spam_filtering_only=spam_filtering_only
            )

            # Statistiken für diesen Account ausgeben
            logger.info("-" * 50)
            logger.info(f"Statistics for {account_name}:")
            logger.info(f"  Processed: {stats['processed']}")
            logger.info(f"  Moved: {stats['moved']}")
            logger.info(f"  Spam detected: {stats['spam_detected']}")
            logger.info(f"  Errors: {stats['errors']}")
            if stats['by_folder']:
                logger.info("  By folder:")
                for folder, count in stats['by_folder'].items():
                    logger.info(f"    {folder}: {count}")
            logger.info("-" * 50)

            # Update overall stats
            overall_stats['total_processed'] += stats['processed']
            overall_stats['total_moved'] += stats['moved']
            overall_stats['total_spam_detected'] += stats['spam_detected']
            overall_stats['total_errors'] += stats['errors']
            overall_stats['accounts_processed'] += 1

        except Exception as e:
            logger.error(f"Email sorting failed for account {account_name}: {e}")
            overall_stats['accounts_skipped'] += 1
            continue

    # Gesamt-Statistiken ausgeben
    logger.info("=" * 70)
    logger.info("OVERALL STATISTICS (ALL ACCOUNTS):")
    logger.info(f"  Accounts processed: {overall_stats['accounts_processed']}")
    logger.info(f"  Accounts skipped: {overall_stats['accounts_skipped']}")
    logger.info(f"  Total emails processed: {overall_stats['total_processed']}")
    logger.info(f"  Total emails moved: {overall_stats['total_moved']}")
    logger.info(f"  Total spam detected: {overall_stats['total_spam_detected']}")
    logger.info(f"  Total errors: {overall_stats['total_errors']}")
    logger.info("=" * 70)

    return 0 if overall_stats['accounts_processed'] > 0 else 1


if __name__ == '__main__':
    exit(main())
