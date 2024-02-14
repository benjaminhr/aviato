#!/usr/bin/env bash

set -eEuo pipefail

_on_error() {
  trap '' ERR
  line_path=$(caller)
  line=${line_path% *}
  path=${line_path#* }

  echo ""
  echo "ERR $path:$line $BASH_COMMAND exited with $1"
  exit 1
}
trap '_on_error $?' ERR

_shutdown() {
  # clear traps when already shutting down
  trap '' TERM INT ERR
  
  # send kill to entire process tree (including self, that's why ingoring above)
  kill 0
  
  # wait for all processes
  wait
  
  # unless called new processes can start after trap exits
  exit 0
}

trap _shutdown TERM INT

echo "> Starting web server"
(
  exec python src/web_server.py 
) >/tmp/web_server.log 2>&1 &

echo "> Starting bot server"
python src/bot_server.py