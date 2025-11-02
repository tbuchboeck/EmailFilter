#!/usr/bin/env python3
"""
Automatically applies suggested email rules from analysis output
Parses the analysis, extracts JSON rule suggestions, and adds them to the appropriate rules file
"""

import sys
import json
import re
from pathlib import Path


def parse_rule_suggestions(content):
    """
    Parse the analysis output and extract JSON rule suggestions

    Returns:
        list: List of rule dictionaries
    """
    suggestions = []

    # Find the suggestions section
    suggestions_section = re.search(
        r'💡 VORSCHLÄGE FÜR NEUE REGELN:.*',
        content,
        re.DOTALL
    )

    if not suggestions_section:
        print("No suggestions section found in analysis output")
        return suggestions

    # Extract each rule suggestion (JSON blocks with comments)
    # Pattern: # comment lines followed by JSON
    # We need to match multi-line JSON, so use DOTALL and a proper pattern
    rule_pattern = r'#[^\n]+\n#[^\n]+\n(\{[\s\S]*?\}),'

    matches = re.finditer(rule_pattern, suggestions_section.group(0))

    for match in matches:
        json_text = match.group(1).strip()
        try:
            # Parse the JSON rule
            rule = json.loads(json_text)
            suggestions.append(rule)
            print(f"  ✓ Parsed rule: {rule.get('name', 'Unknown')}")
        except json.JSONDecodeError as e:
            print(f"  ✗ Failed to parse rule: {e}")
            print(f"    JSON: {json_text[:100]}...")

    return suggestions


def detect_accounts_from_analysis(content):
    """
    Detect which accounts are in the analysis based on the output

    Returns:
        list: List of account_ids found (e.g., ['easyname', 'gmail'])
    """
    # Look for all account names in the analysis headers
    account_matches = re.finditer(r'📧 ANALYZING ACCOUNT:.*?\(([^)]+)\)', content)
    accounts = [match.group(1) for match in account_matches]

    # If no accounts found, default to easyname
    if not accounts:
        return ['easyname']

    return accounts


def extract_suggestions_by_account(content):
    """
    Extract rule suggestions grouped by account

    Returns:
        dict: {account_id: [rules]}
    """
    suggestions_by_account = {}

    # Split content by account sections
    account_sections = re.split(r'={80,}\n📧 ANALYZING ACCOUNT:', content)

    for section in account_sections[1:]:  # Skip first empty section
        # Extract account ID
        account_match = re.search(r'^.*?\(([^)]+)\)', section)
        if not account_match:
            continue

        account_id = account_match.group(1)

        # Find suggestions section for this account
        suggestions_section = re.search(
            r'💡 VORSCHLÄGE FÜR NEUE REGELN:.*?(?=📧 ANALYZING ACCOUNT:|$)',
            section,
            re.DOTALL
        )

        if not suggestions_section:
            continue

        # Extract rules from this section
        rule_pattern = r'#[^\n]+\n#[^\n]+\n(\{[\s\S]*?\}),'
        matches = re.finditer(rule_pattern, suggestions_section.group(0))

        rules = []
        for match in matches:
            json_text = match.group(1).strip()
            try:
                rule = json.loads(json_text)
                rules.append(rule)
            except json.JSONDecodeError:
                continue

        if rules:
            suggestions_by_account[account_id] = rules

    return suggestions_by_account


def add_rules_to_file(rules_file, new_rules):
    """
    Add new rules to the specified rules file

    Args:
        rules_file: Path to the rules JSON file
        new_rules: List of rule dictionaries to add

    Returns:
        int: Number of rules added
    """
    if not new_rules:
        print(f"No rules to add to {rules_file}")
        return 0

    # Read existing rules
    try:
        with open(rules_file, 'r', encoding='utf-8') as f:
            rules_config = json.load(f)
    except FileNotFoundError:
        print(f"Rules file not found: {rules_file}")
        return 0

    existing_rules = rules_config.get('rules', [])

    # Get existing rule names to avoid duplicates
    existing_names = {rule.get('name', '') for rule in existing_rules}

    # Add new rules (avoid duplicates)
    added_count = 0
    for rule in new_rules:
        rule_name = rule.get('name', '')
        if rule_name and rule_name not in existing_names:
            existing_rules.append(rule)
            existing_names.add(rule_name)
            added_count += 1
            print(f"  ✓ Added rule: {rule_name}")
        else:
            print(f"  ⊘ Skipped duplicate: {rule_name}")

    # Write back to file
    if added_count > 0:
        rules_config['rules'] = existing_rules
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules_config, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        print(f"\n✅ Added {added_count} new rule(s) to {rules_file}")
    else:
        print(f"\nℹ️  No new rules added to {rules_file} (all were duplicates)")

    return added_count


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: apply_suggestions.py <analysis_output_file>")
        sys.exit(1)

    analysis_file = sys.argv[1]

    try:
        print(f"📖 Reading analysis from: {analysis_file}")
        with open(analysis_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Detect all accounts in the analysis
        accounts = detect_accounts_from_analysis(content)
        print(f"🔍 Detected {len(accounts)} account(s): {', '.join(accounts)}")

        # Map accounts to rules files
        rules_file_map = {
            'easyname': 'email_rules_easyname.json',
            'gmail': 'email_rules_gmail.json',
            'easyname_wife': None,  # Spam-only, no rules file
        }

        # Extract suggestions grouped by account
        print(f"\n🔍 Parsing rule suggestions by account...")
        suggestions_by_account = extract_suggestions_by_account(content)

        if not suggestions_by_account:
            print("\n⚠️  No rule suggestions found in analysis output")
            print("This is normal if all emails are already filtered!")
            sys.exit(0)

        total_rules = sum(len(rules) for rules in suggestions_by_account.values())
        print(f"\n📊 Found {total_rules} suggested rule(s) across {len(suggestions_by_account)} account(s)")

        # Apply rules for each account
        total_added = 0
        for account_id, suggestions in suggestions_by_account.items():
            print(f"\n{'='*60}")
            print(f"📧 Processing account: {account_id}")
            print(f"{'='*60}")

            rules_file = rules_file_map.get(account_id)
            if not rules_file:
                print(f"⊘ Skipping {account_id} (spam-only account, no rules file)")
                continue

            print(f"📝 Target rules file: {rules_file}")
            print(f"📋 {len(suggestions)} rule(s) to add")

            # Add rules to file
            added_count = add_rules_to_file(rules_file, suggestions)
            total_added += added_count

        # Summary
        print(f"\n{'='*60}")
        if total_added > 0:
            print(f"✅ SUCCESS: Added {total_added} new rule(s) in total")
            sys.exit(0)
        else:
            print(f"ℹ️  No changes made (all rules already exist)")
            sys.exit(0)

    except FileNotFoundError:
        print(f"❌ Error: Analysis file not found: {analysis_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
