# ADR 0003 — SEC EDGAR HTML index parsing + X0202 unit normalization

- **Status:** Accepted
- **Date:** 2026-05-23
- **Supersedes:** none

## Context

The 13F + Form 4 ingestion paths broke on the same day for three
coupled reasons that were not documented anywhere when the code was
first written:

1. **JSON filing index gone.** SEC stopped serving
   `{accession}-index.json` for recent filings — requests now return
   S3's `NoSuchKey` XML error. The codebase's `_find_infotable_url`
   (13F) and `_fetch_form4_xml` (Form 4) both relied on it.
2. **X0202 schema unit change.** The new 13F schema version `X0202`
   (in use since Q3 2023) reports `<value>` in **raw dollars**, not
   the historical thousands-of-dollars. Berkshire's AUM rendered as
   `$263T` instead of `$263B` because the parser stored raw dollars
   into a field downstream code assumed was thousands.
3. **EFTS field rename.** The EDGAR full-text search index changed
   response field names: `accession_no` → `adsh`, `entity_id` →
   `ciks` (now a list, with insider CIK at `[0]` and issuer at `[1]`).
   The Form 4 ingestion service silently inserted zero trades
   because every filing failed the empty-string check.

## Decision

Three changes, all under `app/edgar/` and `app/insiders/`:

1. **Locate filing documents via the HTML index, not JSON.** Fetch
   `{accession}-index.html`, regex-parse the document table, match
   on the **Type** column (`"INFORMATION TABLE"` for 13F infotable,
   `"4"` / `"4/A"` for Form 4 XML). Filename fallbacks (`form4.xml`,
   etc.) remain as a second-tier defence.
2. **Normalize X0202 values at parse time.** In `app/edgar/parser.py`,
   integer-divide `<value>` by 1000 before storing it as
   `value_thousands`. Downstream code keeps its existing
   "thousands of dollars" contract. The comment in the parser
   explicitly names X0202 so future readers don't strip the divide.
3. **Map EFTS new field names.** In
   `app/insiders/ingestion_service.py::_search_form4_filings`, read
   `adsh` and `ciks[0]` (stripped of leading zeros). The CIK used
   for the archive path is the **insider's** CIK, not the issuer's.

## Consequences

**Positive**
- Both 13F and Form 4 pipelines work against current SEC infrastructure.
- Smoke-tested end-to-end on Berkshire (Q1 2026, $263B AUM, 90 holdings)
  and AAPL (26 Form 4 trades ingested, scored as NEUTRAL).

**Negative**
- We are now coupled to SEC's HTML layout, which is less stable
  than a documented JSON schema would be. A future EDGAR redesign
  will require another fix here.
- The `// 1000` divide is silent — pre-X02 (pre-2023) filings, if
  we ever fetch one, would be misinterpreted by a factor of 1000.
  In practice the registry only goes back two quarters per investor
  so this is moot, but it's a sharp edge to be aware of.

## Alternatives considered

- **Use `edgartools` (PyPI package).** The original CLAUDE.md
  suggested this but it isn't installed and pulling it in would
  re-introduce a wrapper layer we'd then have to debug. Direct
  httpx + regex is small enough to own.
- **Detect the X0202 schema from `primary_doc.xml` and conditionally
  divide.** More correct, but every recent filing we'd ever fetch
  is X0202, so the conditional is dead weight today. A revisit
  trigger (below) captures the case where it matters.
- **EDGAR's XBRL frames API.** Doesn't cover 13F infotables — only
  exists for company financials.

## Revisit trigger

- If we ever fetch pre-Q3-2023 filings, detect schema version from
  `primary_doc.xml` (`<schemaVersion>`) before applying the `/ 1000`
  normalisation.
- If SEC restores a stable JSON filing index, swap back — it would be
  less brittle than HTML scraping.

## Related code

- `app/edgar/client.py::_find_infotable_url`
- `app/edgar/parser.py::parse_infotable`
- `app/insiders/ingestion_service.py::_search_form4_filings`
- `app/insiders/ingestion_service.py::_fetch_form4_xml`

## Related commits

- `8d8d10d fix(edgar): use HTML index to locate 13F infotable XML`
- `7024bd2 fix(edgar): normalize X0202 values from raw dollars to thousands`
- `e0efc96 fix(insiders): adapt to EFTS field rename and Form 4 XML discovery`
