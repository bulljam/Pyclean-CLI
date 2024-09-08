# Demo Test Data

This folder contains safe local files for trying `pyclean` commands during development.

Suggested examples:

```bash
.venv/bin/pyclean scan-large --path demo/testdata --min-size 1KB
.venv/bin/pyclean scan-large --path demo/testdata --min-size 1KB --exclude "*.log"
.venv/bin/pyclean clean-temp --path demo/testdata/temp --dry-run
.venv/bin/pyclean clean-temp --path demo/testdata/temp --no-dry-run --yes
.venv/bin/pyclean clean-cache --path demo/testdata/cache --dry-run
```

Notes:

- `demo/testdata/temp` is meant for `clean-temp`.
- `demo/testdata/cache` is meant for `clean-cache`.
- The sample large files live under `demo/testdata/large-files`.
