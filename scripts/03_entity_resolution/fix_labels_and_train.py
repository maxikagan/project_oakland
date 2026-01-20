#!/usr/bin/env python3
"""
Fix labeling errors and train logit model for singleton matching.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import pickle

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
SAMPLE_DIR = PROJECT_DIR / "outputs" / "singleton_matching" / "training_samples"

# IDs that were incorrectly labeled as matches (should be 0)
FALSE_POSITIVES = [
    4,    # Columbus Eye Surgery Center → Columbus Specialty Surgery Center LLC
    144,  # Ohio Department of Education → Ohio Department of Higher Education
    207,  # Highland Elementary School → Highland Park Elementary School
    227,  # St John's Lutheran Church → St Johns Lutheran School
    278,  # Bexley United Methodist Preschool → Bexley United Methodist Church
    285,  # Franklin University → Franklin University Switzerland
    350,  # Nail Spa → Eco Nail Spa
    106,  # Kompass Advisors → Kompass Advisors of Florida LLC (different state)
    423,  # The Pilates Studio → Pilates Studio Brasil
    492,  # Oakland Park Alternative Elementary → Oakland Park Elementary School
    522,  # BMW Financial Services → BMW Financial Services (South Africa)
    540,  # St John Lutheran Church → St Paul's Lutheran Church
    555,  # St Paul Lutheran Church → St. Paul Catholic Church
    638,  # Papa Joes Pizza → Joe's Pizza
    761,  # BMW Financial Services → BMW Group Financial Services Australia
    771,  # Columbus Metropolitan Library Whitehall Branch → Northside Branch
    878,  # Trinity Lutheran School → Trinity Lutheran High School
    915,  # American Gas Company → American Gas Association
    607,  # K & D Plumbing → D&D Plumbing
    137,  # Quality Pools Inc → Quality Swimming Pools, Inc. (questionable)
    392,  # Fit Skin Solutions → Skin Solutions
    554,  # Marble & Granite Works → Marble Works
    650,  # Capstone Wealth Partners → Capstone Partners LLC
    735,  # Wesley Glen The Health Center → Wesley Health Care Center, Inc.
    939,  # Central Ohio Exteriors → Ohio Exteriors, LLC
]

def main():
    print("=" * 70)
    print("Fix Labels and Train Logit Model")
    print("=" * 70)

    # Load labeled data
    df = pd.read_csv(SAMPLE_DIR / "columbus_oh_sample_labeled.csv")
    print(f"\nLoaded {len(df)} labeled pairs")
    print(f"Original: {df['label'].sum()} matches, {(df['label']==0).sum()} non-matches")

    # Fix labels
    print(f"\nFixing {len(FALSE_POSITIVES)} false positive labels...")
    fixes_made = 0
    for sample_id in FALSE_POSITIVES:
        mask = df['sample_id'] == sample_id
        if mask.any() and df.loc[mask, 'label'].values[0] == 1:
            df.loc[mask, 'label'] = 0
            fixes_made += 1

    print(f"Fixed {fixes_made} labels")
    print(f"After fix: {df['label'].sum()} matches, {(df['label']==0).sum()} non-matches")

    # Save corrected labels
    corrected_file = SAMPLE_DIR / "columbus_oh_sample_labeled_corrected.csv"
    df.to_csv(corrected_file, index=False)
    print(f"Saved corrected labels to {corrected_file}")

    # Prepare features for model
    print("\n" + "=" * 70)
    print("Training Logistic Regression Model")
    print("=" * 70)

    feature_cols = ['cos_sim', 'jaro_winkler', 'token_jaccard', 'contains_match']
    X = df[feature_cols].copy()
    X['contains_match'] = X['contains_match'].astype(int)
    y = df['label']

    print(f"\nFeatures: {feature_cols}")
    print(f"Training samples: {len(X)}")
    print(f"Positive rate: {y.mean():.1%}")

    # Train model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X, y)

    # Model coefficients
    print("\nModel Coefficients:")
    for feat, coef in zip(feature_cols, model.coef_[0]):
        print(f"  {feat}: {coef:.4f}")
    print(f"  intercept: {model.intercept_[0]:.4f}")

    # Predictions and evaluation
    y_pred = model.predict(X)
    y_prob = model.predict_proba(X)[:, 1]

    print("\nTraining Set Performance:")
    print(classification_report(y, y_pred, target_names=['Non-match', 'Match']))

    print("Confusion Matrix:")
    cm = confusion_matrix(y, y_pred)
    print(f"  TN={cm[0,0]:4d}  FP={cm[0,1]:4d}")
    print(f"  FN={cm[1,0]:4d}  TP={cm[1,1]:4d}")

    auc = roc_auc_score(y, y_prob)
    print(f"\nAUC-ROC: {auc:.4f}")

    # Save model
    model_file = SAMPLE_DIR / "columbus_oh_logit_model.pkl"
    with open(model_file, 'wb') as f:
        pickle.dump({'model': model, 'features': feature_cols}, f)
    print(f"\nSaved model to {model_file}")

    # Add predictions to dataframe
    df['pred_prob'] = y_prob
    df['pred_label'] = y_pred

    # Analyze errors
    print("\n" + "=" * 70)
    print("Error Analysis")
    print("=" * 70)

    # False positives (predicted match, actually non-match)
    fp = df[(df['pred_label'] == 1) & (df['label'] == 0)]
    print(f"\nFalse Positives ({len(fp)}):")
    if len(fp) > 0:
        for _, r in fp.head(10).iterrows():
            print(f"  [{r['pred_prob']:.3f}] '{r['location_name']}' → '{r['company_name']}'")

    # False negatives (predicted non-match, actually match)
    fn = df[(df['pred_label'] == 0) & (df['label'] == 1)]
    print(f"\nFalse Negatives ({len(fn)}):")
    if len(fn) > 0:
        for _, r in fn.head(10).iterrows():
            print(f"  [{r['pred_prob']:.3f}] '{r['location_name']}' → '{r['company_name']}'")

    # Threshold analysis
    print("\n" + "=" * 70)
    print("Threshold Analysis")
    print("=" * 70)

    thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    print("\nThreshold | Precision | Recall | F1    | Predicted Matches")
    print("-" * 60)

    for thresh in thresholds:
        pred_at_thresh = (y_prob >= thresh).astype(int)
        tp = ((pred_at_thresh == 1) & (y == 1)).sum()
        fp = ((pred_at_thresh == 1) & (y == 0)).sum()
        fn = ((pred_at_thresh == 0) & (y == 1)).sum()

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        n_matches = pred_at_thresh.sum()

        print(f"  {thresh:.1f}     |   {precision:.3f}   |  {recall:.3f} | {f1:.3f} |     {n_matches}")

    # Save predictions
    pred_file = SAMPLE_DIR / "columbus_oh_sample_with_predictions.csv"
    df.to_csv(pred_file, index=False)
    print(f"\nSaved predictions to {pred_file}")

    # Borderline cases around 0.5 threshold
    print("\n" + "=" * 70)
    print("Borderline Cases (pred_prob 0.4-0.6)")
    print("=" * 70)

    borderline = df[(df['pred_prob'] >= 0.4) & (df['pred_prob'] <= 0.6)].sort_values('pred_prob')
    print(f"\n{len(borderline)} pairs in borderline zone:")

    for _, r in borderline.head(20).iterrows():
        label_str = "MATCH" if r['label'] == 1 else "non"
        print(f"  [{r['pred_prob']:.3f}] ({label_str}) '{r['location_name']}' → '{r['company_name']}'")

    print("\n" + "=" * 70)
    print("Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
