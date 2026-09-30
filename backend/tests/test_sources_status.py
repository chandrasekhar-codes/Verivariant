import respx
from fastapi.testclient import TestClient
from httpx import Response

from app.config import DISCLAIMER
from app.main import app

client = TestClient(app)


@respx.mock
def test_sources_status_mocked() -> None:
    respx.get(url__startswith="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi").mock(
        return_value=Response(200, json={"einforesult": {}})
    )
    respx.post("https://gnomad.broadinstitute.org/api").mock(
        return_value=Response(200, json={"data": {"__typename": "Query"}})
    )
    respx.get("https://rest.ensembl.org/info/ping").mock(
        return_value=Response(200, json={"ping": 1})
    )
    response = client.get("/api/sources/status")
    assert response.status_code == 200
    body = response.json()
    assert body["disclaimer"] == DISCLAIMER
    assert body["sources"]["clinvar"]["ok"] is True
    assert body["sources"]["gnomad"]["ok"] is True
    assert body["sources"]["ensembl_vep"]["ok"] is True
