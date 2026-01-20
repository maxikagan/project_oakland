#!/usr/bin/env python3
"""
Label POI-company name pairs as matches (1) or non-matches (0).

Uses deterministic string matching rules rather than ML to ensure reproducibility.
"""

import pandas as pd
import re
from pathlib import Path


def normalize_name(name: str) -> str:
    """Normalize business name for comparison."""
    if pd.isna(name):
        return ""

    name = str(name).lower().strip()

    # Remove common suffixes
    suffixes = [
        r'\b(inc|incorporated|corp|corporation|co|company|llc|llp|ltd|limited)\b\.?',
        r'\b(pllc|pc|plc|pa|psc)\b\.?',
        r'\b(dba|d/b/a)\b',
        r',?\s*(the)$',
        r'^(the)\s+',
    ]
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)

    # Normalize punctuation and whitespace
    name = re.sub(r'[,."\'`]', '', name)
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\s*&\s*', ' and ', name)
    name = re.sub(r'\s*-\s*', ' ', name)

    # Normalize professional titles
    name = re.sub(r'\bd\s*d\s*s\b', 'dds', name)
    name = re.sub(r'\bm\s*d\b', 'md', name)
    name = re.sub(r'\bd\s*o\b', 'do', name)
    name = re.sub(r'\bd\s*p\s*m\b', 'dpm', name)
    name = re.sub(r'\bo\s*d\b', 'od', name)

    return name.strip()


def get_core_tokens(name: str) -> set:
    """Extract meaningful tokens from a name."""
    normalized = normalize_name(name)

    # Remove stopwords
    stopwords = {'the', 'a', 'an', 'of', 'and', 'in', 'at', 'on', 'for', 'to', 'by'}
    tokens = set(normalized.split()) - stopwords

    return tokens


def is_generic_name(name: str) -> bool:
    """Check if a name is too generic to match reliably."""
    normalized = normalize_name(name)
    tokens = normalized.split()

    generic_patterns = [
        r'^(funeral home|pizza|restaurant|bar|grill|salon|spa|clinic|church)$',
        r'^(auto (repair|body|glass|service))$',
        r'^(cleaning service|lawn care|landscaping)$',
        r'^(insurance|real estate|law office)$',
        r'^(medical center|health center|wellness center)$',
    ]

    for pattern in generic_patterns:
        if re.match(pattern, normalized):
            return True

    # Very short names are often generic
    if len(tokens) <= 1 and len(normalized) < 10:
        return True

    return False


def label_pair(location_name: str, company_name: str, cos_sim: float,
               jaro_winkler: float, token_jaccard: float, contains_match: bool) -> int:
    """
    Determine if POI name and company name refer to the same entity.

    Returns 1 for match, 0 for non-match.
    """
    norm_loc = normalize_name(location_name)
    norm_comp = normalize_name(company_name)

    # Exact match after normalization
    if norm_loc == norm_comp:
        return 1

    # Check for generic names - be conservative
    if is_generic_name(location_name) or is_generic_name(company_name):
        # Only match if very high similarity
        if cos_sim >= 0.95 and jaro_winkler >= 0.95:
            return 1
        return 0

    # High confidence matches
    if cos_sim >= 0.90 and jaro_winkler >= 0.90:
        return 1

    # Token-based analysis
    loc_tokens = get_core_tokens(location_name)
    comp_tokens = get_core_tokens(company_name)

    if not loc_tokens or not comp_tokens:
        return 0

    # Check for substring containment (one fully contains the other)
    if norm_loc in norm_comp or norm_comp in norm_loc:
        # But watch out for cases like "Pizza" in "Joe's Pizza"
        shorter = norm_loc if len(norm_loc) < len(norm_comp) else norm_comp
        if len(shorter) >= 10:  # Substantial overlap
            return 1

    # Token overlap analysis
    intersection = loc_tokens & comp_tokens
    union = loc_tokens | comp_tokens

    if len(union) > 0:
        jaccard = len(intersection) / len(union)

        # High token overlap with decent similarity scores
        if jaccard >= 0.6 and cos_sim >= 0.75 and jaro_winkler >= 0.75:
            return 1

    # Check for key discriminating words that suggest different entities
    discriminating_words = {
        'eye', 'specialty', 'wings', 'brew', 'admiral', 'american',
        'discount', 'guardian', 'executive', 'capital', 'central', 'northwest',
        'north', 'south', 'east', 'west', 'wilson', 'chicago', 'columbus',
        'radiant', 'anewu', 'fresh', 'top', 'home'
    }

    loc_disc = loc_tokens & discriminating_words
    comp_disc = comp_tokens & discriminating_words

    # If they have different discriminating words, likely different businesses
    if loc_disc and comp_disc and loc_disc != comp_disc:
        # Extra check - if similarity is very high, might still be same
        if cos_sim < 0.85:
            return 0

    # Medium-high similarity with contains_match flag
    if contains_match and cos_sim >= 0.80 and jaro_winkler >= 0.80:
        # Additional check: ensure substantial overlap
        if token_jaccard >= 0.4:
            return 1

    # Professional names (doctors, lawyers)
    professional_pattern = r'\b(dds|md|do|dpm|od|esq|cpa|phd)\b'
    if re.search(professional_pattern, norm_loc) or re.search(professional_pattern, norm_comp):
        # For professionals, check if the personal name matches
        # Extract name part (before title)
        loc_name_part = re.sub(professional_pattern, '', norm_loc).strip()
        comp_name_part = re.sub(professional_pattern, '', norm_comp).strip()

        if loc_name_part and comp_name_part:
            # Check if names are similar
            loc_name_tokens = set(loc_name_part.split())
            comp_name_tokens = set(comp_name_part.split())

            if len(loc_name_tokens & comp_name_tokens) >= 2:
                return 1

    # Check for organization type mismatches
    org_types = {
        'school': ['high school', 'middle school', 'elementary', 'academy', 'university'],
        'medical': ['hospital', 'clinic', 'medical center', 'surgery center', 'health'],
        'food': ['pizza', 'grill', 'restaurant', 'cafe', 'bar', 'wings', 'brew'],
        'auto': ['auto glass', 'auto body', 'auto repair', 'car wash'],
    }

    for category, keywords in org_types.items():
        loc_in_cat = any(kw in norm_loc for kw in keywords)
        comp_in_cat = any(kw in norm_comp for kw in keywords)

        if loc_in_cat and comp_in_cat:
            # Same category - check for specific mismatches
            loc_specific = [kw for kw in keywords if kw in norm_loc]
            comp_specific = [kw for kw in keywords if kw in norm_comp]

            if loc_specific != comp_specific and cos_sim < 0.90:
                return 0

    # Default: use combined score threshold
    combined_score = (cos_sim * 0.4 + jaro_winkler * 0.4 + token_jaccard * 0.2)

    if combined_score >= 0.85:
        return 1

    return 0


def main():
    input_path = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/singleton_matching/training_samples/columbus_oh_sample_for_labeling.csv")
    output_csv = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/singleton_matching/training_samples/columbus_oh_sample_labeled.csv")
    output_parquet = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology/outputs/singleton_matching/training_samples/columbus_oh_sample_labeled.parquet")

    print(f"Reading input from {input_path}")
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} pairs")

    # Apply labeling
    print("Labeling pairs...")
    df['label'] = df.apply(
        lambda row: label_pair(
            row['location_name'],
            row['company_name'],
            row['cos_sim'],
            row['jaro_winkler'],
            row['token_jaccard'],
            row['contains_match']
        ),
        axis=1
    )

    # Save outputs
    print(f"Saving CSV to {output_csv}")
    df.to_csv(output_csv, index=False)

    print(f"Saving Parquet to {output_parquet}")
    df.to_parquet(output_parquet, index=False)

    # Report statistics
    print("\n" + "="*60)
    print("LABELING RESULTS")
    print("="*60)

    total_matches = df['label'].sum()
    total_nonmatches = len(df) - total_matches
    print(f"\nTotal matches (label=1): {total_matches}")
    print(f"Total non-matches (label=0): {total_nonmatches}")
    print(f"Match rate: {total_matches/len(df)*100:.1f}%")

    print("\n" + "-"*60)
    print("Match rate by stratum:")
    print("-"*60)

    stratum_stats = df.groupby('stratum').agg(
        count=('label', 'count'),
        matches=('label', 'sum'),
        match_rate=('label', 'mean')
    ).round(3)

    # Order strata
    stratum_order = ['high', 'medium_high', 'medium', 'low', 'very_low']
    stratum_stats = stratum_stats.reindex(stratum_order)

    for stratum in stratum_order:
        if stratum in stratum_stats.index:
            row = stratum_stats.loc[stratum]
            print(f"  {stratum:12s}: {int(row['matches']):3d}/{int(row['count']):3d} matches ({row['match_rate']*100:5.1f}%)")

    print("\n" + "-"*60)
    print("Example borderline MATCHES (label=1 with lower similarity):")
    print("-"*60)

    borderline_matches = df[(df['label'] == 1) & (df['cos_sim'] < 0.90)].head(10)
    for _, row in borderline_matches.iterrows():
        print(f"  '{row['location_name']}' vs '{row['company_name']}'")
        print(f"    cos_sim={row['cos_sim']:.3f}, jaro={row['jaro_winkler']:.3f}, stratum={row['stratum']}")

    print("\n" + "-"*60)
    print("Example borderline NON-MATCHES (label=0 with higher similarity):")
    print("-"*60)

    borderline_nonmatches = df[(df['label'] == 0) & (df['cos_sim'] >= 0.75)].head(10)
    for _, row in borderline_nonmatches.iterrows():
        print(f"  '{row['location_name']}' vs '{row['company_name']}'")
        print(f"    cos_sim={row['cos_sim']:.3f}, jaro={row['jaro_winkler']:.3f}, stratum={row['stratum']}")

    print("\n" + "="*60)
    print("Labeling complete!")
    print("="*60)


if __name__ == "__main__":
    main()
