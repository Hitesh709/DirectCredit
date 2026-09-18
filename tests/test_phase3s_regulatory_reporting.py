from backend.phase3s_regulatory_reporting import report
def test_report(): assert report(report_type="MIS",period="2026-09",records=3)["source_lineage_required"] is True
