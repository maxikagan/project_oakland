# Plan: Entity Resolution - Advan POI to Politics at Work Linkage

## Overview

Link Advan POIs to Politics at Work (PAW) employers to enable analysis of employee-consumer partisan alignment. This is the critical data integration step that enables the core research questions.

**Goal**: Match as many POIs as possible to PAW employers while maintaining acceptable match quality.

**Challenge**: Advan data lacks standard company identifiers (no tickers, GVKEYs, EINs). Must rely on name matching.

---

## Data Sources

### Advan Side

| Source | Location | Format | Records | Key Fields |
|--------|----------|--------|---------|------------|
| **Monthly Patterns (Jan 2026 download)** | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/foot_traffic_monthly_complete_2026-01-12/monthly-patterns-foot-traffic/` | CSV.gz | 2,096 files, 804GB, 79 months (2019-01 to 2025-07) | `PLACEKEY`, `BRANDS`, `LOCATION_NAME`, `LATITUDE`, `LONGITUDE`, `POI_CBG`, `VISITOR_HOME_CBGS`, `OPENED_ON`, `CLOSED_ON`, `NAICS_CODE` |
| Brand Info | `/global/scratch/users/maxkagan/01_foot_traffic_location/advan/brand_info/Brand_Info_Places_Patterns_Geometry_Spend_-0.csv` | CSV | ~10K brands | `SAFEGRAPH_BRAND_ID`, `BRAND_NAME`, `STOCK_SYMBOL`, `NAICS_CODE` |
| Brand Summary (dashboard) | `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/dashboard_data/brand_summary.parquet` | Parquet | 8,763 brands | Aggregated brand stats |

**Key advantage of January 2026 data**: Monthly patterns include `POI_CBG` directly, enabling efficient CBSA assignment via county FIPS extraction (no spatial join required). Also includes `LATITUDE` and `LONGITUDE` for distance calculations if needed.

**POI Breakdown** (estimated, to be confirmed by Step 1):
- Branded POIs: ~1.4M (7%) - have `SAFEGRAPH_BRAND_IDS`
- Unbranded POIs: ~18.4M (93%) - only have `LOCATION_NAME`

### Politics at Work Side

| Source | Location | Records | Key Fields |
|--------|----------|---------|------------|
| **VR Scores with GVKeys** (PRIMARY) | `/global/scratch/users/maxkagan/04_vrscores/vr_scores_ensemble_additional_gvkeys.csv` | 535K company-years | `rcid`, `gvkey`, `ticker`, `company_name`, `modal_msa`, `democrat_pct_two_party_imp`, `republican_pct_two_party_imp` |
| Company Crosswalk | `/global/scratch/users/maxkagan/04_vrscores/revelio_20250416/company_crosswalk/company_crosswalk.parquet` | ~500K US companies | `rcid`, `company_name`, `ticker`, `naics_code`, `ultimate_parent_rcid` |
| MSA Position Files | `/global/scratch/users/maxkagan/04_vrscores/merge_splink_fuzzylink/step11_company_enriched/{msa}_positions.parquet` | Varies by MSA | `pos_company_name`, employee records |

**Key PAW fields for analysis**:
- `gvkey` - Compustat identifier (for public companies)
- `ticker` - Stock ticker
- `rcid` - Revelio company ID (universal)
- `final_parent_company_rcid` - Ultimate parent
- `modal_msa` - Company's primary MSA
- `employee_count` - Number of employees
- `democrat_pct_two_party_imp` - Employee Democrat share (imputed)
- `republican_pct_two_party_imp` - Employee Republican share (imputed)
- `political_diversity_imp` - Employee political diversity index

---

## Matching Strategy: Tiered Approach

### Tier 0a: Exact Ticker Match (Trivial)

**Scope**: Brands with stock symbols → PAW companies with tickers

**Method**: Exact string match on ticker symbol

**Expected yield**: ~100-500 major public companies (Walmart, McDonald's, Starbucks, etc.)

**Accuracy**: 100% (exact match)

**Cost**: Free

---

### Tier 0b: GVKey via Ticker (Public Companies)

**Scope**: Advan brands matched via ticker → get GVKey from PAW

**Method**:
1. Match Advan `STOCK_SYMBOL` to PAW `ticker`
2. Pull `gvkey` from PAW for Compustat linkage

**Note**: Advan Brand Info has `STOCK_SYMBOL` but not `gvkey` directly. PAW has both, so ticker match gives us GVKey.

**Expected yield**: Same as ticker match (~100-500 public companies)

**Accuracy**: 100% (exact match)

**Cost**: Free

---

### Tier 1: Brand Name Matching (National)

**Scope**: All ~8,763 unique Advan brands → PAW company names

**Method**:
1. Generate OpenAI embeddings for all brand names
2. Generate OpenAI embeddings for PAW company names (filtered to those with 50+ employees)
3. Compute cosine similarity
4. Manual review of top candidates for each brand
5. Threshold-based auto-accept for high-confidence matches

**Blocking**: None needed - only ~9K brands × ~50K companies = 450M comparisons (manageable with embeddings)

**Cost Estimate**:
- ~60K text items (brands + companies) × ~5 tokens/item = ~300K tokens
- OpenAI text-embedding-3-small: $0.02/1M tokens
- **Total: ~$0.01**

Even with text-embedding-3-large ($0.13/1M tokens): **~$0.04**

**Expected yield**: 2,000-5,000 brand-to-company matches

**Accuracy**: ~90-95% with manual review of edge cases

---

### Tier 2: Unbranded POI Matching (MSA-Blocked)

**Scope**: ~18.4M unbranded POIs → PAW employers within same MSA

**Method**:
1. For each MSA:
   - Extract unbranded POIs in that MSA (via city/region mapping to CBSA)
   - Extract PAW employers in that MSA (from MSA position files)
   - Generate embeddings for `LOCATION_NAME` and `pos_company_name`
   - Compute similarity within MSA pairs only
   - Apply confidence threshold

**Blocking**: Geographic (MSA) - critical for tractability

**Why MSA blocking works**:
- Reduces comparison space from 18.4M × 500K = 9.2 trillion to ~10K × ~5K = 50M per MSA
- Local businesses (dentists, restaurants, etc.) operate within MSA
- PAW data is already organized by MSA

**Cost Estimate**:
- ~18.4M POI names + ~500K company names = ~19M text items
- ~5 tokens/item = ~95M tokens
- text-embedding-3-small: **~$2**
- text-embedding-3-large: **~$12**

**Expected yield**: Highly variable - depends on:
- How many unbranded POIs are matchable businesses (vs. landmarks, parks, etc.)
- Name similarity between Advan `LOCATION_NAME` and PAW `pos_company_name`

**Accuracy**: Lower than Tier 1 - expect 70-80% precision, will need robustness checks

---

### Tier 3: Fallback - String Distance (No API)

**Scope**: Any remaining unmatched POIs

**Method**:
- Jaccard similarity on tokenized names
- Levenshtein distance
- LinkOrgs package (uses LinkedIn network data)

**Cost**: Free

**Expected yield**: Marginal additional matches

**Use case**: Robustness check, not primary method

---

## Pipeline Steps

### Step 1: Extract Unique Entities

**Script**: `/global/home/users/maxkagan/project_oakland/scripts/entity_resolution/01_extract_unique_entities.py`

**Outputs**:
- `advan_brands_unique.parquet` - unique brands with stock symbols
- `paw_companies_with_ticker.parquet` - PAW companies with tickers
- `paw_companies_unique.parquet` - all unique PAW company names
- MSA company counts (diagnostic)

**Status**: Script exists, needs to be run

---

### Step 2: Tier 0 - Exact Ticker Match

**Input**:
- `advan_brands_unique.parquet` (brands with `stock_symbol`)
- `paw_companies_with_ticker.parquet`

**Method**: Exact join on ticker

**Output**: `tier0_ticker_matches.parquet`

| Column | Description |
|--------|-------------|
| `safegraph_brand_id` | Advan brand identifier |
| `brand_name` | Advan brand name |
| `ticker` | Stock symbol |
| `rcid` | PAW company ID |
| `company_name` | PAW company name |
| `match_tier` | "ticker_exact" |
| `confidence` | 1.0 |

---

### Step 3: Tier 1 - Brand Embedding Match

**Input**:
- `advan_brands_unique.parquet` (all brands)
- `paw_companies_unique.parquet` (filtered to 50+ employees)

**Method**:
1. Call OpenAI API to embed all brand names
2. Call OpenAI API to embed all PAW company names
3. Compute pairwise cosine similarity
4. For each brand, rank PAW companies by similarity
5. Auto-accept matches with similarity > 0.95
6. Manual review for 0.80 < similarity < 0.95
7. Reject similarity < 0.80

**Output**: `tier1_brand_matches.parquet`

| Column | Description |
|--------|-------------|
| `safegraph_brand_id` | Advan brand identifier |
| `brand_name` | Advan brand name |
| `rcid` | PAW company ID |
| `company_name` | PAW company name |
| `cosine_similarity` | Embedding similarity score |
| `match_tier` | "brand_embedding" |
| `confidence` | Based on similarity score |
| `manual_review` | Boolean - needs human check |

---

### Step 4: Tier 2 - Unbranded POI Matching (MSA-Blocked)

**Input**:
- `advan_pois_us_only.parquet` (unbranded POIs only) - has `POI_CBG` for CBSA assignment
- PAW company × MSA table (to be created - see Step 3b below)
- NBER CBSA-to-FIPS crosswalk for POI → MSA mapping (via county FIPS extraction from POI_CBG)

#### Step 3b (Prerequisite): Create PAW Company × MSA Table

**Why**: Revelio `rcid` links the same company across MSAs. We need a lookup of which companies operate in which MSAs.

**Input**: MSA position files from `/global/scratch/users/maxkagan/04_vrscores/merge_splink_fuzzylink/step11_company_enriched/{msa}_positions.parquet`

**Method**:
```python
# For each MSA position file:
#   Extract unique (rcid, company_name) pairs
#   Tag with MSA
# Combine into single table

paw_company_msa = []
for msa_file in msa_position_files:
    msa_name = extract_msa_from_filename(msa_file)
    df = read_parquet(msa_file)
    companies = df[['rcid', 'pos_company_name']].drop_duplicates()
    companies['msa'] = msa_name
    paw_company_msa.append(companies)

paw_company_msa = concat(paw_company_msa)
# Result: (rcid, company_name, msa) with one row per company-MSA combination
```

**Output**: `paw_company_by_msa.parquet`

| Column | Description |
|--------|-------------|
| `rcid` | Revelio company ID |
| `company_name` | Company name (may vary slightly across MSAs) |
| `msa` | MSA where company has employees |
| `employee_count_msa` | (Optional) Employee count in this MSA |

#### Step 3c (Prerequisite): Map Advan POIs to CBSA via POI_CBG

**Why**: Advan data includes `POI_CBG` (Census Block Group). First 5 digits = county FIPS, which maps to CBSA.

**Crosswalk already exists**: `/global/scratch/users/maxkagan/measuring_stakeholder_ideology/inputs/cbsa_crosswalk.parquet`
- Created by `scripts/00_setup_cbsa_crosswalk.py`
- Source: NBER CBSA-to-FIPS crosswalk (from Census Bureau)
- Key columns: `county_fips_full` (5-digit), `cbsa_code`, `cbsa_title`, `metro_micro`

**Method**:
```python
# Load existing crosswalk
cbsa_xw = pd.read_parquet('/global/scratch/users/maxkagan/measuring_stakeholder_ideology/inputs/cbsa_crosswalk.parquet')

# Extract county FIPS from POI_CBG (first 5 digits)
pois['county_fips_full'] = pois['POI_CBG'].str[:5]

# Join to get CBSA
pois_with_cbsa = pois.merge(cbsa_xw[['county_fips_full', 'cbsa_code', 'cbsa_title']],
                             on='county_fips_full', how='left')
```

**Note on rural POIs**: POIs in counties not part of a CBSA will have null `cbsa_code`. These are typically rural areas - handle separately or skip for MSA-blocked matching.

---

#### Handling Multi-MSA Presence

**Key insight**: The MSA position files naturally handle multi-MSA companies.

- A regional company (e.g., "Joe's Pizza" with 20 locations across 3 MSAs) will appear in all 3 MSA position files
- When we process MSA X, we match POIs in MSA X to all companies with employees in MSA X
- The same company gets matched in each MSA where it operates

**Advan side**:
- POI has `CITY` and `REGION` → map to CBSA/MSA
- Each POI belongs to exactly one MSA (based on physical location)

**PAW side**:
- MSA position file contains all companies with at least one employee in that MSA
- Same company appears in multiple MSA files if it has multi-MSA presence
- This is the "ground truth" for where the company actually operates

**Matching logic** (per MSA):
```
For MSA X:
  POIs_X = all unbranded POIs located in MSA X
  Companies_X = all companies from {msa_x}_positions.parquet

  Match POIs_X.LOCATION_NAME to Companies_X.pos_company_name
```

**Why this works**:
- If "Joe's Pizza" has employees in Columbus, Cincinnati, and Cleveland MSAs
- It appears in all three MSA position files
- A "Joe's Pizza" POI in Columbus will be matched against companies in Columbus (including Joe's Pizza)
- No need to pre-compute company MSA footprints - the position files already encode this

**Edge cases**:

1. **National brands appearing as unbranded**:
   - Some POIs lack brand IDs but are actually national brands (data quality issue)
   - These will be matched via Tier 2, which is fine - just less efficient than Tier 1
   - After Tier 1: propagate brand → rcid mapping to catch these in Tier 2

2. **POIs outside MSAs (rural areas)**:
   - ~15-20% of US population lives outside MSAs
   - These POIs won't have MSA blocking available
   - Options: (a) match against statewide company list, (b) skip rural POIs, (c) use micropolitan areas
   - **Recommendation**: Start with MSA-only, assess rural POI count, decide later

3. **Same company, different names across MSAs**:
   - PAW position files may have slight name variations for same company
   - "McDonald's" vs "McDonalds" vs "McDonald's Corporation"
   - Mitigated by: (a) embeddings handle synonyms, (b) post-hoc deduplication via `rcid`

4. **Franchises vs corporate**:
   - A McDonald's franchise may appear as separate employer in PAW
   - Advan sees it as "McDonald's" brand
   - For Tier 1 (brands): match to parent company
   - For Tier 2 (unbranded franchises): match to local franchise entity
   - May want both: brand-level and location-level employee data

**Method**:
For each MSA (parallelized as array job):
1. Filter POIs to MSA (via city/region → CBSA mapping)
2. Load PAW employers for that MSA from position file
3. Embed `LOCATION_NAME` values
4. Embed `pos_company_name` values
5. Compute within-MSA similarity matrix
6. Apply threshold (0.85 recommended)
7. Output matches for MSA

**Output**: `tier2_unbranded_matches/` (partitioned by MSA)

| Column | Description |
|--------|-------------|
| `placekey` | POI identifier |
| `location_name` | Advan location name |
| `city` | POI city |
| `msa` | MSA identifier |
| `rcid` | PAW company ID |
| `company_name` | PAW company name |
| `cosine_similarity` | Embedding similarity score |
| `match_tier` | "unbranded_msa_embedding" |
| `confidence` | Based on similarity score |

---

### Step 5: Combine and Validate

**Method**:
1. Combine all tiers into master crosswalk
2. Propagate brand matches to all POIs with that brand
3. Check for conflicts (same POI matched via different tiers)
4. Generate match rate statistics

**Output**: `advan_paw_crosswalk.parquet`

| Column | Description |
|--------|-------------|
| `placekey` | POI identifier |
| `safegraph_brand_id` | Brand ID (if branded) |
| `rcid` | PAW company ID |
| `ultimate_parent_rcid` | Parent company ID |
| `match_tier` | Which tier produced match |
| `confidence` | Match confidence |

---

### Step 6: Merge with Partisan Lean Data

**Method**:
1. Join `advan_paw_crosswalk.parquet` to partisan lean data via `placekey`
2. Aggregate employee ideology from PAW at `rcid` level
3. Compute employee-consumer alignment metrics

**Output**: Analysis-ready dataset with both consumer and employee partisan lean

---

## Cost Summary

| Tier | Method | Estimated Cost |
|------|--------|----------------|
| Tier 0 | Exact ticker match | $0 |
| Tier 1 | Brand embeddings (~60K items) | $0.01 - $0.04 |
| Tier 2 | Unbranded embeddings (~19M items) | $2 - $12 |
| **Total** | | **$2 - $15** |

**Note**: The $500-2000 estimate in the research agenda was incorrect. Actual cost is ~100x lower.

---

## Compute Resources

| Step | Partition | Rationale |
|------|-----------|-----------|
| Step 1: Extract entities | savio3 | Moderate memory for parquet scans |
| Step 2: Ticker match | savio2 | Trivial join |
| Step 3: Brand embeddings | savio2 | API calls, not compute-intensive |
| Step 4: Unbranded (per MSA) | savio3 array | Parallel by MSA |
| Step 5: Combine | savio3_bigmem | Large join |
| Step 6: Final merge | savio3 | Standard joins |

---

## Success Criteria

1. **Tier 0**: 100% of ticker-matched brands linked
2. **Tier 1**: >80% of branded POIs linked to PAW
3. **Tier 2**: >30% of unbranded POIs linked (acceptable given noise)
4. **Overall**: >50% of all POIs have PAW match
5. **Validation**: Manual audit of 100 random matches shows >90% accuracy

---

## Open Questions

1. **CBSA mapping**: ✅ RESOLVED - Use `POI_CBG` field
   - Extract county FIPS (first 5 digits of POI_CBG)
   - Join to Census county → CBSA crosswalk
   - Simpler than spatial join, equally accurate

2. **Parent company rollup**: Should we match to `rcid` or `ultimate_parent_rcid`?
   - For employee ideology: probably ultimate parent (aggregates all subsidiaries)
   - For brand identity: probably direct rcid
   - **Recommendation**: Keep both, analyze sensitivity

3. **Threshold tuning**: What cosine similarity threshold balances precision/recall?
   - Start with 0.85, evaluate on manual audit sample
   - May need different thresholds for Tier 1 vs Tier 2

---

## Next Steps

1. [ ] Run Step 1 to extract unique entities and get counts
2. [ ] Implement Tier 0 ticker matching
3. [ ] Set up OpenAI API for embedding generation
4. [ ] Run Tier 1 brand matching, manual review
5. [ ] Build MSA blocking infrastructure for Tier 2
6. [ ] Run Tier 2 on pilot MSA (e.g., Columbus OH)
7. [ ] Scale Tier 2 to all MSAs
8. [ ] Combine and validate

---

*Created: 2026-01-17*
*Author: Max Kagan (with Claude Code assistance)*
