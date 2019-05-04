#!/bin/sh -e
node index.js
http-server -p 9090 /reports
