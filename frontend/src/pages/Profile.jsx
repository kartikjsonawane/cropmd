import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import api from '../api/axios'
import toast from 'react-hot-toast'
import { User, MapPin, Phone, Leaf, Edit2, Save, X, Plus, Trash2 } from 'lucide-react'

export default function Profile() {
  const { user, updateUser } = useAuth()
  const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    language: user?.language || 'en',
  })
  const [showAddFarm, setShowAddFarm] = useState(false)
  const [farmForm, setFarmForm] = useState({
    name: '', location: { address: '' }, area_acres: '', crops: '', soil_type: '', irrigation_type: ''
  })

  const { data: profileData } = useQuery({
    queryKey: ['profile'],
    queryFn: () => api.get('/farmer/profile').then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: data => api.put('/auth/me', data),
    onSuccess: ({ data }) => {
      updateUser(data.user)
      toast.success('Profile updated')
      setEditing(false)
    },
  })

  const addFarmMutation = useMutation({
    mutationFn: data => api.post('/farmer/farms', data),
    onSuccess: () => {
      toast.success('Farm added')
      qc.invalidateQueries(['profile'])
      setShowAddFarm(false)
      setFarmForm({ name: '', location: { address: '' }, area_acres: '', crops: '', soil_type: '', irrigation_type: '' })
    },
  })

  const deleteFarmMutation = useMutation({
    mutationFn: id => api.delete(`/farmer/farms/${id}`),
    onSuccess: () => { toast.success('Farm deleted'); qc.invalidateQueries(['profile']) },
  })

  const handleSave = e => {
    e.preventDefault()
    updateMutation.mutate(form)
  }

  const handleAddFarm = e => {
    e.preventDefault()
    addFarmMutation.mutate({
      ...farmForm,
      area_acres: parseFloat(farmForm.area_acres),
      crops: farmForm.crops.split(',').map(s => s.trim()).filter(Boolean),
    })
  }

  return (
    <div className="p-6 max-w-3xl mx-auto animate-fade-in space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
        <User className="text-brand-600" size={24} /> My Profile
      </h1>

      {/* Profile Card */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-5">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-brand-100 flex items-center justify-center text-brand-700 font-bold text-2xl">
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="font-semibold text-gray-900 text-lg">{user?.name}</h2>
              <p className="text-sm text-gray-500">{user?.email}</p>
              <span className="badge bg-brand-50 text-brand-700 mt-1 capitalize">{user?.role}</span>
            </div>
          </div>
          <button onClick={() => setEditing(e => !e)} className="btn-secondary text-sm py-2">
            {editing ? <><X size={14} /> Cancel</> : <><Edit2 size={14} /> Edit</>}
          </button>
        </div>

        {editing ? (
          <form onSubmit={handleSave} className="space-y-4">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Full Name</label>
                <input className="input" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
              <div>
                <label className="label">Phone</label>
                <input className="input" value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} placeholder="+1 234 567 8900" />
              </div>
              <div>
                <label className="label">Language</label>
                <select className="input" value={form.language} onChange={e => setForm(f => ({ ...f, language: e.target.value }))}>
                  <option value="en">English</option>
                  <option value="hi">Hindi</option>
                  <option value="es">Spanish</option>
                  <option value="pt">Portuguese</option>
                  <option value="sw">Swahili</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>
              <Save size={15} /> Save Changes
            </button>
          </form>
        ) : (
          <div className="grid sm:grid-cols-2 gap-4 text-sm">
            <div className="flex items-center gap-2 text-gray-600">
              <Phone size={15} className="text-gray-400" />
              {user?.phone || <span className="text-gray-300">No phone added</span>}
            </div>
            <div className="flex items-center gap-2 text-gray-600">
              <Leaf size={15} className="text-gray-400" />
              {user?.scan_count || 0} total scans
            </div>
          </div>
        )}
      </div>

      {/* Farms */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-gray-900">My Farms</h2>
          <button onClick={() => setShowAddFarm(s => !s)} className="btn-primary text-sm py-2">
            {showAddFarm ? <><X size={14} /> Cancel</> : <><Plus size={14} /> Add Farm</>}
          </button>
        </div>

        {showAddFarm && (
          <form onSubmit={handleAddFarm} className="bg-gray-50 rounded-xl p-4 mb-4 space-y-3">
            <div className="grid sm:grid-cols-2 gap-3">
              <div>
                <label className="label">Farm Name *</label>
                <input className="input text-sm" value={farmForm.name} onChange={e => setFarmForm(f => ({ ...f, name: e.target.value }))} required />
              </div>
              <div>
                <label className="label">Area (acres) *</label>
                <input type="number" className="input text-sm" value={farmForm.area_acres} onChange={e => setFarmForm(f => ({ ...f, area_acres: e.target.value }))} required />
              </div>
              <div>
                <label className="label">Address</label>
                <input className="input text-sm" value={farmForm.location.address} onChange={e => setFarmForm(f => ({ ...f, location: { address: e.target.value } }))} />
              </div>
              <div>
                <label className="label">Crops (comma-separated) *</label>
                <input className="input text-sm" value={farmForm.crops} onChange={e => setFarmForm(f => ({ ...f, crops: e.target.value }))} placeholder="Tomato, Potato, Corn" required />
              </div>
              <div>
                <label className="label">Soil Type</label>
                <select className="input text-sm" value={farmForm.soil_type} onChange={e => setFarmForm(f => ({ ...f, soil_type: e.target.value }))}>
                  <option value="">Select…</option>
                  <option>Clay</option><option>Sandy</option><option>Loam</option><option>Silt</option>
                </select>
              </div>
              <div>
                <label className="label">Irrigation Type</label>
                <select className="input text-sm" value={farmForm.irrigation_type} onChange={e => setFarmForm(f => ({ ...f, irrigation_type: e.target.value }))}>
                  <option value="">Select…</option>
                  <option>Drip</option><option>Sprinkler</option><option>Flood</option><option>Furrow</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn-primary text-sm" disabled={addFarmMutation.isPending}>
              Add Farm
            </button>
          </form>
        )}

        {profileData?.farms?.length > 0 ? (
          <div className="space-y-3">
            {profileData.farms.map(farm => (
              <div key={farm.id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                <div className="w-10 h-10 bg-brand-100 rounded-xl flex items-center justify-center flex-shrink-0">
                  <Leaf size={18} className="text-brand-600" />
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900 text-sm">{farm.name}</div>
                  <div className="text-xs text-gray-500 flex flex-wrap gap-2 mt-0.5">
                    <span>{farm.area_acres} acres</span>
                    {farm.crops?.length > 0 && <span>· {farm.crops.join(', ')}</span>}
                    {farm.location?.address && <span className="flex items-center gap-1"><MapPin size={10} />{farm.location.address}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className={`text-sm font-bold ${farm.health_score >= 70 ? 'text-brand-600' : 'text-red-500'}`}>
                    {farm.health_score}%
                  </div>
                  <button
                    onClick={() => deleteFarmMutation.mutate(farm.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            <Leaf size={32} className="mx-auto mb-2 text-gray-200" />
            <p className="text-sm">No farms added yet</p>
          </div>
        )}
      </div>
    </div>
  )
}
