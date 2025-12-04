'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { TrendingUp, Users, Package, DollarSign, RefreshCw } from 'lucide-react'

interface Stats {
  source: {
    customers: number
    products: number
    orders: number
  }
  warehouse: {
    customers: number
    products: number
    orders: number
  }
  in_sync: boolean
}

interface Product {
  product_id: number
  product_name: string
  category: string
  units_sold: number
  total_revenue: number
}

interface Customer {
  customer_id: number
  customer_name: string
  email: string
  total_orders: number
  lifetime_value: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [products, setProducts] = useState<Product[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = async () => {
    try {
      const [statsRes, productsRes, customersRes] = await Promise.all([
        axios.get('http://localhost:5000/api/cdc/stats'),
        axios.get('http://localhost:5000/api/metrics/top-products?limit=5'),
        axios.get('http://localhost:5000/api/metrics/top-customers?limit=5'),
      ])

      setStats(statsRes.data.data)
      setProducts(productsRes.data.data || [])
      setCustomers(customersRes.data.data || [])
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Dashboard</h1>
              <p className="text-sm text-gray-500 mt-1">Real-time data warehouse overview</p>
            </div>
            <button
              onClick={fetchData}
              className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <Users className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Customers</div>
                <div className="text-2xl font-semibold text-gray-900">{stats?.warehouse.customers || 0}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <Package className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Products</div>
                <div className="text-2xl font-semibold text-gray-900">{stats?.warehouse.products || 0}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Orders</div>
                <div className="text-2xl font-semibold text-gray-900">{stats?.warehouse.orders || 0}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${stats?.in_sync ? 'bg-green-50' : 'bg-yellow-50'}`}>
                <DollarSign className={`w-5 h-5 ${stats?.in_sync ? 'text-green-600' : 'text-yellow-600'}`} />
              </div>
              <div>
                <div className="text-xs text-gray-600">Sync Status</div>
                <div className={`text-sm font-medium ${stats?.in_sync ? 'text-green-700' : 'text-yellow-700'}`}>
                  {stats?.in_sync ? 'In Sync' : 'Syncing'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-3 gap-4">
          <a
            href="/analytics"
            className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <h3 className="text-sm font-medium text-gray-900 mb-1">📊 Analytics Dashboard</h3>
            <p className="text-xs text-gray-500">View sales trends and revenue analytics</p>
          </a>
          <a
            href="/cdc-monitoring"
            className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <h3 className="text-sm font-medium text-gray-900 mb-1">🔄 CDC Monitoring</h3>
            <p className="text-xs text-gray-500">Monitor CDC sync status and recent changes</p>
          </a>
          <a
            href="/offset-monitoring"
            className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <h3 className="text-sm font-medium text-blue-900 mb-1">🎯 Offset Monitoring</h3>
            <p className="text-xs text-blue-700">Track Kafka offsets & failed messages</p>
            <span className="inline-block mt-2 text-xs font-semibold text-blue-600 bg-blue-100 px-2 py-1 rounded">NEW</span>
          </a>
        </div>

        {/* Top Products & Customers */}
        <div className="grid grid-cols-2 gap-6">
          {/* Top Products */}
          <div className="bg-white border rounded-lg">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h2 className="text-sm font-medium text-gray-900">Top Selling Products</h2>
            </div>
            <div className="p-4">
              <div className="space-y-3">
                {products.map((product, index) => (
                  <div key={product.product_id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 bg-gray-100 rounded flex items-center justify-center text-xs font-medium text-gray-600">
                        {index + 1}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{product.product_name}</div>
                        <div className="text-xs text-gray-500">{product.category}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">${product.total_revenue.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">{product.units_sold} sold</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Top Customers */}
          <div className="bg-white border rounded-lg">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h2 className="text-sm font-medium text-gray-900">Top Customers</h2>
            </div>
            <div className="p-4">
              <div className="space-y-3">
                {customers.map((customer, index) => (
                  <div key={customer.customer_id} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-6 h-6 bg-gray-100 rounded flex items-center justify-center text-xs font-medium text-gray-600">
                        {index + 1}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{customer.customer_name}</div>
                        <div className="text-xs text-gray-500">{customer.email}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">${customer.lifetime_value.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">{customer.total_orders} orders</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
