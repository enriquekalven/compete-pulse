import os
import sys
from datetime import datetime

# Set path to include src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

try:
    from compete_pulse_agent.core.vector_store import CompetePulseVectorStore
    # Test if we can import the necessary bits
    import vertexai
    from vertexai.preview import rag
except ImportError as e:
    print(f"❌ Error: Could not import dependencies. {e}")
    sys.exit(1)

def verify_vertex_rag():
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "project-maui")
    print(f"📡 Testing Vertex AI RAG connection in project: {project_id}...")
    
    try:
        # Initialize the vector store
        store = CompetePulseVectorStore(project_id=project_id)
        print(f"✅ Connection established. Corpus Name: {store.corpus.name}")
        print(f"✅ Corpus Display Name: {store.corpus.display_name}")

        # 1. Test Pulse Upsert
        test_pulse = {
            "title": "Vertex AI RAG Engine Launch",
            "source": "google-ai-news",
            "summary": "Google announces managed RAG Engine for generative AI agents.",
            "bridge": "Managed memory for agents is here!",
            "category": "roadmap",
            "source_url": "https://cloud.google.com/vertex-ai/docs/rag-engine",
            "date": datetime.now().isoformat()
        }
        
        print(f"📤 Uploading test pulse: {test_pulse['title']}...")
        store.upsert_pulses([test_pulse])
        print("✅ Pulse uploaded successfully.")

        # 2. Test Query
        query_text = "RAG Engine"
        print(f"🔍 Querying for: '{query_text}'...")
        results = store.query(query_text, n_results=1)
        
        if results:
            print(f"✅ Found {len(results)} results.")
            for i, r in enumerate(results):
                print(f"--- Result {i+1} ---")
                print(f"ID: {r['id']}")
                print(f"Content Snippet: {r['document'][:200]}...")
        else:
            print("⚠️ No results found. Note: Vertex AI indexing can take a few minutes for new files.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_vertex_rag()
