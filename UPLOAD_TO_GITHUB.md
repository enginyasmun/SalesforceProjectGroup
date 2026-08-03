# Upload the v6 release to GitHub

## Recommended method: replace the repository from a local clone

1. Download and extract `SalesforceProjectGroup_v6_GitHub_Upload.zip`.
2. Clone the existing repository to your computer.
3. Copy every extracted file and folder into the repository root, including `.github` and `.gitignore`.
4. Allow the new files to replace files with the same names.
5. Review and commit the complete change.

Example commands from Git Bash, macOS Terminal, or Linux:

```bash
git clone https://github.com/enginyasmun/SalesforceProjectGroup.git
cd SalesforceProjectGroup

git checkout -b upgrade/v6-integrated-portal
# Copy the extracted package contents into this folder now.

git status
git add .
git commit -m "Integrate professional v6 learning portal"
git push -u origin upgrade/v6-integrated-portal
```

Open a pull request from `upgrade/v6-integrated-portal` into `main`. After GitHub Actions passes, merge it.

## Files from the old patch pack

These old files are no longer used and may be deleted from GitHub for a cleaner repository:

```text
BACKEND_PATCH_NOTES.md
README_FIX.md
sql_v52_patch.sql
static/dashboard-fix.css
static/v52-fixes.css
```

Leaving them in the repository will not affect v6 because the application does not load them.

## Do not upload production data

Never commit these items:

```text
project_group.db
uploads/
avatars/
.env
__pycache__/
```

They are excluded by the included `.gitignore`.
