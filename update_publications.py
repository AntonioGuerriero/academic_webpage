#!/usr/bin/env python3
"""
Fetch publications from Google Scholar and update the publications
section in index.html.

Usage:
    pip install scholarly
    python update_publications.py
"""

from scholarly import scholarly
from collections import defaultdict
import re

SCHOLAR_ID = "oyH9mWYAAAAJ"

JOURNAL_KEYWORDS = [
    "journal", "transactions", "letters", "review", "magazine",
    "information fusion", "software testing, verification",
    "intelligent systems with applications",
    "future generation computer systems",
]

CONF_KEYWORDS = [
    "conference", "symposium", "workshop", "proceedings",
    "international conference", "icse", "issta", "ast", "qrs",
]


def pub_type(venue: str) -> str:
    v = venue.lower()
    if any(k in v for k in JOURNAL_KEYWORDS):
        return "journal"
    if any(k in v for k in CONF_KEYWORDS):
        return "conf"
    # fallback: if venue starts with "proceedings" or has year pattern like ICSE 20XX
    if re.search(r"\b(20\d\d)\b", venue) or v.startswith("proc"):
        return "conf"
    return "journal"


def format_authors(authors: str) -> str:
    """Highlight Antonio Guerriero in the author list."""
    parts = [a.strip() for a in authors.split(",")]
    highlighted = []
    for a in parts:
        if "guerriero" in a.lower():
            highlighted.append(f"<strong>{a}</strong>")
        else:
            highlighted.append(a)
    return ", ".join(highlighted)


def pub_html(pub: dict) -> str:
    title = pub.get("title", "").strip()
    authors = format_authors(pub.get("author", ""))
    venue = pub.get("venue", "").strip()
    ptype = pub_type(venue)
    tag_class = "tag-jour" if ptype == "journal" else "tag-conf"
    tag_label = "Journal" if ptype == "journal" else "Conference"

    return f"""
        <div class="pub-item">
          <p class="pub-title">{title}</p>
          <p class="pub-authors">{authors}</p>
          <div class="pub-meta">
            <span class="tag {tag_class}">{tag_label}</span>
            <span class="pub-venue">{venue}</span>
          </div>
        </div>"""


def build_publications_section(pubs_by_year: dict) -> str:
    lines = ["    <!-- Publications -->", "    <section id=\"publications\">",
             "      <h2>Publications</h2>", ""]
    for year in sorted(pubs_by_year.keys(), reverse=True):
        lines.append(f"      <div class=\"year-group\">")
        lines.append(f"        <p class=\"year-label\">{year}</p>")
        for pub in pubs_by_year[year]:
            lines.append(pub_html(pub))
        lines.append("      </div>")
        lines.append("")
    lines.append("    </section>")
    return "\n".join(lines)


def update_html(new_section: str):
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()

    pattern = r"<!-- Publications -->.*?</section>"
    updated = re.sub(pattern, new_section, html, flags=re.DOTALL)

    if updated == html:
        print("WARNING: Could not find publications section to replace.")
        return

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated)
    print("index.html updated successfully.")


def main():
    print(f"Fetching publications for Scholar ID: {SCHOLAR_ID}")
    author = scholarly.search_author_id(SCHOLAR_ID)
    scholarly.fill(author, sections=["publications"])

    pubs_by_year = defaultdict(list)
    total = len(author["publications"])
    print(f"Found {total} publications. Fetching details...")

    for i, pub in enumerate(author["publications"], 1):
        try:
            scholarly.fill(pub)
        except Exception as e:
            print(f"  [{i}/{total}] Could not fill pub details: {e}")

        bib = pub.get("bib", {})
        year = bib.get("pub_year", "Unknown")
        title = bib.get("title", "")

        # skip items with no title or that look like workshop chair messages
        if not title or len(title) < 10:
            continue

        pubs_by_year[year].append(bib)
        print(f"  [{i}/{total}] {year} — {title[:60]}")

    section = build_publications_section(pubs_by_year)
    update_html(section)
    print("Done.")


if __name__ == "__main__":
    main()
