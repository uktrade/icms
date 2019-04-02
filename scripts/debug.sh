#!/usr/env/bin bash

live_reload_pid=

start_livereload() {
  ./manage.py livereload &
  live_reload_pid=$!
}


run_server() {
  ./manage.py runserver

}
