# Agent Instructions

## Release Workflow

When committing changes to this repo, always:

1. Bump the version in `custom_components/lifequest/manifest.json`
2. Commit the changes
3. Tag the commit as `v{version}` (e.g. `v0.1.9`)
4. Push to both remotes with tags:
   - `origin` → `git.heathmont.ahpee.net:hacs/lifequest_hacs.git`
   - `github` → `github.com:tahpee/lifequest_hacs.git`

```bash
git push origin main --tags && git push github main --tags
```
