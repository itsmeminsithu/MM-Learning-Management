# Repository setup

Clone the repository:

```bash
git clone https://github.com/itsmeminsithu/MM-Learning-Management.git
cd MM-Learning-Management
```

Work on a branch and open a pull request to `main`; do not push directly to `main`. See README.md for run and Codespaces preview steps, and DEPLOYMENT.md before public hosting.

CI note: `.github/workflows/tests.yml` (checkout, Python 3.11/3.13, `pip install -r requirements.txt`, `manage.py check`, `manage.py makemigrations --check --dry-run`, `manage.py test`) is not committed in this branch because the automated GitHub App cannot push workflow files. Add it via the GitHub web UI after merge.

Before pushing, check `git status`: `.local-data/`, `.venv/`, `staticfiles/` and `.env` must stay out of the repository (see `.gitignore`).

GitHub Pages cannot host the Django backend.
