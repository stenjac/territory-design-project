# GitHub Setup Guide

Your code is ready to push to GitHub! Follow these steps:

## ✅ What's Already Done

- ✅ Git repository initialized
- ✅ All files committed with comprehensive commit message
- ✅ .gitignore file created
- ✅ README.md with complete documentation
- ✅ requirements.txt with dependencies

---

## 🚀 Option 1: Using GitHub.com (Easiest)

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Fill in the form:
   - **Repository name**: `territory-design-project`
   - **Description**: `Sales territory optimization system with interactive dashboard and smart rebalancing algorithm`
   - **Visibility**: Public (or Private if you prefer)
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
3. Click "Create repository"

### Step 2: Push Your Code

GitHub will show you commands. Use these:

```bash
cd /Users/stefanomazzalai/territory-design-project

# Add the remote repository
git remote add origin https://github.com/YOUR_USERNAME/territory-design-project.git

# Push your code
git push -u origin main
```

**Replace `YOUR_USERNAME` with your actual GitHub username!**

### Step 3: Verify

Go to `https://github.com/YOUR_USERNAME/territory-design-project` and you should see your project!

---

## 🚀 Option 2: Using GitHub CLI (Advanced)

If you want to use GitHub CLI:

### Step 1: Install GitHub CLI

```bash
brew install gh
```

### Step 2: Authenticate

```bash
gh auth login
```

Follow the prompts to authenticate with your GitHub account.

### Step 3: Create and Push

```bash
cd /Users/stefanomazzalai/territory-design-project

# Create repo and push in one command
gh repo create territory-design-project --public --source=. --remote=origin --push
```

Or for a private repository:

```bash
gh repo create territory-design-project --private --source=. --remote=origin --push
```

---

## 🔧 Troubleshooting

### Issue: "remote origin already exists"

```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/territory-design-project.git
git push -u origin main
```

### Issue: Authentication failed

If using HTTPS, you need a Personal Access Token (PAT):

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes: `repo` (all sub-options)
4. Generate token and copy it
5. When pushing, use the token as your password

Or switch to SSH:

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: https://github.com/settings/keys

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/territory-design-project.git
git push -u origin main
```

### Issue: Branch name mismatch

If GitHub expects `master` instead of `main`:

```bash
git branch -M main
git push -u origin main
```

---

## 📝 After Pushing

### Update README

1. Replace `YOUR_USERNAME` in README.md line 64:
   ```bash
   # In README.md, change this line:
   git clone https://github.com/YOUR_USERNAME/territory-design-project.git
   # To your actual GitHub username
   ```

2. Commit and push the change:
   ```bash
   git add README.md
   git commit -m "Update README with correct GitHub username"
   git push
   ```

### Add Repository Topics (Optional)

Go to your repository on GitHub and click "Add topics":

Suggested topics:
- `sales-operations`
- `territory-design`
- `data-analysis`
- `streamlit`
- `python`
- `optimization`
- `sales-analytics`
- `territory-management`
- `capacity-planning`

### Enable GitHub Pages (Optional)

If you want to host documentation:

1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` → `/docs` (if you create a docs folder)
4. Save

---

## 🎉 You're Done!

Your repository is now live on GitHub! Share it with:

- **LinkedIn**: Post about your project
- **Twitter/X**: Share with #SalesOps #DataAnalysis
- **Resume**: Link to your GitHub repo
- **Portfolio**: Add to your portfolio website

---

## 📊 Next Steps

1. **Add a LICENSE file** (MIT recommended):
   ```bash
   # Create LICENSE file
   echo "MIT License..." > LICENSE
   git add LICENSE
   git commit -m "Add MIT license"
   git push
   ```

2. **Add GitHub Actions** for CI/CD (optional):
   - Auto-run tests on push
   - Deploy dashboard to Streamlit Cloud

3. **Create Releases**:
   - Go to Releases → Draft a new release
   - Tag version: `v1.0.0`
   - Release title: "Initial Release"
   - Describe features

4. **Add Badges to README**:
   - Build status
   - Code coverage
   - License badge

---

## 🔗 Useful Links

- GitHub Docs: https://docs.github.com
- Git Cheat Sheet: https://education.github.com/git-cheat-sheet-education.pdf
- Markdown Guide: https://www.markdownguide.org/

---

**Need help?** Open an issue or reach out!
