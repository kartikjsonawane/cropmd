import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'
import toast from 'react-hot-toast'
import { ShieldCheck, Users, ScanLine, AlertTriangle, Database, RefreshCw } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function Admin() {
  const qc = useQueryClient()

  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => api.get('/admin/stats').then(r => r.data),
  })

  const { data: users } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.get('/admin/users?limit=20').then(r => r.data),
  })

  const seedMutation = useMutation({
    mutationFn: () => api.post('/admin/seed-diseases'),
    onSuccess: ({ data }) => toast.success(data.message),
  })

  const toggleUser = useMutation({
    mutationFn: ({ id, is_active }) => api.put(`/admin/users/${id}`, { is_active }),
    onSuccess: () => { qc.invalidateQueries(['admin-users']); toast.success('User updated') },
  })

  const statCards = [
    { label: 'Total Users', value: stats?.total_users ?? '—', icon: Users, color: 'text-blue-600 bg-blue-50' },
    { label: 'Total Scans', value: stats?.total_scans ?? '—', icon: ScanLine, color: 'text-brand-600 bg-brand-50' },
    { label: 'Disease Detections', value: stats?.total_disease_detections ?? '—', icon: AlertTriangle, color: 'text-red-600 bg-red-50' },
    { label: 'Health Rate', value: `${stats?.health_rate ?? 100}%`, icon: ShieldCheck, color: 'text-purple-600 bg-purple-50' },
  ]

  return (
    <div className="p-6 max-w-6xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <ShieldCheck className="text-brand-600" size={24} /> Admin Panel
        </h1>
        <button
          onClick={() => seedMutation.mutate()}
          disabled={seedMutation.isPending}
          className="btn-secondary text-sm"
        >
          <Database size={15} />
          {seedMutation.isPending ? 'Seeding…' : 'Seed Disease DB'}
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {statCards.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="stat-card">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>
              <Icon size={20} />
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-sm text-gray-500">{label}</div>
          </div>
        ))}
      </div>

      {/* 7-day summary */}
      <div className="grid sm:grid-cols-2 gap-4 mb-6">
        <div className="card p-5">
          <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-1">New Users (7d)</div>
          <div className="text-3xl font-bold text-gray-900">{stats?.new_users_7d ?? '—'}</div>
        </div>
        <div className="card p-5">
          <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider mb-1">New Scans (7d)</div>
          <div className="text-3xl font-bold text-gray-900">{stats?.new_scans_7d ?? '—'}</div>
        </div>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Users size={18} className="text-gray-400" /> Users
          </h2>
          <span className="text-sm text-gray-400">{users?.total ?? 0} total</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider">
                <th className="px-6 py-3 text-left">Name</th>
                <th className="px-6 py-3 text-left">Email</th>
                <th className="px-6 py-3 text-left">Role</th>
                <th className="px-6 py-3 text-left">Scans</th>
                <th className="px-6 py-3 text-left">Joined</th>
                <th className="px-6 py-3 text-left">Status</th>
                <th className="px-6 py-3 text-left">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users?.users?.map(u => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-6 py-3 font-medium text-gray-900">{u.name}</td>
                  <td className="px-6 py-3 text-gray-500">{u.email}</td>
                  <td className="px-6 py-3">
                    <span className="badge bg-gray-100 text-gray-600 capitalize">{u.role}</span>
                  </td>
                  <td className="px-6 py-3 text-gray-500">{u.scan_count}</td>
                  <td className="px-6 py-3 text-gray-400 text-xs">
                    {formatDistanceToNow(new Date(u.created_at), { addSuffix: true })}
                  </td>
                  <td className="px-6 py-3">
                    <span className={`badge ${u.is_active !== false ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                      {u.is_active !== false ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-3">
                    <button
                      onClick={() => toggleUser.mutate({ id: u.id, is_active: u.is_active === false })}
                      className="text-xs text-brand-600 hover:text-brand-700 font-medium"
                    >
                      {u.is_active !== false ? 'Deactivate' : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Top Diseases */}
      {stats?.top_diseases?.length > 0 && (
        <div className="card p-6 mt-6">
          <h2 className="font-semibold text-gray-900 mb-4">Top Detected Diseases (Global)</h2>
          <div className="space-y-2">
            {stats.top_diseases.map(({ disease, count }, i) => (
              <div key={disease} className="flex items-center gap-3">
                <span className="text-xs text-gray-400 w-4">{i + 1}</span>
                <div className="flex-1 bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="h-full bg-red-500 rounded-full"
                    style={{ width: `${(count / stats.top_diseases[0].count) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-700 truncate w-48">{disease}</span>
                <span className="text-sm font-semibold text-gray-500 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
