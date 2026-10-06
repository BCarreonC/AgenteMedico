import unicodedata


def normalize_text(
    value: str,
) -> str:
    """
    Normaliza texto para comparaciones.

    Ejemplos:
    "Médico" -> "medico"
    "medico" -> "medico"
    "PRÓXIMAS  CITAS" -> "proximas citas"
    "Sí" -> "si"

    No debe utilizarse para reemplazar el texto original
    que se muestra al usuario.
    """

    if not value:
        return ""

    normalized = unicodedata.normalize(
        "NFD",
        value,
    )

    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )

    normalized = normalized.casefold()

    return " ".join(
        normalized.split()
    )


def normalize_key(
    value: str,
) -> str:
    """
    Normalización pensada para claves/intents.

    "Buscar Paciente" -> "buscar_paciente"
    "Médico" -> "medico"
    """

    return normalize_text(
        value
    ).replace(
        " ",
        "_",
    )