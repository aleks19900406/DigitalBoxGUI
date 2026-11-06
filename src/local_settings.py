"""Settings that belong to this computer and must not be stored in git (e.g. the password of the RPi boxes).

The value is read from the environment variable DIGITAL_BOX_PASSWORD or from local_settings.json next to the
application (see local_settings.example.json)."""
import json
import os

from .paths import APPLICATION_ROOT

SETTINGS_FILE = APPLICATION_ROOT / "local_settings.json"
PASSWORD_VARIABLE = "DIGITAL_BOX_PASSWORD"


def load_rpi_password():
    """Password of the user `pi` on the digital boxes; an empty string when it is not configured."""
    password = os.environ.get(PASSWORD_VARIABLE)
    if password:
        return password
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as file:
            return str(json.load(file).get("rpi_password", ""))
    except (OSError, ValueError, AttributeError):
        return ""
