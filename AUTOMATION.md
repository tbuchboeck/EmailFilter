# 🤖 Email Filtering Automation

This repository includes automated weekly analysis to help you maintain your email filtering system.

## 📅 Weekly Analysis Workflow

### What It Does

Every **Sunday at 9:00 AM UTC**, the system automatically:

1. ✅ Connects to your email inbox
2. ✅ Analyzes all unfiltered emails
3. ✅ Groups emails by sender domain
4. ✅ Generates rule suggestions in JSON format
5. ✅ Creates/updates a GitHub Issue with results
6. ✅ Sends you a notification (if GitHub notifications enabled)

### Setup Requirements

**1. Add GitHub Secrets**

Go to your repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `IMAP_SERVER` | Your IMAP server address | `imap.gmail.com` |
| `EMAIL_USER` | Your email address | `your.email@example.com` |
| `EMAIL_PASS` | Your email password/app password | `your-password-here` |

**2. Enable GitHub Actions**

- Go to repository → Actions tab
- If disabled, click "I understand my workflows, go ahead and enable them"

**3. Enable GitHub Notifications** (Optional)

- Go to your GitHub settings → Notifications
- Enable "Issues" notifications for this repository
- You'll get notified when new unfiltered emails are found

## 🚀 Manual Trigger

Don't want to wait until Sunday? Run it manually:

1. Go to repository → **Actions** tab
2. Click **Weekly Email Analysis** workflow
3. Click **Run workflow** button
4. Select branch (usually `main`)
5. Click **Run workflow**

Results will appear as a GitHub Issue within ~2-3 minutes.

## 📋 Using the Analysis Results

The workflow **always creates an issue** with your weekly status. Here's what it looks like:

```
📧 Weekly Email Analysis - 5 unfiltered emails

## 📊 Statistics
- Total emails in inbox: 12
- ✅ Filtered: 7 (58.3%)
- ❓ Unfiltered: 5 (41.7%)

## ❓ Unfiltered Emails

### newstore.com (3 emails)
**From:** `Newsletter <info@newstore.com>`
**Subject:** `Weekly deals inside!`

## 💡 Suggested Rules

{
  "name": "Shopping » NewStore",
  "folder": "INBOX/Shopping/NewStore",
  "conditions": {
    "from_contains": ["newstore.com"]
  }
}
```

### Adding Legitimate Sender Rules

**Option A: GitHub Web UI** (Easiest)

1. Click the file: `email_rules.json`
2. Click the **Edit** (pencil) button
3. Find the `"rules"` array
4. Copy the suggested JSON from the issue
5. Paste it into the rules array (don't forget the comma!)
6. Click **Commit changes**

**Option B: Local Git**

```bash
# Edit email_rules.json
nano email_rules.json

# Add the suggested rule to the "rules" array
# Save and commit
git add email_rules.json
git commit -m "Add NewStore to shopping filters"
git push
```

### Blacklisting Spam

If a domain looks suspicious (weird name, scam keywords):

1. Open `spam_rules.json`
2. Add to `blacklist_domains` array:
```json
"blacklist_domains": [
  "existing-spam.com",
  "new-spam-domain.com"  // Add here
]
```
3. Commit changes

## 🔔 What Happens to Issues?

**You'll get a weekly status report every time the workflow runs!**

- **First run** → Creates new issue with weekly status
- **Unfiltered emails found** → Updates issue + adds `needs-review` label + posts comment
- **All emails filtered** → Updates issue with "✅ All clear" message + removes `needs-review` label
- **Every week** → Posts a new comment with current status

**Benefits:**
- ✅ Always know your email system is working
- ✅ Get weekly confirmation even when inbox is clean
- ✅ Historical tracking of your email filtering health
- ✅ Never wonder "is the automation still running?"

## ⚙️ Customizing the Schedule

Want to run more/less frequently? Edit `.github/workflows/weekly-analysis.yml`:

```yaml
on:
  schedule:
    # Daily at 9 AM UTC
    - cron: '0 9 * * *'

    # Every Monday at 8 AM UTC
    - cron: '0 8 * * 1'

    # Twice per week (Wed & Sun at 10 AM UTC)
    - cron: '0 10 * * 0,3'
```

[Cron syntax reference](https://crontab.guru/)

## 🛠️ Troubleshooting

### Workflow not running?

1. Check Actions tab for errors
2. Verify GitHub Secrets are set correctly
3. Make sure Actions are enabled in repository settings

### No issue created?

- Check if all emails were filtered (no issue = success!)
- Check workflow run logs in Actions tab

### Authentication errors?

- Verify `EMAIL_USER` and `EMAIL_PASS` secrets
- For Gmail: Use App Password, not regular password
- For other providers: Check IMAP is enabled

## 📧 Need Help?

- Check workflow logs: Actions → Weekly Email Analysis → Latest run
- Review existing issues with `email-analysis` label
- The workflow includes detailed error messages

---

**Next analysis:** Check the Actions tab for next scheduled run
**Manual run:** Actions → Weekly Email Analysis → Run workflow
