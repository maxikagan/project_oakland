# Revelio Labs Data Dictionary

Source: https://www.data-dictionary.reveliolabs.com/

## Overview

Revelio Labs provides comprehensive workforce intelligence through multiple datasets, transforming raw professional profile data into actionable insights through standardization and statistical adjustment.

## Available Datasets

### 1. Workforce Dynamics
- **Description**: Employee counts, inflows/outflows, and compensation segmented by role, location, and seniority
- **Update Frequency**: Monthly
- **Historical Coverage**: 2008-present
- **Geographic Scope**: Global

### 2. Transitions
- **Description**: Information on individuals changing roles, including prior and new positions
- **Update Frequency**: Monthly
- **Historical Coverage**: 2008-present
- **Geographic Scope**: Global

### 3. Job Postings
- **Description**: Active and archived job listings from 5.25M+ companies (2B+ postings)
- **Update Frequency**: Weekly
- **Historical Coverage**: 2021-present

### 4. Sentiment Data
- **Description**: Employee reviews with positive/negative text mappings
- **Update Frequency**: Monthly
- **Historical Coverage**: 2008-present

### 5. Layoff Notices
- **Description**: US-based layoff records with effective dates
- **Update Frequency**: Monthly
- **Historical Coverage**: State-dependent

### 6. Individual Level Data
- **Description**: Professional histories including roles, education, and demographics
- **Update Frequency**: Daily
- **Geographic Scope**: Global

## Core Methodologies

### Company Mapping
- Resolves naming inconsistencies and subsidiary relationships
- Assigns Revelio Company ID (RCID) to each company
- Strong identifiers: company name, LinkedIn URL, company URL, FactSet ID, ticker symbol

### Sampling Weights
- Raw profile data overrepresents white-collar and urban workers
- Applies occupation and location adjustments using government labor statistics
- Sources: Bureau of Labor Statistics, International Labor Organization

### Reporting Lag Adjustment (Nowcasting)
- Predicts employee inflows/outflows in recent periods
- Incorporates seasonal trends, special events (layoffs), and hiring patterns
- Corrects underrepresentation in recent data

## Taxonomies & Classifications

### Jobs Taxonomy
- Reduces millions of job titles into manageable occupational groups
- Hierarchy: 1,500 distinct categories down to 7 general categories
- Uses mathematical activity analysis and proprietary clustering

### Skills Taxonomy
- Clusters diverse skill descriptions into universal skill language
- 25 to 3,000 specificity levels
- Enables cross-company and cross-industry comparison

### Job Postings Unification (COSMOS)
- Processes 3.9B+ postings through normalized field comparison
- Temporal overlap analysis eliminates duplicates
- Predicts actual hiring intent

## Individual-Level Attributes

### Gender & Ethnicity Prediction
- Name-based probabilistic modeling
- Sources: Social Security Administration, US Census
- Falls back to countrywide ethnic distributions for uncommon names

### Prestige Scoring
- Continuous values (-1 to 1)
- Uses expectation-maximization models
- Propagates world university rankings through professional networks
- Weighted by seniority and tenure

### Salary Modeling
- Predicts compensation using: job title, seniority, company, location, tenure
- Training data: visa applications, job postings
- Incorporates country multipliers and inflation adjustments

### Seniority Levels
- Seven-tier ordinal scale: Entry through Senior Executive
- Derived from ensemble models combining:
  - Current position analysis
  - Job history review
  - Age assessment

## Data Sources

Aggregates from:
- Publicly available professional profiles
- Job postings
- Visa applications
- Government labor statistics
