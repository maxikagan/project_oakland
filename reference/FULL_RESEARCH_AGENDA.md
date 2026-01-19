# Project Oakland: Complete Research Agenda

**Target**: Fall 2026 job market paper for SMJ/Organization Science/Management Science/ASQ

---

## Core Value Proposition

Combine two unique large-scale datasets to study the relationship between **employee ideology** and **consumer ideology** at the firm level:

| Dataset | Source | Coverage | Measures |
|---------|--------|----------|----------|
| **Politics at Work** | Voter registration + employment records | 45M people with work histories | Employee partisanship (VRscores) |
| **Project Oakland** | Advan foot traffic + CBG election results | ~596M POI-months, 79 months | Visitor/consumer partisanship |

**Novel contribution**: First large-scale study linking who works at companies to who shops at them, ideologically.

---

## Ohio Pilot: Key Findings (2023 Data)

### Data Summary
- **2.9 million** POI-month observations
- **328,000** unique points of interest
- **12 months** of data (Jan-Dec 2023)
- **Mean Republican lean:** 52.4% (slightly right of center)

### 1. The Measure is Reliable (Temporal Consistency)

| Test | Result | Interpretation |
|------|--------|----------------|
| Monthly aggregate variation | 0.35 pts (51.6%-52.9%) | Essentially flat |
| Within-POI std dev (median) | 3.7 pts | Individual locations barely move |
| Brand adjacent-month correlation | 0.90 | Very high stability |
| Brand Jan-Dec correlation | 0.84 | Consistent across full year |
| Q1-Q4 correlation | 0.87 | Quarterly stability |

**Conclusion:** The measure captures a stable characteristic of locations, not monthly noise.

### 2. Geography Dominates Brand

| Level | Variance Explained |
|-------|-------------------|
| Between-brand | 8% |
| Within-brand (location) | 85% |

**Examples of within-brand spread:**
- McDonald's: 14% - 84% R across Ohio locations (70 pt range)
- Starbucks: 17% - 80% R (63 pt range)
- Walmart: 18% - 81% R (63 pt range)

**Conclusion:** A Starbucks in rural Ohio (80% R) has more Republican visitors than almost any Walmart. Location matters ~10x more than brand identity.

### 3. Notable Brand Differences (unconditional)

| Matchup | Gap |
|---------|-----|
| Whole Foods (40%) vs Kroger (54%) | 14 pts |
| Target (48%) vs Walmart (58%) | 10 pts |
| Chick-fil-A (51%) vs McDonald's (55%) | 4 pts |
| Starbucks (49%) vs Dunkin' (52%) | 3 pts |

### 4. Within-Neighborhood Variation

Even controlling for location (same H3 geographic cell), different businesses attract different visitors:

| City | Avg within-neighborhood range |
|------|------------------------------|
| Cleveland | 15.8 pts |
| Columbus | 18.7 pts |
| Cincinnati | 18.5 pts |
| Toledo | 19.0 pts |

**Variance decomposition within cities:**
- Between-neighborhood: 75-87%
- Within-neighborhood (business type): 13-25%

**Conclusion:** Geography is dominant, but business type explains 13-25% of variance *within* neighborhoods.

---

## Literature & Validation

### Primary Comparison: Twitter-Based Consumer Ideology
**Schoenmueller, Netzer, & Stahl (2023)** - "Polarized America: From Political Polarization to Preference Polarization" (*Marketing Science*)
- Uses Twitter followership to measure brand political lean
- **Data available**: 1,289 brands from social-listening.org
- Captures online engagement vs. our physical foot traffic

### Methodological Reference
**Poliquin, Hou, Sakakibara, & Testoni (2024)** - "Using Smartphone Location Data for Strategy Research" (*Strategy Science*)
- Comprehensive guide to Advan/SafeGraph data
- Discusses measurement issues, matching to Compustat

---

## Research Options

### Option A: Descriptive - Employee-Consumer Partisan Alignment ⭐ PRIORITY

**Research question**: To what extent do employees and customers of firms share the same partisan composition?

**Analysis levels**:
1. Firm-level correlation: Do companies with more Republican employees also have more Republican customers?
2. Within-MSA variation: Same brand, different MSAs
3. Within-MSA, across-brand: Same geography, different businesses

**Variance decomposition**:
- Between-firm variance in employee partisanship
- Between-firm variance in consumer partisanship
- Within-firm (across-location) variance
- Covariance between employee and consumer partisanship

### Option B: Validation - Compare to Twitter-Based Measure ⭐ QUICK WIN

**Research question**: How does foot-traffic-based consumer partisanship compare to Twitter followership-based measures?

**Data**: Schoenmueller et al. brand scores (1,289 brands available)
**Method**: Correlate with our foot-traffic-based measures using `normalized_visits_by_state_scaling` weights

### Option C: Consequences - Mismatch and Outcomes

**Research question**: Does employee-consumer partisan mismatch predict organizational outcomes?

**Dependent Variables**:
- Political spending (LobbyView, FEC)
- Consumer spending (SafeGraph Spend - AVAILABLE)
- Firm financials (Compustat)

**Identification Strategies**:
1. Political salience shocks (DiD) - elections, Dobbs
2. CEO/Brand political statements (event study)
3. Border DMA design (RD)
4. New store openings + Bartik IV

### Option D: Site-Level Spending Variation ⭐ PRIORITY

**Research question**: Does political mismatch affect consumer spending at the site level?

**Data**: SafeGraph Spend (83 months, 2019-01 to 2025-11) - AVAILABLE
**Design**: Within-store TWFE

### Option E: Strategy - Location Choice

**Research question**: Do firms strategically locate to minimize employee-consumer partisan mismatch?

### Option F: Brand Similarity - Cross-Shopping Networks

**Research question**: Do brands with similar cross-shopping patterns have similar partisan compositions?

**Using Advan fields**: `RELATED_SAME_DAY_BRAND`, `RELATED_SAME_MONTH_BRAND`

### Option G: Temporal Dynamics - Rising Polarization (DEPRIORITIZED)

**Note**: Limited by data starting in 2019 (post-2016 polarization surge)

### Option H: Worker Mobility as Mechanism ⭐ HIGH POTENTIAL

**Research question**: When workers change jobs, do they move toward firms whose consumers are more politically aligned with them?

**Using PAW longitudinal structure**: Track job-to-job transitions

### Option I: Competitive Dynamics - Relative Alignment ⭐ HIGH POTENTIAL

**Research question**: In head-to-head competition, does relative political alignment predict market share?

### Option J: Industry Heterogeneity - Conspicuous vs. Commodity

**Research question**: Does alignment matter more in "identity-relevant" industries?

### Option K: Geographic Expansion Sequencing ⭐ HIGH PRIORITY

**Research question**: When chains expand to new markets, do they preferentially enter politically aligned areas?

### Option L: Review Sentiment as Outcome (DEPRIORITIZED)

Lower priority for now.

---

## Methodological Notes

### Aggregation Strategy

**For POI-level**: Use `raw_visitor_counts` as computed
**For brand-level aggregation**: Use `normalized_visits_by_state_scaling` to avoid sampling bias

```
brand_lean = Σ(rep_lean_i × normalized_visits_i) / Σ(normalized_visits_i)
```

### Excess Partisan Lean (Gravity Model)

Control for geography using expected visitors based on:
- Distance decay from POI
- Population of origin CBGs
- Category-specific draw patterns (NAICS 4-digit)

```
excess_lean = actual_lean - expected_lean_from_gravity
```

### Employee Contamination

**Potential mitigation via Advan fields**:
- `MEDIAN_DWELL`: Identify employee-heavy POIs
- `BUCKETED_DWELL_TIMES`: Separate 8+ hour (employee) vs. <1 hour (customer) visits

---

## Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Election data | Both 2016 and 2020 | Robustness |
| CBG method | Main Method (RLCR) | Standard approach |
| Entity resolution | Maximum coverage | Include private companies |
| Category grouping | NAICS 4-digit | Replicable, maps to Advan |
| Brand aggregation weight | `normalized_visits_by_state_scaling` | Avoids sampling bias |

---

## Interview Notes (2026-01-02)

**Completed decisions**:
- PAW data structure: Full microdata, can cut by MSA × employer × year
- Timeline: Fall 2026 job market (~8-9 months)
- Entity resolution scope: Maximum coverage (public + private)
- API budget: $500-2000 for FuzzyLink
- Causal ID approach: Hybrid (descriptive core + one causal test)
- Geography threat: Context-dependent, multiple FE strategies

**Novel ideas identified**:
- ⭐ Worker mobility toward consumer-aligned firms (Option H)
- ⭐ Competitive dynamics / relative alignment (Option I)
- ⭐ Geographic expansion sequencing (Option K)

---

*Last updated: 2026-01-18*
