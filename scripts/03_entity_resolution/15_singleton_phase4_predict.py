#!/usr/bin/env python3
"""
Phase 4: Apply trained model to predict matches for all candidate pairs.

Outputs final singleton crosswalk with match probabilities.

Usage: python 15_singleton_phase4_predict.py --msa columbus_oh --threshold 0.4
"""

import argparse
import json
import re
import pickle
from pathlib import Path

import pandas as pd
import numpy as np
import jellyfish

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
CANDIDATE_DIR = PROJECT_DIR / "outputs" / "singleton_matching"
MODEL_DIR = CANDIDATE_DIR / "training_samples"  # Using training_samples where model is saved
OUTPUT_DIR = CANDIDATE_DIR / "crosswalks"
BRAND_MATCHES_FILE = PROJECT_DIR / "outputs" / "entity_resolution" / "brand_matches_validated.parquet"

FEATURES = ['cos_sim', 'jaro_winkler', 'jaro_winkler_norm', 'token_jaccard', 'contains_match']


def normalize_name(name: str) -> str:
    """Normalize company name by removing punctuation, suffixes, and titles."""
    if not name:
        return ""

    s = name.lower()

    suffixes = [
        r'\s+inc\.?$', r'\s+llc\.?$', r'\s+corp\.?$', r'\s+co\.?$',
        r'\s+ltd\.?$', r'\s+llp\.?$', r'\s+pllc\.?$', r'\s+pc\.?$',
        r'\s+incorporated$', r'\s+corporation$', r'\s+company$',
        r'\s+limited$', r'\s+the$', r'^the\s+',
    ]
    for suffix in suffixes:
        s = re.sub(suffix, '', s, flags=re.IGNORECASE)

    title_patterns = [
        (r'd\s*\.?\s*d\s*\.?\s*s\.?', 'dds'),
        (r'm\s*\.?\s*d\.?', 'md'),
        (r'o\s*\.?\s*d\.?', 'od'),
        (r'd\s*\.?\s*o\.?', 'do'),
        (r'ph\s*\.?\s*d\.?', 'phd'),
    ]
    for pattern, replacement in title_patterns:
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

    s = re.sub(r'[^\w\s]', ' ', s)
    s = ' '.join(s.split())

    return s.strip()


def normalized_jaro_winkler(a: str, b: str) -> float:
    """Jaro-Winkler on normalized names."""
    a_norm = normalize_name(a)
    b_norm = normalize_name(b)
    if not a_norm or not b_norm:
        return 0.0
    return jellyfish.jaro_winkler_similarity(a_norm, b_norm)


def load_brand_rcids() -> set:
    """Load rcids from branded POI matches to flag likely uncoded brands."""
    if not BRAND_MATCHES_FILE.exists():
        print("  Warning: Brand matches file not found, skipping uncoded brand flagging")
        return set()

    brands = pd.read_parquet(BRAND_MATCHES_FILE, columns=['rcid'])
    return set(brands['rcid'].unique())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--msa', required=True, help='MSA name (e.g., columbus_oh)')
    parser.add_argument('--threshold', type=float, default=None,
                        help='Match probability threshold (default: use optimal from training)')
    args = parser.parse_args()

    msa = args.msa

    print("=" * 70)
    print(f"Phase 4: Predict Matches - {msa}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load model
    print(f"\n[1] Loading model...")
    model_file = MODEL_DIR / f"{msa}_logit_model_v2.pkl"

    if not model_file.exists():
        raise FileNotFoundError(f"Model not found: {model_file}")

    with open(model_file, 'rb') as f:
        model_data = pickle.load(f)
    model = model_data['model']
    feature_cols = model_data['features']
    print(f"  Loaded model from {model_file.name}")
    print(f"  Features: {feature_cols}")

    # Get threshold (default 0.4 for best F1)
    threshold = args.threshold if args.threshold is not None else 0.4
    print(f"  Using threshold: {threshold:.3f}")

    # Load candidate pairs
    print(f"\n[2] Loading candidate pairs...")
    candidate_file = CANDIDATE_DIR / f"{msa}_candidate_pairs.parquet"
    if not candidate_file.exists():
        raise FileNotFoundError(f"Candidates not found: {candidate_file}")

    candidates = pd.read_parquet(candidate_file)
    print(f"  Loaded {len(candidates):,} candidate pairs")

    # Load brand rcids for flagging
    print(f"\n[3] Loading brand rcids for flagging...")
    brand_rcids = load_brand_rcids()
    print(f"  Loaded {len(brand_rcids):,} brand rcids")

    # Compute normalized Jaro-Winkler feature
    print(f"\n[4] Computing normalized Jaro-Winkler scores...")
    candidates['jaro_winkler_norm'] = candidates.apply(
        lambda r: normalized_jaro_winkler(r['location_name'], r['company_name']),
        axis=1
    )

    # Prepare features
    print(f"\n[5] Predicting match probabilities...")
    X = candidates[feature_cols].copy()
    X['contains_match'] = X['contains_match'].astype(int)

    # Predict
    probs = model.predict_proba(X)[:, 1]
    candidates['match_probability'] = probs

    # Apply threshold
    candidates['is_predicted_match'] = probs >= threshold

    n_matches = candidates['is_predicted_match'].sum()
    print(f"  Predicted matches: {n_matches:,} ({100*n_matches/len(candidates):.2f}%)")

    # Keep only best match per POI name (highest probability)
    print(f"\n[6] Selecting best match per POI name...")
    matches = candidates[candidates['is_predicted_match']].copy()

    if len(matches) > 0:
        # Sort by probability descending, keep first (best) per POI name
        matches = matches.sort_values('match_probability', ascending=False)
        best_matches = matches.groupby('location_name').first().reset_index()
        print(f"  Unique POI names with matches: {len(best_matches):,}")
    else:
        best_matches = pd.DataFrame()
        print("  No matches found above threshold!")

    # Flag likely uncoded brands
    if len(best_matches) > 0 and len(brand_rcids) > 0:
        print(f"\n[7] Flagging likely uncoded brands...")
        # Extract first rcid from rcids list
        best_matches['primary_rcid'] = best_matches['rcids'].apply(lambda x: x[0] if x else None)
        best_matches['is_likely_uncoded_brand'] = best_matches['primary_rcid'].isin(brand_rcids)
        n_uncoded = best_matches['is_likely_uncoded_brand'].sum()
        print(f"  Likely uncoded brands: {n_uncoded:,}")
    else:
        if len(best_matches) > 0:
            best_matches['is_likely_uncoded_brand'] = False

    # Expand to all placekeys
    print(f"\n[8] Expanding to all placekeys...")
    if len(best_matches) > 0:
        expanded_rows = []
        for _, row in best_matches.iterrows():
            placekeys = row['placekeys']
            for pk in placekeys:
                expanded_rows.append({
                    'placekey': pk,
                    'location_name': row['location_name'],
                    'rcid': row['primary_rcid'] if 'primary_rcid' in row else row['rcids'][0],
                    'company_name': row['company_name'],
                    'match_probability': row['match_probability'],
                    'cos_sim': row['cos_sim'],
                    'jaro_winkler': row['jaro_winkler'],
                    'is_likely_uncoded_brand': row.get('is_likely_uncoded_brand', False),
                    'msa': msa,
                })

        crosswalk = pd.DataFrame(expanded_rows)
        print(f"  Total POI-company links: {len(crosswalk):,}")
    else:
        crosswalk = pd.DataFrame()

    # Save outputs
    print(f"\n[9] Saving outputs...")

    # Full crosswalk
    crosswalk_file = OUTPUT_DIR / f"{msa}_singleton_crosswalk.parquet"
    if len(crosswalk) > 0:
        crosswalk.to_parquet(crosswalk_file, index=False)
        print(f"  Crosswalk: {crosswalk_file}")
    else:
        print("  No crosswalk to save (no matches)")

    # Summary statistics
    summary = {
        'msa': msa,
        'threshold': threshold,
        'total_candidates': len(candidates),
        'predicted_matches': int(n_matches),
        'unique_poi_names_matched': len(best_matches) if len(best_matches) > 0 else 0,
        'total_pois_matched': len(crosswalk) if len(crosswalk) > 0 else 0,
        'likely_uncoded_brands': int(best_matches['is_likely_uncoded_brand'].sum()) if len(best_matches) > 0 and 'is_likely_uncoded_brand' in best_matches.columns else 0,
    }

    summary_file = OUTPUT_DIR / f"{msa}_match_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary: {summary_file}")

    # Print summary
    print(f"\n[10] Match summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    if len(crosswalk) > 0:
        print(f"\n[11] Sample matches:")
        sample = crosswalk.nlargest(15, 'match_probability')[
            ['location_name', 'company_name', 'match_probability', 'is_likely_uncoded_brand']
        ]
        print(sample.to_string(index=False))

    print("\n" + "=" * 70)
    print("Phase 4 complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
