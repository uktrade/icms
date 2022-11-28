Using Playwright
----------------
Playwright requires ICMS to be running: `make debug`

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
playwright install
```

To create a test using the codegen tool run this:
```bash
make create_end_to_end
```
