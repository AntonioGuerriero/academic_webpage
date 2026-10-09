#!/usr/bin/env python3
"""
Update the publications section of index.html from a Google Scholar export.

How to get the file:
    Google Scholar profile -> tick the select-all box -> Export -> CSV

Usage:
    python update_publications.py path/to/citations.csv

No dependencies, no scraping: the CSV is exported by hand, so Scholar
cannot block the script.
"""

import csv
import html
import re
import sys
from collections import defaultdict

ME = "guerriero"

CONF_WORDS = ("conference", "symposium", "workshop", "proceedings")

# Scholar lowercases some acronyms in titles
ACRONYMS = {"cnn": "CNN", "ddos": "DDoS"}

# Scholar's CSV truncates long author lists at this many names
MAX_AUTHORS = 10


def clean_title(title: str) -> str:
    return " ".join(ACRONYMS.get(w.lower(), w) for w in title.strip().split(" "))


def clean_venue(venue: str) -> str:
    venue = re.sub(r"^Proceedings of the\s+", "", venue.strip())
    return re.sub(r"^20\d\d\s+", "", venue)


def pub_type(venue: str) -> str:
    return "conf" if any(w in venue.lower() for w in CONF_WORDS) else "journal"


def format_authors(raw: str) -> str:
    """'Last, First; Last, First; ' -> 'First Last, First Last', me in bold."""
    names = []
    for entry in (e.strip() for e in raw.split(";")):
        if not entry:
            continue
        last, _, first = entry.partition(",")
        name = f"{first.strip()} {last.strip()}".strip()
        name = html.escape(name)
        names.append(f"<strong>{name}</strong>" if ME in name.lower() else name)
    if len(names) >= MAX_AUTHORS:
        names.append("et al.")
    return ", ".join(names)


def pub_html(row: dict) -> str:
    title = html.escape(clean_title(row["Title"]))
    authors = format_authors(row["Authors"])
    venue = clean_venue(row["Publication"])
    ptype = pub_type(venue)
    tag_class = "tag-conf" if ptype == "conf" else "tag-jour"
    tag_label = "Conference" if ptype == "conf" else "Journal"
    return f"""
        <div class="pub-item">
          <p class="pub-title">{title}</p>
          <p class="pub-authors">{authors}</p>
          <div class="pub-meta">
            <span class="tag {tag_class}">{tag_label}</span>
            <span class="pub-venue">{html.escape(venue)}</span>
          </div>
        </div>"""


def build_section(by_year: dict) -> str:
    lines = ['    <!-- Publications -->', '    <section id="publications">',
             '      <h2>Publications</h2>', '']
    for year in sorted(by_year, reverse=True):
        lines.append('      <div class="year-group">')
        lines.append(f'        <p class="year-label">{year}</p>')
        lines.extend(pub_html(r) for r in by_year[year])
        lines.append('      </div>')
        lines.append('')
    lines.append('    </section>')
    return "\n".join(lines)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)

    by_year = defaultdict(list)
    with open(sys.argv[1], newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            # committee pages, prefaces and the like have no venue or no year
            if not row["Publication"].strip() or not row["Year"].strip().isdigit():
                print(f"skipped: {row['Title'][:70]}")
                continue
            by_year[int(row["Year"])].append(row)

    with open("index.html", encoding="utf-8") as f:
        page = f.read()
    section = build_section(by_year)
    new_page, n = re.subn(r"<!-- Publications -->.*?</section>",
                          lambda _: section, page, flags=re.DOTALL)
    if n != 1:
        sys.exit("Could not find the publications section in index.html")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(new_page)
    print(f"index.html updated: {sum(map(len, by_year.values()))} publications")


if __name__ == "__main__":
    main()
