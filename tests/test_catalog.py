import pytest

from catalog_lint.catalog import (
    CatalogError,
    default_name,
    library_module,
    normalize,
    parse_catalog,
    version_literals,
    version_ref,
)

TOML = """\
[versions]
kotlin = "2.0.0"
compose = { strictly = "[1.0, 2.0[", prefer = "1.5" }

[libraries]
# a comment
a-b = { module = "g:a", version.ref = "kotlin" }
plain = "g:plain:1.0"
dotted.module = "g:dotted"
dotted.version.ref = "kotlin"
multi = { group = "g", name = "multi", version = "1.0" }

[libraries.subtable]
module = "g:sub"
version = "2"

[bundles]
all = [
  "a-b",
  "plain",
]

[plugins]
p = { id = "x.y", version.ref = "kotlin" }
"""


def test_normalize_and_default_name(tmp_path):
    assert normalize("androidx-core_ktx.x") == "androidx.core.ktx.x"
    assert default_name(tmp_path / "libs.versions.toml") == "libs"
    assert default_name(tmp_path / "test.versions.toml") == "test"


def test_parse_entries_and_spans(tmp_path):
    f = tmp_path / "libs.versions.toml"
    f.write_text(TOML)
    cat = parse_catalog(f)
    assert set(cat.entries["version"]) == {"kotlin", "compose"}
    assert set(cat.entries["library"]) == {"a-b", "plain", "dotted", "multi", "subtable"}
    lines = TOML.splitlines()

    def text_of(kind, alias):
        return [" | ".join(lines[a - 1 : b]) for a, b in cat.get(kind, alias).spans]

    assert text_of("library", "a-b") == ['a-b = { module = "g:a", version.ref = "kotlin" }']
    assert cat.get("library", "dotted").spans == [(9, 9), (10, 10)]  # one span per dotted-key line
    assert cat.get("library", "multi").spans[0] == (11, 11)
    assert text_of("library", "subtable")[0].startswith("[libraries.subtable]")
    assert cat.get("bundle", "all").spans[0][1] - cat.get("bundle", "all").spans[0][0] == 3
    assert cat.get("plugin", "p").line == len(lines)


def test_ignore_comments(tmp_path):
    f = tmp_path / "libs.versions.toml"
    f.write_text(
        '[libraries]\n# catalog-lint: ignore=unused-library, duplicate-library\nfoo = "g:foo:1"\n'
        'bar = "g:bar:1" # catalog-lint: ignore\nbaz = "g:baz:1"\n'
    )
    cat = parse_catalog(f)
    assert cat.get("library", "foo").ignored == {"unused-library", "duplicate-library"}
    assert cat.get("library", "bar").ignored == {"*"}
    assert cat.get("library", "baz").ignored == set()


def test_invalid_toml_raises(tmp_path):
    f = tmp_path / "libs.versions.toml"
    f.write_text("[versions\nx = 1")
    with pytest.raises(CatalogError) as exc:
        parse_catalog(f)
    assert "invalid TOML" in str(exc.value)


def test_non_table_section_raises(tmp_path):
    f = tmp_path / "libs.versions.toml"
    f.write_text('versions = "oops"\n')
    with pytest.raises(CatalogError):
        parse_catalog(f)


def test_missing_file_raises(tmp_path):
    with pytest.raises(CatalogError):
        parse_catalog(tmp_path / "nope.versions.toml")


def test_data_helpers():
    assert library_module("g:n:1") == ("g", "n")
    assert library_module({"module": "g:n"}) == ("g", "n")
    assert library_module({"group": "g", "name": "n"}) == ("g", "n")
    assert library_module({"nonsense": 1}) is None
    assert version_ref({"version": {"ref": "k"}}) == "k"
    assert version_ref({"version": "1"}) is None
    assert version_literals("library", "g:n:1.+") == ["1.+"]
    assert version_literals("library", {"module": "g:n:2"}) == ["2"]
    assert version_literals("version", {"strictly": "[1,2[", "prefer": "1.5"}) == ["1.5"]
    assert version_literals("plugin", {"id": "x", "version": "1.0"}) == ["1.0"]
    assert version_literals("plugin", "x:3") == ["3"]
