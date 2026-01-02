# Project Oakland: Expanded Research Agenda

## Target: Job Market Paper for Top Management Journals
**Venues**: SMJ, Organization Science, Management Science, ASQ
**Timeline**: Fall 2026 job market (~8-9 months to polished draft)

---

## Core Value Proposition

Combine two unique large-scale datasets to study the relationship between **employee ideology** and **consumer ideology** at the firm level:

| Dataset | Source | Coverage | Measures |
|---------|--------|----------|----------|
| **Politics at Work** | Voter registration + employment records | 45M people with work histories, full microdata | Employee partisanship (VRscores) |
| **Project Oakland** | Advan foot traffic + CBG election results | 2.9M+ POI-months, 328K+ locations | Visitor/consumer partisanship |

**Novel contribution**: First large-scale study linking who works at companies to who shops at them, ideologically.

**Key data advantage**: Full PAW microdata access allows flexible aggregation (MSA × employer × year, or other cuts as needed).

---

## Key Literature & Validation Benchmarks

### Primary Comparison: Twitter-Based Consumer Ideology
**Schoenmueller, Netzer, & Stahl (2023)** - "Polarized America: From Political Polarization to Preference Polarization" (*Marketing Science*)
- Uses Twitter followership to measure brand political lean
- **Public API available**: http://www.social-listening.org
- Captures online engagement vs. our physical foot traffic
- **Framing**: Validation if measures converge; complementary constructs if they diverge

### Methodological Reference: Smartphone Location Data
**Poliquin, Hou, Sakakibara, & Testoni (2024)** - "Using Smartphone Location Data for Strategy Research" (*Strategy Science*)
- Comprehensive guide to Advan/SafeGraph data
- Discusses measurement issues, matching to Compustat
- **Action**: Download and review for employee contamination discussion

---

## Phase 1: Data Integration

### Challenge 1A: Entity Resolution

**Problem**: Advan data lack standard company identifiers (no tickers, GVKEYs, EINs)

**Decision**: Maximum coverage approach - match all possible employers regardless of public/private status

**Matching Strategy**:

| Approach | Coverage | Application |
|----------|----------|-------------|
| **Manual crosswalk** | Top 200 brands | Highest accuracy for major chains |
| **FuzzyLink (OpenAI)** | Remaining branded POIs (~2,000 brands) | $500-2000 budget approved |
| **LOCATION_NAME fuzzy matching** | ~80% unbranded POIs | Noisy but maximizes coverage |

**Scale estimates**:
- ~2,000 unique Advan brands to match
- ~80% of POIs lack brand identifiers - will attempt LOCATION_NAME matching
- Politics at Work has ~500K employers; filter to those with sufficient employee counts

### Challenge 1B: Employee Contamination

**Problem**: Foot traffic captures all visitors, including employees. Employee ideology may contaminate consumer ideology measure.

**Available Advan fields for mitigation**:

| Field | Description | Potential Use |
|-------|-------------|---------------|
| `MEDIAN_DWELL` | POI-level median dwell time | Identify employee-heavy POIs |
| `BUCKETED_DWELL_TIMES` | Distribution by duration | Separate 8+ hour (employee) vs. <1 hour (customer) visits |
| `VISITOR_DAYTIME_CBGS` | Where visitors come from during work hours | Cross-reference with home CBGs |
| `DISTANCE_FROM_HOME` | Travel distance distribution | Employees likely live closer |

**Proposed approach**:
1. Use `BUCKETED_DWELL_TIMES` to estimate employee fraction of visits
2. For robustness: exclude POI-months with high long-dwell fractions
3. Compare results with/without adjustment
4. Document limitation transparently

**Note**: CBG-level visitor data cannot distinguish dwell time, so correction is at POI-aggregate level only.

### Challenge 1C: Aggregation Strategy

**Decision**: Visitor-weighted primary, with robustness checks

| Method | Use |
|--------|-----|
| **Visitor-weighted** (primary) | Σ(rep_lean × visitors) / Σ(visitors) |
| **Simple average** (robustness) | Mean across POIs |
| **Normalized** (robustness) | Using `NORMALIZED_VISITS_BY_STATE_SCALING` |

### Challenge 1D: Data Inventory

**Currently available**:
- [x] Advan Monthly Patterns (Jan 2019 - Jul 2024), all states
- [x] Advan Neighborhood Patterns (available - need to confirm structure)
- [x] CBG-level election results (2020, geocoded)
- [x] Politics at Work full microdata

**Needed**:
- [ ] SafeGraph spending data (for within-store outcome analysis)
- [ ] Confirm Neighborhood Patterns structure for Bartik IV

---

## Phase 2: Research Design Options

### Option A: Descriptive - Employee-Consumer Partisan Alignment

**Research question**: To what extent do employees and customers of firms share the same partisan composition?

**Analysis levels**:
1. **Firm-level correlation**: Do companies with more Republican employees also have more Republican customers?
2. **Within-MSA variation**: Same brand, different MSAs - how much heterogeneity?
3. **Within-MSA, across-brand**: Same geography - do employees and customers sort differently across businesses?

**Variance decomposition**:
- Between-firm variance in employee partisanship
- Between-firm variance in consumer partisanship
- Within-firm (across-location) variance for each
- Covariance between employee and consumer partisanship

**Geography threat**: "It's all geography" - both reflect local demographics
- **Mitigation**: Within-MSA FEs, within-firm (across-location) analysis
- For some analyses (overall composition), geography is the point
- For others (site selection), need MSA FEs

**Contribution**: First systematic evidence on whether political sorting operates similarly in labor and consumer contexts.

### Option B: Validation - Compare to Twitter-Based Measure

**Research question**: How does foot-traffic-based consumer partisanship compare to Twitter followership-based measures?

**Comparison**:
- Obtain brand scores from social-listening.org API
- Correlate with our foot-traffic-based measures
- Examine where they diverge (online vs. physical engagement)

**Framing options**:
1. **Validation**: If converge, mutual reinforcement
2. **Complementary constructs**: If diverge, capturing different phenomena (revealed preference vs. stated affiliation)

**Contribution**: Methodological comparison; understanding what different measurement approaches capture.

### Option C: Consequences - Mismatch and Outcomes

**Research question**: Does employee-consumer partisan mismatch predict organizational outcomes?

**Approach**: Hybrid - descriptive core + one causal identification strategy

**Dependent Variables** (by data availability):

| Outcome | Data Source | Effort Required |
|---------|-------------|-----------------|
| **Political spending** | LobbyView, FEC | Moderate - structured data, Claude can help |
| **Consumer spending** | SafeGraph spending | Low if data available - within-store TWFE |
| **Boycotts/activism** | Media mentions (McKean & King approach) | High - manual collection |
| **Firm financials** | Compustat | Low - standard merge |

**Identification Strategies** (ranked by feasibility):

#### Strategy 1: Political Salience Shocks (DiD) - EASIEST
```
Outcome_it = β₁Mismatch_i + β₂Salience_t + β₃(Mismatch_i × Salience_t) + FEs + ε
```

**Salience events**:
- 2016 election (Nov 2016)
- 2020 election (Nov 2020)
- Dobbs decision (June 2022)
- State-level races, ballot initiatives

**Interpretation**: β₃ tests whether mismatch matters more when politics is salient

**Caveat**: Consumer partisanship measured from 2020 election returns - somewhat circular for election shocks. Argument is about salience, not partisanship changes.

#### Strategy 2: CEO/Brand Political Statements (Event Study)
**Design**: When brand makes political statement, examine how pre-existing mismatch predicts magnitude of consumer response

**Examples**:
- Nike/Kaepernick (Sept 2018)
- Bud Light (April 2023)
- Chick-fil-A (ongoing)

**Novel prediction vs. Burbano**: She studies employee response to CEO activism. We study consumer response, conditional on employee-consumer alignment. Firms with aligned stakeholders may have "permission" to speak.

#### Strategy 3: Border DMA Design (RD)
**Reference**: Spenkuch & Toniatti - battleground state media market borders

**Design**: Same chain stores in DMAs straddling battleground/safe state borders
- One side: high political advertising exposure (salient)
- Other side: low exposure
- Test: Does mismatch effect differ by salience exposure?

**Data need**: Identify border DMAs, map to POIs

#### Strategy 4: New Store Openings + Bartik IV - MOST NOVEL
**Design**: When national chain opens new store, initial consumer base is partly "given" by pre-existing neighborhood traffic

**Instrument**:
```
Consumer_Partisanship_NewStore = f(Neighborhood_Baseline_Visitors × Local_Election_Returns)
```

**Data needs**:
- Advan Neighborhood Patterns (available)
- OPENED_ON field to identify new stores
- Pre-opening neighborhood visitor composition

**Exclusion restriction challenge**: Pre-existing visitors could affect outcomes through non-partisan channels (income, density). Need controls or argue orthogonality.

**Contribution**: Novel application of Bartik logic to consumer partisanship.

### Option D: Site-Level Spending Variation

**Research question**: Does political mismatch affect consumer spending at the site level?

**Design**: Within-store TWFE using SafeGraph spending data
```
Spending_it = β(Mismatch_i × Salience_t) + Store_FE + Time_FE + ε
```

**Advantage**: Captures revealed preference (actual spending), not just visits

**Limitation**: SafeGraph spending not comprehensive - better for within-store over-time variation than cross-store levels

**Potential shock**: Election years as salience moderator (though not ideal design)

### Option E: Strategy - Location Choice

**Research question**: Do firms strategically locate to minimize employee-consumer partisan mismatch?

**Analysis**:
1. For new store openings, compare actual location partisan composition to counterfactual (other locations in MSA/industry)
2. Test: Do firms locate where employee pool matches expected customer base?

**Uses Bartik IV from Option C**: Neighborhood patterns as baseline for expected customer composition

### Option F: Brand Similarity - Cross-Shopping Networks

**Research question**: Do brands with similar cross-shopping patterns have similar partisan compositions?

**Using Advan fields**:
- `RELATED_SAME_DAY_BRAND` - brands visited same day
- `RELATED_SAME_MONTH_BRAND` - brands visited same month

**Analysis**:
- Build brand similarity network from cross-shopping
- Test: Are brands clustered by partisan composition?
- Compare to: price tier, category, geography

**Contribution**: Consumer political sorting operates at brand ecosystem level, not just individual firms.

### Option G: Temporal Dynamics - Rising Polarization

**Research question**: Has consumer-employee alignment changed over time as polarization increased (2016-2024)?

**Analysis**:
- Compute alignment metrics at firm/brand level for each year
- Track whether firms became more sorted over time
- Test: Did polarization "spread" to consumer and labor markets?

**Contribution**: Pure descriptive contribution documenting polarization dynamics in markets.

### Option H: Worker Mobility as Mechanism ⭐ HIGH POTENTIAL

**Research question**: When workers change jobs, do they move toward firms whose consumers are more politically aligned with them?

**Core insight**: If workers actively sort toward consumer-aligned employers, this shows revealed preference for ideological matching - not just geographic correlation.

**Research design**:
```
Pr(Move to Firm j) = f(Consumer_Alignment_j, Worker_Partisanship_i, Controls)
```

**Using PAW longitudinal structure**:
1. Identify job-to-job transitions (same worker, different employer)
2. For each transition, compute:
   - Origin firm consumer partisanship (from Project Oakland)
   - Destination firm consumer partisanship
   - Worker's own partisanship (VRscore)
3. Test: Do workers move toward consumer-aligned firms?

**Key controls** (to rule out geography):
- Same-MSA transitions only
- Industry controls (NAICS)
- Firm size, wage tier if available

**Heterogeneity tests** (using Revelio job role typology):
- Customer-facing vs. back-office roles (prediction: retail/service workers sort more)
- Worker partisan extremity (strong partisans sort more?)
- Industry identity-relevance (food/apparel vs. utilities)

**Potential finding patterns**:
- Workers move TOWARD consumer-aligned firms (attraction)
- Workers move AWAY from consumer-misaligned firms (repulsion)
- Asymmetric effects by party?

**Contribution**: First evidence of revealed preference for ideological alignment in job search. Active matching, not just cross-sectional correlation.

### Option I: Competitive Dynamics - Relative Alignment ⭐ HIGH POTENTIAL

**Research question**: In head-to-head competition, does relative political alignment predict market share?

**Research design**:
```
MarketShare_jmt = β(RelativeAlignment_jmt) + Brand_FE + Market_FE + Time_FE + ε
```

**Construction**:
1. Define markets (MSA × NAICS category) - granularity TBD empirically
2. For each brand in market, compute consumer alignment gap:
   ```
   Alignment_jm = |Brand_Consumer_Lean_j - Market_Consumer_Lean_m|
   ```
3. Relative alignment = Brand's alignment minus average competitor alignment

**Prediction**: Lower alignment gap → higher market share

**Identification boost**: Use national brand-level partisanship as "exposure" (Bartik-style)
- National brand lean is plausibly exogenous to local market conditions
- Interacted with local political composition gives predicted local alignment

**Dynamic version**: Does relative alignment matter MORE in election years / high salience periods?

**Contribution**: First evidence that political alignment confers competitive advantage in local markets.

### Option J: Industry Heterogeneity - Conspicuous vs. Commodity

**Research question**: Does employee-consumer alignment matter more in "identity-relevant" industries?

**Theoretical frame**: Conspicuous consumption - some products signal identity (food, apparel, media), others don't (gas, utilities, hardware).

**Analysis**:
- Categorize industries by identity-relevance (manual or theory-driven)
- Test: Is alignment correlation stronger in conspicuous categories?

**Future extension**: Verisk automotive data for vehicle make/model as identity signal (noted for follow-up paper).

### Option K: Geographic Expansion Sequencing ⭐ HIGH PRIORITY

**Research question**: When chains expand to new markets, do they preferentially enter politically aligned areas?

**Research design**:
- Panel of potential expansion locations (adjoining counties/MSAs to existing footprint)
- Gravity model: distance from existing locations as baseline
- Test: Conditional on distance, do firms enter markets where expected consumers align with existing employee/consumer base?

**Identification**:
- Use adjoining geographies as choice set
- Control for market size, demographics, competition

**Data limitation**: Consumer attitudes measure strongest 2020-2024; expansion analysis limited to this window.

**Contribution**: First evidence of political considerations in geographic expansion strategy.

### Option L: Review Sentiment as Outcome

**Research question**: Does employee-consumer mismatch predict negative review sentiment or politically charged language?

**Data sources** (ranked by feasibility):

| Source | Coverage | Cost | Effort |
|--------|----------|------|--------|
| **Yelp Open Dataset** | 11 metros incl. Columbus OH, 6.9M reviews | Free | Low |
| **Apify Google Maps Actor** | National, customizable | ~$100-200 for 100K POIs | Medium |
| **Custom scraper** | Any coverage | Time only | High |

**Recommended approach**:
1. Start with Yelp Open Dataset for proof-of-concept (Columbus overlaps Ohio pilot)
2. If promising, expand via Apify

**Analysis**:
- Sentiment analysis of review text
- Political keyword detection
- Test: Higher mismatch → more negative sentiment / political language?

---

## Scope Note: Related But Separate Papers

**Hiring/Turnover Paper (SEPARATE)**: Already in progress, covers:
- Do firms with partisan consumers hire aligned workers?
- Worker turnover patterns by ideology
- Uses PAW hiring dates and turnover data

**This JMP (Project Oakland)**: Focuses on:
- Consumer-employee alignment and its STRATEGIC consequences
- Competitive dynamics, location choice, market outcomes
- Worker mobility toward consumer-aligned firms (novel: workers caring about CUSTOMER composition, not just coworker composition)

---

## Phase 3: Recommended Paper Structure

### Primary Paper: "Partisan Markets: Employee and Consumer Political Sorting Across U.S. Firms"

**Core contribution**: First comprehensive analysis of political sorting in both labor and consumer markets at firm level.

**Empirical strategy**:
1. **Descriptive correlation**: Employee-consumer partisan alignment at firm level
2. **Validation**: Compare to Twitter-based measure (Schoenmueller et al.)
3. **Variance decomposition**: How much is firm-level vs. location-level?
4. **Consequence analysis**: Mismatch → outcomes with hybrid causal strategy

**Why this works for SMJ/OS/MS/ASQ**:
- Novel data combination (unique contribution)
- Multiple levels of analysis
- Speaks to strategy (location, employee sorting)
- Speaks to organizations (culture, internal politics)
- Policy relevance (polarization, consumer activism)
- Methodological contribution (validation against Twitter measure)

---

## Research Options by Data Readiness

### Tier 1: Ready to Execute (Have All Data)

| Option | Description | Data Status |
|--------|-------------|-------------|
| **A** | Descriptive alignment | ✅ Advan + PAW ready |
| **B** | Validation vs. Twitter | ✅ Just need API call to social-listening.org |
| **G** | Temporal dynamics | ✅ Panel structure exists |
| **F** | Cross-shopping networks | ✅ RELATED_SAME_DAY_BRAND in Advan |
| **J** | Industry heterogeneity | ✅ NAICS codes available |

### Tier 2: Needs Some Construction (Data Exists, Needs Processing)

| Option | Description | What's Needed |
|--------|-------------|---------------|
| **H** | Worker mobility ⭐ | Link PAW job transitions to Oakland consumer data |
| **I** | Competitive dynamics ⭐ | Define markets, compute relative alignment |
| **K** | Geographic expansion ⭐ | Identify new openings via OPENED_ON, build choice sets |
| **E** | Location choice | Similar to K, plus Neighborhood Patterns |
| **C** | Mismatch → outcomes | Need to collect DVs (see below) |

### Tier 3: Needs New Data Collection

| Option | Description | What's Needed | Cost/Effort |
|--------|-------------|---------------|-------------|
| **C** | Political spending DV | LobbyView + FEC download | Low, structured |
| **C** | Firm financials DV | Compustat merge | Low, standard |
| **D** | Site-level spending | SafeGraph spending from Dewey | Medium, check availability |
| **L** | Review sentiment | Yelp Open Dataset OR Apify | Free–$200 |
| **C** | Boycotts/activism DV | Media mentions collection | High, manual |

---

## Prioritized Action Plan

### Phase 1: Foundation (Weeks 1-4)
**Goal**: Validate core data linkage, produce first descriptive results

1. [ ] **Entity resolution pilot**
   - Extract unique brands from Ohio Advan data
   - Build manual crosswalk for top 50 brands to PAW
   - Test FuzzyLink on sample
   - Estimate coverage rate

2. [ ] **Employee contamination check**
   - Examine BUCKETED_DWELL_TIMES structure
   - Estimate employee fraction by POI type
   - Review Poliquin et al. (2024) treatment

3. [ ] **Produce first descriptive stats** (Option A)
   - Firm-level correlation: employee vs. consumer partisanship
   - Variance decomposition

### Phase 2: Validation & Extensions (Weeks 5-8)
**Goal**: Validate measure, test high-potential mechanisms

4. [ ] **Twitter validation** (Option B)
   - Access social-listening.org API
   - Compute correlation with foot-traffic measures

5. [ ] **Worker mobility analysis** (Option H) ⭐
   - Link PAW job transitions to Oakland consumer data
   - Test: Do workers move toward consumer-aligned firms?
   - Heterogeneity by job role (customer-facing vs. back-office)

6. [ ] **Competitive dynamics** (Option I) ⭐
   - Define markets (MSA × NAICS)
   - Compute relative alignment
   - Test market share prediction

### Phase 3: Causal Identification (Weeks 9-12)
**Goal**: Develop at least one credible causal test

7. [ ] **Salience shock DiD** (Strategy 1)
   - Define salience events (elections, Dobbs)
   - Test mismatch × salience interaction

8. [ ] **Geographic expansion** (Option K)
   - Identify new store openings (OPENED_ON field)
   - Build choice set from adjoining counties
   - Test: Do firms enter aligned markets?

9. [ ] **New store Bartik IV** (Strategy 4)
   - Confirm Neighborhood Patterns structure
   - Instrument consumer partisanship with baseline traffic

### Phase 4: Outcome Analysis (Weeks 13-16)
**Goal**: Link mismatch to strategic outcomes

10. [ ] **Political spending** (Option C)
    - Download LobbyView + FEC
    - Merge to matched firms
    - Test mismatch → spending

11. [ ] **Review sentiment pilot** (Option L)
    - Download Yelp Open Dataset
    - Match to Columbus OH POIs
    - Sentiment analysis proof-of-concept

### Phase 5: Robustness & Writing (Weeks 17-24)
**Goal**: Full draft ready for job market

12. [ ] Temporal dynamics (Option G)
13. [ ] Industry heterogeneity (Option J)
14. [ ] Cross-shopping networks (Option F)
15. [ ] Write up, circulate for feedback

---

## Open Questions (Remaining)

1. What is the seniority variable in Politics at Work? How is it constructed?
2. Is Revelio parent-child typology available for rolling up subsidiaries?
3. What is the structure of Neighborhood Patterns data? (CBG × month?)
4. Is SafeGraph spending data available through Dewey?
5. What are the Revelio job role categories? (User adding hierarchy)

---

## Interview Progress

**Completed**:
- [x] PAW data structure: Full microdata, can cut by MSA × employer × year
- [x] Timeline: Fall 2026 job market (~8-9 months)
- [x] Entity resolution scope: Maximum coverage (public + private)
- [x] Unbranded POI strategy: Fuzzy match LOCATION_NAME
- [x] API budget: $500-2000 for FuzzyLink
- [x] Mismatch direction: Both equally interesting (symmetric analysis)
- [x] Chain scope: Everything matchable
- [x] Causal ID approach: Hybrid (descriptive core + one causal test)
- [x] Geography threat: Context-dependent, multiple FE strategies
- [x] Employee contamination: Key threat, mitigate via dwell time fields
- [x] Revelio job roles: Available for customer-facing heterogeneity
- [x] Separate hiring paper: Exists, this JMP focuses on strategic consequences
- [x] Review sentiment data: Yelp Open Dataset (free) or Apify (~$100-200)
- [x] Geographic expansion: High priority, limited to 2020-2024 window

**Key Novel Ideas Identified**:
- ⭐ Worker mobility toward consumer-aligned firms (Option H)
- ⭐ Competitive dynamics / relative alignment (Option I)
- ⭐ Geographic expansion sequencing (Option K)

**Pending**:
- [ ] Revelio hierarchy (user adding)
- [ ] Final prioritization sign-off
- [ ] Additional refinements as needed

---

*Updated: 2026-01-02*
*Interview in progress*
