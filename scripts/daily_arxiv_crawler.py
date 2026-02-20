import urllib.request
import urllib.error
import re
import csv
import os
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time
import subprocess
import shutil

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CSVS_DIR = BASE_DIR / "csvs"
PDFS_DIR = BASE_DIR / "pdfs"
PDF_OLD_DIR = PDFS_DIR / "old"

ABSTRACT_CSV = CSVS_DIR / "scene_graph_papers_abstract.csv"
KOREAN_CSV = CSVS_DIR / "scene_graph_papers_abs_kor.csv"
MINIMAL_CSV = CSVS_DIR / "scene_graph_papers_minimal.csv"

def get_existing_urls():
    """Load existing arXiv urls to check for duplicates."""
    existing_urls = set()
    max_no = 0
    if ABSTRACT_CSV.exists():
        with open(ABSTRACT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row["arxiv_url"].strip())
                no = int(row["no"])
                if no > max_no:
                    max_no = no
    return existing_urls, max_no

def get_arxiv_metadata(arxiv_id: str):
    """Fetch metadata from ArXiv API (copied from main.py)"""
    try:
        url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
            root = ET.fromstring(content)
            
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
    """Fetch citation count from OpenAlex API (copied from main.py)"""
    url = f"https://api.openalex.org/works/https://doi.org/10.48550/arXiv.{arxiv_id}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'mailto:user@example.com'})
        with urllib.request.urlopen(req, timeout=10) as response:
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
    """Translate abstract to Korean using GoogleTranslator (copied from main.py)"""
    try:
        return GoogleTranslator(source="en", target="ko").translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return ""

def download_pdf(arxiv_id: str):
    """Download PDF for the paper and put it in PDFs folder."""
    if not PDFS_DIR.exists():
        PDFS_DIR.mkdir(parents=True, exist_ok=True)
        
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    pdf_path = PDFS_DIR / f"{arxiv_id}.pdf"
    
    if pdf_path.exists():
        print(f"PDF {arxiv_id}.pdf already exists in directory.")
        return
        
    try:
        print(f"Downloading PDF for {arxiv_id}...")
        req = urllib.request.Request(pdf_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(pdf_path, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        print(f"Saved PDF to {pdf_path}")
        time.sleep(1) # Be polite
    except Exception as e:
        print(f"Failed to download PDF for {arxiv_id}: {e}")

def prepend_to_csv(file_path, new_entries):
    if not file_path.exists():
        return
        
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)
        
    with open(file_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        # Sort new entries descending by 'no' to keep newest on top
        writer.writerows(sorted(new_entries, key=lambda x: x["no"], reverse=True))
        writer.writerows(existing_rows)

def main():
    print("Fetching Search Results...")
    search_url = "https://arxiv.org/search/?query=%22scene+graph%22&searchtype=all&abstracts=show&order=-announced_date_first&size=200"
    try:
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req)
        html = resp.read()
        soup = BeautifulSoup(html, 'html.parser')
    except Exception as e:
        print(f"Failed to fetch or parse search URL: {e}")
        return
        
    links = [a['href'] for a in soup.find_all('a', href=re.compile(r'arxiv\.org/abs/\d{4}\.\d{4,5}'))]
    unique_ids = []
    for link in links:
        match = re.search(r'arxiv\.org/abs/(\d{4}\.\d{4,5})', link)
        if match:
            arxiv_id = match.group(1)
            if arxiv_id not in unique_ids:
                unique_ids.append(arxiv_id)
                
    print(f"Found {len(unique_ids)} unique papers from search page.")
    
    existing_urls, max_no = get_existing_urls()
    print(f"Currently have {len(existing_urls)} papers in CSV. Max No: {max_no}")
    
    new_entries_abstract = []
    new_entries_minimal = []
    new_entries_kor = []
    
    # Since search is ordered by announced_date_first, older papers are at the end of unique_ids.
    # We should add them so that the newest gets the highest ID. We reverse the list for appending no.
    new_arxiv_ids = [aid for aid in unique_ids if f"http://arxiv.org/abs/{aid}" not in existing_urls and f"https://arxiv.org/abs/{aid}" not in existing_urls]
    
    print(f"Found {len(new_arxiv_ids)} NEW papers to add.")
    if not new_arxiv_ids:
        print("No new papers found. Exiting.")
        return
        
    # Process from oldest of the new to newest, so newest gets highest max_no
    new_arxiv_ids.reverse()
    
    for arxiv_id in new_arxiv_ids:
        print(f"\nProcessing new paper: {arxiv_id}")
        
        metadata = get_arxiv_metadata(arxiv_id)
        if not metadata:
            print("Failed to get metadata, skipping.")
            continue
            
        citations = get_openalex_citations(arxiv_id)
        abstract_kor = translate_abstract(metadata["abstract"])
        time.sleep(1) # rate limiting
        
        download_pdf(arxiv_id)
        
        max_no += 1
        paper_no = max_no
        
        new_entries_abstract.append({
            "no": paper_no,
            "arxiv_url": metadata["url"] + " ",
            "title": metadata["title"],
            "authors": metadata["authors"],
            "abstract": metadata["abstract"],
        })
        
        new_entries_minimal.append({
            "no": paper_no,
            "category": "Others",
            "subcategory": "Uncategorized",
            "arxiv_url": metadata["url"] + " ",
            "title": metadata["title"],
            "citations": str(citations),
            "source": "uncategorized",
        })
        
        new_entries_kor.append({
            "no": paper_no,
            "arxiv_url": metadata["url"] + " ",
            "title": metadata["title"],
            "authors": metadata["authors"],
            "abstract_kor": abstract_kor,
        })
        
    if new_entries_abstract:
        print("\nUpdating CSV files...")
        prepend_to_csv(ABSTRACT_CSV, new_entries_abstract)
        prepend_to_csv(MINIMAL_CSV, new_entries_minimal)
        prepend_to_csv(KOREAN_CSV, new_entries_kor)
        print("CSV files updated.")
        
    print("\nRunning generate_classified_mds.py...")
    script_path = BASE_DIR / "scripts" / "generate_classified_mds.py"
    subprocess.run(["python3", str(script_path)], check=True)
    print("Done.")

if __name__ == "__main__":
    main()
