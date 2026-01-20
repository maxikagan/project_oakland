#!/usr/bin/env python3
"""
Fix labeling errors v2 and train logit model.
- Fix multi-location businesses (same parent company = match)
- Add string normalization features
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import pickle

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
SAMPLE_DIR = PROJECT_DIR / "outputs" / "singleton_matching" / "training_samples"

# IDs that should be NON-MATCHES (from our review)
FALSE_POSITIVES = [
    4,    # Columbus Eye Surgery Center → Columbus Specialty Surgery Center LLC
    144,  # Ohio Department of Education → Ohio Department of Higher Education
    207,  # Highland Elementary School → Highland Park Elementary School
    227,  # St John's Lutheran Church → St Johns Lutheran School
    278,  # Bexley United Methodist Preschool → Bexley United Methodist Church
    350,  # Nail Spa → Eco Nail Spa (generic vs specific)
    423,  # The Pilates Studio → Pilates Studio Brasil
    540,  # St John Lutheran Church → St Paul's Lutheran Church
    555,  # St Paul Lutheran Church → St. Paul Catholic Church
    638,  # Papa Joes Pizza → Joe's Pizza
    771,  # Columbus Metropolitan Library Whitehall Branch → Northside Branch
    878,  # Trinity Lutheran School → Trinity Lutheran High School
    915,  # American Gas Company → American Gas Association
    607,  # K & D Plumbing → D&D Plumbing
]

# IDs that should be MATCHES (multi-location same parent company)
FALSE_NEGATIVES_TO_FIX = [
    # Germain dealerships - all same parent company
    208,  # Germain Motor Company → Germain Honda of Dublin
    486,  # Germain Honda of Dublin → Germain Volkswagen Of Columbus
    530,  # Germain Hyundai of Columbus → Germain Kia of Columbus
    670,  # Germain Lexus of Easton → Germain Lexus of Dublin
    # BMW Financial Services locations - same parent
    522,  # BMW Financial Services → BMW Financial Services (South Africa)
    761,  # BMW Financial Services → BMW Group Financial Services Australia
    # Petland locations
    # Franklin University - keep as non-match (Switzerland is different institution)
    # Kompass Advisors - different state office, questionable
]


def normalize_name(name: str) -> str:
    """Normalize company name by removing punctuation, suffixes, and titles."""
    if not name:
        return ""

    s = name.lower()

    # Remove common suffixes
    suffixes = [
        r'\s+inc\.?$', r'\s+llc\.?$', r'\s+corp\.?$', r'\s+co\.?$',
        r'\s+ltd\.?$', r'\s+llp\.?$', r'\s+pllc\.?$', r'\s+pc\.?$',
        r'\s+incorporated$', r'\s+corporation$', r'\s+company$',
        r'\s+limited$', r'\s+the$', r'^the\s+',
    ]
    for suffix in suffixes:
        s = re.sub(suffix, '', s, flags=re.IGNORECASE)

    # Normalize professional titles
    title_patterns = [
        (r'd\s*\.?\s*d\s*\.?\s*s\.?', 'dds'),  # D.D.S., D D S, DDS
        (r'm\s*\.?\s*d\.?', 'md'),              # M.D., MD
        (r'o\s*\.?\s*d\.?', 'od'),              # O.D., OD (optometrist)
        (r'd\s*\.?\s*o\.?', 'do'),              # D.O., DO
        (r'ph\s*\.?\s*d\.?', 'phd'),            # Ph.D., PhD
    ]
    for pattern, replacement in title_patterns:
        s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

    # Remove all punctuation
    s = re.sub(r'[^\w\s]', ' ', s)

    # Normalize whitespace
    s = ' '.join(s.split())

    return s.strip()


def normalized_jaro_winkler(a: str, b: str) -> float:
    """Jaro-Winkler on normalized names."""
    import jellyfish
    a_norm = normalize_name(a)
    b_norm = normalize_name(b)
    if not a_norm or not b_norm:
        return 0.0
    return jellyfish.jaro_winkler_similarity(a_norm, b_norm)


def main():
    print("=" * 70)
    print("Fix Labels v2 and Train Logit Model")
    print("=" * 70)

    # Load original labeled data (before v1 fixes)
    df = pd.read_csv(SAMPLE_DIR / "columbus_oh_sample_labeled.csv")
    print(f"\nLoaded {len(df)} labeled pairs")
    print(f"Original: {df['label'].sum()} matches, {(df['label']==0).sum()} non-matches")

    # Apply fixes: set false positives to 0
    fp_fixed = 0
    for sample_id in FALSE_POSITIVES:
        mask = df['sample_id'] == sample_id
        if mask.any() and df.loc[mask, 'label'].values[0] == 1:
            df.loc[mask, 'label'] = 0
            fp_fixed += 1
    print(f"Fixed {fp_fixed} false positives → 0")

    # Apply fixes: set false negatives to 1 (multi-location same parent)
    fn_fixed = 0
    for sample_id in FALSE_NEGATIVES_TO_FIX:
        mask = df['sample_id'] == sample_id
        if mask.any() and df.loc[mask, 'label'].values[0] == 0:
            df.loc[mask, 'label'] = 1
            fn_fixed += 1
    print(f"Fixed {fn_fixed} false negatives → 1 (multi-location businesses)")

    print(f"After fixes: {df['label'].sum()} matches, {(df['label']==0).sum()} non-matches")

    # Compute normalized Jaro-Winkler
    print("\nComputing normalized Jaro-Winkler scores...")
    df['jaro_winkler_norm'] = df.apply(
        lambda r: normalized_jaro_winkler(r['location_name'], r['company_name']),
        axis=1
    )

    # Show improvement from normalization
    print("\nNormalization effect on some false negatives:")
    check_ids = [15, 100, 108]  # David Reich, Zahara, Dinapoli
    for sid in check_ids:
        row = df[df['sample_id'] == sid]
        if len(row) > 0:
            r = row.iloc[0]
            print(f"  '{r['location_name']}' → '{r['company_name']}'")
            print(f"    Original JW: {r['jaro_winkler']:.3f}, Normalized JW: {r['jaro_winkler_norm']:.3f}")

    # Save corrected labels
    corrected_file = SAMPLE_DIR / "columbus_oh_sample_labeled_v2.csv"
    df.to_csv(corrected_file, index=False)
    print(f"\nSaved corrected labels to {corrected_file}")

    # Train model with original features
    print("\n" + "=" * 70)
    print("Training Model A: Original Features")
    print("=" * 70)

    feature_cols_a = ['cos_sim', 'jaro_winkler', 'token_jaccard', 'contains_match']
    X_a = df[feature_cols_a].copy()
    X_a['contains_match'] = X_a['contains_match'].astype(int)
    y = df['label']

    model_a = LogisticRegression(random_state=42, max_iter=1000)
    model_a.fit(X_a, y)

    y_prob_a = model_a.predict_proba(X_a)[:, 1]
    auc_a = roc_auc_score(y, y_prob_a)
    print(f"AUC-ROC: {auc_a:.4f}")

    # Train model with normalized JW
    print("\n" + "=" * 70)
    print("Training Model B: With Normalized Jaro-Winkler")
    print("=" * 70)

    feature_cols_b = ['cos_sim', 'jaro_winkler', 'jaro_winkler_norm', 'token_jaccard', 'contains_match']
    X_b = df[feature_cols_b].copy()
    X_b['contains_match'] = X_b['contains_match'].astype(int)

    model_b = LogisticRegression(random_state=42, max_iter=1000)
    model_b.fit(X_b, y)

    y_prob_b = model_b.predict_proba(X_b)[:, 1]
    auc_b = roc_auc_score(y, y_prob_b)
    print(f"AUC-ROC: {auc_b:.4f}")

    print("\nModel B Coefficients:")
    for feat, coef in zip(feature_cols_b, model_b.coef_[0]):
        print(f"  {feat}: {coef:.4f}")
    print(f"  intercept: {model_b.intercept_[0]:.4f}")

    # Compare models
    print("\n" + "=" * 70)
    print("Model Comparison at Threshold 0.5")
    print("=" * 70)

    for name, y_prob in [("Model A (original)", y_prob_a), ("Model B (+ normalized JW)", y_prob_b)]:
        y_pred = (y_prob >= 0.5).astype(int)
        tp = ((y_pred == 1) & (y == 1)).sum()
        fp = ((y_pred == 1) & (y == 0)).sum()
        fn = ((y_pred == 0) & (y == 1)).sum()
        tn = ((y_pred == 0) & (y == 0)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        print(f"\n{name}:")
        print(f"  Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
        print(f"  TP={tp}, FP={fp}, FN={fn}, TN={tn}")

    # Use model B as final model
    print("\n" + "=" * 70)
    print("Threshold Analysis (Model B)")
    print("=" * 70)

    print("\nThreshold | Precision | Recall | F1    | Predicted Matches")
    print("-" * 60)

    for thresh in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
        pred_at_thresh = (y_prob_b >= thresh).astype(int)
        tp = ((pred_at_thresh == 1) & (y == 1)).sum()
        fp = ((pred_at_thresh == 1) & (y == 0)).sum()
        fn = ((pred_at_thresh == 0) & (y == 1)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        n_matches = pred_at_thresh.sum()

        print(f"  {thresh:.1f}     |   {precision:.3f}   |  {recall:.3f} | {f1:.3f} |     {n_matches}")

    # Save final model
    model_file = SAMPLE_DIR / "columbus_oh_logit_model_v2.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump({
            'model': model_b,
            'features': feature_cols_b,
            'normalize_func': 'normalize_name'
        }, f)
    print(f"\nSaved model to {model_file}")

    # Add predictions
    df['pred_prob_v2'] = y_prob_b
    df['pred_label_v2'] = (y_prob_b >= 0.5).astype(int)

    # Error analysis
    print("\n" + "=" * 70)
    print("Remaining Errors (Model B, threshold 0.5)")
    print("=" * 70)

    fp = df[(df['pred_label_v2'] == 1) & (df['label'] == 0)]
    print(f"\nFalse Positives ({len(fp)}):")
    for _, r in fp.head(10).iterrows():
        print(f"  [{r['pred_prob_v2']:.3f}] '{r['location_name']}' → '{r['company_name']}'")

    fn = df[(df['pred_label_v2'] == 0) & (df['label'] == 1)]
    print(f"\nFalse Negatives ({len(fn)}):")
    for _, r in fn.head(10).iterrows():
        print(f"  [{r['pred_prob_v2']:.3f}] '{r['location_name']}' → '{r['company_name']}'")

    # Save predictions
    pred_file = SAMPLE_DIR / "columbus_oh_sample_with_predictions_v2.csv"
    df.to_csv(pred_file, index=False)
    print(f"\nSaved predictions to {pred_file}")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
