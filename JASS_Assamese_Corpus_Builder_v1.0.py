#!/usr/bin/env python3
import csv, hashlib, sqlite3, time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SOURCE = BASE_DIR / 'assamese_monolingual_sentences_final_cleaned.csv'
DATABASE = BASE_DIR / 'JASS_Assamese_Corpus.db'
REPORT = BASE_DIR / 'assamese_build_report.txt'
EXPECTED_RECORDS = 1_613_879
BATCH_SIZE = 10_000

def sha256_file(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()

def main():
    print('JASS ASSAMESE CORPUS BUILDER v1.0')
    print('='*40)
    if not SOURCE.exists():
        print(f'ERROR: Source file not found:\n{SOURCE}'); return 1
    size=SOURCE.stat().st_size; mtime=SOURCE.stat().st_mtime_ns
    print(f'Source: {SOURCE}\nSize: {size/(1024*1024):,.2f} MB\nMode: READ-ONLY\n')
    if DATABASE.exists(): DATABASE.unlink()
    print('Calculating source SHA-256...')
    started=time.time(); source_hash=sha256_file(SOURCE)
    print(f'SHA-256: {source_hash}\nHash time: {time.time()-started:.1f} seconds\n')
    print('Creating SQLite database...')
    conn=sqlite3.connect(DATABASE)
    conn.execute('PRAGMA journal_mode=WAL'); conn.execute('PRAGMA synchronous=NORMAL'); conn.execute('PRAGMA temp_store=MEMORY')
    conn.executescript('''CREATE TABLE records(id INTEGER PRIMARY KEY, source_line INTEGER NOT NULL UNIQUE, text TEXT NOT NULL);
CREATE VIRTUAL TABLE assamese_fts USING fts5(text, content='records', content_rowid='id');
CREATE TRIGGER records_ai AFTER INSERT ON records BEGIN INSERT INTO assamese_fts(rowid,text) VALUES(new.id,new.text); END;''')
    insert='INSERT INTO records(id,source_line,text) VALUES(?,?,?)'
    batch=[]; count=0; blanks=0; build_start=time.time()
    print('Scanning and building database...')
    try:
        with SOURCE.open('r',encoding='utf-8-sig',newline='') as f:
            reader=csv.DictReader(f)
            if not reader.fieldnames or 'text' not in reader.fieldnames: raise ValueError(f'CSV must contain a text column. Found: {reader.fieldnames}')
            for source_line,row in enumerate(reader,start=2):
                text=(row.get('text') or '').strip()
                if not text: blanks+=1; continue
                count+=1; batch.append((count,source_line,text))
                if len(batch)>=BATCH_SIZE:
                    conn.executemany(insert,batch); conn.commit(); batch.clear()
                    if count%100000==0: print(f'  {count:,} records...')
            if batch: conn.executemany(insert,batch); conn.commit()
    except Exception:
        conn.close();
        if DATABASE.exists(): DATABASE.unlink()
        raise
    print('Finalizing FTS index...')
    conn.execute("INSERT INTO assamese_fts(assamese_fts) VALUES ('optimize')"); conn.commit()
    db_count=conn.execute('SELECT COUNT(*) FROM records').fetchone()[0]
    fts_count=conn.execute('SELECT COUNT(*) FROM assamese_fts').fetchone()[0]
    min_line,max_line=conn.execute('SELECT MIN(source_line),MAX(source_line) FROM records').fetchone()
    integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
    fts_test=conn.execute("SELECT COUNT(*) FROM assamese_fts WHERE assamese_fts MATCH ?",('আৰু',)).fetchone()[0]
    conn.close()
    modified=mtime != SOURCE.stat().st_mtime_ns
    passed=(db_count==EXPECTED_RECORDS and fts_count==EXPECTED_RECORDS and min_line==2 and integrity=='ok' and not modified)
    db_size=DATABASE.stat().st_size
    report=f'''JASS ASSAMESE CORPUS BUILD COMPLETE\n========================================\n\nSOURCE\nFile: {SOURCE}\nSize: {size/(1024*1024):,.2f} MB\nMode: READ-ONLY\n\nDATABASE\nFile: {DATABASE}\nSize: {db_size/(1024*1024):,.2f} MB\n\nRECORDS\nExpected records: {EXPECTED_RECORDS:,}\nDatabase records: {db_count:,}\nFTS records: {fts_count:,}\nBlank records skipped: {blanks:,}\n\nSOURCE LINE RANGE\nFirst source line: {min_line}\nLast source line: {max_line}\n\nSOURCE SHA-256\n{source_hash}\n\nVERIFICATION\nRecord count: {'PASSED' if db_count==EXPECTED_RECORDS else 'FAILED'}\nFTS count: {'PASSED' if fts_count==EXPECTED_RECORDS else 'FAILED'}\nSource integrity: {'PASSED' if not modified else 'FAILED'}\nSQLite integrity: {'PASSED' if integrity=='ok' else 'FAILED'}\nFTS search test (word: আৰু): {fts_test:,} matches\nOverall verification: {'PASSED' if passed else 'FAILED'}\n\nBUILD TIME\n{time.time()-build_start:.1f} seconds\n\nSource modification: {'NONE' if not modified else 'DETECTED'}\n'''
    REPORT.write_text(report,encoding='utf-8'); print('\n'+report); print(f'Report written to: {REPORT}')
    return 0 if passed else 2

if __name__=='__main__':
    try: raise SystemExit(main())
    except KeyboardInterrupt: print('\nBuild cancelled by user.'); raise SystemExit(130)
    except Exception as e: print(f'\nERROR: {e}'); raise SystemExit(1)
