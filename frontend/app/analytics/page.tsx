'use client'

import { useEffect, useState } from 'react'
import axios from 'axios'
import { BarChart3, TrendingUp, Package, Users, DollarSign, ShoppingCart } from 'lucide-react'

interface Product {
  product_id: number
  product_name: string
  category: string
  brand: string
  current_price: number
  units_sold: number
  total_revenue: number
}

interface Customer {
  customer_id: number
  customer_name: string
  email: string
  city: string
  country: string
  total_orders: number
  lifetime_value: number
}

interface CategorySales {
  category: string
  num_orders: number
  units_sold: number
  revenue: number
  avg_price: number
}

export default function Analytics() {
  const [products, setProducts] = useState<Product[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [categories, setCategories] = useState<CategorySales[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes, customersRes, categoriesRes] = await Promise.all([
          axios.get('http://localhost:5000/api/metrics/top-products?limit=10'),
          axios.get('http://localhost:5000/api/metrics/top-customers?limit=10'),
          axios.get('http://localhost:5000/api/metrics/sales-by-category'),
        ])

        setProducts(productsRes.data.data || [])
        setCustomers(customersRes.data.data || [])
        setCategories(categoriesRes.data.data || [])
      } catch (error) {
        console.error('Error fetching data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  const totalRevenue = categories.reduce((sum, cat) => sum + cat.revenue, 0)
  const totalOrders = categories.reduce((sum, cat) => sum + cat.num_orders, 0)
  const totalUnits = categories.reduce((sum, cat) => sum + cat.units_sold, 0)

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="px-6 py-4">
          <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Analytics
          </h1>
          <p className="text-sm text-gray-500 mt-1">Detailed metrics and insights from data warehouse</p>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-50 rounded-lg">
                <DollarSign className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Total Revenue</div>
                <div className="text-2xl font-semibold text-gray-900">
                  ${totalRevenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-50 rounded-lg">
                <ShoppingCart className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Total Orders</div>
                <div className="text-2xl font-semibold text-gray-900">{totalOrders.toLocaleString()}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-50 rounded-lg">
                <Package className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Units Sold</div>
                <div className="text-2xl font-semibold text-gray-900">{totalUnits.toLocaleString()}</div>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-50 rounded-lg">
                <TrendingUp className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <div className="text-xs text-gray-600">Avg Order Value</div>
                <div className="text-2xl font-semibold text-gray-900">
                  ${totalOrders > 0 ? (totalRevenue / totalOrders).toFixed(2) : '0.00'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Category Sales */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="text-sm font-medium text-gray-900">Sales by Category</h2>
          </div>
          <div className="p-4">
            <div className="grid grid-cols-2 gap-4">
              {categories.map((category) => (
                <div key={category.category} className="border rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-sm font-medium text-gray-900">{category.category}</div>
                    <div className="text-lg font-bold text-gray-900">
                      ${category.revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <div className="text-gray-500">Orders</div>
                      <div className="font-medium text-gray-700">{category.num_orders}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Units</div>
                      <div className="font-medium text-gray-700">{category.units_sold}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Avg Price</div>
                      <div className="font-medium text-gray-700">${category.avg_price.toFixed(2)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="text-sm font-medium text-gray-900">Top 10 Products</h2>
          </div>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">#</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Product</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Category</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Brand</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Price</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Units Sold</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {products.map((product, index) => (
                  <tr key={product.product_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500">{index + 1}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{product.product_name}</td>
                    <td className="px-4 py-3 text-gray-600">{product.category}</td>
                    <td className="px-4 py-3 text-gray-600">{product.brand}</td>
                    <td className="px-4 py-3 text-right text-gray-900">${product.current_price.toFixed(2)}</td>
                    <td className="px-4 py-3 text-right text-gray-900">{product.units_sold}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      ${product.total_revenue.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Customers */}
        <div className="bg-white border rounded-lg">
          <div className="px-4 py-3 border-b bg-gray-50">
            <h2 className="text-sm font-medium text-gray-900">Top 10 Customers</h2>
          </div>
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">#</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Customer</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-600">Location</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Orders</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-600">Lifetime Value</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {customers.map((customer, index) => (
                  <tr key={customer.customer_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500">{index + 1}</td>
                    <td className="px-4 py-3 font-medium text-gray-900">{customer.customer_name}</td>
                    <td className="px-4 py-3 text-gray-600">{customer.email}</td>
                    <td className="px-4 py-3 text-gray-600">
                      {customer.city}, {customer.country}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-900">{customer.total_orders}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-900">
                      ${customer.lifetime_value.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
