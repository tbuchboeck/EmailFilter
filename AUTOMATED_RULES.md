# 🤖 Automated Rule Management

Your EmailFilter now has **fully automated rule management**! Every week, the system analyzes your inbox and automatically creates Pull Requests with suggested email filtering rules.

## How It Works

### 1. Weekly Analysis (Automatic)
Every Sunday at 9:00 AM UTC, the system:
- Analyzes all configured email accounts
- Identifies unfiltered emails
- Groups them by sender domain
- Suggests filtering rules

### 2. Automatic PR Creation (NEW! 🎉)
If new rules are suggested, the workflow automatically:
- ✅ Parses the suggested rules
- ✅ Creates a new branch (`weekly-analysis/YYYY-MM-DD`)
- ✅ Adds rules to the appropriate config files (`email_rules_*.json`)
- ✅ Commits the changes
- ✅ Pushes to GitHub
- ✅ Creates a Pull Request for review

### 3. You Review & Merge
All you need to do:
1. 📧 Check your email or GitHub notifications for the PR
2. 👀 Review the suggested rules in the PR
3. ✅ Merge the PR if rules look good
4. 🎉 Done! Rules are applied automatically

## What You Get

### GitHub Issue (Weekly Report)
- 📊 Statistics about your inbox
- 📧 List of unfiltered email senders
- 🔗 Link to the automatically created PR (if rules were added)

### Pull Request (Automatic)
- 📝 New email rules ready to merge
- 🔍 Clear diff showing what was added
- 🏷️ Labeled with `email-analysis` and `automated`

## Manual Trigger

Want to run the analysis now?

1. Go to **Actions** → **Weekly Email Analysis**
2. Click **Run workflow**
3. Wait 1-2 minutes
4. Check for new PR!

## Customization

### Disable Automation

If you prefer manual rule management, you can remove the automation steps from `.github/workflows/weekly-analysis.yml`:

```yaml
# Remove or comment out these steps:
- name: Apply rule suggestions automatically
- name: Create Pull Request with new rules
- name: Create Pull Request
```

The workflow will still create issues with suggestions, but won't auto-create PRs.

### Change Schedule

Edit `.github/workflows/weekly-analysis.yml`:

```yaml
on:
  schedule:
    - cron: '0 9 * * 0'  # Sunday at 9:00 AM UTC
```

**Examples:**
- `'0 9 * * 1'` - Every Monday at 9:00 AM
- `'0 20 * * 5'` - Every Friday at 8:00 PM
- `'0 9 1 * *'` - First day of each month

### Rule Categories

The automation suggests categories based on domain keywords:

| Category | Keywords |
|----------|----------|
| Shopping | shop, store, amazon, ebay, sale |
| Streaming | netflix, spotify, youtube, prime video |
| Finanzen | bank, paypal, payment, invoice |
| Newsletter | newsletter, news, blog, update |
| Social | facebook, twitter, linkedin |
| DevOps | github, gitlab, docker, aws, cloud |

You can adjust categories manually in the PR before merging!

## Technical Details

### Files Involved

| File | Purpose |
|------|---------|
| `.github/workflows/weekly-analysis.yml` | Main automation workflow |
| `.github/scripts/apply_suggestions.py` | Parses analysis and adds rules |
| `.github/scripts/format_analysis.py` | Formats analysis for GitHub issues |
| `analyze_inbox.py` | Analyzes inbox and suggests rules |

### Workflow Permissions

The workflow requires these permissions (already configured):
- `contents: write` - To create branches and commit
- `pull-requests: write` - To create PRs
- `issues: write` - To create/update issues

### Branch Naming

Branches are automatically named: `weekly-analysis/YYYY-MM-DD`

Example: `weekly-analysis/2025-11-02`

### Duplicate Prevention

The script automatically:
- ✅ Skips rules that already exist (by name)
- ✅ Won't create PRs if no new rules
- ✅ Won't create duplicate PRs for same date

## Troubleshooting

### No PR was created

**Possible reasons:**
- ✅ All emails are already filtered (good!)
- ✅ Suggested rules already exist in config files
- ✅ Analysis found no unfiltered emails

Check the GitHub issue for details.

### PR has wrong rules

**Solution:**
1. Close the PR
2. Edit the rules manually via GitHub UI
3. Or: Edit locally, push to a new branch, create manual PR

### Want to add rules manually

**Option 1 - GitHub UI:**
1. Go to your repository
2. Click on `email_rules_gmail.json` or `email_rules_easyname.json`
3. Click "Edit file" (pencil icon)
4. Add your rules
5. Commit directly to main branch

**Option 2 - Local:**
1. Clone the repository
2. Edit the rules file
3. Commit and push
4. Create PR or push to main

## Benefits

✅ **Zero manual work** - Rules are added automatically
✅ **Safe** - Always creates PR for review (never commits to main)
✅ **Transparent** - Clear diffs show what changed
✅ **Flexible** - Easy to customize or disable
✅ **Continuous** - Runs weekly, keeps your inbox clean

## Next Steps

1. ✅ Wait for next Sunday (or trigger manually)
2. ✅ Review the PR when it arrives
3. ✅ Merge to apply rules
4. ✅ Enjoy your automated email management! 🎉

---

**Questions?** Open an issue in the repository!
