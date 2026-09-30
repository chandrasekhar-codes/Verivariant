from fastapi.testclient import TestClient

from app.config import DISCLAIMER
from app.main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "GENESIS"
    assert data["status"] == "online"


def test_demo_analysis_pipeline() -> None:
    # Test POST /api/demo
    resp = client.post("/api/demo")
    assert resp.status_code == 200
    report = resp.json()

    assert report["total_variants"] == 8
    assert report["disclaimer"] == DISCLAIMER
    assert report["is_demo"] is True
    assert len(report["variants"]) == 8
    assert report["total_claims"] > 0
    assert report["supported_claims"] > 0

    # Verify each variant has evidence from ClinVar, gnomAD, and Ensembl VEP
    first_var = report["variants"][0]
    sources = [e["source"] for e in first_var["evidence"]]
    assert "clinvar" in sources
    assert "gnomad" in sources
    assert "ensembl_vep" in sources

    # Verify Research Agent claims exist and are verified
    assert len(first_var["claims"]) > 0
    for claim in first_var["claims"]:
        assert claim["text"]
        assert claim["source"]
        assert claim["verification"] is not None
        assert claim["verification"]["verdict"] in [
            "supported",
            "partially_supported",
            "unsupported",
            "unclear",
        ]

    # Check conflict detection
    conflicts = report["conflicts"]
    assert len(conflicts) > 0  # e.g., MTHFR conflict detected
    genes_with_conflicts = [c["gene"] for c in conflicts]
    assert "MTHFR" in genes_with_conflicts


def test_get_report_and_variant_details() -> None:
    # Run demo first to create job
    resp = client.post("/api/demo")
    assert resp.status_code == 200
    job_id = resp.json()["job_id"]

    # Test GET /api/report/{job_id}
    rep_resp = client.get(f"/api/report/{job_id}")
    assert rep_resp.status_code == 200
    assert rep_resp.json()["job_id"] == job_id

    # Test GET /api/variant/{job_id}/{variant_id}
    var_resp = client.get(f"/api/variant/{job_id}/17-43045712-C-CG")
    assert var_resp.status_code == 200
    vdata = var_resp.json()
    assert vdata["variant"]["gene"] == "BRCA1"
    assert vdata["variant"]["clinvar_sig"] == "Pathogenic"


def test_verify_claim_endpoint() -> None:
    resp = client.post(
        "/api/verify",
        json={
            "claim": {
                "id": "c1",
                "variant_key": "17-43045712-C-CG",
                "text": "ClinVar classifies this variant as Pathogenic for Hereditary breast and ovarian cancer syndrome.",
                "source": "ClinVar",
                "category": "clinical_significance",
            },
            "evidence_items": [
                {
                    "id": "e1",
                    "variant_key": "17-43045712-C-CG",
                    "source": "clinvar",
                    "status": "found",
                    "url": "https://www.ncbi.nlm.nih.gov/clinvar/variation/17677/",
                    "retrieved_at": "2026-09-30T12:00:00Z",
                    "data": {
                        "clinical_significance": "Pathogenic",
                        "condition": "Hereditary breast and ovarian cancer syndrome",
                    },
                }
            ],
        },
    )
    assert resp.status_code == 200
    res = resp.json()
    assert res["verification"]["verdict"] == "supported"
    assert res["verification"]["confidence"] >= 0.9
