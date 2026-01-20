import { Brand, BrandSummary, FeaturedBrand, Category, TimeSeriesPoint } from '@/types'

const DATA_BASE_URL = process.env.NEXT_PUBLIC_DATA_URL || '/data'

export async function getBrands(): Promise<BrandSummary> {
  const res = await fetch(`${DATA_BASE_URL}/brands.json`, { next: { revalidate: 3600 } })
  if (!res.ok) throw new Error('Failed to fetch brands')
  return res.json()
}

export async function getFeaturedBrands(): Promise<FeaturedBrand[]> {
  const res = await fetch(`${DATA_BASE_URL}/featured_brands.json`, { next: { revalidate: 3600 } })
  if (!res.ok) throw new Error('Failed to fetch featured brands')
  return res.json()
}

export async function getCategories(): Promise<Record<string, Category>> {
  const res = await fetch(`${DATA_BASE_URL}/categories.json`, { next: { revalidate: 3600 } })
  if (!res.ok) throw new Error('Failed to fetch categories')
  return res.json()
}

export async function getBrandTimeSeries(slug: string): Promise<TimeSeriesPoint[] | null> {
  const res = await fetch(`${DATA_BASE_URL}/brand_timeseries.json`, { next: { revalidate: 3600 } })
  if (!res.ok) throw new Error('Failed to fetch time series')
  const data = await res.json()
  return data[slug] || null
}

export function formatLean(lean: number | null): string {
  if (lean === null) return 'N/A'
  const pct = (lean * 100).toFixed(1)
  return `${pct}% R`
}

export function getLeanLabel(lean: number | null): string {
  if (lean === null) return 'Unknown'
  if (lean < 0.45) return 'Leans Democratic'
  if (lean > 0.55) return 'Leans Republican'
  return 'Balanced'
}

export function getLeanColor(lean: number | null): string {
  if (lean === null) return 'bg-gray-200'
  if (lean < 0.45) return 'bg-democratic-500'
  if (lean > 0.55) return 'bg-republican-500'
  return 'bg-gray-400'
}
