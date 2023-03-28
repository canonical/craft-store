# Craft Store

This project aims to provide python interfaces for communicating with
Canonical Stores, such as Charmhub and the Snap Store.

# License

Free software: GNU Lesser General Public License v3

# Documentation:

https://craft-store.readthedocs.io.

# Contributing

A `Makefile` is provided for easy interaction with the project. To see
all available options run:

```
make help
```

## Running tests

To run all tests in the suite run:

```
make tests
```

### Integration tests

Some integration tests require collaborator permission on the `craft-store-test-charm`
charm package on the staging craft-store. These can be run by creating a pull request.

Other integration tests simply require a valid login to the staging charmhub store.
These can be run by exporting charmhub staging credentials to the environment
variable `CRAFT_STORE_CHARMCRAFT_CREDENTIALS`. An easy way to do this is to 
create a `charmcraft.yaml` file containing the lines:

    charmhub:
      api-url: "https://api.staging.charmhub.io"
      storage-url: "https://storage.staging.snapcraftcontent.com"

and then running `charmcraft login --export cc.cred` to do the login and
`export CRAFT_STORE_CHARMCRAFT_CREDENTIALS=$(cat cc.cred)` to put the credentials
into the environment variable. Note that if you do not have collaborator permissions
on `craft-store-test-charm`, some tests will fail rather than being skipped.

## Adding new requirements

If a new dependency is added to the project run:

```
make freeze-requirements
```

## Verifying documentation changes

To locally verify documentation changes run:

```
make docs
```

After running, newly generated documentation shall be available at
`./docs/_build/html/`.

## Committing code

Please follow these guidelines when committing code for this project:

- Use a topic with a colon to start the subject
- Separate subject from body with a blank line
- Limit the subject line to 50 characters
- Do not capitalize the subject line
- Do not end the subject line with a period
- Use the imperative mood in the subject line
- Wrap the body at 72 characters
- Use the body to explain what and why (instead of how)

As an example:


    endpoints: support package attenuations

    Required in order to obtain credentials that apply only to a given package;
    be it charm, snap or bundle.

