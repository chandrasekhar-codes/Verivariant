from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import DISCLAIMER, get_settings
from app.jobs import clear_jobs, get_job
from app.models import GenomeBuild
from app.parsing.vcf_parser import VCFParseError, parse_vcf


def _write_vcf(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    return path


MINIMAL_VCF = """##fileformat=VCFv4.2
##INFO=<ID=AF,Number=A,Type=Float,Description="Allele frequency from the file">
##INFO=<ID=GENE,Number=1,Type=String,Description="Gene symbol from the file">
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
chr1	100	rsTEST1	A	G,T	99	PASS	AF=0.1,0.2;GENE=TESTGENE
2	200	.	C	A	.	.	.
"""

GRCH37_REF_VCF = """##fileformat=VCFv4.2
##reference=GRCh37
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
1	100	.	A	G	.	PASS	.
"""

GRCH37_CONTIG_VCF = """##fileformat=VCFv4.2
##contig=<ID=1,length=249250621>
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
1	100	.	A	G	.	PASS	.
"""

GRCH38_CONTIG_VCF = """##fileformat=VCFv4.2
##contig=<ID=1,length=248956422>
#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO
1	100	.	A	G	.	PASS	.
"""


@pytest.fixture(params=["cyvcf2", "python"])
def vcf_backend(request, monkeypatch: pytest.MonkeyPatch) -> str:
    if request.param == "python":
        monkeypatch.setenv("GENOMESCOPE_VCF_BACKEND", "python")
    else:
        monkeypatch.delenv("GENOMESCOPE_VCF_BACKEND", raising=False)
    return request.param


def test_parse_multiallelic_and_chr_prefix(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(tmp_path / "mini.vcf", MINIMAL_VCF)
    result = parse_vcf(path)
    keys = [v.key for v in result.variants]
    assert keys == ["1-100-A-G", "1-100-A-T", "2-200-C-A"]
    assert result.variants[0].chrom == "1"
    assert result.variants[0].rsid == "rsTEST1"
    assert result.variants[0].info.get("GENE") == "TESTGENE"
    assert result.variants[2].rsid is None
    assert result.variants[2].filter == "PASS"


def test_malformed_missing_fileformat(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(
        tmp_path / "bad.vcf",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t100\t.\tA\tG\t.\tPASS\t.\n",
    )
    with pytest.raises(VCFParseError, match="fileformat"):
        parse_vcf(path)


def test_malformed_short_row(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(
        tmp_path / "short.vcf",
        "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t100\t.\tA\n",
    )
    with pytest.raises(VCFParseError, match="Malformed|missing ALT"):
        parse_vcf(path, genome_build=GenomeBuild.grch38)


def test_python_parser_rejects_short_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GENOMESCOPE_VCF_BACKEND", "python")
    path = _write_vcf(
        tmp_path / "short.vcf",
        "##fileformat=VCFv4.2\n#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n1\t100\t.\tA\n",
    )
    with pytest.raises(VCFParseError, match="expected at least 8 columns"):
        parse_vcf(path)


def test_max_variants(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(tmp_path / "mini.vcf", MINIMAL_VCF)
    with pytest.raises(VCFParseError, match="more than 2"):
        parse_vcf(path, max_variants=2)


def test_genome_build_from_reference(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(tmp_path / "b37.vcf", GRCH37_REF_VCF)
    result = parse_vcf(path)
    assert result.genome_build == GenomeBuild.grch37
    assert result.genome_build_source == "header_reference"


def test_genome_build_from_contig_length(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(tmp_path / "c37.vcf", GRCH37_CONTIG_VCF)
    result = parse_vcf(path)
    assert result.genome_build == GenomeBuild.grch37
    assert result.genome_build_source == "contig_length"
    path38 = _write_vcf(tmp_path / "c38.vcf", GRCH38_CONTIG_VCF)
    result38 = parse_vcf(path38)
    assert result38.genome_build == GenomeBuild.grch38
    assert result38.genome_build_source == "contig_length"


def test_user_genome_build_override(tmp_path: Path, vcf_backend: str) -> None:
    path = _write_vcf(tmp_path / "b37.vcf", GRCH37_REF_VCF)
    result = parse_vcf(path, genome_build=GenomeBuild.grch38)
    assert result.genome_build == GenomeBuild.grch38
    assert result.genome_build_source == "user"


def test_gzip_vcf(tmp_path: Path, vcf_backend: str) -> None:
    import gzip

    gz_path = tmp_path / "mini.vcf.gz"
    gz_path.write_bytes(gzip.compress(MINIMAL_VCF.encode("utf-8")))
    result = parse_vcf(gz_path)
    assert len(result.variants) == 3


@pytest.fixture
def api_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("UPLOADS_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("SAMPLE_DATA_DIR", str(tmp_path / "sample_data"))
    (tmp_path / "sample_data").mkdir()
    get_settings.cache_clear()
    clear_jobs()
    from app.main import app

    with TestClient(app) as client:
        yield client
    clear_jobs()
    get_settings.cache_clear()


def test_upload_ok(api_client: TestClient, tmp_path: Path) -> None:
    files = {"file": ("mini.vcf", MINIMAL_VCF.encode("utf-8"), "text/plain")}
    response = api_client.post("/api/upload", files=files)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["disclaimer"] == DISCLAIMER
    assert body["variant_count"] == 3
    assert body["variants"][0]["key"] == "1-100-A-G"
    job = get_job(body["job_id"])
    assert job is not None
    assert job.vcf_path.exists()


def test_upload_rejects_malformed(api_client: TestClient) -> None:
    files = {"file": ("bad.vcf", b"not a vcf", "text/plain")}
    response = api_client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "Malformed" in response.json()["detail"] or "fileformat" in response.json()["detail"]


def test_upload_rejects_wrong_extension(api_client: TestClient) -> None:
    files = {"file": ("notes.txt", MINIMAL_VCF.encode("utf-8"), "text/plain")}
    response = api_client.post("/api/upload", files=files)
    assert response.status_code == 400


def test_upload_demo_missing(api_client: TestClient) -> None:
    response = api_client.post("/api/upload?demo=true")
    assert response.status_code == 404


def test_upload_too_large(api_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    get_settings.cache_clear()
    files = {"file": ("mini.vcf", MINIMAL_VCF.encode("utf-8"), "text/plain")}
    response = api_client.post("/api/upload", files=files)
    assert response.status_code == 413
