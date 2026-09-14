#!/usr/bin/env python3
import csv, hashlib, re, unicodedata
from collections import Counter
from pathlib import Path

BASE = Path(__file__).parent
SOURCE = BASE / "assamese_monolingual_sentences_final_cleaned.csv"
REPORT = BASE / "assamese_inspection_report.txt"

ASSAM_RE = re.compile(r"[\u0980-\u09FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
URL_RE = re.compile(r"(?:https?://|www\.)", re.I)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
LIST_RE = re.compile(r"(?:\s*,\s*){5,}|(?:\s*;\s*){4,}|(?:\s*\|\s*){3,}")

def sha(text):
    return hashlib.sha256(text.encode("utf-8")).digest()

def main():
    if not SOURCE.exists():
        print("ERROR: Source file not found:")
        print(SOURCE)
        return 1

    size = SOURCE.stat().st_size
    total = blank = nonempty = dup = short = nums = urls = emails = lists = 0
    assam = english_heavy = 0
    chars = Counter()
    words = Counter()
    seen = set()
    char_total = word_total = 0
    shortest = None
    longest = ""
    longest_line = 0
    samples = []

    print("JASS ASSAMESE CORPUS INSPECTOR v1.0")
    print("=" * 40)
    print(f"Source: {SOURCE}")
    print(f"Size: {size/(1024**2):,.2f} MB")
    print("Mode: READ-ONLY")
    print("\nScanning corpus...")

    with SOURCE.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["text"]:
            print(f"ERROR: Expected header ['text']; got {reader.fieldnames!r}")
            return 1

        for row in reader:
            total += 1
            text = (row.get("text") or "").strip()
            if not text:
                blank += 1
                continue

            nonempty += 1
            digest = sha(text)
            if digest in seen:
                dup += 1
            else:
                seen.add(digest)

            nchar = len(text)
            nword = len(text.split())
            char_total += nchar
            word_total += nword
            chars.update(text)
            words.update(text.split())

            if shortest is None or nchar < shortest[0]:
                shortest = (nchar, text, total)
            if nchar > len(longest):
                longest = text
                longest_line = total

            short += nchar < 20
            nums += any(c.isdigit() for c in text)
            urls += bool(URL_RE.search(text))
            emails += bool(EMAIL_RE.search(text))
            lists += bool(LIST_RE.search(text))

            a = len(ASSAM_RE.findall(text))
            l = len(LATIN_RE.findall(text))
            assam += a >= 3
            english_heavy += l > a and l >= 5

            if len(samples) < 20:
                samples.append((total, text))

            if total % 100000 == 0:
                print(f"  {total:,} records...")

    def pct(n):
        return (100*n/nonempty) if nonempty else 0

    lines = [
        "JASS ASSAMESE CORPUS INSPECTOR v1.0",
        "=" * 40, "",
        "SOURCE",
        f"File: {SOURCE}",
        f"Size: {size/(1024**2):,.2f} MB",
        "Mode: READ-ONLY", "",
        "RECORDS",
        f"Total records: {total:,}",
        f"Blank records: {blank:,}",
        f"Non-empty records: {nonempty:,}",
        f"Unique records: {nonempty-dup:,}",
        f"Duplicate records: {dup:,}", "",
        "TEXT PROFILE",
        f"Average characters: {char_total/nonempty:,.2f}" if nonempty else "Average characters: 0.00",
        f"Average words: {word_total/nonempty:,.2f}" if nonempty else "Average words: 0.00",
        f"Shortest record: {shortest[0]:,} chars" if shortest else "Shortest record: 0 chars",
        f"Longest record: {len(longest):,} chars", "",
        "QUALITY / CONTENT SIGNALS",
        f"Very short records (<20 chars): {short:,} ({pct(short):.2f}%)",
        f"Records containing numbers: {nums:,} ({pct(nums):.2f}%)",
        f"Records containing URLs: {urls:,} ({pct(urls):.2f}%)",
        f"Records containing email-like text: {emails:,} ({pct(emails):.2f}%)",
        f"Assamese-script candidates (heuristic): {assam:,} ({pct(assam):.2f}%)",
        f"English-heavy candidates (heuristic): {english_heavy:,} ({pct(english_heavy):.2f}%)",
        f"List-like candidates (heuristic): {lists:,} ({pct(lists):.2f}%)", "",
        "TOP WORDS"
    ]
    lines += [f"  {w}: {n:,}" for w,n in words.most_common(30)]
    lines += ["", "TOP CHARACTERS"]
    lines += [f"  {repr(c)}: {n:,}" for c,n in chars.most_common(30)]
    lines += ["", "SAMPLE RECORDS"]
    lines += [f"{i:02d}. [source line {ln}] {txt}" for i,(ln,txt) in enumerate(samples,1)]
    lines += ["", "SHORTEST RECORD SAMPLE"]
    if shortest:
        lines.append(f"[source line {shortest[2]}] {shortest[1]}")
    lines += ["", "LONGEST RECORD SAMPLE",
              f"[source line {longest_line}] {longest[:3000]}{' ...' if len(longest)>3000 else ''}",
              "", "ASSESSMENT",
              "Descriptive inspection only; heuristic categories are not authoritative linguistic labels.",
              "The source corpus was not modified."]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines))
    print(f"\nReport written to: {REPORT}")

if __name__ == "__main__":
    raise SystemExit(main())
