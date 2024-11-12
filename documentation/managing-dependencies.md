# Managing dependencies

## Overview

Dependencies in this project are managed using
[pip-compile  (from pip-tools)](https://github.com/jazzband/pip-tools).

Dependencies files are found in the `requirements` folder. When updating or adding a dependency manually update the relevant `.in` file. 
Dependencies for all platforms are specified in `requirements-base.in`.
Production only dependencies in `requirements-prod.in` and development dependencies only in `requirements-dev.in`.
These are pinned to a specific version to make it easier to control
and track upgrades to direct dependencies. A small number of indirect dependencies are also
included in `requirements-base.in` where we have previously had breakages caused by updates to
those libraries.

`requirements-playwright.txt`,  `requirements-prod.txt`,  `requirements-dev.txt`, are lock files generated using pip-compile and should not be manually edited.

Anything that does not need to be in production should be included within the `requirments-dev.in` (which is manually edited).

## Installing dependencies

Dependencies should always be installed using `requirements-dev.txt` or `requirements-prod.txt`. The first time you do this locally,
you should run:

```shell
make setup
```

After that, you can run `pip-sync requirements-dev.txt` instead.
(Note that pip-sync will also remove any installed dependencies that are not specified in the
lock file, such as removed dependencies or packages manually installed using pip.)

## How to add a new dependency

1. Add the package to the relevant section in `requirements-base.in`, specifying a particular version
   (typically the latest at time of adding).

2. Run `make update-requirements` to regenerate all requirements
  Note: This will also update indirect dependencies.

3. Run `pip-sync requirements-dev.txt` to install the new locked dependencies locally. (You can also use
   `pip install -r requirements-dev.txt`, but that may leave behind redundant packages that
   have been removed which can cause problems.)

4. Commit the changes as part of your feature branch.

5. Before merging remove the image cache from aws ecr to ensure no unintended packages are included in the image build.

## Updating package-lock.json

1. Run the following to update the sub-dependencies of pinned packages:
```bash
npm i --package-lock-only
npm audit fix
```

## Updating V2 Javascript dependencies (When they get updated):
Run the following command, this will install dependencies and copy them to the correct place

```bash
make requirements-web
```

see the following code for the config:

```
# icms/config/settings_local.py
NPM_STATIC_FILES_LOCATION =
NPM_FILE_PATTERNS
```

## V3 Front-end Dependencies

The front-end assets were initially added by doing the following:

```bash
# Install nvm
# Download and install nvm, node & npm (https://nodejs.org/en/download/package-manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install --lts

# check everything installed correctly.
node -v
npm -v

# Install gds package
npm install sass
npm install govuk-frontend --save
```

The govuk-frontend package assets are currently manually copied from node_modules/ to assets/ by following these instructions:

https://frontend.design-system.service.gov.uk/installing-with-npm/#get-the-css-assets-and-javascript-working

This will change if and when we need to use a bundler to customise our gds frontend.

https://frontend.design-system.service.gov.uk/install-using-precompiled-files/#what-you-cannot-do-with-the-precompiled-files
