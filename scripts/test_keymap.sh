#!/usr/bin/env bash
# Runs tests/keymap.toml in RMK's scenario simulator against this keyboard.toml.
# Requires cargo-nextest and an RMK checkout at ../rmk (override with RMK_DIR).
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
rmk_dir="${RMK_DIR:-$root/../rmk}/rmk"
scenarios="$rmk_dir/tests/scenarios"

cleanup() {
    rm -f "$scenarios/sweep36.toml" "$scenarios/boards/sweep36.toml"
    touch "$rmk_dir/tests/integration/main.rs"
}
trap cleanup EXIT

# The simulator rejects [rmk]: its capacities are compile-time constants.
awk '/^\[rmk\]/ { skip = 1; next } /^\[/ { skip = 0 } !skip' \
    "$root/keyboard.toml" > "$scenarios/boards/sweep36.toml"
cp "$root/tests/keymap.toml" "$scenarios/sweep36.toml"
touch "$rmk_dir/tests/integration/main.rs"

cd "$rmk_dir"
cargo nextest run --config-file ../.config/nextest.toml \
    --no-default-features --features=split,vial,storage,async_matrix,_ble \
    --test integration sweep36::
