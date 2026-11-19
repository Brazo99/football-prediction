import pandas as pd
from football_prediction.ingestion import import_report

def test_write_import_report(tmp_path):
    # Create a sample ImportResult object
    accepted_df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    rejected_df = pd.DataFrame({"A": [5], "B": [6]})
    duplicate_candidates_df = pd.DataFrame({"A": [7], "B": [8]})
    issues = []
    from football_prediction.ingestion.rules import ImportResult
    result = ImportResult(
        accepted=accepted_df,
        rejected=rejected_df,
        duplicate_candidates=duplicate_candidates_df,
        issues=issues,
        source_path="dummy_path",
        source_column_map={"A": "Column A", "B": "Column B"}
    )
    
    # Call the function to write the report
    output_dir = tmp_path / "report"
    paths = import_report.write_import_report(result, output_dir)
    
    # Check that the files were created
    assert paths["accepted"].exists()
    assert paths["rejected"].exists()
    assert paths["duplicates"].exists()
    assert paths["report"].exists()
    
    # Check that the report file contains the expected content
    report_content = paths["report"].read_text(encoding="utf-8")
    assert "Football match CSV import report" in report_content
    assert "accepted_rows: 2" in report_content
    assert "rejected_rows: 1" in report_content
    assert "duplicate_candidates: 1" in report_content
    assert "errors: 0" in report_content
    assert "warnings: 0" in report_content