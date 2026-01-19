# Analysis Plan: Political Alignment and Firm Performance

## Research Questions

### Primary Question
**Does political alignment between firms and their customers improve firm performance?**

### Secondary Questions
1. Is there partisan sorting in where firms open new locations?
2. Do stores in politically aligned areas have lower closure rates?
3. Does political alignment affect customer spending (not just foot traffic)?
4. Is the alignment-performance relationship stronger when partisan conflict is salient?

---

## Available Performance Measures

| Measure | Data Source | Level | Coverage | Pros | Cons |
|---------|-------------|-------|----------|------|------|
| **Store openings** | SafeGraph POI Core | POI | Full period | Direct measure of expansion | Selection bias |
| **Store closures** | SafeGraph POI Core | POI | Full period | Direct measure of failure | May miss relocations |
| **Foot traffic** | Advan Monthly Patterns | POI × Month | 2019-2024 | Rich panel, visitor CBGs | Doesn't capture $$ |
| **Spending** | SafeGraph Spend | POI × Month | 2019-2021 | Actual revenue | Shorter coverage |
| **Brand spending** | Consumer Edge | Brand × CSA | 2021 | Year-over-year change | Aggregate, not POI |

---

## Time-Varying Moderators

| Measure | Source | Frequency | Coverage | Description |
|---------|--------|-----------|----------|-------------|
| **Partisan Conflict Index (PCI)** | Philadelphia Fed | Monthly | 1981-2025 | Newspaper-based measure of political disagreement among federal lawmakers. Higher values = more salient partisan conflict. Normalized to mean=100 for 1981-2010. |

**File location**: `/global/home/users/maxkagan/measuring_stakeholder_ideology/reference/partisan_conflict_index.csv`

**Theoretical rationale**: If political alignment affects firm performance through political consumerism (consumers preferring ideologically aligned businesses), the effect should be **amplified** when partisan conflict is salient. When PCI is high, political identity is more top-of-mind, making alignment more valuable. This interaction helps establish causality—if alignment merely proxied for demographics or other confounds, there is no reason the effect would vary with PCI.

---

## Proposed Analyses

### Analysis 1: POI Lifecycle and Political Geography
**Question**: Are stores in politically aligned areas less likely to close?

**Method**:
1. Compute visitor political lean for each POI using visitor_home_cbgs × election results
2. Compute firm political lean using Politics at Work employee data (where available)
3. Calculate alignment = |visitor_lean - firm_lean|
4. Survival analysis: Cox proportional hazards with closure as event
5. Controls: NAICS, region, population density, income levels

**Data needed**:
- POI open/close dates (SafeGraph POI Core) ← running now
- Visitor home CBGs × election results (already have)
- Politics at Work firm-level ideology

### Analysis 2: Store Opening Location Choices
**Question**: Do firms open in areas with favorable political alignment?

**Method**:
1. Identify new store openings (opened_on in 2019-2024)
2. For each brand with multiple openings, compare:
   - Political lean of areas where they opened
   - Political lean of areas where they could have opened (same metro, similar demographics)
3. Matched difference-in-differences or conditional logit

**Outcome**: Is there evidence of partisan sorting in location decisions?

### Analysis 3: Performance and Alignment (Cross-sectional)
**Question**: Do aligned stores have higher spending/traffic?

**Method**:
1. Merge SafeGraph Spend with visitor political composition
2. Regression: log(spending) ~ alignment + controls
3. Within-brand variation: brand fixed effects to control for firm-level confounds

**Key controls**:
- Population/income in catchment area
- Competition density (other POIs nearby)
- Time trends (month FEs)

### Analysis 4: COVID Shock as Natural Experiment
**Question**: Did political alignment buffer stores from COVID impact?

**Method**:
1. Pre-COVID baseline (Jan-Feb 2020) vs. COVID period (Mar-Dec 2020)
2. Triple diff: Before/After × High/Low alignment × Exposed/Not exposed industries
3. Hypothesis: Aligned stores maintained more loyal customers during disruption

### Analysis 5: Partisan Climate Moderation (Identification Strategy)
**Question**: Is the alignment-performance relationship stronger when partisan conflict is salient?

**Theoretical motivation**:
- Political consumerism theory predicts consumers reward/punish firms based on perceived political alignment
- This behavior should be more pronounced when partisan identity is activated (high media coverage of political conflict)
- The Partisan Conflict Index (PCI) captures month-to-month variation in the salience of partisan disagreement

**Method**:
1. Construct POI × month panel with:
   - `misalignment_it` = |visitor_republican_share - firm_employee_republican_share|
   - `PCI_t` = Partisan Conflict Index in month t (standardized)
   - `performance_it` = foot traffic or spending
2. Estimate interaction model:
   ```
   log(performance_it) = β₁ × misalignment_i + β₂ × PCI_t + β₃ × (misalignment_i × PCI_t)
                         + POI_FE + Month_FE + controls + ε_it
   ```
3. Key coefficient: **β₃** (interaction term)
   - If β₃ < 0: Misalignment hurts performance MORE when partisan conflict is high
   - This supports the political consumerism mechanism

**Identification logic**:
- PCI varies at the national level over time, orthogonal to store-level characteristics
- Misalignment varies cross-sectionally across stores
- The interaction exploits both dimensions of variation
- Alternative explanations (demographics, income, etc.) would need to explain why their effects vary with PCI—implausible

**Robustness checks**:
- Lagged PCI (1-2 months) to allow for consumer response time
- Exclude months with major confounding events (e.g., holidays, natural disasters)
- Heterogeneity by industry (politically salient industries should show stronger effects)
- Placebo test: Interaction with unrelated time series (e.g., weather index)

**Expected results**:
- Main effect (β₁): Misalignment negatively associated with performance
- Interaction (β₃): Negative—the misalignment penalty is amplified during high-PCI periods
- This pattern is consistent with political consumerism and difficult to explain with confounds

---

## Data Pipeline

```
Phase 1: POI Lifecycle (current job)
├── Count opens/closes during measurement period
├── Identify which categories have most opens/closes
└── Output: poi_opened_2019_2024.parquet, poi_closed_all.parquet

Phase 2: Merge Visitor Ideology
├── Load Advan monthly patterns with visitor_home_cbgs
├── Merge with CBG-level election results
├── Compute visitor_republican_share per POI × month
└── Output: poi_visitor_ideology.parquet

Phase 3: Merge Firm Ideology (if available)
├── Link POIs to brands/companies
├── Match to Politics at Work using company names
├── Compute firm_employee_republican_share
└── Output: poi_firm_ideology.parquet

Phase 4: Merge Performance
├── Link to SafeGraph Spend (revenue, transactions)
├── Alternatively: Advan normalized visits
└── Output: poi_performance_panel.parquet

Phase 5: Merge Time-Varying Moderators
├── Load Partisan Conflict Index (partisan_conflict_index.csv)
├── Standardize PCI (z-score or percentile)
├── Merge to panel by year-month
├── Compute lagged versions (PCI_t-1, PCI_t-2) for robustness
└── Output: poi_panel_with_moderators.parquet

Phase 6: Analysis
├── Survival analysis for closures (Analysis 1)
├── Location choice models for openings (Analysis 2)
├── Panel regressions for spending/traffic (Analysis 3)
├── COVID natural experiment (Analysis 4)
└── Partisan climate moderation / interaction models (Analysis 5)
```

---

## Questions to Resolve

1. **Spend data coverage**: SafeGraph Spend only goes to 2021. Is that sufficient or do we need to rely on foot traffic for 2022-2024?

2. **Firm-level ideology**: What proportion of POIs can we match to Politics at Work? Do we have brand → parent company mappings?

3. **Causality**: What's our identification strategy beyond correlations?
   - Option A: Within-brand variation (some stores in aligned areas, others not)
   - Option B: New store openings (did the firm have a choice?)
   - Option C: COVID shock as exogenous variation
   - Option D: Boundary discontinuity (stores near county/district boundaries)
   - **Option E: Partisan climate moderation (PCI interaction)** ← Primary strategy
     - If alignment effects are causal (political consumerism), they should be amplified when partisan conflict is salient
     - PCI provides exogenous time-varying activation of partisan identity
     - Confounds (demographics, income) cannot explain why their effects would vary with PCI
     - This is analogous to using "salience shocks" in other behavioral economics contexts

4. **Dewey additional data**: Check if there are more recent spending data releases or POI-level consumer edge data.

---

## Next Steps

1. [ ] Review POI lifecycle results when job completes
2. [ ] Explore Dewey for additional data sources
3. [ ] Check Politics at Work coverage for major retail brands
4. [x] Decide on primary identification strategy → **PCI interaction (Option E)**
5. [ ] Begin data pipeline construction
6. [x] Download Partisan Conflict Index data → **Done** (partisan_conflict_index.csv)
7. [ ] Visualize PCI over sample period (2019-2024) to identify high/low conflict periods
8. [ ] Literature review: Papers using time-varying salience/attention as identification
