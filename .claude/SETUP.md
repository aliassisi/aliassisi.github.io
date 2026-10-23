# Set up your Mac to work on the ALIA website

You do this once. It takes about 20 minutes.
You will use the Claude Desktop app (the Code tab) to make changes.

## 1. What you need first
- A Mac.
- A GitHub account. Ask the team to add you to the `aliassisi` organization with write access.
- A Claude account that can use Claude Code.

## 2. Install the tools
Open the Terminal app. Paste each command, one at a time.

### Xcode command line tools (this gives you git)
```bash
xcode-select --install
```
Click Install in the window that opens. Wait until it ends.
Check it:
```bash
git --version
```

### Homebrew (installs the other tools)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
At the end, Homebrew prints two or three "Next steps" commands. Run them.
Then check it:
```bash
brew --version
```

### GitHub CLI (`gh`)
```bash
brew install gh
```

### Python 3 and wget
The site scripts need Python 3. The re-crawl script needs `wget` and `rsync`.
```bash
brew install python wget rsync
```

### Node.js
Only needed to build the search index on your computer (`npx pagefind`).
```bash
brew install node
```

### Google Chrome
The `run-site` skill uses Chrome to take screenshots. Install it from
https://www.google.com/chrome/ and put it in `/Applications`.

### Claude Desktop
Download it from https://claude.ai/download. Open it and sign in.

## 3. Tell git who you are
Use the same email as your GitHub account.
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

## 4. Sign in to GitHub
```bash
gh auth login
```
Pick these answers:
- Account: GitHub.com
- Protocol: SSH
- Generate a new SSH key: Yes (set a passphrase if you want)
- Authenticate: Login with a web browser

Check it:
```bash
gh auth status
```

## 5. Get the code
```bash
mkdir -p ~/dev
cd ~/dev
gh repo clone aliassisi/aliassisi.github.io
```
The folder is `~/dev/aliassisi.github.io`.

If you plan to re-crawl WordPress, the raw crawl is stored next to the repo,
in `~/dev/aliassisi-crawl`. The script creates it for you.

## 6. Open the project in Claude Desktop
1. Open Claude Desktop and go to the Code tab.
2. Choose the folder `~/dev/aliassisi.github.io`.
3. Start a session.

Claude reads `CLAUDE.md` and `.claude/` in the repo on its own.
That gives it the project rules, the allowed commands, the link check hook
and the `run-site` skill. You do not need to set anything up for this.

## 7. Make your first change
Ask Claude in plain words. For example:
"Fix the typo on the method page. Make a branch and open a PR."

Claude will:
1. Make a branch and edit the page.
2. Run the site locally and look at it.
3. Open a pull request.

Then:
1. Wait for the PR preview. It is at `https://aliassisi.github.io/pr-preview/pr-N/`.
2. Look at the preview. Check the page on a phone-size window too.
3. Ask a teammate to review the PR.
4. Merge it. The "Deploy production" workflow publishes the site.

Never push straight to `main`.

## 8. Good habits
- Ask Claude to say what it did not check.
- A re-crawl wipes direct HTML edits. If a fix must last, ask Claude to add a rule
  to `.github/scripts/postprocess.py` too.
- The contact and newsletter forms do not work yet.
- Do not edit the `pagefind/` folder. The deploy rebuilds it.

## 9. If something fails
- `command not found: brew`: close Terminal, open it again, or run the "Next steps" commands from the Homebrew install.
- `Permission denied (publickey)` on clone or push: run `gh auth login` again and choose SSH.
- Port 8800 is busy: run `pkill -f "http.server 8800"`.
- Screenshots fail: check that Chrome is in `/Applications/Google Chrome.app`.
- Ask Claude to help. Paste the error text.
