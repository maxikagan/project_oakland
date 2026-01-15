# Methodological Appendix: Constructing Visitor Partisan Lean from Foot Traffic Data

## Overview

This appendix describes the complete methodology for constructing measures of visitor partisan lean for points of interest (POIs) across the United States. The methodology links anonymized mobile phone location data to Census Block Group (CBG)-level presidential election results to estimate the political composition of visitors to retail establishments, restaurants, and other commercial locations.

The final output is a panel dataset at the POI-month level containing weighted average Republican vote share of visitors, computed using both 2016 and 2020 presidential election results.

---

## 1. Data Sources

### 1.1 Foot Traffic Data: Advan Monthly Patterns

**Source:** Advan (formerly SafeGraph) Monthly Patterns
**Coverage:** January 2019 through July 2025 (79 months)
**Geographic scope:** All 50 U.S. states plus the District of Columbia
**File format:** Compressed CSV files (`.csv.gz`)
**Total size:** Approximately 804 GB across 2,096 files

The Advan Monthly Patterns dataset provides aggregated foot traffic statistics for approximately 6 million POIs in the United States. For each POI-month observation, the dataset includes:

| Field | Description |
|-------|-------------|
| `PLACEKEY` | Unique identifier for each POI using the Placekey standard |
| `DATE_RANGE_START` | First day of the month (YYYY-MM-DD format) |
| `BRANDS` | Brand name if the POI is part of a chain (e.g., "Walmart", "Starbucks") |
| `TOP_CATEGORY` | High-level business category (e.g., "Restaurants and Other Eating Places") |
| `SUB_CATEGORY` | Detailed business category (e.g., "Full-Service Restaurants") |
| `NAICS_CODE` | 6-digit North American Industry Classification System code |
| `CITY` | City where the POI is located |
| `REGION` | Two-letter U.S. state abbreviation |
| `POI_CBG` | 12-digit Census Block Group FIPS code where the POI is located |
| `PARENT_PLACEKEY` | Parent location identifier (for POIs within larger complexes) |
| `MEDIAN_DWELL` | Median dwell time in minutes for visitors |
| `VISITOR_HOME_CBGS` | JSON object mapping visitor home CBGs to visitor counts |
| `RAW_VISITOR_COUNTS` | Total raw visitor count for the month |

The critical field for our methodology is `VISITOR_HOME_CBGS`, which contains a JSON-encoded dictionary where keys are 12-digit CBG FIPS codes and values are integer visitor counts. For example:

```json
{"060371234001": 45, "060371234002": 23, "060371235001": 12}
```

This indicates that 45 visitors came from CBG 060371234001, 23 from CBG 060371234002, and 12 from CBG 060371235001.

**Privacy protections:** Advan applies differential privacy techniques to protect individual privacy. CBGs with fewer than 4 visitors are suppressed, and visitor counts are subject to noise injection. These protections may introduce measurement error but do not systematically bias partisan lean estimates.

### 1.2 Election Data: CBG-Level Presidential Vote Estimates

**Source:** Election results geocoded to Census Block Groups using the "Main Method" approach with RLCR (Registered Voter List with Candidate Records) methodology
**Files:** `bg-2016-RLCR.csv` and `bg-2020-RLCR.csv`
**Location:** Contained within `000 Contiguous USA - Main Method.zip`
**Coverage:** All Census Block Groups in the contiguous United States

The election data provides estimated vote counts at the Census Block Group level for the 2016 and 2020 presidential elections:

**2020 Election Fields:**
| Field | Description |
|-------|-------------|
| `bg_GEOID` | 12-digit Census Block Group FIPS code |
| `G20PRERTRU` | Estimated votes for Donald Trump (Republican) |
| `G20PREDBID` | Estimated votes for Joseph Biden (Democrat) |

**2016 Election Fields:**
| Field | Description |
|-------|-------------|
| `bg_GEOID` | 12-digit Census Block Group FIPS code |
| `G16PRERTRU` | Estimated votes for Donald Trump (Republican) |
| `G16PREDCLI` | Estimated votes for Hillary Clinton (Democrat) |

**Methodology note:** The RLCR method estimates block group-level vote shares by combining precinct-level official election returns with voter file data that includes geocoded addresses and modeled partisanship. This produces more granular estimates than precinct-level data alone, though estimates are subject to modeling uncertainty.

### 1.3 Metropolitan Statistical Area Crosswalk

**Source:** National Bureau of Economic Research (NBER) CBSA-to-FIPS County Crosswalk
**Original data:** U.S. Census Bureau Core Based Statistical Area (CBSA) Delineation File
**Version:** 2023 delineations
**URL:** `https://data.nber.org/cbsa-csa-fips-county-crosswalk/2023/cbsa2fipsxw_2023.csv`

This crosswalk maps 5-digit county FIPS codes to CBSA codes and titles (Metropolitan Statistical Area names). We use this to assign each POI to its MSA based on the county portion of the POI's CBG code. The NBER provides a cleaned CSV version of the Census Bureau's original Excel delineation file, facilitating programmatic access.

---

## 2. Data Processing Pipeline

### 2.1 Step 0: Construct CBSA Crosswalk

**Purpose:** Create a lookup table mapping county FIPS codes to Metropolitan Statistical Area names.

**Process:**
1. Download the NBER CBSA-to-FIPS crosswalk CSV file (derived from Census Bureau delineations)
2. Extract relevant columns: `cbsacode`, `cbsatitle`, `fipsstatecode`, `fipscountycode`, `metropolitanmicropolitanstatis`
3. Construct 5-digit county FIPS code by concatenating:
   - 2-digit state FIPS (zero-padded)
   - 3-digit county FIPS (zero-padded)
4. Create mapping: `county_fips_full` → `cbsa_title`

**Output schema:**
| Column | Type | Description |
|--------|------|-------------|
| `cbsa_code` | string | CBSA identifier code |
| `cbsa_title` | string | Full MSA name (e.g., "San Francisco-Oakland-Berkeley, CA") |
| `state_fips` | string | 2-digit state FIPS code |
| `county_fips` | string | 3-digit county FIPS code |
| `metro_micro` | string | Classification ("Metropolitan Statistical Area" or "Micropolitan Statistical Area") |
| `county_fips_full` | string | 5-digit combined county FIPS code |

**Output file:** `cbsa_crosswalk.parquet`
**Records:** 1,915 county-to-CBSA mappings covering 935 unique CBSAs

### 2.2 Steps 1-2: Construct National CBG Partisan Lean Lookup

**Purpose:** Create a national lookup table containing Republican two-party vote share for each Census Block Group using both 2016 and 2020 election data.

**Process:**

#### 2.2.1 Load and Process 2020 Election Data

1. Extract `bg-2020-RLCR.csv` from the national zip file
2. Select columns: `bg_GEOID`, `G20PRERTRU`, `G20PREDBID`
3. Rename columns to: `GEOID`, `Trump_2020`, `Biden_2020`
4. **CRITICAL:** Zero-pad GEOID to 12 digits: `GEOID = str(GEOID).zfill(12)`
5. Convert vote counts to numeric, replacing non-numeric values with 0
6. Compute two-party Republican vote share:

$$\text{two\_party\_rep\_share\_2020} = \frac{\text{Trump\_2020}}{\text{Trump\_2020} + \text{Biden\_2020}}$$

7. **Edge case handling:** For CBGs where `Trump_2020 + Biden_2020 = 0` (zero total votes), set `two_party_rep_share_2020 = 0.5` (neutral)

#### 2.2.2 Load and Process 2016 Election Data

1. Extract `bg-2016-RLCR.csv` from the national zip file
2. Select columns: `bg_GEOID`, `G16PRERTRU`, `G16PREDCLI`
3. Rename columns to: `GEOID`, `Trump_2016`, `Clinton_2016`
4. **CRITICAL:** Zero-pad GEOID to 12 digits: `GEOID = str(GEOID).zfill(12)`
5. Convert vote counts to numeric, replacing non-numeric values with 0
6. Compute two-party Republican vote share:

$$\text{two\_party\_rep\_share\_2016} = \frac{\text{Trump\_2016}}{\text{Trump\_2016} + \text{Clinton\_2016}}$$

7. **Edge case handling:** For CBGs where `Trump_2016 + Clinton_2016 = 0`, set `two_party_rep_share_2016 = 0.5`

#### 2.2.3 Merge 2016 and 2020 Data

1. Perform outer join on `GEOID` to retain all CBGs from both years
2. Fill missing values with 0.5 (neutral) for CBGs that appear in only one year
3. This accounts for CBG boundary changes between decennial censuses

**Output schema:**
| Column | Type | Description |
|--------|------|-------------|
| `GEOID` | string | 12-digit Census Block Group FIPS code |
| `two_party_rep_share_2020` | float | Republican share of two-party vote (2020), range [0, 1] |
| `two_party_rep_share_2016` | float | Republican share of two-party vote (2016), range [0, 1] |

**Output file:** `cbg_partisan_lean_national_both_years.parquet`

**Validation statistics logged:**
- Number of CBGs in each year
- Range and mean of Republican vote share
- Correlation between 2016 and 2020 measures
- Mean shift (2020 minus 2016)

### 2.3 Step 3: Compute Visitor Partisan Lean (Single-Pass Processing)

**Purpose:** For each POI-month observation, compute the weighted average Republican vote share of visitors based on their home CBGs. This step combines data filtering and partisan lean computation in a single pass through the source files.

**Architecture:** The raw Advan data consists of 2,096 compressed CSV files. Rather than filtering by state first (which would require reading each file 51 times), we process each file exactly once, computing partisan lean for all POIs in that file regardless of state.

**Process (executed as parallel array job with 2,096 tasks, one per source file):**

#### 2.3.1 Load Lookup Data

At the start of each task, load lookup tables into memory:
- **CBG partisan lean lookup** (~24 MB): Python dictionaries for O(1) lookup
  - `CBG_DICT_2020`: Maps GEOID → `two_party_rep_share_2020`
  - `CBG_DICT_2016`: Maps GEOID → `two_party_rep_share_2016`
- **CBSA crosswalk** (~1 MB): Maps county FIPS → MSA name

#### 2.3.2 Read and Process Single Source File

For each array task:

1. **Identify input file:** Map task index to filename via pre-generated sorted file list
2. **Read with column selection:** Load only required columns to minimize memory:
   - `PLACEKEY`, `DATE_RANGE_START`, `BRANDS`, `TOP_CATEGORY`, `SUB_CATEGORY`
   - `NAICS_CODE`, `CITY`, `REGION`, `POI_CBG`, `PARENT_PLACEKEY`
   - `MEDIAN_DWELL`, `VISITOR_HOME_CBGS`, `RAW_VISITOR_COUNTS`
3. **Rename columns:** Convert uppercase to lowercase (e.g., `PLACEKEY` → `placekey`, `BRANDS` → `brand`)
4. **Add CBSA information:**
   - Zero-pad `poi_cbg` to 12 digits
   - Extract county FIPS: `county_fips = poi_cbg[:5]`
   - Map to CBSA title using crosswalk
5. **Compute partisan lean** for each row (see Section 2.3.3)
6. **Filter output:** Exclude rows with zero total visitors
7. **Save output:** Write to Parquet with Snappy compression

**Column rename mapping:**
| Original | Renamed |
|----------|---------|
| `PLACEKEY` | `placekey` |
| `DATE_RANGE_START` | `date_range_start` |
| `BRANDS` | `brand` |
| `TOP_CATEGORY` | `top_category` |
| `SUB_CATEGORY` | `sub_category` |
| `NAICS_CODE` | `naics_code` |
| `CITY` | `city` |
| `REGION` | `region` |
| `POI_CBG` | `poi_cbg` |
| `PARENT_PLACEKEY` | `parent_placekey` |
| `MEDIAN_DWELL` | `median_dwell` |
| `VISITOR_HOME_CBGS` | `visitor_home_cbgs` |
| `RAW_VISITOR_COUNTS` | `raw_visitor_counts` |

**Output file:** One parquet file per source file, preserving original filename with `.parquet` extension

#### 2.3.3 Partisan Lean Computation

For each POI-month row:

1. **Parse visitor CBGs:** Parse the `visitor_home_cbgs` JSON string into a dictionary
   - Handle null/missing values by returning empty dictionary
   - Handle pre-parsed dictionaries (pass through)
   - Handle JSON decode errors by returning empty dictionary

2. **Iterate over visitor CBGs:** For each `(cbg_geoid, visitor_count)` pair:
   - Convert `visitor_count` to integer (skip if conversion fails)
   - Zero-pad `cbg_geoid` to 12 digits: `str(cbg_geoid).zfill(12)`
   - Accumulate `total_visitors`
   - If CBG exists in lookup:
     - Retrieve `rep_share_2020` from `CBG_DICT_2020`
     - Retrieve `rep_share_2016` from `CBG_DICT_2016` (default to 0.5 if missing)
     - Accumulate: `weighted_rep_2020 += rep_share_2020 × visitor_count`
     - Accumulate: `weighted_rep_2016 += rep_share_2016 × visitor_count`
     - Accumulate `matched_visitors`

3. **Compute weighted averages:**

$$\text{rep\_lean\_2020} = \frac{\sum_{c \in C} (\text{rep\_share}_{c,2020} \times \text{visitors}_c)}{\sum_{c \in C} \text{visitors}_c}$$

$$\text{rep\_lean\_2016} = \frac{\sum_{c \in C} (\text{rep\_share}_{c,2016} \times \text{visitors}_c)}{\sum_{c \in C} \text{visitors}_c}$$

Where $C$ is the set of matched CBGs (those found in the election data lookup).

4. **Handle edge cases:**
   - If `total_visitors = 0`: Set `rep_lean_2020 = NaN`, `rep_lean_2016 = NaN`
   - If `matched_visitors = 0` (no CBGs matched): Set both measures to `NaN`
   - Observations with `total_visitors = 0` are excluded from output

5. **Compute match rate:**

$$\text{pct\_visitors\_matched} = \frac{\text{matched\_visitors}}{\text{total\_visitors}} \times 100$$

#### 2.4.3 Output Schema

| Column | Type | Description |
|--------|------|-------------|
| `placekey` | string | Unique POI identifier |
| `date_range_start` | date | First day of the month |
| `brand` | string | Brand name (null for non-chain POIs) |
| `top_category` | string | High-level business category |
| `sub_category` | string | Detailed business category |
| `naics_code` | string | 6-digit NAICS code |
| `city` | string | City name |
| `region` | string | Two-letter state code |
| `poi_cbg` | string | 12-digit CBG FIPS code of POI location |
| `cbsa_title` | string | Metropolitan Statistical Area name |
| `parent_placekey` | string | Parent location identifier |
| `median_dwell` | float | Median visitor dwell time (minutes) |
| `rep_lean_2020` | float | Weighted Republican vote share (2020 election), range [0, 1] |
| `rep_lean_2016` | float | Weighted Republican vote share (2016 election), range [0, 1] |
| `total_visitors` | integer | Total visitor count from all CBGs |
| `matched_visitors` | integer | Visitor count from CBGs with election data |
| `pct_visitors_matched` | float | Percentage of visitors successfully matched |

**Output file:** `{STATE}.parquet` (one per state)

### 2.5 Step 5: Combine States and Partition by Month

**Purpose:** Combine all state-level outputs into a single national dataset, then partition by month for efficient downstream analysis.

**Process:**

1. **Identify unique months:** Scan all state files to identify all unique year-month values (e.g., "2019-01", "2019-02", ..., "2025-07")
2. **Memory-efficient processing:** For each month:
   - Read each state file
   - Filter to rows matching the target month
   - Concatenate month-specific chunks from all states
   - Write to month-specific Parquet file
   - Release memory before processing next month
3. **Compute summary statistics:** Track running sums of `rep_lean_2020` and `rep_lean_2016` across all observations

**Output files:** `{YYYY-MM}.parquet` (one per month, e.g., `2019-01.parquet`, ..., `2025-07.parquet`)

**Output directory:** `outputs/location_partisan_lean/national_full/`

### 2.6 Step 7: Brand Heterogeneity Analysis

**Purpose:** Decompose variance in visitor partisan lean into between-MSA (geographic) and within-MSA (brand/location) components.

**Process:**

#### 2.6.1 Compute Location-Level Time Averages

For each unique POI (identified by `placekey`), compute:
- `mean_rep_lean_2020`: Average of `rep_lean_2020` across all months observed
- `mean_rep_lean_2016`: Average of `rep_lean_2016` across all months observed
- `n_months`: Number of months the POI was observed

This aggregation removes monthly variation and focuses on stable location-level characteristics.

#### 2.6.2 Filter to Eligible Brands

Include brands meeting minimum coverage thresholds:
- `MIN_LOCATIONS_PER_BRAND = 10`: Brand must have at least 10 unique locations
- `MIN_MSAS_PER_BRAND = 3`: Brand must be present in at least 3 distinct MSAs

#### 2.6.3 Variance Decomposition

For each eligible brand, compute:

**Between-MSA Variance (Geography):**
1. Compute mean partisan lean for each MSA: $\bar{y}_{m} = \frac{1}{n_m} \sum_{i \in m} y_i$
2. Compute variance of MSA means: $\sigma^2_{\text{between}} = \text{Var}(\bar{y}_{m})$

**Within-MSA Variance (Location):**
1. For each MSA, compute variance of locations within that MSA: $\sigma^2_{m} = \text{Var}(y_i | i \in m)$
2. Average across MSAs: $\sigma^2_{\text{within}} = \frac{1}{M} \sum_{m=1}^{M} \sigma^2_{m}$

**Intraclass Correlation Coefficient (ICC):**

$$\text{ICC} = \frac{\sigma^2_{\text{between}}}{\sigma^2_{\text{between}} + \sigma^2_{\text{within}}}$$

**Interpretation:**
- ICC close to 1: Most variance is between MSAs (geography dominates)
- ICC close to 0: Most variance is within MSAs (brand/location effects dominate)

#### 2.6.4 Output Files

**`brand_heterogeneity_summary.parquet`:**
| Column | Type | Description |
|--------|------|-------------|
| `brand` | string | Brand name |
| `n_locations` | integer | Number of unique locations |
| `n_msas` | integer | Number of unique MSAs |
| `mean_rep_lean_2020` | float | Overall mean Republican lean (2020) |
| `sd_rep_lean_2020` | float | Overall standard deviation |
| `between_msa_var_2020` | float | Between-MSA variance |
| `within_msa_var_2020` | float | Within-MSA variance |
| `total_var_2020` | float | Total variance |
| `icc_2020` | float | Intraclass correlation coefficient |
| `mean_rep_lean_2016` | float | Overall mean Republican lean (2016) |
| `sd_rep_lean_2016` | float | Overall standard deviation (2016) |
| `between_msa_var_2016` | float | Between-MSA variance (2016) |
| `within_msa_var_2016` | float | Within-MSA variance (2016) |
| `total_var_2016` | float | Total variance (2016) |
| `icc_2016` | float | Intraclass correlation coefficient (2016) |

**`brand_msa_summary.parquet`:**
| Column | Type | Description |
|--------|------|-------------|
| `brand` | string | Brand name |
| `cbsa_title` | string | MSA name |
| `n_locations` | integer | Number of locations in this brand-MSA |
| `mean_rep_lean_2020` | float | Mean Republican lean for brand in MSA |
| `sd_rep_lean_2020` | float | Standard deviation within MSA |
| `mean_rep_lean_2016` | float | Mean Republican lean (2016) |
| `sd_rep_lean_2016` | float | Standard deviation (2016) |
| `avg_months_observed` | float | Average months observed per location |

---

## 3. Key Methodological Decisions

### 3.1 Use of Two-Party Vote Share

We compute Republican vote share as a proportion of the two-party (Republican + Democratic) vote rather than total votes. This approach:
- Excludes third-party and write-in votes
- Creates a bounded measure in [0, 1]
- Is standard in political science literature
- Facilitates interpretation: 0.5 represents a perfectly competitive area

### 3.2 Handling of Zero-Vote CBGs

CBGs with zero recorded votes for both major-party candidates are assigned a partisan lean of 0.5 (neutral). This is a conservative assumption that avoids excluding these CBGs while not biasing results in either partisan direction.

### 3.3 Weighting by Visitor Count

Partisan lean is computed as a visitor-count-weighted average rather than a simple average across CBGs. This ensures that CBGs contributing more visitors have proportionally greater influence on the final measure, reflecting the actual composition of the visitor population.

### 3.4 Use of Both 2016 and 2020 Election Data

We compute partisan lean using both election years for several reasons:
1. **Robustness:** Allows comparison of results across election cycles
2. **Temporal coverage:** The data spans 2019-2025, including periods before and after each election
3. **Methodological flexibility:** Researchers can choose the measure most appropriate for their analysis
4. **Validation:** High correlation between measures provides confidence in the methodology

Note that we do **not** use 2016 data for pre-2020 periods and 2020 data for post-2020 periods. Both measures are computed for all POI-months, allowing researchers to assess sensitivity to this choice.

### 3.5 Handling of Unmatched CBGs

Some visitor home CBGs in the Advan data cannot be matched to the election data lookup. This may occur due to:
- CBG boundary changes between census years
- Data entry errors in either source
- CBGs in non-contiguous states (Alaska, Hawaii) if using contiguous-only election data

We track the match rate (`pct_visitors_matched`) for each observation. Researchers may choose to exclude observations with low match rates from analysis.

### 3.6 Geographic Assignment via POI Location

MSA assignment is based on the POI's physical location (derived from `poi_cbg`), not the home locations of visitors. This reflects where consumption occurs rather than where consumers reside.

---

## 4. Computational Implementation

### 4.1 Parallel Processing

Steps 3 and 4 are implemented as SLURM array jobs, processing each state independently in parallel. This design:
- Enables horizontal scaling across compute nodes
- Provides fault isolation (one state's failure does not affect others)
- Respects memory constraints by processing manageable data chunks

### 4.2 Memory Optimization

Several techniques reduce memory requirements:
- **Column selection:** Only required columns are loaded from CSV files
- **Dictionary lookups:** Election data is loaded into Python dictionaries for O(1) lookup rather than DataFrame joins
- **Month-by-month processing:** The combine step processes one month at a time rather than loading all data into memory
- **Explicit memory release:** Intermediate DataFrames are deleted after use

### 4.3 Data Types

Specific data types are enforced during loading to ensure consistency:
- `POI_CBG`: String (to preserve leading zeros)
- `PLACEKEY`: String
- `NAICS_CODE`: String (to preserve leading zeros)
- `bg_GEOID`: String (to preserve leading zeros)

### 4.4 Compression

All Parquet files use Snappy compression, which provides a good balance between compression ratio and read/write speed.

---

## 5. Output Data Dictionary

### 5.1 Primary Output: POI-Month Panel

**Location:** `outputs/location_partisan_lean/national_full/{YYYY-MM}.parquet`

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `placekey` | string | Unique POI identifier | `zzw-222@5vg-7gv-d9q` |
| `date_range_start` | datetime | First day of month | `2023-01-01` |
| `brand` | string | Brand name (null if unbranded) | `Starbucks` |
| `top_category` | string | High-level category | `Restaurants and Other Eating Places` |
| `sub_category` | string | Detailed category | `Snack and Nonalcoholic Beverage Bars` |
| `naics_code` | string | NAICS code | `722515` |
| `city` | string | City | `San Francisco` |
| `region` | string | State | `CA` |
| `poi_cbg` | string | POI's Census Block Group | `060750123001` |
| `cbsa_title` | string | Metropolitan Statistical Area | `San Francisco-Oakland-Berkeley, CA` |
| `parent_placekey` | string | Parent location ID | `zzw-223@5vg-7gv-d9q` |
| `median_dwell` | float | Median dwell time (minutes) | `45.0` |
| `rep_lean_2020` | float | Republican lean (2020 election) | `0.423` |
| `rep_lean_2016` | float | Republican lean (2016 election) | `0.418` |
| `total_visitors` | integer | Total visitors from all CBGs | `1,245` |
| `matched_visitors` | integer | Visitors matched to election data | `1,198` |
| `pct_visitors_matched` | float | Match rate percentage | `96.2` |

### 5.2 Brand Heterogeneity Summary

**Location:** `outputs/brand_heterogeneity/brand_heterogeneity_summary.parquet`

Contains brand-level variance decomposition statistics (see Section 2.6.4).

### 5.3 Brand-MSA Summary

**Location:** `outputs/brand_heterogeneity/brand_msa_summary.parquet`

Contains brand × MSA level statistics (see Section 2.6.4).

---

## 6. Validation and Quality Assurance

### 6.1 Schema Validation

Before processing, the pipeline validates that all required columns exist in the source data.

### 6.2 GEOID Format Consistency

All Census Block Group identifiers are standardized to 12-digit format with leading zero padding to ensure consistent matching.

### 6.3 Range Validation

Partisan lean measures are constrained to the [0, 1] interval by construction. Any values outside this range would indicate a computational error.

### 6.4 Match Rate Monitoring

The percentage of visitors successfully matched to election data is tracked for each observation, enabling researchers to assess data quality and potentially filter low-quality observations.

### 6.5 Cross-Year Correlation

The correlation between 2016 and 2020 partisan lean measures is logged as a validation check. High correlation (typically > 0.95) indicates consistency in the methodology.

---

## 7. Limitations

### 7.1 Mobile Phone Sampling

The Advan data is derived from mobile phone location signals, which may not be representative of all visitors. Demographic groups with lower smartphone adoption or location-sharing rates may be underrepresented.

### 7.2 Privacy-Preserving Noise

Advan applies differential privacy protections that introduce noise into visitor counts. This may attenuate measured partisan differences, biasing results toward null findings.

### 7.3 CBG-Level Election Estimates

The election data uses modeled estimates of block group-level vote shares rather than actual precinct-level returns. This introduces measurement error, though the methodology is well-established in political science.

### 7.4 Ecological Inference

We observe aggregate CBG-level voting patterns, not individual-level political preferences. The partisan lean measure reflects the voting behavior of the CBG as a whole, which may differ from the specific individuals who visited the POI.

### 7.5 Home Location vs. Current Residence

The "home" CBG in Advan data is inferred from nighttime location patterns and may not reflect current residence for all individuals (e.g., college students, seasonal residents).

---

## 8. Replication

### 8.1 Code Availability

All processing scripts are available at: `[GitHub repository URL]`

### 8.2 Data Access

- **Advan foot traffic data:** Requires commercial license from Advan/Dewey
- **Election data:** Available from [source]
- **CBSA crosswalk:** Publicly available from NBER (`https://data.nber.org/cbsa-csa-fips-county-crosswalk/`), derived from U.S. Census Bureau delineation files

### 8.3 Computational Requirements

- **Storage:** Approximately 1 TB for raw inputs and outputs
- **Memory:** 128-386 GB RAM recommended for state-level processing
- **Compute time:** Approximately 24-48 hours for full pipeline on HPC cluster

---

## 9. Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-01-13 | Initial methodology for national scale-up |

---

## References

[To be added: citations for Advan/SafeGraph methodology, RLCR election geocoding methodology, ICC/variance decomposition methods, etc.]
