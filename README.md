[![documentation](https://img.shields.io/badge/documentation-online-blue)](https://usegalaxy-eu.github.io/operations/)

# Operations Manual for usegalaxy.eu

This repository holds the operations documentation for the European Galaxy server.

- The rendered documentation site (with search) lives at <https://usegalaxy-eu.github.io/operations/>
- All content is in [`docs/`](./docs/) and built with [Zensical](https://zensical.org/) — configuration in [`mkdocs.yml`](./mkdocs.yml) (Zensical reads MkDocs configuration)
- The former bwCloud documentation has been archived under [`docs/archived/`](./docs/archived/)

## Working on the docs

```bash
pip install zensical
zensical serve         # live preview with search at http://localhost:8000
zensical build --strict # build check: fails on broken links and anchors (same check as CI)
```

CI validates every pull request with `zensical build --strict`, and pushes to `main` are deployed to GitHub Pages automatically.
