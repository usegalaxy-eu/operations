[![documentation](https://img.shields.io/badge/documentation-online-blue)](https://usegalaxy-eu.github.io/operations/)

# Operations Manual for usegalaxy.eu

This repository holds the operations documentation for the European Galaxy server.

- The rendered documentation site (with search) lives at <https://usegalaxy-eu.github.io/operations/>
- All content is in [`docs/`](./docs/) and built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) — configuration in [`mkdocs.yml`](./mkdocs.yml)
- The former bwCloud documentation has been archived under [`docs/archived/`](./docs/archived/)

## Working on the docs

```bash
pip install 'mkdocs>=1.6,<2' 'mkdocs-material>=9.5,<10'
mkdocs serve          # live preview with search at http://localhost:8000
mkdocs build --strict # build check: fails on broken links (same check as CI)
```

CI validates every pull request with `mkdocs build --strict`, and pushes to `main` are deployed to GitHub Pages automatically.
