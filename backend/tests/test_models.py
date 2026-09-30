from datetime import UTC

from app.models import DISCLAIMER, Report, Variant


def test_report_disclaimer_default() -> None:
    from datetime import datetime

    from app.models import GenomeBuild

    report = Report(
        job_id="test",
        created_at=datetime.now(UTC),
        genome_build=GenomeBuild.grch38,
        variants=[],
    )
    assert report.disclaimer == DISCLAIMER


def test_variant_key_is_required() -> None:
    variant = Variant(
        id="v1",
        chrom="11",
        pos=1,
        ref="A",
        alt="T",
        key="11-1-A-T",
    )
    assert variant.key == "11-1-A-T"
