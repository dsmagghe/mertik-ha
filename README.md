# Mertik Maxitrol fireplace for Home Assistant

Control a gas fireplace with a **Mertik Maxitrol WiFi module** from Home Assistant, locally, without any cloud.

This is a maintained fork of [djerik/mertik-ha](https://github.com/djerik/mertik-ha), with all credit for the protocol work going to the original author. The fork adds the fireplace's status sensors and groups everything under one device. It also keeps the integration domain (`mertik`) and the unique IDs, so an existing installation switches over without losing entities or automations.

Use at your own risk: this talks to a gas appliance. The integration only sends the same commands the Mertik app sends, but you remain responsible for safe use.

## What this fork adds (1.1.0)

- **Three binary sensors** that the module already reports but the original integration did not expose:
  - **Igniting**: on while the fireplace is lighting.
  - **Shutting Down**: on while it is going out.
  - **Guard Flame**: on while the pilot (guard) flame burns.
- **One device per fireplace.** All entities now belong to a single device (manufacturer Mertik Maxitrol), so they show up together on the device page and can be given an area at once.
- **No more "burning at height 13" while the fire is out.** With the guard (pilot) flame out, the module reports the maximum flame value (`FF`), which the original read as a burning fire. A fire now only counts as on when its guard flame burns or it is igniting, and the flame height never exceeds 12.
- **Correct status bits when the leading bit of the status word is 0.** The status word is 16 bits, but it was padded to 8, which shifted every bit when the first one was not set. All existing behaviour is unchanged when that leading bit is set.
- **Safe defaults** before the first status arrives, instead of an `AttributeError`.
- A Dutch translation of the setup dialog.
- Unit tests for the status parsing.

## Requirements

- A Mertik Maxitrol WiFi module connected to your network. The integration connects to it on TCP port 2000.
- **Give the module a fixed IP address** with a DHCP reservation in your router. The IP address is stored in the integration; if the module gets a new address, Home Assistant loses it until you set it up again.

## Installation

### Through HACS / the Home Assistant Marketplace (recommended)

1. Open HACS (in recent Home Assistant versions: the Marketplace).
2. Open the menu (three dots), choose **Custom repositories**, add `https://github.com/dsmagghe/mertik-ha` with category **Integration**.
3. Search for **Mertik Maxitrol**, download it, and restart Home Assistant.

### Manually

Copy the folder `custom_components/mertik` from this repository into the `custom_components` folder of your Home Assistant configuration, then restart Home Assistant.

## Setup

**Settings → Devices & services → Add integration → Mertik Maxitrol**, then enter:

- a **name** for the fireplace (it becomes the start of every entity name), and
- the **IP address** of the WiFi module.

## Entities

For a fireplace named `Fireplace`:

| Entity | What it does |
|---|---|
| `switch.fireplace` | Ignite the fireplace (on) or put it out via the guard flame (off). It is also on while igniting. |
| `switch.fireplace_aux` | Second burner (auxiliary flame), only on fireplaces that have one. |
| `number.fireplace_flame_height` | Flame height, 1 (lowest) to 12 (highest). |
| `light.fireplace_light` | The fireplace light, with brightness. |
| `sensor.fireplace_ambient_temperature` | Room temperature measured by the module or handset, in °C. |
| `binary_sensor.fireplace_igniting` | On while the fireplace is lighting. |
| `binary_sensor.fireplace_shutting_down` | On while the fireplace is going out. |
| `binary_sensor.fireplace_guard_flame` | On while the pilot flame burns. |

The module is polled every 10 seconds.

## Example: set the flame height once the fire is lit

A flame height sent during ignition is ignored by some fireplaces. Wait for the ignition to finish first:

```yaml
sequence:
  - action: switch.turn_on
    target:
      entity_id: switch.fireplace
  - wait_template: "{{ is_state('binary_sensor.fireplace_igniting', 'off') and is_state('switch.fireplace', 'on') }}"
    timeout: "00:02:00"
    continue_on_timeout: true
  - action: number.set_value
    target:
      entity_id: number.fireplace_flame_height
    data:
      value: 6
```

## Switching from djerik/mertik-ha

The domain and unique IDs are the same, so your config entry, entity IDs and automations stay as they are. After a restart the three binary sensors and the device appear.

Both repositories install into `custom_components/mertik`, and HACS / the Home Assistant Marketplace treats that folder as owned by the repository that installed it. It refuses to install this fork over it ("The mertik directory belongs to djerik/mertik-ha") and only uninstalls the original once the integration's setup is removed, which also deletes its devices and entities. Two ways to switch:

1. **Keep your setup (no re-configuration).** Copy `custom_components/mertik` from this repository's latest release over the existing folder, restart Home Assistant, then disable the update entity of `djerik/mertik-ha` (Settings → Entities, e.g. `update.mertik_maxitrol_update`) so an "update all" cannot put the original back. Updates of this fork are then installed the same way.
2. **Let HACS / the Marketplace manage this fork.** Write down your entity IDs, delete the Mertik integration, uninstall `djerik/mertik-ha`, add `https://github.com/dsmagghe/mertik-ha` as a custom repository, install it, restart, set up the fireplace again and rename the entities back to your old IDs.

## Development

The status parsing can be tested without Home Assistant:

```bash
python3 -m unittest discover -s tests -v
```

`PROTOCOL.md` describes what is known of the WiFi module's protocol.

## Changelog

- 2026-11-08 **1.1.0** (fork): binary sensors for igniting, shutting down and guard flame; one device per fireplace; the fire is off when the guard flame is out (no more height 13 on a cold fireplace); flame height capped at 12; 16-bit status parsing; defaults before the first status; Dutch translation; tests.
- 2026-02-24 1.0.0 (upstream): bug fixes for breaking Home Assistant changes.
- 2023-01-15 Initial version (upstream).

## License

GPL-3.0, like the original. See [LICENSE](LICENSE).
