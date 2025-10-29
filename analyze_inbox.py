#!/usr/bin/env python3
"""
Inbox Analyse Tool
Zeigt welche E-Mails von den aktuellen Regeln erfasst werden
und welche E-Mails noch keine passende Regel haben.
"""

import os
import sys
import json
import re
from collections import defaultdict, Counter
from email import message_from_bytes
from email.utils import parseaddr
from email.header import decode_header
from imapclient import IMAPClient

# Logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def decode_mime_words(s):
    """Dekodiert MIME-kodierte Strings"""
    if not s:
        return ""
    decoded_fragments = decode_header(s)
    result = []
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            if encoding:
                try:
                    result.append(fragment.decode(encoding))
                except:
                    result.append(fragment.decode('utf-8', errors='ignore'))
            else:
                result.append(fragment.decode('utf-8', errors='ignore'))
        else:
            result.append(str(fragment))
    return ''.join(result)


def extract_email_domain(email_address):
    """Extrahiert die Domain aus einer E-Mail-Adresse"""
    name, addr = parseaddr(email_address)
    if '@' in addr:
        return addr.split('@')[1].lower()
    return None


def load_rules(rules_file='email_rules.json'):
    """Lädt die E-Mail-Sortierregeln"""
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Rules file not found: {rules_file}")
        return {'rules': []}


def load_spam_rules(spam_file='spam_rules.json'):
    """Lädt die Spam-Erkennungsregeln"""
    try:
        with open(spam_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Spam rules file not found: {spam_file}")
        return {'enabled': False}


def check_rule_match(email_data, rule):
    """
    Prüft, ob eine E-Mail zu einer Regel passt

    Returns:
        bool: True wenn die Regel passt
    """
    conditions = rule.get('conditions', {})

    # From-Contains
    if 'from_contains' in conditions:
        for pattern in conditions['from_contains']:
            if pattern.lower() in email_data.get('from', '').lower():
                return True

    # Subject-Contains
    if 'subject_contains' in conditions:
        for pattern in conditions['subject_contains']:
            if pattern.lower() in email_data.get('subject', '').lower():
                return True

    # To-Contains
    if 'to_contains' in conditions:
        for pattern in conditions['to_contains']:
            if pattern.lower() in email_data.get('to', '').lower():
                return True

    return False


def is_spam_simple(email_data, spam_rules, whitelist_domains):
    """
    Einfache Spam-Prüfung (ohne volle Headeranalyse)
    """
    if not spam_rules.get('enabled', False):
        return False

    from_address = email_data.get('from', '')
    subject = email_data.get('subject', '')
    domain = extract_email_domain(from_address)

    # Whitelist Check
    for pattern in whitelist_domains:
        if domain and domain == pattern.lower():
            return False
        if domain and domain.endswith('.' + pattern.lower()):
            return False

    # Blacklist Domains
    for blacklist_domain in spam_rules.get('blacklist_domains', []):
        if blacklist_domain.startswith('*.'):
            tld = blacklist_domain[2:]
            if domain and domain.endswith(tld):
                return True
        elif blacklist_domain.lower() in (domain or ''):
            return True

    # Keyword Check
    subject_upper = subject.upper()
    for keyword in spam_rules.get('blacklist_keywords_subject', []):
        if keyword.upper() in subject_upper:
            return True

    return False


def analyze_inbox():
    """Hauptfunktion zur Inbox-Analyse"""

    # Lade Konfiguration
    imap_server = os.environ.get('IMAP_SERVER', 'imap.gmail.com')
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')

    if not email_user or not email_pass:
        logger.error("❌ Fehlende Credentials! Bitte setze EMAIL_USER und EMAIL_PASS")
        logger.info("\nUsage:")
        logger.info("  export IMAP_SERVER='imap.example.com'")
        logger.info("  export EMAIL_USER='user@example.com'")
        logger.info("  export EMAIL_PASS='password'")
        logger.info("  python analyze_inbox.py")
        sys.exit(1)

    # Lade Regeln
    rules_config = load_rules()
    spam_rules = load_spam_rules()
    rules = rules_config.get('rules', [])

    logger.info(f"📋 {len(rules)} Sortierregeln geladen")
    logger.info(f"🔒 Verbinde zu {imap_server}...")

    # Verbinde zu IMAP
    try:
        with IMAPClient(imap_server, use_uid=True, ssl=True) as client:
            client.login(email_user, email_pass)
            client.select_folder('INBOX', readonly=True)  # READ-ONLY Modus!

            # Hole alle E-Mails aus Inbox
            messages = client.search(['ALL'])
            total_emails = len(messages)

            logger.info(f"📧 {total_emails} E-Mails in Inbox gefunden\n")

            if total_emails == 0:
                logger.info("✅ Deine Inbox ist leer! 🎉")
                return

            # Analysiere E-Mails
            matched_emails = []  # E-Mails die von Regeln erfasst werden
            unmatched_emails = []  # E-Mails ohne Regel
            spam_emails = []  # Als Spam erkannt

            logger.info("🔍 Analysiere E-Mails...")

            for i, msg_id in enumerate(messages, 1):
                if i % 50 == 0:
                    logger.info(f"   Fortschritt: {i}/{total_emails}")

                try:
                    # Fetch email (READ-ONLY)
                    fetch_data = client.fetch([msg_id], ['FLAGS', 'BODY.PEEK[]'])
                    raw_email = fetch_data[msg_id][b'BODY[]']
                    email_msg = message_from_bytes(raw_email)

                    # Extrahiere Felder
                    from_header = decode_mime_words(email_msg.get('From', ''))
                    subject = decode_mime_words(email_msg.get('Subject', ''))
                    to_header = decode_mime_words(email_msg.get('To', ''))
                    date = email_msg.get('Date', '')

                    email_data = {
                        'from': from_header,
                        'subject': subject,
                        'to': to_header,
                        'date': date,
                        'domain': extract_email_domain(from_header)
                    }

                    # Prüfe Spam
                    whitelist_domains = spam_rules.get('whitelist_domains', [])
                    if is_spam_simple(email_data, spam_rules, whitelist_domains):
                        spam_emails.append(email_data)
                        continue

                    # Prüfe Regeln
                    matched = False
                    matched_rule = None
                    for rule in rules:
                        if check_rule_match(email_data, rule):
                            matched = True
                            matched_rule = rule
                            break

                    if matched:
                        email_data['rule'] = matched_rule.get('name', 'Unknown')
                        email_data['folder'] = matched_rule.get('folder', 'Unknown')
                        matched_emails.append(email_data)
                    else:
                        unmatched_emails.append(email_data)

                except Exception as e:
                    logger.warning(f"Fehler bei E-Mail {msg_id}: {e}")

            # Statistiken
            print("\n" + "="*80)
            print("📊 ANALYSE ERGEBNISSE")
            print("="*80)
            print(f"\n📧 Gesamt:              {total_emails} E-Mails")
            print(f"✅ Gefiltert:          {len(matched_emails)} E-Mails ({len(matched_emails)/total_emails*100:.1f}%)")
            print(f"🗑️  Als Spam erkannt:   {len(spam_emails)} E-Mails ({len(spam_emails)/total_emails*100:.1f}%)")
            print(f"❓ Ungefiltert:        {len(unmatched_emails)} E-Mails ({len(unmatched_emails)/total_emails*100:.1f}%)")

            # Top Zielordner
            if matched_emails:
                print(f"\n📁 TOP 10 ZIELORDNER:")
                folder_counts = Counter([e['folder'] for e in matched_emails])
                for folder, count in folder_counts.most_common(10):
                    print(f"   {count:3d}x → {folder}")

            # Spam Details
            if spam_emails:
                print(f"\n🗑️  SPAM E-MAILS:")
                spam_domains = Counter([e['domain'] for e in spam_emails if e['domain']])
                for domain, count in spam_domains.most_common(10):
                    print(f"   {count:3d}x {domain}")

            # Ungefilterte E-Mails
            if unmatched_emails:
                print(f"\n❓ UNGEFILTERTE E-MAILS (keine Regel gefunden):")
                print("="*80)

                # Gruppiere nach Domain
                by_domain = defaultdict(list)
                for email in unmatched_emails:
                    domain = email['domain'] or 'unknown'
                    by_domain[domain].append(email)

                # Sortiere nach Anzahl
                sorted_domains = sorted(by_domain.items(), key=lambda x: len(x[1]), reverse=True)

                for domain, emails in sorted_domains[:20]:  # Top 20 Domains
                    print(f"\n📮 {domain} ({len(emails)} E-Mails):")
                    for email in emails[:3]:  # Zeige max 3 Beispiele pro Domain
                        print(f"   From: {email['from'][:60]}")
                        print(f"   Subject: {email['subject'][:60]}")
                        print()

                # Regelvorschläge
                print("\n💡 VORSCHLÄGE FÜR NEUE REGELN:")
                print("="*80)

                for domain, emails in sorted_domains[:10]:
                    if len(emails) >= 2:  # Nur wenn mind. 2 E-Mails
                        example_from = emails[0]['from']
                        print(f"\n# {domain} ({len(emails)} E-Mails)")
                        print(f"# Beispiel: {example_from[:60]}")

                        # Vorschlag für Kategorisierung
                        category = suggest_category(domain, emails)

                        print(f'''{{
  "name": "{category} » {domain.split('.')[0].title()}",
  "folder": "{category}/{domain.split('.')[0].title()}",
  "conditions": {{
    "from_contains": ["{domain}"]
  }}
}},''')

    except Exception as e:
        logger.error(f"❌ Fehler bei IMAP-Verbindung: {e}")
        sys.exit(1)


def suggest_category(domain, emails):
    """Schlägt eine Kategorie basierend auf Domain und Inhalt vor"""

    # Keywords für Kategorien
    categories = {
        'Shopping': ['shop', 'store', 'retail', 'amazon', 'ebay', 'kaufen', 'sale'],
        'Streaming': ['netflix', 'spotify', 'youtube', 'prime', 'video', 'music', 'disney'],
        'Finanzen': ['bank', 'paypal', 'payment', 'invoice', 'rechnung', 'zahlung', 'finance'],
        'Newsletter': ['newsletter', 'news', 'blog', 'update', 'digest'],
        'Social': ['facebook', 'twitter', 'linkedin', 'instagram', 'xing', 'social'],
        'Contracts': ['vertrag', 'contract', 'subscription', 'abo', 'service'],
        'DevOps': ['github', 'gitlab', 'docker', 'aws', 'cloud', 'server', 'deploy'],
        'Notifications': ['notification', 'alert', 'benachrichtigung', 'reminder'],
    }

    domain_lower = domain.lower()

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in domain_lower:
                return category

    # Prüfe Subjects
    subjects = ' '.join([e['subject'].lower() for e in emails[:5]])
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in subjects:
                return category

    return 'Newsletter'


if __name__ == '__main__':
    analyze_inbox()
