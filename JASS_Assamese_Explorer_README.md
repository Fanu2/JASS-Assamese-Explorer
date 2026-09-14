# JASS Assamese Explorer

**JASS Assamese Explorer** is a lightweight desktop application for exploring a large Assamese-language corpus and turning selected Assamese text into attractive shareable cards.

It is part of the JASS language-exploration work and follows the same practical philosophy used for the Mizo project:

> **Inspect the corpus → build a verified searchable database → explore it interactively → create useful language artifacts.**

---

## Current Version

**JASS Assamese Explorer v1.1.1**

This is the current working version after fixing the Romantic Card Studio / Create Card source-line formatting issue.

### Current status

**STABLE WORKING CHECKPOINT**

The Explorer, corpus database, full-text search, and Romantic Card Studio are operational.

---

# 1. Assamese Corpus

The Explorer is built around the Assamese monolingual corpus:

```text
assamese_monolingual_sentences_final_cleaned.csv
```

### Source size

Approximately:

```text
624.52 MB
```

### Corpus statistics

| Metric | Result |
|---|---:|
| Total records | **1,613,879** |
| Blank records | **0** |
| Non-empty records | **1,613,879** |
| Unique records | **1,613,879** |
| Duplicate records | **0** |
| Assamese-script candidates | **1,613,879 (100%)** |
| English-heavy candidates | **0** |
| URL-containing records | **35** |
| Email-like records | **3** |
| Average characters | **152.99** |
| Average words | **23.96** |
| Shortest record | **20 characters** |
| Longest record | **85,133 characters** |

The inspection was descriptive and heuristic. The source corpus itself was not modified.

---

# 2. Corpus Inspector

Before creating the application database, the source corpus was inspected using:

```text
JASS_Assamese_Corpus_Inspector_v1.0.py
```

The inspector performs read-only analysis including:

- record count
- blank records
- duplicate detection
- character statistics
- word statistics
- URL/email signals
- Assamese-script heuristic
- English-heavy heuristic
- list-like records
- top words
- top characters
- sample records
- shortest record
- longest record

The resulting report is:

```text
assamese_inspection_report.txt
```

---

# 3. Verified SQLite Database

The corpus was converted into a searchable SQLite database using:

```text
JASS_Assamese_Corpus_Builder_v1.0.py
```

Database:

```text
JASS_Assamese_Corpus.db
```

### Database size

Approximately:

```text
947.60 MB
```

### Build verification

The database build completed with:

```text
Record count: PASSED
FTS count: PASSED
Source integrity: PASSED
SQLite integrity: PASSED
FTS search test: PASSED
Overall verification: PASSED
```

The database contains:

```text
1,613,879 records
1,613,879 FTS records
```

A full-text search test for the Assamese word:

```text
আৰু
```

returned:

```text
517,534 matches
```

### Source integrity

The source SHA-256 recorded during the build is:

```text
6b8cd9c4e948fc675491aef6ceb51a7a64d0a55184c268aea5c97d97b1257c79
```

The builder did not modify the source corpus.

Build report:

```text
assamese_build_report.txt
```

---

# 4. Explorer Application

The Explorer provides an interactive interface over the SQLite/FTS database.

Its purpose is not to edit the corpus. The corpus remains a protected read-only source.

The application allows the user to:

- search the Assamese corpus
- browse matching records
- inspect Assamese text
- view source-line information
- work with selected corpus records
- create visual text cards

The database provides the searchable working layer while the original CSV remains untouched.

---

# 5. Romantic Card Studio

One of the main features of the Explorer is the **Romantic Card Studio**.

A selected Assamese record can be transformed into a visually styled card.

The Card Studio supports the working card workflow developed during the Explorer project.

### Current capabilities

- Assamese text preview
- editable English/secondary text area where applicable
- live card preview
- typography controls
- bold/text styling
- positioning controls
- theme/background styling
- source-line information
- PNG/JPEG output
- card creation directly from an Explorer result

### Create Card

The **Create Card** button opens the Romantic Card Studio for the selected corpus record.

The current v1.1.1 checkpoint fixes the earlier failure caused by source-line values being stored as strings.

The faulty formatting:

```python
f"{self.source_line:,}"
```

could fail when `source_line` was a string.

The current implementation safely handles the source-line value.

---

# 6. Font and Assamese Rendering

The application uses Qt/PySide6 for its interface and rendering.

Windows may display Qt font-database messages such as:

```text
OpenType support missing for ...
```

for fallback fonts.

These messages are warnings and are not the cause of the previous Create Card crash.

The important requirement is that an Assamese-capable font is available for correct Assamese glyph rendering.

---

# 7. Project Files

The Assamese Explorer working directory contains the principal components:

```text
Assamese_Corpus/
│
├── assamese_monolingual_sentences_final_cleaned.csv
├── JASS_Assamese_Corpus.db
├── JASS_Assamese_Corpus_Inspector_v1.0.py
├── JASS_Assamese_Corpus_Builder_v1.0.py
├── JASS_Assamese_Explorer_v1.1.1_card_fixed.py
├── assamese_inspection_report.txt
├── assamese_build_report.txt
└── README.md
```

The exact set of auxiliary/cache files may vary depending on the local environment.

---

# 8. Running the Explorer

Open PowerShell in the Assamese corpus directory:

```powershell
cd "C:\Users\singh\Downloads\Assamese_Corpus"
```

Run:

```powershell
py .\JASS_Assamese_Explorer_v1.1.1_card_fixed.py
```

The application should start using the local Assamese SQLite database.

---

# 9. Data Safety

The original corpus is treated as **READ-ONLY**.

The project deliberately separates:

```text
SOURCE CORPUS
      ↓
INSPECTION
      ↓
VERIFIED DATABASE
      ↓
EXPLORER
      ↓
USER-SELECTED OUTPUT
```

The Explorer does not need to modify the original CSV.

This makes the source corpus reproducible and protects the underlying linguistic resource.

---

# 10. Mizo and Assamese

The Assamese project is intentionally being developed alongside the earlier JASS Mizo work.

The two projects provide useful low-resource-language experimentation environments.

### Mizo

- larger corpus
- approximately 4 million sentences
- strong resource for large-scale experimentation

### Assamese

- 1.61 million verified records
- approximately 624.52 MB source CSV
- 947.60 MB SQLite/FTS database
- excellent Assamese-script coverage
- interactive Explorer
- Romantic Card Studio

The goal is not to declare one language universally better.

Instead, the two projects allow JASS to compare:

- corpus quality
- search behaviour
- vocabulary
- sentence characteristics
- database performance
- language exploration
- AI/model possibilities
- practical usefulness

---

# 11. Design Philosophy

JASS Assamese Explorer is intentionally a practical language tool rather than a large framework.

Core principles:

### Preserve the source

The original corpus remains untouched.

### Verify before building

Corpus statistics and integrity are checked before the database becomes an application dependency.

### Search locally

SQLite + FTS provides fast local exploration without requiring an external service.

### Keep the application lightweight

The Explorer works with the corpus database rather than requiring the entire language model to be loaded into memory.

### Create useful artifacts

The Romantic Card Studio turns interesting Assamese corpus records into visual cards.

### Experiment before expanding

The Assamese Explorer is an experimental language laboratory. New capabilities should be added only when they provide clear value.

---

# 12. Current Checkpoint

## JASS Assamese Explorer v1.1.1

**Status: WORKING / STABLE CHECKPOINT**

Completed:

- [x] Assamese corpus downloaded
- [x] Corpus inspected
- [x] 1,613,879 records verified
- [x] Duplicate check completed
- [x] SQLite database built
- [x] FTS index built
- [x] Database integrity verified
- [x] Source SHA-256 recorded
- [x] Explorer operational
- [x] Assamese search operational
- [x] Romantic Card Studio operational
- [x] Create Card workflow fixed
- [x] Source-line formatting fixed
- [x] PNG/JPEG card output operational

---

# 13. Recommended Next Step

Do **not** immediately add a large number of features.

The current working Explorer should first be treated as a stable checkpoint.

A sensible next phase is controlled experimentation:

1. compare Assamese and Mizo database/search behaviour
2. examine corpus vocabulary and sentence distributions
3. test useful search features
4. evaluate Assamese language-model possibilities
5. add only high-value capabilities to the Explorer

The application should remain proportional to the value of the corpus.

---

# 14. Project Direction

The long-term direction is:

```text
Assamese Corpus
       │
       ▼
Corpus Inspection
       │
       ▼
Verified SQLite + FTS
       │
       ▼
JASS Assamese Explorer
       │
       ├── Search
       ├── Browse
       ├── Inspect
       └── Romantic Card Studio
                    │
                    ▼
             Visual Language Artifacts
```

The Explorer therefore serves as both:

- a practical Assamese-language browsing tool
- a controlled experimental platform for future low-resource-language work

---

**JASS Assamese Explorer v1.1.1**

*Explore Assamese. Preserve the corpus. Build useful tools.*
