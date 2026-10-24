# Upload to GitHub

Suggested repository name: `mm-learning-management`

Suggested description:

> An original Django learning platform with courses, quizzes, progress tracking, certificates, instructor tools, Myanmar payment reviews and optional hosted card checkout.

Create a new empty repository on your GitHub account. Do not initialize it with another README or license. From this extracted folder:

```bash
git init
git add .
git commit -m "Initial MM Learning Management release"
git branch -M main
git remote add origin https://github.com/devminsithu/mm-learning-management.git
git push -u origin main
```

Authenticate using your own GitHub credentials when prompted. If you choose a different account/name, change the remote URL. Before pushing, inspect `git status` to ensure local databases, private receipts, environment secrets and virtual environments are excluded.

Alternatively, upload the extracted project files using GitHub's upload interface. Include `.github/`, `.gitignore`, migration files and all source folders. Do not upload your generated `.local-data/` or `.venv/` folders.

This source package does not itself create or publish a GitHub repository. GitHub Pages cannot host the Django backend.
