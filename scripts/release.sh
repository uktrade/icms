#!/usr/bin/env bash

#Exit on error
set -oe pipefail

# define branch names
BRANCH=$(git rev-parse --abbrev-ref HEAD) # current Git branch
DEV_BRANCH="develop"
PRODUCTION_BRANCH="master"
BUMP="$1" # major|minor|patch
REMOTE=origin


function validate() {
  # validate bump string
  [ -z "$BUMP" ] && echo "Please speficy version (major|minor|patch)" && exit 1

  if [[ -n $(git status --porcelain) ]]; then
    echo "Repo is dirty" && \
    echo "Please stash or commit your changes before releasing" && \
    exit 1;
  fi
}

function switch_to() {
    echo "Switching to $1"
    git checkout --quiet $1
}

function update() {
    switch_to $1
    echo "Pulling latest $1"
    git pull --rebase --quiet
}

function merge_release_to() {
  update "$1"
   echo "Merging release to $1"
   git merge --quiet --no-edit --no-ff $releaseBranch
}

function fetch() {
  #Fetch remote trackers for releasing
  echo "Fetching remote branches (git fetch)"
  git fetch --quiet
}

function on_error() {
  local line="$1"
  echo "Error on line:$line"
  git stash drop # drop all changes made by release script
  git reset --head "$REMOTE" "$DEV_BRANCH"
  switch_to "$BRANCH"
  git branch -D "$releaseBranch" || true
}

trap 'on_error $LINENO' ERR # Run on_error on any error

# ------- MAIN --------#
validate
fetch
update $PRODUCTION_BRANCH
update $DEV_BRANCH

# Read current version on dev branch
version=$(<VERSION)
echo "Current version is $version"
newVersion=$(scripts/bump_version.py "$BUMP" "$version")  # Bumped version
releaseBranch="release/$newVersion"

# create the release branch from develop branch
echo "Creating release branch $releaseBranch from $DEV_BRANCH"
git checkout --quiet -b $releaseBranch

echo "$newVersion" > VERSION
echo "Bumped version to $newVersion"

# commit version number increment
git commit -am "version $version"

merge_release_to $PRODUCTION_BRANCH
merge_release_to $DEV_BRANCH

git branch -d $releaseBranch # Delete release branch

# create tag for new version from -master
git tag $newVersion
#Atomic ensures nothing is pushed if any of the repos fails to push
git push --atomic "$REMOTE" $DEV_BRANCH $PRODUCTION_BRANCH $newVersion

#switch back to branch started with
switch_to $BRANCH
