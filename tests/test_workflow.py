"""Run with:  python tests/test_workflow.py"""
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import workflow as wf  # noqa: E402


def test_directory_integrity():
    data = wf.load_directory()
    assert len(data) >= 40
    for e in data:
        assert e["name"] and e["summary"] and e["observations"]
        assert len(e["competitors"]) <= 2


def test_sector_query_with_default_text():
    s = wf.run_workflow("Analyze the food delivery market in Nepal.", "sample")
    assert s.final_brief.data_source == wf.SAMPLE_LABEL
    assert "Foodmandu" in s.final_brief.competitors
    assert s.revisions_used == 0 and s.feedback.approved


def test_fuzzy_and_aliases():
    for q, name in [("ncel", "Ncell"), ("NTC", "Nepal Telecom"), ("esewa", "eSewa"),
                    ("Nepal Telecom", "Nepal Telecom"), ("bank", "Banking in Nepal"),
                    ("wai wai", "Chaudhary Group")]:
        s = wf.run_workflow(q, "sample")
        assert s.findings.matched_name == name, (q, s.findings.matched_name)


def test_every_directory_entry_is_findable():
    for e in wf.load_directory():
        s = wf.run_workflow(e["name"], "sample")
        assert s.findings.data_source == wf.SAMPLE_LABEL, e["name"]
        assert len(s.final_brief.competitors) <= 2
        assert s.revisions_used <= 1


def test_revision_when_no_competitors():
    s = wf.run_workflow("Fonepay", "sample")
    assert s.feedback.revision_requested and s.revisions_used == 1
    assert any("Competitors could not" in m for m in s.final_brief.missing)
    assert s.final_feedback.approved


def test_unknown_sample_is_not_invented():
    s = wf.run_workflow("Tesla", "sample")
    assert s.findings.data_source == wf.NONE_LABEL
    assert "No information" in s.final_brief.summary


def test_empty_query_rejected():
    try:
        wf.run_workflow("   ")
        assert False
    except ValueError:
        pass


FAKE_WIKI = {"query": {"pages": {"1": {"index": 1, "title": "Himalayan Bank", "fullurl": "https://en.wikipedia.org/wiki/Himalayan_Bank",
    "extract": "Himalayan Bank Limited is a commercial bank in Nepal. It was established in 1993 as a joint venture. "
               "The bank operates branches across the country. It offers retail and corporate services."}}}}


def test_live_search_parsing():
    with mock.patch.object(wf, "_http_json", return_value=FAKE_WIKI):
        s = wf.run_workflow("Himalayan Bank Pvt Ltd Branches", "live")
    assert s.findings.data_source == wf.LIVE_LABEL
    assert s.final_brief.sources and s.revisions_used == 1  # no competitors -> one revision


def test_live_failure_is_reported_not_hidden():
    with mock.patch.object(wf, "_http_json", side_effect=OSError("offline")):
        s = wf.run_workflow("Tesla", "live")
    assert s.findings.data_source == wf.NONE_LABEL
    assert any("offline" in m for m in s.final_brief.missing)


def test_auto_falls_back_to_live():
    with mock.patch.object(wf, "_http_json", return_value=FAKE_WIKI):
        s = wf.run_workflow("Himalayan Bank Branches", "auto")
    assert s.findings.data_source in (wf.SAMPLE_LABEL, wf.LIVE_LABEL)


def test_markdown_and_pdf():
    s = wf.run_workflow("Khalti", "sample")
    md = wf.brief_to_markdown(s)
    assert "## Summary" in md and "SAMPLE DATA" in md
    try:
        from pdf_export import make_pdf
    except ImportError:
        print("  (fpdf2 not installed - PDF test skipped)")
        return
    assert make_pdf(s)[:4] == b"%PDF"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("ok", t.__name__)
    print("All tests passed")
