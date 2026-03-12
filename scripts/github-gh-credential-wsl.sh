#!/bin/sh
set -eu

CMD_EXE="/mnt/host/c/Windows/System32/cmd.exe"
WIN_GH='C:\Program Files\GitHub CLI\gh.exe'

op="${1:-}"
if [ "$op" != "get" ]; then
  exit 0
fi

token="$("$CMD_EXE" /c "\"$WIN_GH\" auth token" | tr -d '\r')"
if [ -z "$token" ]; then
  exit 1
fi

printf 'username=x-access-token\n'
printf 'password=%s\n' "$token"
