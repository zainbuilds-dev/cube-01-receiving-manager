from fastapi import Header, HTTPException

from .config import ORG_TOKENS

def require_org(authorization: str = Header(default="")) -> str:
    """Resolve the caller's organisation from a bearer token.
    Demo-grade static tokens; see ARCHITECTURE.md for the production path."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization: Bearer <token> header")
    org = ORG_TOKENS.get(authorization[7:].strip())
    if not org:
        raise HTTPException(401, "Invalid token")
    return org