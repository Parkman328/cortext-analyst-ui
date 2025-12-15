# How to Create GitHub Repository for Cortex Analyst UI

## Step 1: Create GitHub Repository

### Option A: Using GitHub Website

1. Go to https://github.com/new
2. Repository name: `cortex-analyst-ui`
3. Description: `Beautiful FastAPI web interface for Snowflake Cortex Analyst`
4. Select: **Public** (or Private if you prefer)
5. **DO NOT** check "Initialize with README" (we already have one)
6. Click "Create repository"

### Option B: Using GitHub CLI

```bash
# Install GitHub CLI first if you haven't
# macOS: brew install gh
# Then authenticate
gh auth login

# Create repository
gh repo create cortex-analyst-ui --public --description "Beautiful FastAPI web interface for Snowflake Cortex Analyst"
```

## Step 2: Initialize Git and Push Code

### On Your Mac Terminal:

```bash
# Navigate to project directory
cd cortex-analyst-ui

# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Cortex Analyst UI v1.0.0"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/cortex-analyst-ui.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Add Repository Topics (Optional)

On GitHub repository page:

1. Click "⚙️ Settings" (top right, near repository name, not account settings)
2. Or click "About" gear icon on the right side
3. Add topics:
   - `snowflake`
   - `cortex-analyst`
   - `fastapi`
   - `python`
   - `data-analysis`
   - `web-ui`

## Step 4: Enable GitHub Pages for Documentation (Optional)

1. Go to repository Settings
2. Scroll to "Pages" section
3. Source: Deploy from branch
4. Branch: main, folder: / (root)
5. Save

## Step 5: Add Repository Secrets (for CI/CD if needed)

1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Add any secrets needed for automated testing/deployment

## Step 6: Create Releases

### First Release

```bash
# Tag the first version
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

Then on GitHub:

1. Go to "Releases" tab
2. Click "Create a new release"
3. Choose tag: v1.0.0
4. Release title: `v1.0.0 - Initial Release`
5. Description: Copy features from README.md
6. Click "Publish release"

## Step 7: Protect Main Branch (Recommended)

1. Settings > Branches
2. Click "Add rule"
3. Branch name pattern: `main`
4. Check:
   - ✅ Require pull request before merging
   - ✅ Require status checks to pass
5. Save

## Complete Git Commands Cheat Sheet

```bash
# Initial setup (do once)
cd cortex-analyst-ui
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/cortex-analyst-ui.git
git push -u origin main

# Daily workflow
git add .
git commit -m "Your commit message"
git push

# Create a new feature
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
# Create pull request on GitHub

# Tag a release
git tag -a v1.0.1 -m "Bug fixes"
git push origin v1.0.1
```

## Repository Structure on GitHub

```
cortex-analyst-ui/
├── .github/
│   └── workflows/          # CI/CD workflows (optional)
├── static/
│   └── index.html         # Frontend UI
├── uploads/               # Git ignored
├── outputs/               # Git ignored
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.sh
├── main.py
├── cortex_processor.py
└── sample_questions.csv
```

## Recommended Repository Settings

### General

- ✅ Issues
- ✅ Discussions (optional, good for Q&A)
- ✅ Projects (optional, for roadmap)
- ❌ Wiki (use README instead)
- ✅ Sponsorships (if you want)

### Features to Add Later

1. **GitHub Actions** - CI/CD pipeline
2. **Issue Templates** - Bug reports, feature requests
3. **Pull Request Template**
4. **Code of Conduct**
5. **Contributing Guidelines**

## Sample Issue Templates

Create `.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior

**Expected behavior**
What you expected to happen

**Screenshots**
If applicable, add screenshots

**Environment:**
 - OS: [e.g. macOS 14]
 - Python version: [e.g. 3.10]
 - Browser: [e.g. Chrome]

**Additional context**
Any other context about the problem.
```

## Clone Your Repository (to verify)

```bash
# In a different directory
git clone https://github.com/YOUR_USERNAME/cortex-analyst-ui.git
cd cortex-analyst-ui
./setup.sh
python main.py
```

## Sharing Your Repository

Share link: `https://github.com/YOUR_USERNAME/cortex-analyst-ui`

Add badges to README.md:

```markdown
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Stars](https://img.shields.io/github/stars/YOUR_USERNAME/cortex-analyst-ui)
```

## Next Steps

1. ✅ Create repository on GitHub
2. ✅ Push your code
3. ✅ Add topics and description
4. ✅ Create first release
5. 📢 Share with community
6. 🐛 Create issues for known bugs
7. 📝 Update documentation as needed
8. 🎉 Celebrate your open source project!

## Troubleshooting

### Issue: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/cortex-analyst-ui.git
```

### Issue: "Permission denied (publickey)"

Use HTTPS instead:
```bash
git remote set-url origin https://github.com/YOUR_USERNAME/cortex-analyst-ui.git
```

Or set up SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh

### Issue: "Large files rejected"

Add to `.gitignore`:
```
*.csv
*.json
uploads/*
outputs/*
```

Then:
```bash
git rm --cached large_file.csv
git commit -m "Remove large files"
git push
```

---

🎉 **Congratulations! Your repository is live on GitHub!**
