from typing import Literal
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import vertexai
from vertexai.preview import rag
from vertexai.preview.rag import RagCorpus, RagFile

class CompetePulseVectorStore:
    def __init__(self, project_id: str = "project-maui", location: str = "us-east1"):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", project_id)
        self.location = os.environ.get("GOOGLE_CLOUD_REGION", location)
        self.enabled = False
        
        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.corpus_display_name = "compete_pulses_corpus"
            self.corpus = self._get_or_create_corpus()
            self.enabled = True
        except Exception as e:
            # Handle DefaultCredentialsError or other initialization failures gracefully
            from rich.console import Console
            console = Console()
            console.print(f"[yellow]Warning: Vertex AI RAG Engine initialization skipped: {e}[/yellow]")
            console.print("[yellow]Persistence and RAG features will be disabled for this session.[/yellow]")

    def _get_or_create_corpus(self) -> RagCorpus:
        """Finds or creates the RagCorpus for CompetePulse pulses."""
        # Using list_corpora as seen in the SDK inspection
        existing_corpora = list(rag.list_corpora())
        for corpus in existing_corpora:
            if corpus.display_name == self.corpus_display_name:
                return corpus
        
        # Create a new corpus if not found
        # Using create_corpus as seen in the SDK inspection
        return rag.create_corpus(
            display_name=self.corpus_display_name,
            description="Historical Compete Pulse updates for RAG retrieval"
        )

    def upsert_pulses(self, pulses: List[Dict[str, Any]]):
        """
        Stores pulses into the Vertex AI RAG Engine.
        """
        if not pulses or not self.enabled:
            return

        for pulse in pulses:
            pulse_id = pulse.get('id') or f"{pulse.get('source')}_{pulse.get('title')}_{pulse.get('date', datetime.now().isoformat())}"
            filename = "".join([c if c.isalnum() or c in "._-" else "_" for c in pulse_id]) + ".txt"
            
            doc_text = f"""Title: {pulse['title']}
Source: {pulse['source']}
Category: {pulse.get('category', 'general')}
Date: {pulse.get('date', '')}
Tags: {", ".join(pulse.get('tags', [])) if isinstance(pulse.get('tags'), list) else ""}
URL: {pulse.get('source_url', '')}

Summary: {pulse.get('summary', '')}

Bridge: {pulse.get('bridge', '')}
"""
            
            temp_path = f"/tmp/{filename}"
            with open(temp_path, "w") as f:
                f.write(doc_text)
            
            try:
                # Upload to RAG Engine
                rag.upload_file(
                    corpus_name=self.corpus.name,
                    path=temp_path,
                    display_name=filename
                )
            except Exception as e:
                print(f"Warning: Could not upload {filename}: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    def query_pulses(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Queries the Vertex AI RAG Engine for relevant pulses.
        """
        if not self.enabled:
            return []
            
        response = rag.retrieval_query(
            text=text,
            rag_corpora=[self.corpus.name],
            similarity_top_k=limit
        )
        
        pulses = []
        if response.contexts and response.contexts.contexts:
            for context in response.contexts.contexts:
                pulses.append({
                    "id": context.source_uri,
                    "document": context.text,
                    "metadata": {
                        "source": "vertex_rag_engine",
                        "distance": 0.0 
                    },
                    "distance": 0.0
                })
        return pulses

    def get_all_pulses(self):
        """Lists files in the corpus."""
        if not self.enabled:
            return []
        return rag.list_files(corpus_name=self.corpus.name)

    def ingest_uris(self, uris: List[str]):
        """
        Ingests documents from Google Drive or GCS into the RAG corpus.
        Specifically supports Slides, Docs, and Sheets via Google Drive URLs.
        """
        if not uris or not self.enabled:
            return
        
        print(f"📥 Starting ingestion for {len(uris)} URIs into {self.corpus_display_name}...")
        try:
            # Vertex RAG Engine's import_files handles Drive URLs automatically
            # if they start with https://drive.google.com/
            response = rag.import_files(
                corpus_name=self.corpus.name,
                paths=uris,
                chunk_size=1024,
                chunk_overlap=200
            )
            print(f"✅ Ingestion task started. Import ID: {response.name}")
            return response
        except Exception as e:
            print(f"❌ Ingestion failed: {e}")
            raise e
