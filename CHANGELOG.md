# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-02

First public release.

### Added
- `catalog-lint` CLI (also installed as `gradle-catalog-lint`) with zero runtime dependencies.
- Rules: `unused-library`, `unused-plugin`, `unused-version`, `unused-bundle`,
  `undefined-version-ref`, `undefined-bundle-member`, `duplicate-library`, `dynamic-version`,
  `snapshot-version`, `hardcoded-dependency`, `unknown-lookup`.
- Usage detection for type-safe accessors (`libs.a.b`, `libs.versions.x`, `libs.plugins.x`,
  `libs.bundles.x`), `findLibrary/findPlugin/findVersion/findBundle` lookups, Groovy and Kotlin
  DSL, convention plugins in `buildSrc`/`build-logic`, comment stripping.
- Multiple catalogs, custom catalog names from `settings.gradle(.kts)`, nested builds with their own catalog.
- `--fix` / `--fix --dry-run` to remove unused entries, validated by re-parsing the TOML.
- Output formats: `text`, `json`, `github` (workflow annotations) and `sarif` (code scanning).
- `.catalog-lint.toml` configuration and inline `# catalog-lint: ignore[=rule,...]` comments.
- Composite GitHub Action (`action.yml`) and `.pre-commit-hooks.yaml`.

[0.1.0]: https://github.com/cosmichackerx/gradle-version-catalog-lint/releases/tag/v0.1.0
