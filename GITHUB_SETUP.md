# GitHub Setup Guide

## Option 1: GitHub CLI (Easiest) ✅ Recommended

### Step 1: Install GitHub CLI (if not installed)
```powershell
winget install --id GitHub.cli
```

### Step 2: Login to GitHub
```powershell
gh auth login
```
Follow the prompts:
- Choose "GitHub.com"
- Choose "HTTPS"
- Choose "Login with a web browser"
- Copy the code shown and press Enter
- Browser will open - paste code and authorize

### Step 3: Verify login
```powershell
gh auth status
```

---

## Option 2: Personal Access Token (Manual)

### Step 1: Create a Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it: "PolyMarketBot-V2"
4. Select scopes: ✅ `repo` (full control of private repositories)
5. Click "Generate token"
6. **COPY THE TOKEN** (you won't see it again!)

### Step 2: Use token when pushing
When you push, Git will prompt for password - use the token instead.

---

## Option 3: SSH Keys

### Step 1: Generate SSH key
```powershell
ssh-keygen -t ed25519 -C "Samcatterson@dseccapital.com"
```
Press Enter to accept default location.

### Step 2: Add SSH key to GitHub
1. Copy your public key:
```powershell
cat ~/.ssh/id_ed25519.pub
```
2. Go to: https://github.com/settings/keys
3. Click "New SSH key"
4. Paste the key and save

### Step 3: Test connection
```powershell
ssh -T git@github.com
```

---

## Quick Start (After Authentication)

### Initialize Repository
```powershell
cd C:\Users\Owner\PolyMarketBot-V2
git init
git add .
git commit -m "Initial commit: Polymarket arbitrage bot"
```

### Create Repository on GitHub
1. Go to: https://github.com/new
2. Name it: `PolyMarketBot-V2` (or whatever you want)
3. Don't initialize with README (we already have files)
4. Click "Create repository"

### Push to GitHub
```powershell
git remote add origin https://github.com/YOUR_USERNAME/PolyMarketBot-V2.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username!

