[![Documentation Status](https://readthedocs.com/projects/canonical-craft-store/badge/?version=latest)](https://canonical-craft-store.readthedocs-hosted.com/en/latest/?badge=latest)

# Craft Store

This project aims to provide python interfaces for communicating with
Canonical Stores, such as Charmhub and the Snap Store.

# License

Free software: GNU Lesser General Public License v3

# Documentation:

https://canonical-craft-store.readthedocs-hosted.com.

# Contributing

## Set up a development environment

To install the necessary build tools, first run:

```bash
make setup
```

## Running tests

To run all tests in the suite run:

```
make test
```

### Integration tests

Some integration tests require collaborator permission on the `craft-store-test-charm`
charm package on the staging craft-store. These can be run by creating a pull request.

Other integration tests simply require a valid login to the staging charmhub store.
These can be run by exporting charmhub staging credentials to the environment
variable `CRAFT_STORE_CHARMCRAFT_CREDENTIALS`. An easy way to do this is to
run the following command:

```
CHARMCRAFT_STORE_API_URL=https://api.staging.charmhub.io charmcraft login --export cc.cred
```

to login and `export CRAFT_STORE_CHARMCRAFT_CREDENTIALS=$(cat cc.cred)` to put the
credentials into the environment variable. Note that if you do not have collaborator
permissions on the charm `craft-store-test`, you can override the environment variable
`CRAFT_STORE_TEST_CHARM` to point to a charm you do own.

## Adding new requirements

If a new dependency is added to the project run:

```
uv add '<dependency spec>'
```


## Verifying documentation changes

To locally verify documentation changes run:

```
make lint-docs
make docs
```


After running, newly generated documentation shall be available at
`./docs/_build/html/`.

While writing documentation, it may be useful to run `make docs-auto`, which will run
sphinx-autobuild.

## Committing code

craft-store uses the code and commit conventions common to the Starcraft team, which
can be found
[in our common base project](https://github.com/canonical/starbase/blob/main/HACKING.rst)
