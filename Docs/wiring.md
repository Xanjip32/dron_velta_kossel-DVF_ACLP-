# Wiring: stock Kossel Linear Plus → SKR Pico v1.0 + Pi 3B

Power off and unplug before rewiring. The SKR Pico takes 12–24 V, so the stock **12 V** supply is fine.

| Stock part | SKR Pico connector | Klipper pin |
|---|---|---|
| Tower A motor (front-left, "X") | X-motor | gpio11/10/12 |
| Tower B motor (front-right, "Y" on TriGorilla) | **Z-motor** (matches config) | gpio19/28/2 |
| Tower C motor (rear, "Z" on TriGorilla) | **Y-motor** | gpio6/5/7 |
| Extruder motor | E-motor | gpio14/13/15 |
| Tower A / B / C top endstops | X-STOP / Z-STOP / Y-STOP | gpio4 / gpio25 / gpio3 |
| Clip-on Z probe | Z-probe header (signal + GND) | gpio22 |
| Hotend heater | HE | gpio23 |
| Hotend thermistor | TH0 | gpio27 |
| Bed heater | HB (bed MOSFET) | gpio21 |
| Bed thermistor | TB | gpio26 |
| 5015 part fan | FAN1 | gpio17 |
| 3010 hotend fan | FAN2 | gpio18 |
| 4010 electronics fan | FAN3 | gpio20 |

If a tower moves the wrong way, flip `dir_pin` (`!`) for that stepper. If the towers are swapped, swap the motor plugs, not the config.

## Raspberry Pi 3B

* **Data:** USB-A (Pi) → USB-C (Pico). Easiest option. Alternative: the Pico's Pi header with UART (`[mcu] serial: /dev/ttyAMA0`). That needs `enable_uart=1` and `dtoverlay=disable-bt` on the Pi.
* **Power:** the Pi 3B needs 5 V / 2.5 A. Either use the Pico's Pi power header (check BTT's manual for your board revision and its 5 V rating), or fit a separate 12 V → 5 V 3 A buck converter.
* Install MainsailOS on the SD card, then build Klipper for the RP2040 (`make menuconfig`: Raspberry Pi RP2040, 16 KiB bootloader, USB). Flash the Pico by holding BOOT and plugging in USB, then copy `klipper.uf2`.
* Copy `Firmware/printer.cfg` and set your `serial:` id from `ls /dev/serial/by-id/`.

## First start checklist

1. `QUERY_ENDSTOPS`: all open, then press each switch and check that the right one triggers.
2. Check that the temperatures read room temperature. Then run `PID_CALIBRATE HEATER=extruder TARGET=210` and `PID_CALIBRATE HEATER=heater_bed TARGET=60`.
3. `G28`, then `PROBE_CALIBRATE`, then `DELTA_CALIBRATE`, then `SAVE_CONFIG`. **Required**, because the new effector changes the geometry.
4. Move the head slowly around the edge of the bed and check that the arms, duct and fans clear the frame and skirts.
