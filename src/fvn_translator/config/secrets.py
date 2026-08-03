import os

import keyring
from keyring.errors import KeyringError

SERVICE = "fvn-translator"


def environment_name(secret_ref: str) -> str:
    return "FVN_TRANSLATOR_" + "".join(
        character if character.isalnum() else "_" for character in secret_ref.upper()
    )


def get_secret(secret_ref: str, *, temporary: str | None = None) -> str | None:
    try:
        stored = keyring.get_password(SERVICE, secret_ref)
    except KeyringError:
        stored = None
    return stored or os.getenv(environment_name(secret_ref)) or temporary


def set_secret(secret_ref: str, value: str) -> None:
    keyring.set_password(SERVICE, secret_ref, value)
