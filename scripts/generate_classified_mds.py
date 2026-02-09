import pandas as pd
import os
import shutil
import urllib.parse

# Paths
BASE_DIR = '/Users/username/GitHub/scene-graph-papers'
CSV_PATH = os.path.join(BASE_DIR, 'csvs/scene_graph_papers_minimal.csv')
OUTPUT_DIR = os.path.join(BASE_DIR, 'classified')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
README_PATH = os.path.join(BASE_DIR, 'README.md')

def get_source_emoji(source):
    source = str(source).lower().strip()
    if source == 'manual':
        return '👤'
    elif 'ai' in source:
        return '🤖'
    else:
        return '❌'

def generate_markdown_table(df):
    header = "| no | date | category | subcategory | sorted by | arXiv | title | citation |\n"
    separator = "|---:|:---:|:---|:---|:---:|:---:|:---|---:|\n"
    
    rows = []
    for _, row in df.iterrows():
        source_emoji = get_source_emoji(row['source'])
        arxiv_url = row['arxiv_url'].strip()
        arxiv_link = f"[📎]({arxiv_url})"
        
        # Extract date from ArXiv ID (e.g., 2602 from 2602.12345 -> 26.02)
        arxiv_id = arxiv_url.split('/')[-1]
        if len(arxiv_id) >= 4 and arxiv_id[:4].isdigit():
            date_display = f"{arxiv_id[0:2]}.{arxiv_id[2:4]}"
        else:
            date_display = "-"
            
        title = str(row['title']).strip()
        citations = row['citations']
        citation_display = "-" if citations == -1 else str(int(citations) if not pd.isna(citations) else 0)
        
        # Clean title from any vertical bars to avoid breaking markdown table
        title = title.replace('|', '\\|')
        
        # Use row['no'] instead of sequential index
        rows.append(f"| {row['no']} | {date_display} | {row['category']} | {row['subcategory']} | {source_emoji} | {arxiv_link} | {title} | {citation_display} |")
    
    return header + separator + "\n".join(rows)

def update_readme_categories(tree_md):
    if not os.path.exists(README_PATH):
        return

    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    header = "## 📚 Categories"
    if header in content:
        # split by header
        prefix, rest = content.split(header, 1)
        
        # Determine where the category section ends
        # Look for the next major separator like "---" or next "## "
        # But specifically the prompt shows a "---" after the category list
        suffix = ""
        
        # Look for the next separator after some content
        marker = "\n---"
        if marker in rest:
            # We found a separator, keep it and everything after it
            actual_rest = rest.split(marker, 1)[1]
            suffix = marker + actual_rest
        
        new_content = prefix + header + "\n\n" + tree_md + "\n" + suffix
    else:
        # Append to the end if not found
        new_content = content.rstrip() + "\n\n---\n\n" + header + "\n\n" + tree_md
        print(f"Warning: '{header}' header not found. Appending to the end of README.md.")
    
    with open(README_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Updated README.md with new category tree.")

def main():
    # Load data
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return
    
    df = pd.read_csv(CSV_PATH)
    
    # Remove existing classified directory to start fresh
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)
    
    # Group by Category
    categories = df['category'].unique()
    
    # Sort categories to keep a consistent order (Custom order preferred)
    custom_order = ["Scene Graph", "Robotics", "Reasoning", "Others"]
    sorted_categories = sorted(categories, key=lambda x: custom_order.index(x) if x in custom_order else 999)
    
    tree_lines = []
    
    for cat in sorted_categories:
        if pd.isna(cat): continue
        
        cat_name = str(cat).strip()
        cat_filename = cat_name.replace('/', '_')
        cat_dir_rel = os.path.join('classified', cat_filename)
        cat_dir_abs = os.path.join(OUTPUT_DIR, cat_filename)
        os.makedirs(cat_dir_abs, exist_ok=True)
        
        # URL encoding for links in README
        encoded_cat_name = urllib.parse.quote(cat_filename)
        cat_md_link = f"./classified/{encoded_cat_name}/{encoded_cat_name}.md"
        tree_lines.append(f"- [**{cat_name}**]({cat_md_link})")
        
        # 1. Category-wide MD
        cat_df = df[df['category'] == cat].sort_values(by='no', ascending=False)
        cat_md_path = os.path.join(cat_dir_abs, f"{cat_filename}.md")
        
        with open(cat_md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {cat_name}\n\n")
            f.write(generate_markdown_table(cat_df))
            
        # 2. Subcategory-specific MDs
        # Sort subcategories: alphabetical but "Others" always last
        raw_subs = cat_df['subcategory'].unique()
        def sub_sort_key(x):
            x_str = str(x).strip()
            x_lower = x_str.lower()
            tail = ["others", "weakly related", "not related", "uncategorized"]
            if x_lower in tail:
                return (1, tail.index(x_lower), x_str)
            return (0, 0, x_str)
        
        subcategories = sorted(raw_subs, key=sub_sort_key)
        
        for sub in subcategories:
            if pd.isna(sub): continue
            
            sub_name = str(sub).strip()
            sub_filename = sub_name.replace('/', '_')
            sub_df = cat_df[cat_df['subcategory'] == sub].sort_values(by='no', ascending=False)
            
            sub_full_filename = f"{cat_filename}-{sub_filename}"
            encoded_sub_full_filename = urllib.parse.quote(sub_full_filename)
            sub_md_link = f"./classified/{encoded_cat_name}/{encoded_sub_full_filename}.md"
            tree_lines.append(f"  - [{sub_name}]({sub_md_link})")
            
            sub_md_path = os.path.join(cat_dir_abs, f"{sub_full_filename}.md")
            
            with open(sub_md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {cat_name} - {sub_name}\n\n")
                f.write(generate_markdown_table(sub_df))

    # Update README.md
    update_readme_categories("\n".join(tree_lines) + "\n")
    print(f"Successfully generated markdown files in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
