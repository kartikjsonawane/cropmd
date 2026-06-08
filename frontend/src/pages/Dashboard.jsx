import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'
import {
  ScanLine, Activity, AlertTriangle, CheckCircle,
  ArrowRight, TrendingUp, Leaf, Clock
} from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
import { formatDistanceToNow } from 'date-fns'

function SeverityBadge({ severity }) {
  const map = {
    High: 'severity-high',
    Medium: 'severity-medium',
    Low: 'severity-low',
    None: 'severity-none',
  }
  return <span className={map[severity] || 'badge bg-gray-100 text-gray-600'}>{severity || 'N/A'}</span>
}

export default function Dashboard() {
  const { user } = useAuth()

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/analytics/dashboard?days=30').then(r => r.data),
  })

  const { data: history } = useQuery({
    queryKey: ['recent-scans'],
    queryFn: () => api.get('/predictions/history?limit=5').then(r => r.data),
  })

  const { data: trends } = useQuery({
    queryKey: ['trends-7d'],
    queryFn: () => api.get('/analytics/trends?days=14').then(r => r.data),
  })

  const statCards = [
    {
      icon: ScanLine,
      label: 'Total Scans',
      value: stats?.total_scans ?? '—',
      sub: `${stats?.recent_scans ?? 0} this month`,
      color: 'text-blue-600 bg-blue-50',
    },
    {
      icon: CheckCircle,
      label: 'Healthy',
      value: stats?.healthy ?? '—',
      sub: `${stats?.health_rate ?? 100}% health rate`,
      color: 'text-brand-600 bg-brand-50',
    },
    {
      icon: AlertTriangle,
      label: 'Disease Detections',
      value: stats?.diseased ?? '—',
      sub: 'This period',
      color: 'text-red-600 bg-red-50',
    },
    {
      icon: Activity,
      label: 'Crop Types',
      value: stats?.top_crops?.length ?? '—',
      sub: 'Crops monitored',
      color: 'text-purple-600 bg-purple-50',
    },
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Good morning, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-gray-500 text-sm mt-1">Here's your farm health overview</p>
        </div>
        <Link to="/scanner" className="btn-primary">
          <ScanLine size={16} /> New Scan
        </Link>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(({ icon: Icon, label, value, sub, color }) => (
          <div key={label} className="stat-card">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
              <Icon size={20} />
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div>
              <div className="text-sm font-medium text-gray-700">{label}</div>
              <div className="text-xs text-gray-400">{sub}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Trend Chart */}
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <TrendingUp size={18} className="text-brand-600" /> Scan Activity (14 days)
            </h2>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={trends?.trends || []}>
              <defs>
                <linearGradient id="healthy" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="diseased" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d?.slice(5)} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="healthy" stroke="#22c55e" fill="url(#healthy)" strokeWidth={2} name="Healthy" />
              <Area type="monotone" dataKey="diseased" stroke="#f43f5e" fill="url(#diseased)" strokeWidth={2} name="Diseased" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Top Diseases */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle size={18} className="text-orange-500" /> Top Diseases
          </h2>
          {stats?.top_diseases?.length > 0 ? (
            <div className="space-y-3">
              {stats.top_diseases.map(({ disease, count }) => (
                <div key={disease} className="flex items-center justify-between">
                  <div className="text-sm text-gray-700 truncate flex-1">{disease}</div>
                  <span className="ml-2 text-xs font-medium bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                    {count}x
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Leaf size={32} className="mx-auto mb-2 text-brand-200" />
              <p className="text-sm">No diseases detected yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Recent Scans */}
      <div className="card">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Clock size={18} className="text-gray-400" /> Recent Scans
          </h2>
          <Link to="/history" className="text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
            View all <ArrowRight size={14} />
          </Link>
        </div>
        <div className="divide-y divide-gray-50">
          {history?.scans?.length > 0 ? history.scans.map(scan => (
            <Link
              key={scan.id}
              to={`/results/${scan.id}`}
              className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              {scan.image_url ? (
                <img src={scan.image_url} alt="" className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />
              ) : (
                <div className="w-12 h-12 rounded-lg bg-brand-50 flex items-center justify-center flex-shrink-0">
                  <Leaf size={20} className="text-brand-400" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 text-sm">{scan.prediction?.disease_name || 'Unknown'}</span>
                  <SeverityBadge severity={scan.prediction?.severity} />
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {scan.prediction?.crop_name} · {formatDistanceToNow(new Date(scan.created_at), { addSuffix: true })}
                </div>
              </div>
              <div className="text-sm font-medium text-gray-600">
                {Math.round((scan.prediction?.confidence || 0) * 100)}%
              </div>
              <ArrowRight size={16} className="text-gray-300" />
            </Link>
          )) : (
            <div className="text-center py-12 text-gray-400">
              <ScanLine size={40} className="mx-auto mb-3 text-gray-200" />
              <p className="text-sm font-medium">No scans yet</p>
              <p className="text-xs mt-1">Upload your first crop photo to get started</p>
              <Link to="/scanner" className="btn-primary mt-4 text-sm">Start Scanning</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
