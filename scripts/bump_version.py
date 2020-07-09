#!/usr/bin/env python
import sys
import semver

bump = sys.argv[1]
version = sys.argv[2]

if bump == "major":
    newVersion = semver.bump_major(version)
elif bump == "minor":
    newVersion = semver.bump_minor(version)
elif bump == "patch":
    newVersion = semver.bump_patch(version)
else:
    error = "Invalid version '{}', please specify version in (major|minor|patch)".format(bump)
    print(error)
    exit(1)

print(newVersion)
