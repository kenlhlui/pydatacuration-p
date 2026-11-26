# Bump the Version

## Prerequisites

1. [Commitizen](https://commitizen-tools.github.io/commitizen/)

This repository has set up [Commitizen](https://commitizen-tools.github.io/commitizen/) for automatic version bumping. To bump the version, run the following command in the main branch:

```sh
cz bump
```

Then push the bump commit and its tag:

```sh
git push --follow-tags
```

Pushing the `bump:` commit to `main` triggers the release workflow, which publishes a GitHub Release for the pushed tag.

Test the version bumping by running:

```sh
cz bump --dry-run
```
