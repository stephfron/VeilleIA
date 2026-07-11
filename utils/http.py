"""
Helper HTTP partagé — GET avec retry sur erreurs transitoires.
Utilisé par api_sirene.py et api_dole.py.
"""
import time
import requests
from requests import Response


def get_with_retry(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    retryable: tuple[int, ...] = (429, 502, 503),
    max_attempts: int = 5,
    base_delay: float = 5.0,
    timeout: int = 30,
) -> Response:
    """
    Effectue un GET avec retry exponentiel sur les codes HTTP transitoires.

    Paramètres
    ----------
    retryable    : codes HTTP qui déclenchent un retry (défaut : 429, 502, 503)
    max_attempts : nombre total de tentatives
    base_delay   : délai de base en secondes (multiplié par le numéro de tentative)

    Retourne la dernière Response, succès ou échec — l'appelant appelle raise_for_status().
    Les erreurs réseau transitoires (timeout, connexion) déclenchent aussi un retry ;
    la dernière exception est relevée si toutes les tentatives échouent.
    """
    last_resp: Response | None = None
    last_exc: requests.exceptions.RequestException | None = None

    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            time.sleep(base_delay * (attempt + 1))
            continue

        last_resp = resp
        if resp.status_code not in retryable:
            return resp
        time.sleep(base_delay * (attempt + 1))

    if last_resp is not None:
        return last_resp
    raise last_exc  # type: ignore[misc]
