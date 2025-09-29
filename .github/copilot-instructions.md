1. Please use single quotes (') when doing auto-completion, then fall back to double quotes (") if single quotes have been used in the same line.
2. When generating commit messages, use the following conventional commit types, based on the Conventional Commits specification:
    1. fix: a commit of the type fix patches a bug in your codebase (this correlates with PATCH in Semantic Versioning).
    2. feat: a commit of the type feat introduces a new feature to the codebase (this correlates with MINOR in Semantic Versioning).
    3. BREAKING CHANGE: a commit that has a footer BREAKING CHANGE:, or appends a ! after the type/scope, introduces a breaking API change (correlating with MAJOR in Semantic Versioning). A BREAKING CHANGE can be part of commits of any type.
    4. types other than fix: and feat: are allowed, for example @commitlint/config-conventional (based on the Angular convention) recommends build:, chore:, ci:, docs:, style:, refactor:, perf:, test:, and others.
    5. footers other than BREAKING CHANGE: <description> may be provided and follow a convention similar to git trailer format.
