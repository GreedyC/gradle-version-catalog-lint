import json
import tomllib

import pytest

from catalog_lint import __version__
from catalog_lint.cli import main

CATALOG = """\
[versions]
used = "1"
orphan = "2"  # leftover

[libraries]
live = { module = "g:live", version.ref = "used" }
dead = { module = "g:dead", version.ref = "orphan" }
dotted.module = "g:dotted"
dotted.version = "1"
multi = { group = "g", name = "multi" }

[bundles]
dead-b = [
  "dead",
  "multi",
]

[plugins]
p = { id = "x.p", version = "1" }
"""

FILES = {
    "settings.gradle.kts": "",
    "gradle/libs.versions.toml": CATALOG,
    "app/build.gradle.kts": "dependencies { implementation(libs.live) }",
}


@pytest.fixture
def proj(make_project):
    return make_project({k: v for k, v in FILES.items()})


def test_exit_codes(proj, capsys):
    assert main([str(proj), "--no-color"]) == 1
    assert main([str(proj), "--fail-on", "never"]) == 0
    assert main([str(proj), "--fail-on", "error"]) == 0  # only warnings present
    capsys.readouterr()


def test_clean_project_exit_zero(make_project, capsys):
    root = make_project(
        {
            "settings.gradle.kts": "",
            "gradle/libs.versions.toml": "[libraries]\na = 'g:a:1'\n",
            "build.gradle.kts": "libs.a",
        }
    )
    assert main([str(root)]) == 0
    assert "No problems found." in capsys.readouterr().out


def test_usage_errors(tmp_path, capsys):
    assert main([str(tmp_path / "missing")]) == 2
    assert main([str(tmp_path)]) == 2  # no catalog
    assert main([str(tmp_path), "--disable", "nope"]) == 2
    assert main([str(tmp_path), "--dry-run"]) == 2
    err = capsys.readouterr().err
    assert "does not exist" in err and "no version catalog" in err and "unknown rule" in err


def test_invalid_catalog_exit_two(make_project, capsys):
    root = make_project({"gradle/libs.versions.toml": "[versions\n"})
    assert main([str(root)]) == 2
    assert "invalid TOML" in capsys.readouterr().err


def test_json_output(proj, capsys):
    main([str(proj), "--format", "json"])
    doc = json.loads(capsys.readouterr().out)
    assert doc["schema"] == 1 and doc["tool"]["version"] == __version__
    assert doc["summary"]["warning"] == len(doc["findings"]) > 0
    assert {f["rule"] for f in doc["findings"]} >= {"unused-library", "unused-version", "unused-bundle"}
    assert all(f["file"] == "gradle/libs.versions.toml" for f in doc["findings"])


def test_github_output(proj, capsys):
    main([str(proj), "--format", "github"])
    lines = capsys.readouterr().out.splitlines()
    assert lines and all(ln.startswith("::warning file=gradle/libs.versions.toml,line=") for ln in lines)


def test_sarif_output(proj, capsys):
    main([str(proj), "--format", "sarif"])
    doc = json.loads(capsys.readouterr().out)
    assert doc["version"] == "2.1.0"
    run = doc["runs"][0]
    rule_ids = {r["id"] for r in run["tool"]["driver"]["rules"]}
    assert run["results"] and all(r["ruleId"] in rule_ids for r in run["results"])
    loc = run["results"][0]["locations"][0]["physicalLocation"]
    assert loc["artifactLocation"]["uri"] == "gradle/libs.versions.toml"
    assert loc["region"]["startLine"] >= 1


def test_fix_dry_run_does_not_write(proj, capsys):
    path = proj / "gradle/libs.versions.toml"
    before = path.read_text()
    assert main([str(proj), "--fix", "--dry-run"]) == 0
    assert path.read_text() == before
    out = capsys.readouterr().out
    assert "-dead = " in out and "-orphan" in out.replace('= "2"', "orphan")


def test_fix_removes_unused_and_result_is_clean(proj, capsys):
    path = proj / "gradle/libs.versions.toml"
    assert main([str(proj), "--fix"]) == 0
    data = tomllib.loads(path.read_text())
    assert set(data["libraries"]) == {"live"}
    assert set(data["versions"]) == {"used"}
    assert "bundles" in data and data["bundles"] == {}  # header kept, entries gone
    assert "plugins" in data and data["plugins"] == {}
    assert main([str(proj)]) == 0
    err = capsys.readouterr().err
    assert "removed 6 unused" in err


def test_disable_and_config(proj, capsys):
    (proj / ".catalog-lint.toml").write_text(
        'disable = ["unused-bundle"]\nignore = ["libraries:dead", "orphan"]\nfail-on = "error"\n'
    )
    assert main([str(proj), "--format", "json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    aliases = {(f["rule"], f["alias"]) for f in doc["findings"]}
    assert ("unused-bundle", "dead-b") not in aliases
    assert ("unused-library", "dead") not in aliases
    assert ("unused-version", "orphan") not in aliases
    assert ("unused-library", "dotted") in aliases


@pytest.mark.parametrize(
    "content,msg",
    [
        ('disable = ["nope"]', "unknown rule"),
        ("wat = 1", "unknown option"),
        ('fail-on = "loud"', "fail-on"),
        ("disable = 5", "list of strings"),
        ("[[[", "invalid TOML"),
    ],
)
def test_bad_config(proj, capsys, content, msg):
    (proj / ".catalog-lint.toml").write_text(content)
    assert main([str(proj)]) == 2
    assert msg in capsys.readouterr().err


def test_list_rules(capsys):
    assert main(["--list-rules"]) == 0
    assert "unused-library" in capsys.readouterr().out


def test_explicit_toml_path(proj, capsys):
    assert main([str(proj / "gradle/libs.versions.toml"), "--format", "json"]) == 1
    assert json.loads(capsys.readouterr().out)["findings"]


def test_example_project(capsys):
    from pathlib import Path

    example = Path(__file__).parent.parent / "examples" / "android-app"
    assert main([str(example), "--format", "json"]) == 1
    doc = json.loads(capsys.readouterr().out)
    rules = {f["rule"] for f in doc["findings"]}
    assert {"unused-library", "unused-version", "unused-plugin", "unused-bundle", "duplicate-library",
            "dynamic-version", "snapshot-version", "hardcoded-dependency", "unknown-lookup"} <= rules  # fmt: skip
