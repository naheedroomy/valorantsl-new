"""Geo-restriction dependency for limiting registration by country."""
from fastapi import Request, HTTPException
import logging

from ..config import settings

logger = logging.getLogger(__name__)


async def require_allowed_country(request: Request):
    """Reject requests from countries not in the allowed list.

    Uses Cloudflare's CF-IPCountry header which is automatically added
    to every request when the site is proxied through Cloudflare.
    Falls back to allowing the request if the header is missing (e.g. local dev).
    """
    if not settings.geo_restrict_registration:
        return

    country = request.headers.get("CF-IPCountry")

    if country is None:
        # Header missing — likely local dev or non-Cloudflare traffic.
        # In debug mode, allow through; in production, block unknown origins.
        if settings.debug:
            logger.debug("CF-IPCountry header missing — skipping geo check (debug mode)")
            return
        logger.warning("CF-IPCountry header missing on a geo-restricted endpoint")
        raise HTTPException(
            status_code=403,
            detail="You are ineligible to sign up. For any inquiries, contact xeno_sl on Discord.",
        )

    country = country.upper()
    allowed = settings.allowed_countries_list

    if country not in allowed:
        logger.info(f"Registration blocked for country: {country}")
        raise HTTPException(
            status_code=403,
            detail="You are ineligible to sign up. For any inquiries, contact xeno_sl on Discord.",
        )

    logger.debug(f"Geo check passed: {country}")
