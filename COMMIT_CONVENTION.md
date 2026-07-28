# Commit Convention

This project uses **Conventional Commits v1.0.0**. A machine-readable decision tree for choosing a type lives alongside this file in `commit-decision-tree.yaml`. This file is self-contained — everything needed to write a compliant message is here. It is designed to be copied verbatim into any project; only the [Project-specific notes](#project-specific-notes) section at the bottom should change per repo.

## Format

```
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

## Rules

1. A commit MUST be prefixed with a type (a noun: `feat`, `fix`, etc.), followed by an optional scope, an optional `!`, and a required terminal colon and space.
2. `feat` MUST be used when a commit adds a new feature.
3. `fix` MUST be used when a commit patches a bug.
4. A scope MAY be provided after a type: a noun describing the section of the codebase, in parentheses — e.g. `fix(parser):`.
5. A description MUST immediately follow the colon and space: a short summary of the change, e.g. `fix: array parsing issue when multiple spaces were contained in string`.
6. A longer body MAY follow the description, beginning one blank line after it. It is free-form and may span multiple paragraphs.
7. One or more footers MAY follow the body, one blank line after it. Each footer is a token, then `: ` (or ` #`), then a value (git-trailer style). Footer tokens use `-` in place of whitespace (e.g. `Acked-by`); `BREAKING CHANGE` is the one exception.
8. A footer's value may span multiple lines; parsing stops at the next valid footer token.
9. **Breaking changes** MUST be indicated either by a `!` immediately before the colon (`feat(api)!: ...`) or by a `BREAKING CHANGE: <description>` footer — or both. With `!`, the footer may be omitted and the description explains the break.
10. `BREAKING-CHANGE` (hyphenated) is synonymous with `BREAKING CHANGE`, and the token is case-insensitive for this footer only; all other units of the message are case-insensitive except that consistency is expected.
11. Types other than `feat` and `fix` MAY be used freely (see the recommended set below).

## Recommended types

| Type | Use for |
|---|---|
| `feat` | New capability or behavior (correlates with **MINOR** in SemVer) |
| `fix` | Bug fix (correlates with **PATCH** in SemVer) |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding or correcting tests |
| `build` | Build system or external dependencies |
| `ci` | CI configuration and scripts |
| `chore` | Maintenance that touches no src/test behavior (tooling, config) |
| `style` | Formatting, whitespace — no meaning change |
| `revert` | Reverts a previous commit (reference it in the body/footer) |

A `!`/`BREAKING CHANGE` on **any** type correlates with **MAJOR** in SemVer.

## House style

- Description: imperative mood ("add", not "added"/"adds"), lowercase, no trailing period, aim for ≤ 72 characters.
- Body: explain *what* and *why*, not *how*.
- One logical change per commit.

## Examples

```
feat(lang): add Polish language
```

```
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Reviewed-by: Z
Refs: #123
```

```
feat(api)!: send an email to the customer when a product is shipped
```

```
chore!: drop support for Node 6

BREAKING CHANGE: use JavaScript features not available in Node 6.
```

## Project-specific notes

<!-- Edit this section per project; everything above is portable as-is. -->

- Planning-phase repo: most commits are `docs` (ADRs, POLICY, Overview, diagrams) or `chore` (justfile, uv config, scripts).
- Suggested scopes: `adr`, `policy`, `diagrams`, `overview`, `just`, `scripts`.
- A ratified change to `docs/POLICY.md` **Laws** is a breaking change: `docs(policy)!: ratify ADR-0003 deltas`.