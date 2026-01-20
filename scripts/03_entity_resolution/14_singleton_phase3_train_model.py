#!/usr/bin/env python3
"""
Phase 3: Train logistic regression model on labeled pairs.

Uses features: cos_sim, jaro_winkler, token_jaccard, contains_match
Target: is_match (from manual labeling)

Outputs: trained model coefficients and evaluation metrics.

Usage: python 14_singleton_phase3_train_model.py --msa columbus_oh
"""

import argparse
import json
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
import joblib

PROJECT_DIR = Path("/global/scratch/users/maxkagan/measuring_stakeholder_ideology")
INPUT_DIR = PROJECT_DIR / "outputs" / "singleton_matching" / "training_samples"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "singleton_matching" / "models"

FEATURES = ['cos_sim', 'jaro_winkler', 'token_jaccard', 'contains_match']


def load_labeled_data(msa: str) -> pd.DataFrame:
    """Load sample with labels."""
    sample_file = INPUT_DIR / f"{msa}_sample_full.parquet"
    labels_file = INPUT_DIR / f"{msa}_labels.parquet"

    if not sample_file.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_file}")
    if not labels_file.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_file}")

    sample = pd.read_parquet(sample_file)
    labels = pd.read_parquet(labels_file)

    # Join labels to sample
    df = sample.merge(labels[['sample_id', 'is_match']], on='sample_id', how='inner')

    print(f"  Loaded {len(df):,} labeled pairs")
    print(f"  Matches: {df['is_match'].sum():,} ({100*df['is_match'].mean():.1f}%)")
    print(f"  Non-matches: {(~df['is_match']).sum():,}")

    return df


def train_model(df: pd.DataFrame) -> tuple:
    """Train logistic regression and return model + metrics."""
    X = df[FEATURES].copy()
    X['contains_match'] = X['contains_match'].astype(int)
    y = df['is_match'].astype(int)

    # Train/test split for evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train logistic regression
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)

    # Cross-validation on training set
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='roc_auc')

    # Predictions on test set
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    # Metrics
    metrics = {
        'cv_auc_mean': float(cv_scores.mean()),
        'cv_auc_std': float(cv_scores.std()),
        'test_auc': float(roc_auc_score(y_test, y_prob)),
        'test_accuracy': float((y_pred == y_test).mean()),
        'n_train': len(X_train),
        'n_test': len(X_test),
        'n_matches_train': int(y_train.sum()),
        'n_matches_test': int(y_test.sum()),
    }

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    metrics['confusion_matrix'] = cm.tolist()

    # Classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    metrics['precision_match'] = report['1']['precision'] if '1' in report else report['True']['precision']
    metrics['recall_match'] = report['1']['recall'] if '1' in report else report['True']['recall']
    metrics['f1_match'] = report['1']['f1-score'] if '1' in report else report['True']['f1-score']

    # Coefficients
    coef_dict = dict(zip(FEATURES, model.coef_[0]))
    coef_dict['intercept'] = model.intercept_[0]

    return model, metrics, coef_dict, (X_test, y_test, y_prob)


def find_optimal_threshold(y_true, y_prob):
    """Find threshold that maximizes F1 score."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)

    # F1 = 2 * (precision * recall) / (precision + recall)
    f1_scores = 2 * (precision[:-1] * recall[:-1]) / (precision[:-1] + recall[:-1] + 1e-10)

    best_idx = np.argmax(f1_scores)
    best_threshold = thresholds[best_idx]
    best_f1 = f1_scores[best_idx]

    return best_threshold, best_f1, precision[best_idx], recall[best_idx]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--msa', required=True, help='MSA name (e.g., columbus_oh)')
    args = parser.parse_args()

    msa = args.msa

    print("=" * 70)
    print(f"Phase 3: Train Logit Model - {msa}")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n[1] Loading labeled data...")
    df = load_labeled_data(msa)

    print(f"\n[2] Feature summary:")
    for feat in FEATURES:
        if feat == 'contains_match':
            print(f"  {feat}: {df[feat].sum():,} pairs ({100*df[feat].mean():.1f}%)")
        else:
            print(f"  {feat}: mean={df[feat].mean():.3f}, std={df[feat].std():.3f}")

    print(f"\n[3] Training logistic regression...")
    model, metrics, coef_dict, (X_test, y_test, y_prob) = train_model(df)

    print(f"\n[4] Model coefficients:")
    for feat, coef in coef_dict.items():
        print(f"  {feat}: {coef:.4f}")

    print(f"\n[5] Evaluation metrics:")
    print(f"  Cross-validation AUC: {metrics['cv_auc_mean']:.3f} (+/- {metrics['cv_auc_std']:.3f})")
    print(f"  Test AUC: {metrics['test_auc']:.3f}")
    print(f"  Test accuracy: {metrics['test_accuracy']:.3f}")
    print(f"  Precision (match): {metrics['precision_match']:.3f}")
    print(f"  Recall (match): {metrics['recall_match']:.3f}")
    print(f"  F1 (match): {metrics['f1_match']:.3f}")

    print(f"\n[6] Confusion matrix (test set):")
    cm = np.array(metrics['confusion_matrix'])
    print(f"                 Predicted")
    print(f"              No Match  Match")
    print(f"  Actual No Match  {cm[0,0]:5d}  {cm[0,1]:5d}")
    print(f"  Actual Match     {cm[1,0]:5d}  {cm[1,1]:5d}")

    print(f"\n[7] Finding optimal threshold...")
    best_thresh, best_f1, best_prec, best_rec = find_optimal_threshold(y_test, y_prob)
    print(f"  Optimal threshold: {best_thresh:.3f}")
    print(f"  At this threshold: precision={best_prec:.3f}, recall={best_rec:.3f}, F1={best_f1:.3f}")

    metrics['optimal_threshold'] = float(best_thresh)
    metrics['optimal_f1'] = float(best_f1)
    metrics['optimal_precision'] = float(best_prec)
    metrics['optimal_recall'] = float(best_rec)

    print(f"\n[8] Saving outputs...")

    # Save model
    model_file = OUTPUT_DIR / f"{msa}_logit_model.joblib"
    joblib.dump(model, model_file)
    print(f"  Model: {model_file}")

    # Save coefficients
    coef_file = OUTPUT_DIR / f"{msa}_coefficients.json"
    with open(coef_file, 'w') as f:
        json.dump(coef_dict, f, indent=2)
    print(f"  Coefficients: {coef_file}")

    # Save metrics
    metrics_file = OUTPUT_DIR / f"{msa}_metrics.json"
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"  Metrics: {metrics_file}")

    print("\n" + "=" * 70)
    print("Phase 3 complete!")
    print(f"Recommended threshold: {best_thresh:.3f} (F1={best_f1:.3f})")
    print("=" * 70)


if __name__ == '__main__':
    main()
