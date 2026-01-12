# LinkOrgs Package Investigation

## Summary

**LinkOrgs** is an R package for organizational record linkage that uses LinkedIn's organizational network data (~500M records, calibrated to 2017) for matching.

**Source**: https://github.com/cjerzak/LinkOrgs-software

## Matching Algorithms

| Algorithm | Type | Internet Required | Dependencies |
|-----------|------|-------------------|--------------|
| `fuzzy` | String distance (Jaccard) | No | R only |
| `bipartite` | Network-informed | Yes | Downloads LinkedIn data |
| `markov` | Network-informed | Yes | Downloads LinkedIn data |
| `ml` | Transformer/SBERT | Yes | JAX backend, Python |
| `transfer` | Network + ML hybrid | Yes | Both above |

## Installation

```r
devtools::install_github("cjerzak/LinkOrgs-software/LinkOrgs")

# For ML functionality:
LinkOrgs::BuildBackend(conda = "auto")
```

## Applicability to Project Oakland

### Pros
- Free (academic license)
- Uses LinkedIn data which may have employer names we need
- Multiple algorithm options from fast/simple to slow/accurate
- R package integrates with our existing workflow

### Cons
- LinkedIn data is from ~2017 - may miss newer businesses
- Designed for employer-to-employer matching, not necessarily brand-to-employer
- Network algorithms require internet during matching
- ML backend requires Python/JAX setup

### Key Question
**Does LinkedIn data include the brands we need?**
- Major chains (McDonald's, Walmart, Target) → likely yes
- Local businesses → may have LinkedIn presence
- Advan "brands" field → need to compare to LinkedIn org names

## Recommendation

1. **Test on sample**: Extract top 200 Advan brands, test fuzzy and ml algorithms
2. **Compare to alternatives**:
   - Claude-based FuzzyLink (semantic, ~$50-200)
   - Traditional string distance (free but less accurate)
3. **Benchmark**: Measure match rate, accuracy (manual audit), and cost

## Next Steps

- [ ] Install LinkOrgs on Savio
- [ ] Extract unique brands from Ohio Advan data
- [ ] Run benchmark comparison
- [ ] Document results

---

*Created: 2026-01-08*

Sources:
- [LinkOrgs GitHub](https://github.com/cjerzak/LinkOrgs-software)
