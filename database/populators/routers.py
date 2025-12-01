from __future__ import annotations

from typing import Dict, Tuple

from sqlmodel import Session, select

from database.provider.models import Router

try:
    from settings import (
        FREE_PROVIDER_API_KEY,
        PROVIDER_API_BASE,
        PROVIDER_API_KEY,
        PROVIDER_GROUNDING_MODEL,
        PROVIDER_MODEL,
        PROVIDER_VISION_MODEL,
        PROVIDER_VISION_TOOL_MODEL,
    )
except Exception:
    raise ImportError(
        "Failed to import settings. Ensure that the settings module is correctly configured."
    )


def _existing_router(
    session: Session, model_name: str, api_endpoint: str
) -> Router | None:
    """
    Return an existing Router matching model_name + api_endpoint, or None.
    """
    return session.exec(
        select(Router).where(
            (Router.model_name == model_name) & (Router.api_endpoint == api_endpoint)
        )
    ).first()


def _create_router(
    session: Session, api_key: str, model_name: str, api_endpoint: str
) -> Router:
    """
    Create and persist a Router record.
    """
    router = Router(
        api_key=api_key,
        model_name=model_name,
        api_endpoint=api_endpoint,
        provider_type=Router.Provider.OPENAI,
    )
    session.add(router)
    session.commit()
    session.refresh(router)
    print(f"[populate_routers] Created router for model '{model_name}'.")
    return router


def populate_routers(engine) -> None:
    """
    Populate Router entries for each configured model.

    Creates routers for:
        - General model
        - Vision model
        - Vision tool model
        - Grounding model

    Skips creation if a router already exists for (model_name, api_endpoint).
    """
    desired: Dict[str, Tuple[str, str]] = {}

    if PROVIDER_MODEL:
        desired[PROVIDER_MODEL] = (FREE_PROVIDER_API_KEY, PROVIDER_API_BASE)

    if PROVIDER_VISION_MODEL and PROVIDER_VISION_MODEL != PROVIDER_MODEL:
        desired[PROVIDER_VISION_MODEL] = (FREE_PROVIDER_API_KEY, PROVIDER_API_BASE)

    if PROVIDER_VISION_TOOL_MODEL and PROVIDER_VISION_TOOL_MODEL not in desired:
        desired[PROVIDER_VISION_TOOL_MODEL] = (FREE_PROVIDER_API_KEY, PROVIDER_API_BASE)

    if PROVIDER_GROUNDING_MODEL:
        desired[PROVIDER_GROUNDING_MODEL] = (PROVIDER_API_KEY, PROVIDER_API_BASE)

    if not desired:
        print("[populate_routers] No configured models found; nothing to populate.")
        return

    created = 0
    skipped = 0
    with Session(engine) as session:
        for model_name, (api_key, endpoint) in desired.items():
            if _existing_router(session, model_name, endpoint):
                skipped += 1
                continue
            _create_router(
                session, api_key=api_key, model_name=model_name, api_endpoint=endpoint
            )
            created += 1

    print(
        f"[populate_routers] Completed. Created: {created}, Skipped (already existed): {skipped}"
    )
