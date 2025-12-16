import pytest
from src.server import list_templates, list_rubrics, list_checklists, identify_risks
import json

def test_list_templates():
    # FastMCP wraps functions, use .fn() to call underlying logic
    response = list_templates.fn()
    templates = json.loads(response)
    assert isinstance(templates, list)
    assert len(templates) > 0

def test_list_rubrics():
    response = list_rubrics.fn()
    rubrics = json.loads(response)
    assert isinstance(rubrics, list)
    assert len(rubrics) > 0

def test_list_checklists():
    response = list_checklists.fn()
    checklists = json.loads(response)
    assert isinstance(checklists, list)
    assert len(checklists) > 0

def test_identify_risks_found(monkeypatch):
    # Mock extract_text to return something with "missing signature"
    # This assumes "loan_risk_v1" is present and has "missing_info" criteria
    import src.server as server
    
    class MockProcessor:
        def extract_text(self, filename):
            return "This document is blank and incomplete."

    monkeypatch.setattr(server, "processor", MockProcessor())

    response = identify_risks.fn(document_id="fake_doc.txt", rubric_id="loan_risk_v1")
    data = json.loads(response)
    
    # We expect 'missing_info' risk because 'signature' is missing in mock text
    found_missing_info = any(r['id'] == 'missing_info' for r in data.get('risks', []))
    assert found_missing_info, "Should detect missing signature risk"
