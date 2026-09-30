from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import APIRouter

from app.config import DISCLAIMER

router = APIRouter()

SOURCE_CHECKS: dict[str, dict[str, Any]] = {
    "clinvar": {
        "method": "GET",
        "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi",
        "params": {"db": "clinvar", "retmode": "json"},
    },
    "gnomad": {
        "method": "POST",
        "url": "https://gnomad.broadinstitute.org/api",
        # Standard GraphQL typename query — does not depend on gnomAD-specific fields.
        "json": {"query": "{ __typename }"},
    },
    "ensembl_vep": {
        "method": "GET",
        "url": "https://rest.ensembl.org/info/ping",
        "headers": {"Content-Type": "application/json", "Accept": "application/json"},
    },
}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "disclaimer": DISCLAIMER}


async def _check_source(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    timeout = httpx.Timeout(8.0, connect=4.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.request(
                spec["method"],
                spec["url"],
                params=spec.get("params"),
                json=spec.get("json"),
                headers=spec.get("headers"),
            )
        ok = response.status_code < 500
        return {
            "name": name,
            "ok": ok,
            "status_code": response.status_code,
            "url": spec["url"],
        }
    except Exception as exc:  # network/timeout — surface as down, do not crash
        return {
            "name": name,
            "ok": False,
            "status_code": None,
            "url": spec["url"],
            "error": type(exc).__name__,
        }


@router.get("/sources/status")
async def sources_status() -> dict[str, Any]:
    results = await asyncio.gather(
        *(_check_source(name, spec) for name, spec in SOURCE_CHECKS.items())
    )
    return {
        "disclaimer": DISCLAIMER,
        "sources": {item["name"]: item for item in results},
    }
