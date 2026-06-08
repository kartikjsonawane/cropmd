import { useQuery } from '@tanstack/react-query'
import api from '../api/axios'
import {
  BarChart3, TrendingUp, Activity, Leaf
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, AreaChart, Area, Legend
} from 'recharts'

const COLORS = ['#22c55e', '#f59e0b', '#f43f5e', '#3b82f6', '#8b5cf6', '#ec4899']

export default function Analytics() {
  const { data: dash } = useQuery({
    queryKey: ['analytics-dashboard'],
    queryFn: () => api.get('/analytics/dashboard?days=30').then(r => r.data),
  })
  const { data: trends } = useQuery({
    queryKey: ['analytics-trends'],
    queryFn: () => api.get('/analytics/trends?days=30').then(r => r.data),
  })
  const { data: cropHealth } = useQuery({
    queryKey: ['crop-health'],
    queryFn: () => api.get('/analytics/crop-health').then(r => r.data),
  })

  const severityData = dash?.severity_breakdown
    ? Object.entries(dash.severity_breakdown).map(([k, v]) => ({ name: k, value: v }))
    : []

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="text-brand-600" size={24} /> Analytics
        </h1>
        <p className="text-gray-500 text-sm mt-1">30-day farm health insights</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Scans', value: dash?.total_scans ?? '—', color: 'text-blue-600' },
          { label: 'Health Rate', value: `${dash?.health_rate ?? 100}%`, color: 'text-brand-600' },
          { label: 'Disease Detections', value: dash?.diseased ?? '—', color: 'text-red-500' },
          { label: 'Crop Types', value: dash?.top_crops?.length ?? '—', color: 'text-purple-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="stat-card">
            <div className={`text-2xl font-bold ${color}`}>{value}</div>
            <div className="text-sm text-gray-500">{label}</div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6 mb-6">
        {/* Scan Trends */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-brand-600" /> Disease Trends (30 days)
          </h2>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trends?.trends || []}>
              <defs>
                <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="g2" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => d?.slice(5)} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Legend />
              <Area type="monotone" dataKey="healthy" stroke="#22c55e" fill="url(#g1)" strokeWidth={2} name="Healthy" />
              <Area type="monotone" dataKey="diseased" stroke="#f43f5e" fill="url(#g2)" strokeWidth={2} name="Diseased" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Pie */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Activity size={18} className="text-orange-500" /> Severity Distribution
          </h2>
          {severityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%" cy="50%"
                  innerRadius={55} outerRadius={90}
                  paddingAngle={3} dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {severityData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-400">
              <div className="text-center">
                <Activity size={32} className="mx-auto mb-2 text-gray-200" />
                <p className="text-sm">No scan data yet</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Crop Health */}
      {cropHealth?.crop_health?.length > 0 && (
        <div className="card p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Leaf size={18} className="text-brand-600" /> Crop Health Breakdown
          </h2>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={cropHealth.crop_health} layout="vertical">
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="crop" tick={{ fontSize: 11 }} width={80} />
              <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
              <Bar dataKey="health_pct" name="Health %" radius={[0, 4, 4, 0]}>
                {cropHealth.crop_health.map((entry, i) => (
                  <Cell
                    key={i}
                    fill={entry.health_pct >= 80 ? '#22c55e' : entry.health_pct >= 50 ? '#f59e0b' : '#f43f5e'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top Diseases */}
      {dash?.top_diseases?.length > 0 && (
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Top Detected Diseases</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={dash.top_diseases}>
              <XAxis dataKey="disease" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#f43f5e" radius={[4, 4, 0, 0]} name="Detections" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
