from typing import Literal
from unittest.mock import MagicMock, patch
import pytest
import os
from compete_pulse_agent.core.vector_store import CompetePulseVectorStore

@patch('vertexai.init')
@patch('vertexai.preview.rag.list_corpora')
@patch('vertexai.preview.rag.create_corpus')
def test_vector_store_initialization(mock_create, mock_list, mock_init):
    # Mock existing corpus
    mock_corpus = MagicMock()
    mock_corpus.display_name = "compete_pulses_corpus"
    mock_corpus.name = "projects/p/locations/l/ragCorpora/c1"
    mock_list.return_value = [mock_corpus]
    
    store = CompetePulseVectorStore(project_id="test-project")
    
    assert mock_init.called
    assert store.corpus.name == "projects/p/locations/l/ragCorpora/c1"
    assert not mock_create.called

@patch('vertexai.init')
@patch('vertexai.preview.rag.list_corpora')
@patch('vertexai.preview.rag.upload_file')
def test_upsert_pulses(mock_upload, mock_list, mock_init):
    mock_corpus = MagicMock()
    mock_corpus.display_name = "compete_pulses_corpus"
    mock_list.return_value = [mock_corpus]
    
    store = CompetePulseVectorStore()
    test_pulse = {
        "title": "Test Pulse",
        "source": "src",
        "summary": "sum",
        "bridge": "bridge"
    }
    
    store.upsert_pulses([test_pulse])
    assert mock_upload.called

@patch('vertexai.init')
@patch('vertexai.preview.rag.list_corpora')
@patch('vertexai.preview.rag.retrieval_query')
def test_query(mock_retrieval, mock_list, mock_init):
    mock_corpus = MagicMock()
    mock_corpus.display_name = "compete_pulses_corpus"
    mock_list.return_value = [mock_corpus]
    
    # Mock response
    mock_resp = MagicMock()
    mock_context = MagicMock()
    mock_context.text = "Relevant context text"
    mock_context.source_uri = "gs://bucket/file.txt"
    mock_resp.contexts.contexts = [mock_context]
    mock_retrieval.return_value = mock_resp
    
    store = CompetePulseVectorStore()
    results = store.query_pulses("test query")
    
    assert len(results) == 1
    assert results[0]["document"] == "Relevant context text"

@patch('vertexai.init')
@patch('vertexai.preview.rag.list_corpora')
@patch('vertexai.preview.rag.import_files')
def test_ingest_uris(mock_import, mock_list, mock_init):
    mock_corpus = MagicMock()
    mock_corpus.display_name = "compete_pulses_corpus"
    mock_list.return_value = [mock_corpus]
    
    store = CompetePulseVectorStore()
    uris = ["https://drive.google.com/open?id=123"]
    store.ingest_uris(uris)
    
    assert mock_import.called
    args, kwargs = mock_import.call_args
    assert kwargs['paths'] == uris
