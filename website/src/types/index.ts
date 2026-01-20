export interface Brand {
  name: string
  slug: string
  lean_2020: number | null
  lean_2016: number | null
  lean_std: number | null
  total_visits: number
  n_months: number
  avg_locations: number | null
  avg_states: number | null
  category: string | null
  naics: string | null
  company: string | null
  ticker: string | null
}

export interface BrandSummary {
  brands: Brand[]
  count: number
}

export interface TimeSeriesPoint {
  month: string
  lean_2020: number | null
  lean_2016: number | null
  visits: number
  n_pois: number
}

export interface FeaturedBrand {
  name: string
  actual_name: string
  slug: string
  lean_2020: number | null
  category: string | null
  avg_locations: number | null
}

export interface CategoryStats {
  n_brands: number
  mean_lean: number
  min_lean: number
  max_lean: number
}

export interface SubCategory {
  code: string
  level: number
  brands: { name: string; lean_2020: number | null }[]
  stats: CategoryStats
}

export interface Category {
  code: string
  level: number
  subcategories: Record<string, SubCategory>
  brands: { name: string; lean_2020: number | null }[]
  stats: CategoryStats
}
