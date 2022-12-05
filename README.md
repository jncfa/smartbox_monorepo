# smartbox_monorepo

> Refactored version of the Smartbox Python services in a single repo.

## Getting Started

Install the package and its requirements using:

```bash
# go to the package folder
cd smartbox_monorepo

# create a virtual environment
virtualenv venv

# install package and its dependencies
pip install -e .
```

## How to use

After installing the package, you need to use one of the example configurations `config_mqtt_publico.json`, `config_mqtt_tailscale.json` or `config_sem_mqtt.json` and adjust it to work for the given smartbox, and place it in the same folder under the name `config.json`.

> TODO: In the future, this should still remain the default behaviour, but we should support passing a parameter a path to the configuration file.

After setting up everything you can start it using:

```bash
# go to the package folder
cd smartbox_monorepo

# start the acquisition service
smartbox_init_services
```

## Contributing

Please use the [issue tracker](https://github.com/WoW-Institute-of-Systems-and-Robotics/smartbox_monorepo/issues) for submmitting any issues, and use [pull requests](https://github.com/WoW-Institute-of-Systems-and-Robotics/smartbox_monorepo/pulls/) to patch those issues!

### Changelog

- Version 0.1.0:
    - First working version of the smartbox code, with all required base functionality, still missing the MQTT syncronization feature.
