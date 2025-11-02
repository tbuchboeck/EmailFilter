#!/usr/bin/env python3
"""
Formats analyze_inbox.py output for GitHub Issues
"""

import sys
import re

def parse_analysis(content):
    """Parse the analysis output and format for GitHub"""

    # Extract key statistics
    total_match = re.search(r'Gesamt:\s+(\d+)\s+E-Mails', content)
    filtered_match = re.search(r'Gefiltert:\s+(\d+)\s+E-Mails\s+\(([\d.]+)%\)', content)
    spam_match = re.search(r'Als Spam erkannt:\s+(\d+)\s+E-Mails\s+\(([\d.]+)%\)', content)
    unfiltered_match = re.search(r'Ungefiltert:\s+(\d+)\s+E-Mails\s+\(([\d.]+)%\)', content)

    total = int(total_match.group(1)) if total_match else 0
    filtered = int(filtered_match.group(1)) if filtered_match else 0
    spam = int(spam_match.group(1)) if spam_match else 0
    unfiltered = int(unfiltered_match.group(1)) if unfiltered_match else 0

    # Build formatted output
    output = []

    # Statistics section
    output.append("## 📊 Statistics\n")
    output.append(f"- **Total emails in inbox:** {total}")
    output.append(f"- **✅ Filtered:** {filtered} ({filtered_match.group(2)}%)" if filtered_match else "- **✅ Filtered:** 0 (0%)")
    output.append(f"- **🗑️ Spam detected:** {spam} ({spam_match.group(2)}%)" if spam_match else "- **🗑️ Spam detected:** 0 (0%)")
    output.append(f"- **❓ Unfiltered:** {unfiltered} ({unfiltered_match.group(2)}%)" if unfiltered_match else "- **❓ Unfiltered:** 0 (0%)")
    output.append("")

    if unfiltered == 0:
        output.append("## ✅ Perfect! All emails are filtered!\n")
        output.append("Your email sorting system is working perfectly. No action needed.\n")
        return "\n".join(output)

    # Extract unfiltered emails section
    unfiltered_section = re.search(
        r'❓ UNGEFILTERTE E-MAILS.*?(?=💡 VORSCHLÄGE|$)',
        content,
        re.DOTALL
    )

    if unfiltered_section:
        output.append("## ❓ Unfiltered Emails\n")

        # Parse each domain group
        domain_pattern = r'📮 ([\w\.-]+) \((\d+) E-Mails?\):(.*?)(?=📮|💡|$)'
        domains = re.finditer(domain_pattern, unfiltered_section.group(0), re.DOTALL)

        for domain in domains:
            domain_name = domain.group(1)
            email_count = domain.group(2)
            emails_text = domain.group(3)

            output.append(f"### {domain_name} ({email_count} email{'s' if int(email_count) > 1 else ''})\n")

            # Extract from/subject examples
            from_matches = re.findall(r'From: (.+)', emails_text)
            subject_matches = re.findall(r'Subject: (.+)', emails_text)

            if from_matches:
                output.append(f"**From:** `{from_matches[0].strip()}`")
            if subject_matches:
                output.append(f"**Subject:** `{subject_matches[0].strip()}`")
            output.append("")

    # Note: Rule suggestions are now automatically applied and included in PRs
    # No need to show them in the issue - see the PR for details

    return "\n".join(output)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: format_analysis.py <analysis_output_file>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            content = f.read()

        formatted = parse_analysis(content)
        print(formatted)
    except FileNotFoundError:
        print(f"## ⚠️ Analysis Error\n\nCould not find analysis output file: {sys.argv[1]}")
    except Exception as e:
        print(f"## ⚠️ Analysis Error\n\nError parsing analysis results:\n```\n{str(e)}\n```")
