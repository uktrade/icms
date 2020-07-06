#!/usr/bin/env bash

# Start the server
make debug > /dev/null & sleep 5

# Run bdd tests
make bdd
result=$?

# Stop the server
make down

exit $result

