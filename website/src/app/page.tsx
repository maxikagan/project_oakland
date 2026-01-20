import Link from 'next/link'
import { getFeaturedBrands, getBrands } from '@/lib/data'
import { LeanIndicator, LeanBadge } from '@/components/LeanIndicator'
import { ArrowRight, Users, Building2, MapPin } from 'lucide-react'

export default async function HomePage() {
  const [featured, brandData] = await Promise.all([
    getFeaturedBrands(),
    getBrands(),
  ])

  return (
    <div className="py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Hero */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Brand Partisan Lean Explorer
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Explore the partisan composition of brand customer bases using anonymized
            foot traffic data from millions of visits across the United States.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Building2 className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{brandData.count.toLocaleString()}</p>
                <p className="text-sm text-gray-500">Brands analyzed</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <MapPin className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">6M+</p>
                <p className="text-sm text-gray-500">Points of interest</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Users className="w-6 h-6 text-purple-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">2019-2024</p>
                <p className="text-sm text-gray-500">Coverage period</p>
              </div>
            </div>
          </div>
        </div>

        {/* Featured Brands */}
        <div className="mb-16">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Featured Brands</h2>
            <Link
              href="/brands"
              className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium"
            >
              View all brands
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {featured.map((brand) => (
              <Link
                key={brand.slug}
                href={`/brands/${brand.slug}`}
                className="bg-white rounded-lg shadow-sm border p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{brand.name}</h3>
                    <p className="text-sm text-gray-500">{brand.category}</p>
                  </div>
                  <LeanBadge lean={brand.lean_2020} />
                </div>
                <LeanIndicator lean={brand.lean_2020} size="md" />
                {brand.avg_locations && (
                  <p className="text-xs text-gray-400 mt-2">
                    ~{brand.avg_locations.toLocaleString()} locations
                  </p>
                )}
              </Link>
            ))}
          </div>
        </div>

        {/* Methodology Note */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">About this data</h3>
          <p className="text-blue-800 text-sm">
            Partisan lean is calculated using anonymized mobile device foot traffic data
            combined with census block group-level election results. Values represent the
            estimated two-party Republican vote share among a brand&apos;s visitors, where 50%
            indicates a balanced customer base.
          </p>
          <p className="text-blue-700 text-sm mt-2">
            This is research data. For methodology details or data access, please contact
            the research team.
          </p>
        </div>
      </div>
    </div>
  )
}
