import { Brand, BrandSummary, FeaturedBrand, Category, TimeSeriesPoint } from '@/types'
import { promises as fs } from 'fs'
import path from 'path'

async function readJsonFile<T>(filename: string): Promise<T> {
  const filePath = path.join(process.cwd(), 'public', 'data', filename)
  const data = await fs.readFile(filePath, 'utf-8')
  return JSON.parse(data)
}

export async function getBrands(): Promise<BrandSummary> {
  return readJsonFile<BrandSummary>('brands.json')
}

export async function getFeaturedBrands(): Promise<FeaturedBrand[]> {
  return readJsonFile<FeaturedBrand[]>('featured_brands.json')
}

export async function getCategories(): Promise<Record<string, Category>> {
  return readJsonFile<Record<string, Category>>('categories.json')
}

export async function getBrandTimeSeries(slug: string): Promise<TimeSeriesPoint[] | null> {
  const data = await readJsonFile<Record<string, TimeSeriesPoint[]>>('brand_timeseries.json')
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
