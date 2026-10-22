# Sweep36 — RMK firmware

[RMK](https://github.com/rmk-rs/rmk) firmware for a Sweep36 split keyboard with two nice!nano v2 controllers, connected over BLE. It ports the ZMK config in [riccardoflp/swweeep_36](https://github.com/riccardoflp/swweeep_36).

The left half is the central: it connects to the host over USB or BLE. The right half is the peripheral: it only talks to the left half.

## Prerequisites

- Rust stable with the `thumbv7em-none-eabihf` target (`rust-toolchain.toml` installs it)
- [Arm GNU toolchain](https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads), with `arm-none-eabi-gcc` on `PATH`. RMK uses it to build the P-256 assembly for BLE pairing.
- A checkout of RMK `main` next to this folder, at `../rmk`.
- `cargo-make`, `flip-link`, `cargo-binutils` and `cargo-hex-to-uf2`:

  ```bash
  cargo install cargo-make flip-link cargo-binutils cargo-hex-to-uf2
  ```

## Build

```bash
cargo make uf2 --release
```

This writes `sweep36-left.uf2` and `sweep36-right.uf2`.

## Flash

1. Put one half into bootloader mode: double-tap its reset button, or press `Bootloader` on the ADJ layer (see [Layers](#layers)). A USB drive named `NICENANO` appears.
2. Copy the matching `.uf2` file onto the drive. The half reboots into the new firmware.
3. Repeat for the other half.

The `Bootloader` key always reboots the **left** half, because the left half processes every key. Flash the right half with a double tap on its reset button.

The firmware is linked at `0x1000`, so it replaces the SoftDevice left by the factory firmware. A regular ZMK `.uf2` expects that SoftDevice and does not boot afterwards.

### Go back to ZMK

[riccardoflp/swweeep_36](https://github.com/riccardoflp/swweeep_36) also builds ZMK without the SoftDevice reservation. To switch back:

1. Download the `firmware` artifact from the latest successful run in its [Actions tab](https://github.com/riccardoflp/swweeep_36/actions).
2. Flash `settings_reset-nosd` to each half, to clear the RMK settings.
3. Flash `swweeep_left-nosd` to the left half and `swweeep_right-nosd` to the right half.

## Layers

| # | Name    | Reached by                       |
|---|---------|----------------------------------|
| 0 | `base`  | default                          |
| 1 | `nav`   | hold Tab (left thumb, inner)     |
| 2 | `mouse` | hold Delete (right thumb, outer) |
| 3 | `sym`   | hold Backspace (right thumb)     |
| 4 | `func`  | hold Escape (left thumb, outer)  |
| 5 | `num`   | hold Enter (right thumb, inner)  |
| 6 | `adj`   | hold Q or P                      |

Press F and J together to toggle Caps Word. This works on every layer except `adj`.

The keymap and all behaviors are defined in [`keyboard.toml`](keyboard.toml). You can also edit the keymap live with [Vial](https://get.vial.today/), over USB or BLE.

## Bluetooth

The ADJ layer holds the BLE keys, on the right half:

- `BT0`–`BT3`: switch to profile 0–3. Hold the key for 5 seconds to clear that profile and pair a new host.
- `Next BT` / `Prev BT`: cycle through the profiles.
- `Clear BT`: forget the host paired to the current profile.
- `Switch Output`: toggle between USB and BLE when a USB cable is connected.

## Reset stored settings

Hold P and press Q (`ClearEeprom` on the ADJ layer) to erase the left half's storage and reboot it. Storage holds Vial changes and BLE bonds.

If the halves stop linking, the right half still holds the old bond. To reset both halves, add `clear_storage = true` under a `[storage]` section in `keyboard.toml`. Then build and flash both halves, remove the line, and flash both halves again.

## Test the keymap

The files in [`tests/`](tests) replay key presses through RMK's simulator and check the reports the host would receive:

- [`keymap.toml`](tests/keymap.toml) checks tap-hold timing: home-row mods, layer-taps, rolls, quick-tap and the Caps Word combo.
- [`zmk_parity.toml`](tests/zmk_parity.toml) taps every key on every layer and expects what the ZMK keymap sends. It is generated, so do not edit it by hand.

Run them after changing `keyboard.toml`:

```bash
bash scripts/test_keymap.sh
```

The script needs [`cargo-nextest`](https://nexte.st/).

To regenerate the parity tests from the ZMK keymap, run:

```bash
python scripts/gen_zmk_parity.py path/to/swweeep.keymap > tests/zmk_parity.toml
```

The tests cover keymap logic only. They do not exercise the hardware: pins, BLE pairing, battery reading, sleep and USB still need a check on the real keyboard.

## Differences from the ZMK config

- **Tap-hold mode**: timings match ZMK (200 ms hold, 150 ms quick-tap), but the keys use permissive hold instead of tap-preferred. RMK's tap-preferred equivalent sends keys pressed during the decision before the tap-hold key, so a fast F→H roll would type `hf`. With permissive hold:
  - a key pressed **and released** while a layer-tap is held uses the layer;
  - a same-hand key tapped while a home-row mod is held stays a tap;
  - an opposite-hand key tapped while a home-row mod is held gets the modifier.
- **Caps Word**: it also continues through Backspace and Delete, types `-` as `_`, and turns off after 5 seconds without typing. In ZMK only `_` and `-` continued it.
- **`C_PAUSE`**: RMK has no consumer Pause keycode, so the key sends Play/Pause.
- **`K_REDO`**: in RMK the `Again` keycode repeats the last key, so Redo sends Ctrl+Shift+Z.
- **`&ext_power`**: RMK has no equivalent. The Sweep powers nothing through VCC, so these keys are `No`.
- **`&out OUT_USB` / `OUT_BLE`**: RMK has a single USB/BLE toggle, so all four output keys send `Switch Output`.
- **Scroll keys**: RMK sends `MouseWheelUp` as a negative wheel value, which scrolls down, so the keymap swaps `MouseWheelUp` and `MouseWheelDown`. Remove the `scroll_up` and `scroll_down` aliases once RMK fixes the sign, or the keys scroll the wrong way.
- **Mouse keys**: the speed is tuned through `mouse_key_interval` and `mouse_wheel_interval`, so acceleration does not match ZMK exactly.
- **Sleep**: after an hour idle the keyboard enters BLE idle sleep, not ZMK's deep sleep. Any key wakes it.
