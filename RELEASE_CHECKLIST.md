# SQLProbe v0.0.1 Release Checklist

Use this checklist before tagging or publishing a release.

## Required Before Release

- [x] Tests passing locally with `pytest -v`
- [x] Coverage measured with `pytest --cov=sqlprobe --cov-report=term-missing`
- [x] Package installs with `pip install -e .`
- [x] Console entrypoint verified
- [x] CLI help renders
- [x] `sqlprobe validate cases/examples` works
- [x] `sqlprobe run cases/examples` works
- [x] `sqlprobe demo` works
- [x] README quickstart matches current behavior
- [x] CHANGELOG.md updated
- [x] PROJECT_STATUS.md updated
- [ ] Version tagged in git
- [ ] Release notes prepared

## Known Release Notes

- `v0.0.1` is a local/source-install release candidate.
- PyPI publishing is not implemented yet.
- Database execution, LLM judging, regression baselines, semantic annotations, and tracing are planned but not implemented.
- On Windows, `pip install -e .` may install `sqlprobe.exe` into the user Python Scripts directory. If that directory is not on `PATH`, use `python -m sqlprobe.cli.main`.
