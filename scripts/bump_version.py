import sys,semver
from pathlib import Path

update=sys.argv[1]
version=Path('VERSION').read_text().strip()
newVersion=''

if update=='major':
  newVersion=semver.bump_major(version)
elif update=='minor':
  newVersion=semver.bump_minor(version)
elif update=='patch':
  newVersion=semver.bump_patch(version)
else:
  error="Invalid version '{}', please specify version in (major|minor|patch)".format(update)
  print(error)
  exit(1)

print(newVersion)
