#!/bin/bash

# BEGIN REPO CONFIGURATIONS
origin_repositories='/path/to/directory/with/git/origin/repositories'
shadow_repositories='/path/to/directory/with/git/shadow/repositories'
# ENDOF REPO CONFIGURATIONS

# BEGIN PROGRAMME PATHES
git="git"
python="python"
git_save_them_all_py="${0%/*}/git-save-them-all.py"
# ENDOF PROGRAMME PATHES

for repo in "$origin_repositories"/*
do
  if [ ! -d "$repo" ]
  then
    continue
  fi

  repo_name="${repo##*/}"
  shadow_repo="$shadow_repositories/$repo_name"

  echo "$repo -> $shadow_repo: begin..."

  if [ ! -d "$shadow_repo" ]
  then
    echo "$repo -> $shadow_repo: init..."

    GIT_DIR="$shadow_repo" "$git" init --bare
    GIT_DIR="$shadow_repo" "$git" remote add origin -- "$repo"
  fi

  GIT_DIR="$shadow_repo" "$git" fetch -pPt
  "$python" "$git_save_them_all_py" -- "$shadow_repo"

  echo "$repo -> $shadow_repo: done!"
done

# vi:ts=2:sw=2:et
