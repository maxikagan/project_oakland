# POI Identifier Compatibility: SafeGraph vs Advan

## Summary

**Both datasets use PLACEKEY as the primary POI identifier.**

This means SafeGraph Spend data can be directly joined with Advan Monthly Patterns data.

## Verification

### SafeGraph Spend Patterns
- **Key column**: `PLACEKEY`
- **Sample values**: `226-222@5vh-7ym-bp9`, `226-222@5vh-9s4-68v`
- **Format**: Standard Placekey format (what@where)

### Advan Monthly Patterns
- **Key column**: `PLACEKEY`
- **Sample values**: `222-222@5pn-k8x-mzf`, `222-222@5y-bh3-v4v`
- **Format**: Standard Placekey format (what@where)

## Placekey Format

Placekey is a universal POI identifier with format: `what@where`

- **what**: Encodes the POI name/category (first part before @)
- **where**: H3 geospatial index of location (part after @)

## Implications for Project Oakland

1. **Direct join possible**: Can merge SafeGraph spending data with Advan visitor data on PLACEKEY
2. **No crosswalk needed**: Same identifier system eliminates matching complexity
3. **Coverage question**: Need to verify overlap rate (are the same POIs in both datasets?)

## Next Steps

- [ ] After refreshing SafeGraph data from Dewey, compute overlap statistics:
  - How many Advan placekeys appear in SafeGraph Spend?
  - How many SafeGraph placekeys appear in Advan Monthly Patterns?
  - What categories have best/worst coverage?

---

*Created: 2026-01-08*
