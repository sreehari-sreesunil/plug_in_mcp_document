import pytest
from src.document_processor import DocumentProcessor
from pathlib import Path

def test_list_documents(tmp_path):
    # Setup temp storage
    processor = DocumentProcessor(storage_dir=tmp_path)
    
    # Create dummy files
    (tmp_path / "doc1.txt").write_text("content1")
    (tmp_path / "doc2.pdf").write_text("content2")
    
    docs = processor.list_documents()
    assert "doc1.txt" in docs
    assert "doc2.pdf" in docs
    assert len(docs) == 2

def test_save_upload(tmp_path):
    processor = DocumentProcessor(storage_dir=tmp_path)
    path = processor.save_upload("test.txt", b"hello world")
    assert Path(path).exists()
    assert (tmp_path / "test.txt").read_text() == "hello world"
