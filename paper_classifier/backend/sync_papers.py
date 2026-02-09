
import sys
from pathlib import Path

# Add backend directory to path to import logic
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from main import load_papers, load_classifications, sync_new_pdfs

def perform_sync():
    print("=== Starting Paper Synchronization ===")
    load_papers()
    load_classifications()
    sync_new_pdfs()
    print("=== Synchronization Complete ===")

if __name__ == "__main__":
    perform_sync()
