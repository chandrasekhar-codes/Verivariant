from __future__ import annotations

import gzip
import math
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from app.models import GenomeBuild, Variant

# Assembly chromosome 1 lengths from NCBI GRCh37/GRCh38 reports (header detection only).
CHR1_LENGTH_GRCH38 = 248956422
CHR1_LENGTH_GRCH37 = 249250621

_RSID_RE = re.compile(r"^rs\S+$", re.IGNORECASE)
_FILEFORMAT_RE = re.compile(r"^##fileformat=VCFv(\d+(\.\d+)?)", re.IGNORECASE)
_CONTIG_LEN_RE = re.compile(
    r"^##contig=<ID=([^,>]+).*length=(\d+)",
    re.IGNORECASE,
)
_REFERENCE_RE = re.compile(r"^##reference=(.+)$", re.IGNORECASE)


class VCFParseError(ValueError):
    """User-facing VCF validation/parse failure."""


@dataclass
class ParseResult:
    variants: list[Variant]
    genome_build: GenomeBuild
    genome_build_source: str
    warnings: list[str] = field(default_factory=list)
    header_lines: list[str] = field(default_factory=list)


def normalize_chrom(chrom: str) -> str:
    value = chrom.strip()
    if value.lower().startswith("chr"):
        value = value[3:]
    return value


def make_variant_key(chrom: str, pos: int, ref: str, alt: str) -> str:
    return f"{chrom}-{pos}-{ref}-{alt}"


def extract_rsid(vcf_id: str | None) -> str | None:
    if not vcf_id or vcf_id == ".":
        return None
    for token in re.split(r"[;,]", vcf_id):
        token = token.strip()
        if _RSID_RE.match(token):
            return token
    return None


def _jsonish(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, tuple):
        return [_jsonish(item) for item in value]
    if isinstance(value, list):
        return [_jsonish(item) for item in value]
    return value


def _open_text(path: Path) -> TextIO:
    name_lower = path.name.lower()
    if name_lower.endswith((".gz", ".bgz")):
        return gzip.open(path, "rt", encoding="utf-8-sig", errors="replace")
    return path.open("rt", encoding="utf-8-sig", errors="replace")


def _detect_genome_build(
    header_lines: list[str],
    user_build: GenomeBuild | None,
) -> tuple[GenomeBuild, str]:
    if user_build is not None:
        return user_build, "user"

    for line in header_lines:
        match = _REFERENCE_RE.match(line.strip())
        if not match:
            continue
        ref = match.group(1).lower()
        if any(token in ref for token in ("grch38", "hg38", "grch38.p14", "grch38.p13")):
            return GenomeBuild.grch38, "header_reference"
        if any(token in ref for token in ("grch37", "hg19", "b37", "hs37d5")):
            return GenomeBuild.grch37, "header_reference"

    contig_lengths: dict[str, int] = {}
    for line in header_lines:
        match = _CONTIG_LEN_RE.match(line.strip())
        if match:
            contig_lengths[normalize_chrom(match.group(1))] = int(match.group(2))

    chr1 = contig_lengths.get("1")
    if chr1 == CHR1_LENGTH_GRCH38:
        return GenomeBuild.grch38, "contig_length"
    if chr1 == CHR1_LENGTH_GRCH37:
        return GenomeBuild.grch37, "contig_length"

    return GenomeBuild.grch38, "default"


def _parse_info(info_field: str) -> dict[str, Any]:
    if not info_field or info_field == ".":
        return {}
    parsed: dict[str, Any] = {}
    for part in info_field.split(";"):
        if not part:
            continue
        if "=" in part:
            key, raw = part.split("=", 1)
            parsed[key] = raw
        else:
            parsed[part] = True
    return parsed


def _alts(alt_field: str) -> list[str]:
    if not alt_field or alt_field == ".":
        raise VCFParseError("Variant is missing ALT alleles.")
    alts = [allele.strip() for allele in alt_field.split(",") if allele.strip()]
    if not alts:
        raise VCFParseError("Variant is missing ALT alleles.")
    return alts


def _qual(raw: str | float | None) -> float | None:
    if raw is None or raw == ".":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if math.isnan(value):
        return None
    return value


def _filter_value(raw: Any) -> str | None:
    if raw is None:
        return "PASS"
    if isinstance(raw, (list, tuple)):
        if not raw:
            return "PASS"
        return ";".join(str(item) for item in raw)
    text = str(raw)
    if text in {"", ".", "None"}:
        return "PASS"
    return text


def _prefer_python_parser() -> bool:
    return os.environ.get("GENOMESCOPE_VCF_BACKEND", "").lower() in {"python", "pure", "fallback"}


def _try_cyvcf2() -> Any:
    try:
        from cyvcf2 import VCF  # type: ignore
    except Exception:
        return None
    return VCF


def parse_vcf(
    path: Path,
    *,
    genome_build: GenomeBuild | None = None,
    max_variants: int = 200,
    cap_variants: bool = False,
) -> ParseResult:
    if not path.exists() or not path.is_file():
        raise VCFParseError("VCF file was not found.")
    if path.stat().st_size == 0:
        raise VCFParseError("VCF file is empty.")

    header_lines = _read_header_lines(path)
    if not any(_FILEFORMAT_RE.match(line.strip()) for line in header_lines):
        raise VCFParseError("Malformed VCF: missing ##fileformat header.")

    build, build_source = _detect_genome_build(header_lines, genome_build)
    warnings: list[str] = []

    use_python = _prefer_python_parser()
    vcf_cls = None if use_python else _try_cyvcf2()
    if vcf_cls is not None:
        try:
            variants = _parse_with_cyvcf2(
                path,
                vcf_cls,
                build,
                max_variants=max_variants,
                warnings=warnings,
                cap_variants=cap_variants,
            )
            return ParseResult(
                variants=variants,
                genome_build=build,
                genome_build_source=build_source,
                warnings=warnings,
                header_lines=header_lines,
            )
        except VCFParseError:
            raise
        except Exception:
            warnings.append("cyvcf2 failed; using the built-in VCF parser.")

    variants = _parse_with_python(
        path,
        build,
        max_variants=max_variants,
        warnings=warnings,
        cap_variants=cap_variants,
    )
    return ParseResult(
        variants=variants,
        genome_build=build,
        genome_build_source=build_source,
        warnings=warnings,
        header_lines=header_lines,
    )


def _read_header_lines(path: Path) -> list[str]:
    lines: list[str] = []
    with _open_text(path) as handle:
        for line in handle:
            if line.startswith("##"):
                lines.append(line.rstrip("\n"))
            elif line.startswith("#CHROM"):
                lines.append(line.rstrip("\n"))
                break
            elif line.strip():
                break
    return lines


def _split_number_a_fields(info: dict[str, Any], allele_index: int) -> None:
    """If an INFO value is comma-separated (Number=A style), keep the matching allele."""
    for key in list(info):
        value = info[key]
        if not isinstance(value, str) or "," not in value:
            continue
        parts = value.split(",")
        if 0 <= allele_index < len(parts):
            info[key] = parts[allele_index]


def _build_variant(
    *,
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    vcf_id: str,
    qual: float | None,
    filt: str | None,
    info: dict[str, Any],
    genome_build: GenomeBuild,
) -> Variant:
    key = make_variant_key(chrom, pos, ref, alt)
    clean_info = {k: _jsonish(v) for k, v in info.items()}
    if vcf_id and vcf_id != ".":
        clean_info.setdefault("vcf_id", vcf_id)
    return Variant(
        id=key,
        chrom=chrom,
        pos=pos,
        ref=ref,
        alt=alt,
        rsid=extract_rsid(vcf_id),
        qual=qual,
        filter=filt,
        info=clean_info,
        genome_build=genome_build,
        key=key,
    )


def _parse_with_cyvcf2(
    path: Path,
    vcf_cls: Any,
    build: GenomeBuild,
    max_variants: int,
    warnings: list[str],
    cap_variants: bool = False,
) -> list[Variant]:
    variants: list[Variant] = []
    reader = vcf_cls(str(path))
    reached_cap = False
    try:
        for record in reader:
            chrom = normalize_chrom(str(record.CHROM))
            pos = int(record.POS)
            vcf_id = record.ID if record.ID not in {None, "."} else "."
            ref = str(record.REF)
            alts = [str(a) for a in (record.ALT or []) if a and str(a) != "."]
            if not alts:
                raise VCFParseError(f"Variant {chrom}:{pos} is missing ALT alleles.")
            info_raw: dict[str, Any] = {}
            try:
                info_raw = dict(record.INFO)
            except Exception:
                warnings.append("Could not read all INFO fields from a record.")
            for i, alt in enumerate(alts):
                allele_info = {k: _jsonish(v) for k, v in info_raw.items()}
                for key, value in list(allele_info.items()):
                    if isinstance(value, list) and 0 <= i < len(value):
                        allele_info[key] = value[i]
                variants.append(
                    _build_variant(
                        chrom=chrom,
                        pos=pos,
                        ref=ref,
                        alt=alt,
                        vcf_id=str(vcf_id),
                        qual=_qual(record.QUAL),
                        filt=_filter_value(record.FILTER),
                        info=allele_info,
                        genome_build=build,
                    )
                )
                if len(variants) >= max_variants:
                    if cap_variants:
                        warnings.append(
                            f"VCF has more than {max_variants} alleles after splitting multi-allelic records; "
                            f"truncated to first {max_variants} for analysis."
                        )
                        reached_cap = True
                        break
                    elif len(variants) > max_variants or (len(variants) == max_variants and not cap_variants):
                        # For testing max_variants check
                        pass
                if not cap_variants and len(variants) > max_variants:
                    raise VCFParseError(
                        f"VCF has more than {max_variants} alleles after splitting multi-allelic records."
                    )
            if reached_cap:
                break
    finally:
        try:
            reader.close()
        except Exception:
            pass
    if not variants:
        raise VCFParseError("VCF contains no variant records.")
    return variants


def _parse_with_python(
    path: Path,
    build: GenomeBuild,
    max_variants: int,
    warnings: list[str] | None = None,
    cap_variants: bool = False,
) -> list[Variant]:
    variants: list[Variant] = []
    reached_cap = False
    with _open_text(path) as handle:
        columns_ok = False
        for line_no, raw in enumerate(handle, start=1):
            line = raw.rstrip("\n")
            if not line or line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                columns = line[1:].split("\t")
                required = ["CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO"]
                if columns[:8] != required:
                    raise VCFParseError(
                        "Malformed VCF: column header must start with "
                        "CHROM POS ID REF ALT QUAL FILTER INFO."
                    )
                columns_ok = True
                continue
            if line.startswith("#"):
                continue
            if not columns_ok:
                raise VCFParseError("Malformed VCF: missing #CHROM header row.")
            fields = line.split("\t")
            if len(fields) < 8:
                raise VCFParseError(
                    f"Malformed VCF at line {line_no}: expected at least 8 columns, got {len(fields)}."
                )
            chrom, pos_s, vcf_id, ref, alt_s, qual_s, filt, info_s = fields[:8]
            try:
                pos = int(pos_s)
            except ValueError as exc:
                raise VCFParseError(
                    f"Malformed VCF at line {line_no}: POS is not an integer."
                ) from exc
            if pos < 1:
                raise VCFParseError(f"Malformed VCF at line {line_no}: POS must be >= 1.")
            chrom_n = normalize_chrom(chrom)
            info = _parse_info(info_s)
            for i, alt in enumerate(_alts(alt_s)):
                allele_info = dict(info)
                _split_number_a_fields(allele_info, i)
                variants.append(
                    _build_variant(
                        chrom=chrom_n,
                        pos=pos,
                        ref=ref,
                        alt=alt,
                        vcf_id=vcf_id,
                        qual=_qual(qual_s),
                        filt=_filter_value(filt),
                        info=allele_info,
                        genome_build=build,
                    )
                )
                if len(variants) >= max_variants:
                    if cap_variants:
                        if warnings is not None:
                            warnings.append(
                                f"VCF has more than {max_variants} alleles after splitting multi-allelic records; "
                                f"truncated to first {max_variants} for analysis."
                            )
                        reached_cap = True
                        break
                if not cap_variants and len(variants) > max_variants:
                    raise VCFParseError(
                        f"VCF has more than {max_variants} alleles after splitting multi-allelic records."
                    )
            if reached_cap:
                break
    if not columns_ok:
        raise VCFParseError("Malformed VCF: missing #CHROM header row.")
    if not variants:
        raise VCFParseError("VCF contains no variant records.")
    return variants


def iter_variant_keys(variants: Iterable[Variant]) -> list[str]:
    return [v.key for v in variants]
