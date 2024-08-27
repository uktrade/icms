Using Playwright
----------------

Running `make end_to_end_test` will run the tests against the environment defined in the `E2E_XXX` environment variables in `.env`

`.env.local-docker` provides defaults for all required environment variables.

If running against the V2 Dev / Staging environments a VPN connection is required.

The tests can only be run when Staff-SSO and GOV.UK One Login are disabled.

```dotenv
STAFF_SSO_ENABLED=False
GOV_UK_ONE_LOGIN_ENABLED=False
```

The tests can be run locally or in a container.
```bash
make end_to_end_test
make end_to_end_test_local
```

To run Playwright locally follow the following commands (this is for running the tests and test generation):
```bash
# Activate a venv before doing this
pip install --upgrade pip
pip install pytest-playwright
playwright install chromium
```

Example showing how to debug a single test locally:
```bash
make end_to_end_test_local args="--headed --slowmo 250 -k test_can_create_fa_dfl"
```

To create a test using the codegen tool run this:
```bash
make create_end_to_end
```

To run the tests run either of the following
```bash
make end_to_end_test
# Supply any pytest / playwright args in args=""
make end_to_end_test args="--numprocesses 4"
```

Known issues
=============
- Invalid cookies cause tests to fail (this can happen if you swap between running tests locally and in a container).
  - Solution is to run: `make end_to_end_clear_session`
- The firearm tests will fail if the following environment variable is set to True e.g. `SEND_LICENCE_TO_CHIEF=True`