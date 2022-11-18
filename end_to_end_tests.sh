#!/bin/zsh
clear
. .venv/bin/activate
echo "Running end to end tests"

# Some useful flags / options
# To Run tests in headed mode: --headed
# To slow down the tests: --slowmo 250
# Run tests in parallel (requires pytest-xdist): --numprocesses auto


# TODO: ICMSLST-1793 Use an Environment Variable for the base url.
#You can specify the base URL by setting the PYTEST_BASE_URL environment variable.
pytest --base-url http://localhost:8080 web/tests/end_to_end "$@"

echo "removing test cookies"
rm importer_user.json
rm exporter_user.json
rm ilb_admin.json
