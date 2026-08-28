"""Autenticação das rotas da API."""

from __future__ import annotations

from fastapi import Header, HTTPException

from acc_nomad.config import settings
from acc_nomad.services.supabase_client import SupabaseNotConfiguredError, get_supabase_client


def verify_api_secret(x_api_secret: str | None = Header(default=None)) -> None:
    if settings.api_secret and x_api_secret != settings.api_secret:
        raise HTTPException(status_code=401, detail="API secret inválido")


def verify_api_secret_or_user(
    x_api_secret: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
) -> None:
    """Aceita X-Api-Secret (server) ou Bearer JWT Supabase (browser)."""
    if settings.api_secret and x_api_secret == settings.api_secret:
        return

    token = _bearer_token(authorization)
    if token and _jwt_valid(token):
        return

    raise HTTPException(
        status_code=401,
        detail="Não autorizado. Faça login novamente ou verifique API_SECRET no servidor.",
    )


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization[7:].strip()
    return token or None


def _jwt_valid(token: str) -> bool:
    try:
        client = get_supabase_client()
    except SupabaseNotConfiguredError:
        return False

    try:
        response = client.auth.get_user(jwt=token)
        return response is not None and response.user is not None
    except Exception:
        return False
