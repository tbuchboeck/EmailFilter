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


def detect_account_from_analysis(content):
    """
    Detect which account the analysis is for based on the output

    Returns:
        str: account_id (e.g., 'easyname', 'gmail')
    """
    # Look for the account name in the analysis header
    account_match = re.search(r'📧 ANALYZING ACCOUNT:.*?\(([^)]+)\)', content)
    if account_match:
        return account_match.group(1)

    # Default to easyname if not found
    return 'easyname'


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

        # Detect account
        account_id = detect_account_from_analysis(content)
        print(f"🔍 Detected account: {account_id}")

        # Map account to rules file
        rules_file_map = {
            'easyname': 'email_rules_easyname.json',
            'gmail': 'email_rules_gmail.json',
            'easyname_wife': 'email_rules_easyname.json',  # Wife uses same rules
        }

        rules_file = rules_file_map.get(account_id, 'email_rules_easyname.json')
        print(f"📝 Target rules file: {rules_file}")

        # Parse suggestions
        print(f"\n🔍 Parsing rule suggestions...")
        suggestions = parse_rule_suggestions(content)

        if not suggestions:
            print("\n⚠️  No rule suggestions found in analysis output")
            print("This is normal if all emails are already filtered!")
            sys.exit(0)

        print(f"\n📊 Found {len(suggestions)} suggested rule(s)")

        # Add rules to file
        print(f"\n📝 Adding rules to {rules_file}...")
        added_count = add_rules_to_file(rules_file, suggestions)

        if added_count > 0:
            print(f"\n✅ SUCCESS: Added {added_count} new rule(s)")
            sys.exit(0)
        else:
            print(f"\nℹ️  No changes made (no new rules to add)")
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
