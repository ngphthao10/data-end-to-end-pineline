'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

interface MetricCard {
  title: string;
  value: string | number;
  change?: string;
  icon: string;
}

interface Product {
  product_id: number;
  product_name: string;
  category: string;
  units_sold: number;
  total_revenue: number;
}

interface Customer {
  customer_id: number;
  customer_name: string;
  email: string;
  total_orders: number;
  lifetime_value: number;
}

interface CategorySales {
  category: string;
  revenue: number;
  units_sold: number;
}

export default function Home() {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [categories, setCategories] = useState<CategorySales[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [productsRes, customersRes, categoriesRes] = await Promise.all([
          axios.get('http://localhost:5000/api/metrics/top-products?limit=5'),
          axios.get('http://localhost:5000/api/metrics/top-customers?limit=5'),
          axios.get('http://localhost:5000/api/metrics/sales-by-category'),
        ]);

        setProducts(productsRes.data.data || []);
        setCustomers(customersRes.data.data || []);
        setCategories(categoriesRes.data.data || []);
      } catch (error) {
        console.error('Error fetching data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  const totalRevenue = categories.reduce((sum, cat) => sum + cat.revenue, 0);
  const totalProducts = products.length;
  const totalCustomers = customers.length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">E-commerce Data Warehouse</h1>
              <p className="text-gray-600 mt-1">Real-time CDC with SCD Type 2</p>
            </div>
            <div className="flex items-center space-x-2">
              <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm text-gray-600">Live</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
                <p className="text-3xl font-bold text-gray-900">
                  ${totalRevenue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </p>
              </div>
              <div className="h-12 w-12 bg-primary-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">💰</span>
              </div>
            </div>
          </div>

          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Top Products</p>
                <p className="text-3xl font-bold text-gray-900">{totalProducts}</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">📦</span>
              </div>
            </div>
          </div>

          <div className="card hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Top Customers</p>
                <p className="text-3xl font-bold text-gray-900">{totalCustomers}</p>
              </div>
              <div className="h-12 w-12 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">👥</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Top Products */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="mr-2">🏆</span>
              Top Selling Products
            </h2>
            <div className="space-y-4">
              {products.map((product, index) => (
                <div key={product.product_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-primary-100 rounded-full flex items-center justify-center font-bold text-primary-600">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{product.product_name}</p>
                      <p className="text-sm text-gray-500">{product.category}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">${product.total_revenue.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">{product.units_sold} units</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Top Customers */}
          <div className="card">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="mr-2">⭐</span>
              Top Customers
            </h2>
            <div className="space-y-4">
              {customers.map((customer, index) => (
                <div key={customer.customer_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center font-bold text-purple-600">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{customer.customer_name}</p>
                      <p className="text-sm text-gray-500">{customer.email}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">${customer.lifetime_value.toLocaleString()}</p>
                    <p className="text-sm text-gray-500">{customer.total_orders} orders</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Sales by Category */}
          <div className="card lg:col-span-2">
            <h2 className="text-xl font-bold mb-4 flex items-center">
              <span className="mr-2">📊</span>
              Sales by Category
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {categories.map((category) => (
                <div key={category.category} className="p-4 bg-gradient-to-br from-primary-50 to-primary-100 rounded-lg">
                  <p className="text-sm text-gray-600 mb-1">{category.category}</p>
                  <p className="text-2xl font-bold text-gray-900">${category.revenue.toLocaleString()}</p>
                  <p className="text-xs text-gray-500 mt-1">{category.units_sold} units</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Powered by CDC (Change Data Capture) with Debezium + Kafka + PostgreSQL</p>
          <p className="mt-1">Real-time data warehouse with SCD Type 2 implementation</p>
        </div>
      </div>
    </div>
  );
}
