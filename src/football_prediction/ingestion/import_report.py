from .rules import ImportResult
from pathlib import Path

def write_import_report(result: ImportResult, output_dir: str | Path) -> dict[str, Path]:
    """Write accepted/rejected/duplicate CSVs and a compact summary report."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    accepted_path = destination / "accepted_matches.csv"
    rejected_path = destination / "rejected_matches.csv"
    duplicates_path = destination / "duplicate_candidates.csv"
    report_path = destination / "import_report.txt"

    result.accepted.to_csv(accepted_path, index=False)
    result.rejected.to_csv(rejected_path, index=False)
    result.duplicate_candidates.to_csv(duplicates_path, index=False)
    lines = ["Football match CSV import report", "=" * 32]
    lines.extend(f"{key}: {value}" for key, value in result.summary.items())
    lines.extend(["", "Issues:"])
    lines.extend(
        f"row {item.source_row} [{item.severity}/{item.code}]: {item.message}"
        for item in result.issues
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    return {
        "accepted": accepted_path,
        "rejected": rejected_path,
        "duplicates": duplicates_path,
        "report": report_path,
    }