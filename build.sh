#!/bin/bash

# Description: Make the PCB file from the keyboard.yaml file.

set -e
OUTPUT_DIR=output

pcbnew_pid=

build() {
  /usr/local/lib/node_modules/ergogen/src/cli.js . -o $OUTPUT_DIR &&
    {
      if [[ "$pcbnew_pid" ]]; then
        kill "$pcbnew_pid" || true
        rm -rf $OUTPUT_DIR/pcbs/\~main.kicad_pcb.lck
      fi
      flatpak run --command=pcbnew org.kicad.KiCad $OUTPUT_DIR/pcbs/main.kicad_pcb &
      pcbnew_pid=$!
    } || true
}

build
