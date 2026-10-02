# Security policy

`catalog-lint` only reads local files (and, with `--fix`, rewrites `*.versions.toml` files you point it
at). It performs no network access and executes no project code.

If you find a security issue (for example a crafted file that makes the tool hang, crash, or write
outside the target catalog), please report it privately through GitHub's
["Report a vulnerability"](https://github.com/cosmichackerx/gradle-version-catalog-lint/security/advisories/new)
form instead of opening a public issue.
