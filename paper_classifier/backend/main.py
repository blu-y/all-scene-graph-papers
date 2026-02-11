"""
FastAPI backend for Paper Classifier Tool
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json
import csv
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import shutil
import re
import time
import subprocess
import os
import signal
import threading
from typing import Optional, List, Dict
from datetime import datetime

app = FastAPI(title="Paper Classifier API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "Content-Range",
        "Content-Length",
        "Accept-Ranges",
        "Content-Disposition",
    ],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SURVEY_DIR = BASE_DIR.parent / "csvs"
PDF_DIR = BASE_DIR.parent / "pdfs"
PDF_OLD_DIR = BASE_DIR.parent / "pdfs" / "old"

ABSTRACT_CSV = SURVEY_DIR / "scene_graph_papers_abstract.csv"
KOREAN_CSV = SURVEY_DIR / "scene_graph_papers_abs_kor.csv"
MINIMAL_CSV = SURVEY_DIR / "scene_graph_papers_minimal.csv"
CATEGORY_JSON = DATA_DIR / "category_metadata.json"
# CLASSIFICATION_JSON is deprecated, using MINIMAL_CSV as single source of truth


# Models
class Paper(BaseModel):
    no: int
    arxiv_url: str
    title: str
    authors: str
    abstract: str
    abstract_kor: Optional[str] = None


class Classification(BaseModel):
    paper_no: int
    category: str
    subcategory: str
    timestamp: Optional[str] = None


class CategoryUpdate(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    description: str
    parent_category: Optional[str] = None


# Caches
papers_cache: Dict[int, Paper] = {}
classifications_cache: Dict[int, Dict] = {}


def load_papers():
    """Load papers from CSV files"""
    global papers_cache

    papers_dict = {}
    with open(ABSTRACT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            no = int(row["no"])
            papers_dict[no] = Paper(
                no=no,
                arxiv_url=row["arxiv_url"],
                title=row["title"],
                authors=row["authors"],
                abstract=row["abstract"],
            )

    if KOREAN_CSV.exists():
        with open(KOREAN_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                no = int(row["no"])
                if no in papers_dict and "abstract_kor" in row:
                    papers_dict[no].abstract_kor = row["abstract_kor"]

    papers_cache = papers_dict
    return papers_cache


def load_classifications():
    """Load existing classifications from minimal CSV into cache"""
    global classifications_cache
    if not MINIMAL_CSV.exists():
        return

    classifications = {}
    with open(MINIMAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            no = int(row["no"])
            category = row.get("category", "").strip()
            subcategory = row.get("subcategory", "").strip()
            source = row.get("source", "").strip()

            if category and subcategory:
                classifications[no] = {
                    "paper_no": no,
                    "category": category,
                    "subcategory": subcategory,
                    "source": source or "ai_generated",
                    "timestamp": None,  # CSV doesn't store timestamps currently
                }

    classifications_cache = classifications
    print(f"Loaded {len(classifications_cache)} classifications from CSV")


def get_arxiv_metadata(arxiv_id: str):
    """Fetch metadata from ArXiv API"""
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
            root = ET.fromstring(content)

            # ArXiv API uses atom namespace
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            if entry is None:
                return None

            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            abstract = entry.find("atom:summary", ns).text.strip().replace("\n", " ")
            authors = [
                author.find("atom:name", ns).text
                for author in entry.findall("atom:author", ns)
            ]

            return {
                "title": title,
                "abstract": abstract,
                "authors": ", ".join(authors),
                "url": f"http://arxiv.org/abs/{arxiv_id}",
            }
    except Exception as e:
        print(f"Error fetching ArXiv metadata for {arxiv_id}: {e}")
        return None


def get_openalex_citations(arxiv_id: str):
    """Fetch citation count from OpenAlex API (from fetch_citations.py)"""
    url = f"https://api.openalex.org/works/https://doi.org/10.48550/arXiv.{arxiv_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            return data.get("cited_by_count", 0)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Stats not yet available on OpenAlex for {arxiv_id}")
            return 0
        print(f"OpenAlex HTTP Error {e.code} for {arxiv_id}")
        return 0
    except Exception as e:
        print(f"Error fetching OpenAlex citations for {arxiv_id}: {e}")
        return 0


def translate_abstract(text: str):
    """Translate abstract to Korean using deep-translator or placeholder"""
    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source="en", target="ko").translate(text)
    except ImportError:
        print(
            "Warning: deep-translator not installed. Please run 'pip install deep-translator'"
        )
        return "SEOUL (번역 대기 중): " + text[:100] + "..."
    except Exception as e:
        print(f"Translation error: {e}")
        return ""


def sync_new_pdfs():
    """Check for new PDFs and add them to CSVs"""
    if not PDF_DIR.exists():
        return

    new_pdfs = [f for f in PDF_DIR.glob("*.pdf") if f.is_file() and f.parent == PDF_DIR]
    if not new_pdfs:
        return

    print(f"Found {len(new_pdfs)} new PDFs to process...")

    # Load all existing papers to get the max 'no' and avoid duplicates
    existing_urls = {p.arxiv_url.strip() for p in papers_cache.values()}
    max_no = max(papers_cache.keys()) if papers_cache else 0

    new_entries_abstract = []
    new_entries_minimal = []
    new_entries_kor = []

    for pdf_path in new_pdfs:
        # Extract arxiv_id from filename (e.g., 2301.1234.pdf)
        arxiv_id_match = re.search(r"(\d{4}\.\d{4,5})", pdf_path.name)
        if not arxiv_id_match:
            print(f"Could not extract ArXiv ID from {pdf_path.name}, skipping.")
            continue

        arxiv_id = arxiv_id_match.group(1)
        arxiv_url = f"http://arxiv.org/abs/{arxiv_id}"

        if arxiv_url in existing_urls:
            print(
                f"Paper {arxiv_id} already exists in CSV, deleting redundant PDF file."
            )
            pdf_path.unlink()
            continue

        print(f"Fetching metadata and citations for {arxiv_id}...")
        metadata = get_arxiv_metadata(arxiv_id)
        if not metadata:
            print(f"Failed to fetch metadata for {arxiv_id}, skipping.")
            continue

        citations = get_openalex_citations(arxiv_id)
        time.sleep(0.5)  # Be polite to APIs

        print(f"Translating abstract for {arxiv_id}...")
        abstract_kor = translate_abstract(metadata["abstract"])

        max_no += 1
        paper_no = max_no

        new_entries_abstract.append(
            {
                "no": paper_no,
                "arxiv_url": metadata["url"] + " ",
                "title": metadata["title"],
                "authors": metadata["authors"],
                "abstract": metadata["abstract"],
            }
        )

        new_entries_minimal.append(
            {
                "no": paper_no,
                "category": "Others",
                "subcategory": "Uncategorized",
                "arxiv_url": metadata["url"] + " ",
                "title": metadata["title"],
                "citations": str(citations),
                "source": "uncategorized",
            }
        )

        new_entries_kor.append(
            {
                "no": paper_no,
                "arxiv_url": metadata["url"] + " ",
                "title": metadata["title"],
                "authors": metadata["authors"],
                "abstract_kor": abstract_kor,
            }
        )

        # Move PDF to old directory with clean name (no version suffix)
        if not PDF_OLD_DIR.exists():
            PDF_OLD_DIR.mkdir(parents=True)
        shutil.move(str(pdf_path), str(PDF_OLD_DIR / f"{arxiv_id}.pdf"))

    if not new_entries_abstract:
        return

    # Prepend to CSVs (read existing, then write new + existing)
    def prepend_to_csv(file_path, new_entries):
        if not file_path.exists():
            return

        existing_rows = []
        fieldnames = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            existing_rows = list(reader)

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            # New entries first (sorted descending by 'no')
            writer.writerows(sorted(new_entries, key=lambda x: x["no"], reverse=True))
            writer.writerows(existing_rows)

    prepend_to_csv(ABSTRACT_CSV, new_entries_abstract)
    prepend_to_csv(MINIMAL_CSV, new_entries_minimal)
    prepend_to_csv(KOREAN_CSV, new_entries_kor)

    print(f"Added {len(new_entries_abstract)} new papers to CSVs.")
    # Reload caches
    load_papers()
    load_classifications()


def update_minimal_csv(paper_no: int, category: str, subcategory: str, source: str):
    """Update a specific paper's classification in the minimal CSV file"""
    if not MINIMAL_CSV.exists():
        return

    rows = []
    fieldnames = []
    with open(MINIMAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            if int(row["no"]) == paper_no:
                row["category"] = category
                row["subcategory"] = subcategory
                row["source"] = source
            rows.append(row)

    with open(MINIMAL_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# Load papers on startup
@app.on_event("startup")
async def startup_event():
    load_papers()
    load_classifications()
    sync_new_pdfs()


# Endpoints
@app.get("/")
async def root():
    return {"message": "Paper Classifier API", "papers_loaded": len(papers_cache)}


@app.get("/api/papers/{no}", response_model=Paper)
async def get_paper(no: int):
    """Get paper by number"""
    if no not in papers_cache:
        raise HTTPException(status_code=404, detail=f"Paper {no} not found")
    return papers_cache[no]


@app.get("/api/papers/{no}/classification")
async def get_paper_classification(no: int):
    """Get existing classification for a paper from cache"""
    return classifications_cache.get(no)


@app.get("/api/papers/{no}/next")
async def get_next_paper(no: int):
    """Get next unclassified or AI-classified paper"""
    target_sources = {"ai_generated", "uncategorized"}

    unclassified_nos = {
        paper_no
        for paper_no, c in classifications_cache.items()
        if c.get("source") in target_sources
    }

    all_nos = sorted(papers_cache.keys(), reverse=True)
    current_idx = all_nos.index(no) if no in all_nos else -1

    for next_no in all_nos[current_idx + 1 :]:
        if next_no in unclassified_nos:
            return {"next_no": next_no}

    for next_no in all_nos:
        if next_no in unclassified_nos:
            return {"next_no": next_no}

    return {"next_no": None, "message": "All papers manually classified!"}


@app.get("/api/papers/{no}/next-asc")
async def get_next_paper_ascending(no: int):
    target_sources = {"ai_generated", "uncategorized"}

    unclassified_nos = {
        paper_no
        for paper_no, c in classifications_cache.items()
        if c.get("source") in target_sources
    }

    all_nos = sorted(papers_cache.keys())
    current_idx = all_nos.index(no) if no in all_nos else -1

    for next_no in all_nos[current_idx + 1 :]:
        if next_no in unclassified_nos:
            return {"next_no": next_no}

    for next_no in all_nos:
        if next_no in unclassified_nos:
            return {"next_no": next_no}

    return {"next_no": None, "message": "All papers manually classified!"}


@app.get("/api/categories")
async def get_categories():
    """Get category tree"""
    with open(CATEGORY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/categories")
async def add_category(update: CategoryUpdate):
    """Add new category or subcategory"""
    with open(CATEGORY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if update.parent_category:
        if update.parent_category not in data["categories"]:
            raise HTTPException(
                status_code=404,
                detail=f"Parent category '{update.parent_category}' not found",
            )

        if update.subcategory:
            data["categories"][update.parent_category]["subcategories"][
                update.subcategory
            ] = {"description": update.description}
    else:
        if not update.category:
            raise HTTPException(
                status_code=400,
                detail="Category name is required when adding a new category",
            )
        data["categories"][update.category] = {
            "description": update.description,
            "subcategories": {},
        }

    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(CATEGORY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"message": "Category added successfully", "data": data}


@app.put("/api/categories")
async def update_category(update: CategoryUpdate):
    """Update existing category"""
    with open(CATEGORY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    if update.parent_category and update.subcategory:
        # Update subcategory
        if update.parent_category not in data["categories"]:
            raise HTTPException(
                status_code=404, detail=f"Category '{update.parent_category}' not found"
            )
        if (
            update.subcategory
            not in data["categories"][update.parent_category]["subcategories"]
        ):
            raise HTTPException(
                status_code=404, detail=f"Subcategory '{update.subcategory}' not found"
            )

        data["categories"][update.parent_category]["subcategories"][update.subcategory][
            "description"
        ] = update.description
    else:
        # Update category
        if update.category not in data["categories"]:
            raise HTTPException(
                status_code=404, detail=f"Category '{update.category}' not found"
            )

        data["categories"][update.category]["description"] = update.description

    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    with open(CATEGORY_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"message": "Category updated successfully"}


@app.post("/api/classify")
async def classify_paper(classification: Classification):
    """Save paper classification to CSV and cache"""
    if not classification.timestamp:
        classification.timestamp = datetime.now().isoformat()

    # Determine source: if set to Others-Uncategorized, treat as uncategorized
    source = "manual"
    if (
        classification.category == "Others"
        and classification.subcategory == "Uncategorized"
    ):
        source = "uncategorized"

    # Update cache
    classification_dict = classification.dict()
    classification_dict["source"] = source
    classifications_cache[classification.paper_no] = classification_dict

    # Update minimal CSV
    update_minimal_csv(
        classification.paper_no,
        classification.category,
        classification.subcategory,
        source,
    )

    return {"message": "Classification saved", "paper_no": classification.paper_no}


@app.get("/api/pdf/{no}")
async def get_pdf(no: int):
    """Serve PDF file"""
    if no not in papers_cache:
        raise HTTPException(status_code=404, detail=f"Paper {no} not found")

    paper = papers_cache[no]
    arxiv_id = (
        paper.arxiv_url.strip()
        .replace("http://arxiv.org/abs/", "")
        .replace("https://arxiv.org/abs/", "")
    )

    pdf_paths = [
        PDF_DIR / f"{arxiv_id}.pdf",
        PDF_DIR / f"{no}.pdf",
        PDF_OLD_DIR / f"{arxiv_id}.pdf",
        PDF_OLD_DIR / f"{no}.pdf",
    ]

    for pdf_path in pdf_paths:
        if pdf_path and pdf_path.exists():
            return FileResponse(pdf_path, media_type="application/pdf")

    raise HTTPException(
        status_code=404, detail=f"PDF for paper {no} not found (tried: {arxiv_id}.pdf)"
    )


@app.get("/api/stats")
async def get_stats():
    """Get classification statistics from cache"""
    total_papers = len(papers_cache)
    manually_classified_list = [
        c for c in classifications_cache.values() if c.get("source") != "ai_generated"
    ]
    manually_classified_count = len(manually_classified_list)
    remaining = total_papers - manually_classified_count

    by_category = {}
    for c in manually_classified_list:
        cat = c["category"]
        if cat not in by_category:
            by_category[cat] = 0
        by_category[cat] += 1

    return {
        "total": total_papers,
        "classified": manually_classified_count,
        "remaining": remaining,
        "percentage": round(manually_classified_count / total_papers * 100, 1)
        if total_papers > 0
        else 0,
        "by_category": by_category,
    }


@app.post("/api/finish")
async def finish_classification():
    """Run generation script and shutdown server"""
    try:
        # Run the generation script
        script_path = BASE_DIR.parent / "scripts" / "generate_classified_mds.py"

        # Determine python executable (backend venv)
        if os.name == "nt":
            python_executable = BASE_DIR / "backend" / "venv" / "Scripts" / "python.exe"
        else:
            python_executable = BASE_DIR / "backend" / "venv" / "bin" / "python3"

        # Check if venv exists, fallback to system python if not
        if not python_executable.exists():
            python_executable = "python3"
        else:
            python_executable = str(python_executable)

        print(f"Running generation script: {script_path}")
        subprocess.run([python_executable, str(script_path)], check=True)
        print("Generation script completed successfully.")

        # Shutdown signal
        # We'll use a delayed shutdown to allow the response to reach the client
        def shutdown():
            time.sleep(2)
            print("Shutting down everything (backend, frontend, and parent process)...")
            # Send SIGINT to the entire process group to kill concurrently and the frontend
            try:
                os.killpg(os.getpgrp(), signal.SIGINT)
            except Exception:
                # Fallback to single process kill if process group kill fails
                os.kill(os.getpid(), signal.SIGINT)

        threading.Thread(target=shutdown).start()

        return {
            "message": "Classification complete. Markdown files generated. Shutting down..."
        }
    except Exception as e:
        print(f"Error in finish_classification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
