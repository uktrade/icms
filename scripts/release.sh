#!/usr/bin/env bash

#Exit on error
set -oe pipefail

# define branch names
WORK_BRANCH=$(git rev-parse --abbrev-ref HEAD) # current Git branch
BUMP="$1" # major|minor|patch
REMOTE=origin
DEV="develop"
PROD="master"
dev_head=
prod_head=



# if [[ -n $(git status --porcelain) ]]; then
#   echo "Repo is dirty" && \
#   echo "Please stash or commit your changes before releasing" && \
#   exit 1;
# fi

# validate bump string
[ -z "$BUMP" ] && echo "Please speficy version (major|minor|patch)" && exit 1

function switch_to() {
    echo "Switching to $1"
    git checkout --quiet "$1"
}

function exists() {
  if [ -n "$1" ]; then
    git show-ref -q --heads "$1"
  else
    exit 1
  fi
}

function reset() {
  local branch="$1"
  local rev="$2" # reset reference, commit id or branch name
  if [[ -n "$rev" ]]; then
    echo "Resetting branch $branch to commit $rev"
    switch_to "$branch"
    git reset --hard "$rev"
  fi
}

function merge_release_to() {
   switch_to "$1"
   echo "Merging release to $1"
   git merge --quiet --no-edit --no-ff $releaseBranch
}

function fetch() {
  #Fetch remote trackers for releasing
  echo "Fetching remote branches (git fetch)"
  git fetch --quiet
}

function clean() {
  reset "$PROD" "$prod_head"
  reset "$DEV" "$dev_head"
  if exists "$releaseBranch"; then git branch -D "$releaseBranch"; fi
  if exists "$newVersion"; then git tag -D "$newVersion"; fi
  switch_to "$WORK_BRANCH" # switch back
}

function on_error() {
  local line="$1"
  echo "Error on line:$line, reverting all changes"
  git checkout -f # drop all changes
  clean
}

# ------- MAIN --------#
fetch
trap 'on_error $LINENO' INT # Run on_error on interrupts
trap 'on_error $LINENO' ERR # Run on_error on any error

switch_to "$PROD"
prod_head="$(git rev-parse HEAD)"
reset "$PROD" "${REMOTE}/$PROD"
switch_to "$DEV"
dev_head="$(git rev-parse HEAD)"
reset "$DEV" "${REMOTE}/$DEV"

# Read current version on dev branch
version=$(<VERSION)
echo "Current version is $version"
newVersion=v"$(scripts/bump_version.py "$BUMP" "$version")" # Bumped version

# create the release branch from develop branch
releaseBranch="release/$newVersion"
echo "Creating release branch $releaseBranch from $DEV"
git checkout --quiet -b $releaseBranch

echo "$newVersion" > VERSION
echo "Bumped version to $newVersion"

# commit version number increment
git commit -am "version $version"

merge_release_to "$PROD"
merge_release_to "$DEV"

# create tag for new version from -master
# git tag "${newVersion}"
#Atomic ensures nothing is pushed if any of the repos fails to push
# git push --atomic "$REMOTE" "$DEV" "$PROD" "${newVersion}"

clean
