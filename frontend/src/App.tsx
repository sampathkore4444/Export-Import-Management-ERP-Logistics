import { BrowserRouter, Routes, Route, Navigate, Link } from 'react-router-dom'
import { useState, useEffect, createContext, useContext } from 'react'
import axios from 'axios'

const API_BASE = '/api'

interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: string
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  language: string
  setLanguage: (lang: string) => void
  darkMode: boolean
  setDarkMode: (mode: boolean) => void
}

const AuthContext = createContext<AuthContextType | null>(null)

const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}

const canManage = (user: User | null) => user?.role === 'admin' || user?.role === 'manager'
const isAdmin = (user: User | null) => user?.role === 'admin'

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [language, setLanguage] = useState<string>(localStorage.getItem('language') || 'en')
  const [darkMode, setDarkMode] = useState<boolean>(localStorage.getItem('darkMode') === 'true')

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    }
    if (darkMode) {
      document.body.classList.add('dark-mode')
    } else {
      document.body.classList.remove('dark-mode')
    }
  }, [token, darkMode])

  const logout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('token')
    delete axios.defaults.headers.common['Authorization']
  }

  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      res => res,
      async (error) => {
        const original = error.config as any
        const isLoginOrRefresh = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/refresh')
        if (error.response?.status === 401 && !isLoginOrRefresh && !original?._retry && token) {
          original._retry = true
          try {
            const res = await axios.post(`${API_BASE}/auth/refresh`, { token })
            const newToken = res.data.access_token
            localStorage.setItem('token', newToken)
            setToken(newToken)
            axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`
            original.headers = original.headers || {}
            original.headers['Authorization'] = `Bearer ${newToken}`
            return axios(original)
          } catch (refreshErr) {
            logout()
          }
        }
        return Promise.reject(error)
      }
    )
    return () => axios.interceptors.response.eject(interceptor)
  }, [token])

  const login = async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    const response = await axios.post(`${API_BASE}/auth/login`, formData)
    setToken(response.data.access_token)
    localStorage.setItem('token', response.data.access_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
    const meRes = await axios.get(`${API_BASE}/auth/me`)
    setUser(meRes.data)
  }

  const handleSetLanguage = (lang: string) => {
    setLanguage(lang)
    localStorage.setItem('language', lang)
  }

  const handleSetDarkMode = (mode: boolean) => {
    setDarkMode(mode)
    localStorage.setItem('darkMode', String(mode))
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, language, setLanguage: handleSetLanguage, darkMode, setDarkMode: handleSetDarkMode }}>
      {children}
    </AuthContext.Provider>
  )
}

function Login() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(username, password)
    } catch (err) {
      setError('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-logo">
          <div className="login-logo-icon">C</div>
          <span className="login-logo-text">CargoFlow</span>
        </div>
        <h2 className="login-title">Welcome Back</h2>
        <p className="login-subtitle">Sign in to manage your import operations</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p style={{ color: 'var(--danger-color)', marginBottom: '1rem', fontSize: '0.875rem' }}>{error}</p>}
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? <span className="loading-spinner"></span> : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  )
}

function Dashboard() {
  const [stats, setStats] = useState({ 
    pending: 0, 
    inProgress: 0, 
    delivered: 0, 
    closed: 0,
    rejected: 0,
    total: 0,
    licenseRequired: 0,
    awaitingClearance: 0
  })
  const [recentJobs, setRecentJobs] = useState<any[]>([])
  const [truckCount, setTruckCount] = useState(0)
  const [customerCount, setCustomerCount] = useState(0)
  const [vendorCount, setVendorCount] = useState(0)

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE}/jobs`),
      axios.get(`${API_BASE}/trucks`),
      axios.get(`${API_BASE}/customers`),
      axios.get(`${API_BASE}/vendors`)
    ]).then(([jobsRes, trucksRes, customersRes, vendorsRes]) => {
      const jobs = jobsRes.data
      setStats({
        pending: jobs.filter((j: any) => j.status === 'PENDING_APPROVAL').length,
        inProgress: jobs.filter((j: any) => ['APPROVED', 'TEAM_ASSIGNED', 'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED', 'VESSEL_ARRIVED', 'CUSTOMS_CLEARED', 'PICKED_UP'].includes(j.status)).length,
        delivered: jobs.filter((j: any) => j.status === 'DELIVERED').length,
        closed: jobs.filter((j: any) => j.status === 'CLOSED').length,
        rejected: jobs.filter((j: any) => j.status === 'REJECTED').length,
        total: jobs.length,
        licenseRequired: jobs.filter((j: any) => j.license_required).length,
        awaitingClearance: jobs.filter((j: any) => j.status === 'PERMIT_SUBMITTED').length
      })
      setRecentJobs(jobs.slice(0, 5))
      setTruckCount(trucksRes.data.length)
      setCustomerCount(customersRes.data.length)
      setVendorCount(vendorsRes.data.length)
    }).catch(() => {})
  }, [])

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of your import operations</p>
      </div>
      
      <div className="grid grid-4 mt-4">
        <div className="stat-card">
          <div className="stat-icon yellow">!</div>
          <div className="stat-value">{stats.pending}</div>
          <div className="stat-label">Pending Approval</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">&rarr;</div>
          <div className="stat-value">{stats.inProgress}</div>
          <div className="stat-label">In Progress</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">&#10003;</div>
          <div className="stat-value">{stats.delivered}</div>
          <div className="stat-label">Delivered</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon purple">&#128196;</div>
          <div className="stat-value">{stats.closed}</div>
          <div className="stat-label">Closed</div>
        </div>
      </div>

      <div className="grid grid-4 mt-4">
        <div className="stat-card">
          <div className="stat-icon red">&#10060;</div>
          <div className="stat-value">{stats.rejected}</div>
          <div className="stat-label">Rejected</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">&#128664;</div>
          <div className="stat-value">{truckCount}</div>
          <div className="stat-label">Active Trucks</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">&#128101;</div>
          <div className="stat-value">{customerCount}</div>
          <div className="stat-label">Customers</div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">&#128188;</div>
          <div className="stat-value">{vendorCount}</div>
          <div className="stat-label">Vendors</div>
        </div>
      </div>

      <div className="grid grid-2 mt-6">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Job Status Overview</span>
          </div>
          <div style={{ padding: '20px' }}>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>Pending</span>
                <span>{stats.pending}</span>
              </div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '20px' }}>
                <div style={{ background: '#f59e0b', borderRadius: '4px', height: '100%', width: `${stats.total ? (stats.pending / stats.total * 100) : 0}%`, transition: 'width 0.3s' }}></div>
              </div>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>In Progress</span>
                <span>{stats.inProgress}</span>
              </div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '20px' }}>
                <div style={{ background: '#3b82f6', borderRadius: '4px', height: '100%', width: `${stats.total ? (stats.inProgress / stats.total * 100) : 0}%`, transition: 'width 0.3s' }}></div>
              </div>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>Delivered</span>
                <span>{stats.delivered}</span>
              </div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '20px' }}>
                <div style={{ background: '#10b981', borderRadius: '4px', height: '100%', width: `${stats.total ? (stats.delivered / stats.total * 100) : 0}%`, transition: 'width 0.3s' }}></div>
              </div>
            </div>
            <div style={{ marginBottom: '15px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>Closed</span>
                <span>{stats.closed}</span>
              </div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '20px' }}>
                <div style={{ background: '#8b5cf6', borderRadius: '4px', height: '100%', width: `${stats.total ? (stats.closed / stats.total * 100) : 0}%`, transition: 'width 0.3s' }}></div>
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                <span>Rejected</span>
                <span>{stats.rejected}</span>
              </div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '20px' }}>
                <div style={{ background: '#ef4444', borderRadius: '4px', height: '100%', width: `${stats.total ? (stats.rejected / stats.total * 100) : 0}%`, transition: 'width 0.3s' }}></div>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Completion Rate</span>
          </div>
          <div style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column' }}>
            <div style={{ position: 'relative', width: '150px', height: '150px' }}>
              <svg viewBox="0 0 36 36" style={{ width: '100%', height: '100%', transform: 'rotate(-90deg)' }}>
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#eee" strokeWidth="3" />
                <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#10b981" strokeWidth="3" strokeDasharray={`${stats.total ? ((stats.delivered + stats.closed) / stats.total * 100) : 0}, 100`} />
              </svg>
              <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#10b981' }}>{stats.total ? Math.round((stats.delivered + stats.closed) / stats.total * 100) : 0}%</div>
                <div style={{ fontSize: '12px', color: '#888' }}>Completed</div>
              </div>
            </div>
            <div style={{ marginTop: '20px', textAlign: 'center' }}>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.delivered + stats.closed}</div>
              <div style={{ color: '#888' }}>of {stats.total} jobs completed</div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-2 mt-6">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Recent Jobs</span>
            <Link to="/jobs" className="card-action">View All</Link>
          </div>
          {recentJobs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">&#128196;</div>
              <p>No jobs yet</p>
            </div>
          ) : (
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th>Job #</th>
                    <th>Container</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentJobs.map(job => (
                    <tr key={job.id}>
                      <td>{job.job_number}</td>
                      <td>{job.container_number || '-'}</td>
                      <td>
                        <span className={`badge ${job.status === 'CLOSED' ? 'badge-completed' : job.status === 'PENDING_APPROVAL' ? 'badge-pending' : job.status === 'REJECTED' ? 'badge-rejected' : 'badge-in-progress'}`}>
                          {job.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function JobList() {
  const { user } = useAuth()
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = () => {
    axios.get(`${API_BASE}/jobs`)
      .then(res => setJobs(res.data))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false))
  }

  const handleApprove = async (jobId: string) => {
    try {
      await axios.put(`${API_BASE}/jobs/${jobId}/approve`)
      loadJobs()
    } catch (err) {
      alert('Failed to approve job')
    }
  }

  const handleReject = async (jobId: string) => {
    try {
      await axios.put(`${API_BASE}/jobs/${jobId}/reject`)
      loadJobs()
    } catch (err) {
      alert('Failed to reject job')
    }
  }

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this job? This cannot be undone.')) return
    try {
      await axios.delete(`${API_BASE}/jobs/${jobId}`)
      loadJobs()
    } catch (err) {
      alert('Failed to delete job')
    }
  }

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = !searchTerm || 
      job.job_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.container_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.vessel_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.consignee?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = !statusFilter || job.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      PENDING_APPROVAL: 'badge-pending',
      APPROVED: 'badge-approved',
      REJECTED: 'badge-rejected',
      CLOSED: 'badge-completed',
      DELIVERED: 'badge-approved'
    }
    const inProgress = ['TEAM_ASSIGNED', 'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED', 'VESSEL_ARRIVED', 'CUSTOMS_CLEARED', 'PICKED_UP']
    if (inProgress.includes(status)) return 'badge-in-progress'
    return statusMap[status] || 'badge-pending'
  }

  const statusOptions = [
    'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'TEAM_ASSIGNED', 'LICENSE_APPROVED',
    'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED', 'VESSEL_ARRIVED', 'CUSTOMS_CLEARED',
    'PICKED_UP', 'DELIVERED', 'UNLOADED', 'CONTAINER_RETURNED', 'CLOSED'
  ]

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Import Jobs</h1>
          <p className="page-subtitle">Manage your import shipments</p>
        </div>
        <Link to="/jobs/new" className="btn btn-primary">+ New Job</Link>
      </div>
      
      <div className="card mb-4">
        <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
          <div className="form-group" style={{ marginBottom: 0, minWidth: '250px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search by job number, container, vessel, consignee..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0, minWidth: '200px' }}>
            <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              {statusOptions.map(s => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div style={{ marginLeft: 'auto', color: '#64748b', fontSize: '0.875rem' }}>
            Showing {filteredJobs.length} of {jobs.length} jobs
          </div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state"><span className="loading-spinner"></span></div>
        ) : filteredJobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">&#128196;</div>
            <p>{searchTerm || statusFilter ? 'No jobs match your search criteria' : 'No import jobs found'}</p>
            {!searchTerm && !statusFilter && <Link to="/jobs/new" className="btn btn-primary mt-4">Create First Job</Link>}
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Job Number</th>
                  <th>Container</th>
                  <th>Vessel</th>
                  <th>ETA</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredJobs.map(job => (
                  <tr key={job.id}>
                    <td><strong>{job.job_number}</strong></td>
                    <td>{job.container_number || '-'}</td>
                    <td>{job.vessel_name || '-'}</td>
                    <td>{job.eta ? new Date(job.eta).toLocaleDateString() : '-'}</td>
                    <td>
                      <span className={`badge ${getStatusBadge(job.status)}`}>
                        {job.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        {job.status === 'PENDING_APPROVAL' && canManage(user) && (
                          <>
                            <button onClick={() => handleApprove(job.id)} className="btn btn-success btn-sm">Approve</button>
                            <button onClick={() => handleReject(job.id)} className="btn btn-danger btn-sm">Reject</button>
                          </>
                        )}
                        <Link to={`/jobs/${job.id}`} className="btn btn-outline btn-sm">View</Link>
                        {isAdmin(user) && (
                          <button onClick={() => handleDelete(job.id)} className="btn btn-danger btn-sm">Delete</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function CreateJob() {
  const [formData, setFormData] = useState({
    container_number: '',
    vessel_name: '',
    eta: '',
    bl_number: '',
    consignee: '',
    cargo_description: '',
    quantity: '',
    license_required: false
  })
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    const selected = localStorage.getItem('selectedTemplate')
    if (selected) {
      const t = JSON.parse(selected)
      setFormData({
        container_number: t.container_number || '',
        vessel_name: t.vessel_name || '',
        eta: '',
        bl_number: '',
        consignee: '',
        cargo_description: t.cargo_description || '',
        quantity: t.quantity ? String(t.quantity) : '',
        license_required: !!t.license_required
      })
      localStorage.removeItem('selectedTemplate')
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await axios.post(`${API_BASE}/jobs`, {
        ...formData,
        eta: formData.eta ? new Date(formData.eta).toISOString() : null,
        quantity: formData.quantity ? parseFloat(formData.quantity) : null
      })
      window.location.href = '/jobs'
    } catch (err) {
      alert('Failed to create job')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Create Import Job</h1>
        <p className="page-subtitle">Enter shipment details</p>
      </div>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Container Number</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., MAEU1234567"
                value={formData.container_number}
                onChange={e => setFormData({...formData, container_number: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Vessel Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., Ever Given"
                value={formData.vessel_name}
                onChange={e => setFormData({...formData, vessel_name: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">ETA</label>
              <input
                type="datetime-local"
                className="form-input"
                value={formData.eta}
                onChange={e => setFormData({...formData, eta: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">BL Number</label>
              <input
                type="text"
                className="form-input"
                placeholder="Bill of Lading number"
                value={formData.bl_number}
                onChange={e => setFormData({...formData, bl_number: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Consignee</label>
              <input
                type="text"
                className="form-input"
                placeholder="Consignee name"
                value={formData.consignee}
                onChange={e => setFormData({...formData, consignee: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Quantity</label>
              <input
                type="number"
                className="form-input"
                placeholder="0.00"
                value={formData.quantity}
                onChange={e => setFormData({...formData, quantity: e.target.value})}
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Cargo Description</label>
            <textarea
              className="form-input"
              rows={3}
              placeholder="Describe the cargo..."
              value={formData.cargo_description}
              onChange={e => setFormData({...formData, cargo_description: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.license_required}
                onChange={e => setFormData({...formData, license_required: e.target.checked})}
                style={{ width: '18px', height: '18px' }}
              />
              <span>Import License Required</span>
            </label>
          </div>
          <div className="flex gap-4">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? <span className="loading-spinner"></span> : 'Create Job'}
            </button>
            <Link to="/jobs" className="btn btn-outline">Cancel</Link>
          </div>
        </form>
      </div>
    </div>
  )
}

function Trucks() {
  const { user } = useAuth()
  const [trucks, setTrucks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    plate_number: '',
    driver_name: '',
    brand: '',
    model: '',
    year_of_manufacture: ''
  })

  useEffect(() => {
    loadTrucks()
  }, [])

  const loadTrucks = () => {
    axios.get(`${API_BASE}/trucks`)
      .then(res => setTrucks(res.data))
      .catch(() => setTrucks([]))
      .finally(() => setLoading(false))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = {
        ...formData,
        year_of_manufacture: formData.year_of_manufacture ? parseInt(formData.year_of_manufacture) : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/trucks/${editingId}`, data)
      } else {
        await axios.post(`${API_BASE}/trucks`, data)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ plate_number: '', driver_name: '', brand: '', model: '', year_of_manufacture: '' })
      loadTrucks()
    } catch (err) {
      alert(editingId ? 'Failed to update truck' : 'Failed to create truck')
    }
  }

  const handleEdit = (truck: any) => {
    setEditingId(truck.id)
    setFormData({
      plate_number: truck.plate_number || '',
      driver_name: truck.driver_name || '',
      brand: truck.brand || '',
      model: truck.model || '',
      year_of_manufacture: truck.year_of_manufacture?.toString() || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this truck?')) return
    try {
      await axios.delete(`${API_BASE}/trucks/${id}`)
      loadTrucks()
    } catch (err) {
      alert('Failed to delete truck')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ plate_number: '', driver_name: '', brand: '', model: '', year_of_manufacture: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Fleet Management</h1>
          <p className="page-subtitle">Manage trucks and drivers</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Truck'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header">
            <span className="card-title">{editingId ? 'Edit Truck' : 'Add New Truck'}</span>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Plate Number <span className="required">*</span></label>
                <input type="text" className="form-input" required placeholder="ABC-1234"
                  value={formData.plate_number}
                  onChange={e => setFormData({...formData, plate_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Driver Name</label>
                <input type="text" className="form-input" placeholder="Driver name"
                  value={formData.driver_name}
                  onChange={e => setFormData({...formData, driver_name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Brand</label>
                <input type="text" className="form-input" placeholder="e.g., Toyota"
                  value={formData.brand}
                  onChange={e => setFormData({...formData, brand: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Model</label>
                <input type="text" className="form-input" placeholder="e.g., Dyna"
                  value={formData.model}
                  onChange={e => setFormData({...formData, model: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Year</label>
                <input type="number" className="form-input" placeholder="2024"
                  value={formData.year_of_manufacture}
                  onChange={e => setFormData({...formData, year_of_manufacture: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Truck' : 'Save Truck'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? (
          <div className="empty-state"><span className="loading-spinner"></span></div>
        ) : trucks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">&#128664;</div>
            <p>No trucks added yet</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Plate Number</th>
                  <th>Driver</th>
                  <th>Brand</th>
                  <th>Model</th>
                  <th>Year</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {trucks.map(truck => (
                  <tr key={truck.id}>
                    <td><strong>{truck.plate_number}</strong></td>
                    <td>{truck.driver_name || '-'}</td>
                    <td>{truck.brand || '-'}</td>
                    <td>{truck.model || '-'}</td>
                    <td>{truck.year_of_manufacture || '-'}</td>
                    <td><span className="badge badge-approved">{truck.status}</span></td>
                    <td>
                      <div className="flex gap-2">
                        {canManage(user) && (
                          <>
                            <button onClick={() => handleEdit(truck)} className="btn btn-outline btn-sm">Edit</button>
                            <button onClick={() => handleDelete(truck.id)} className="btn btn-danger btn-sm">Delete</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Customers() {
  const { user } = useAuth()
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name_kh: '',
    name_eng: '',
    address_1: '',
    contact_person_order: '',
    address_2: '',
    contact_person_payment: '',
    tin: '',
    credit_term: '',
    credit_limit: '',
    sales_person: ''
  })

  useEffect(() => {
    loadCustomers()
  }, [])

  const loadCustomers = () => {
    axios.get(`${API_BASE}/customers`)
      .then(res => setCustomers(res.data))
      .catch(() => setCustomers([]))
      .finally(() => setLoading(false))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = {
        ...formData,
        credit_term: formData.credit_term ? parseInt(formData.credit_term) : null,
        credit_limit: formData.credit_limit ? parseFloat(formData.credit_limit) : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/customers/${editingId}`, data)
      } else {
        await axios.post(`${API_BASE}/customers`, data)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ name_kh: '', name_eng: '', address_1: '', contact_person_order: '', address_2: '', contact_person_payment: '', tin: '', credit_term: '', credit_limit: '', sales_person: '' })
      loadCustomers()
    } catch (err) {
      alert(editingId ? 'Failed to update customer' : 'Failed to create customer')
    }
  }

  const handleEdit = (customer: any) => {
    setEditingId(customer.id)
    setFormData({
      name_kh: customer.name_kh || '',
      name_eng: customer.name_eng || '',
      address_1: customer.address_1 || '',
      contact_person_order: customer.contact_person_order || '',
      address_2: customer.address_2 || '',
      contact_person_payment: customer.contact_person_payment || '',
      tin: customer.tin || '',
      credit_term: customer.credit_term?.toString() || '',
      credit_limit: customer.credit_limit?.toString() || '',
      sales_person: customer.sales_person || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this customer?')) return
    try {
      await axios.delete(`${API_BASE}/customers/${id}`)
      loadCustomers()
    } catch (err) {
      alert('Failed to delete customer')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ name_kh: '', name_eng: '', address_1: '', contact_person_order: '', address_2: '', contact_person_payment: '', tin: '', credit_term: '', credit_limit: '', sales_person: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Customers</h1>
          <p className="page-subtitle">Manage customer accounts</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Customer'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header">
            <span className="card-title">{editingId ? 'Edit Customer' : 'Add New Customer'}</span>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Name (Khmer) <span className="required">*</span></label>
                <input type="text" className="form-input" required
                  value={formData.name_kh}
                  onChange={e => setFormData({...formData, name_kh: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Name (English) <span className="required">*</span></label>
                <input type="text" className="form-input" required
                  value={formData.name_eng}
                  onChange={e => setFormData({...formData, name_eng: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Address</label>
                <input type="text" className="form-input"
                  value={formData.address_1}
                  onChange={e => setFormData({...formData, address_1: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Contact Person (Order)</label>
                <input type="text" className="form-input"
                  value={formData.contact_person_order}
                  onChange={e => setFormData({...formData, contact_person_order: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Address 2 (Payment)</label>
                <input type="text" className="form-input"
                  value={formData.address_2}
                  onChange={e => setFormData({...formData, address_2: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Contact Person (Payment)</label>
                <input type="text" className="form-input"
                  value={formData.contact_person_payment}
                  onChange={e => setFormData({...formData, contact_person_payment: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">TIN</label>
                <input type="text" className="form-input"
                  value={formData.tin}
                  onChange={e => setFormData({...formData, tin: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Credit Term (days)</label>
                <input type="number" className="form-input"
                  value={formData.credit_term}
                  onChange={e => setFormData({...formData, credit_term: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Credit Limit</label>
                <input type="number" className="form-input"
                  value={formData.credit_limit}
                  onChange={e => setFormData({...formData, credit_limit: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Sales Person</label>
                <input type="text" className="form-input"
                  value={formData.sales_person}
                  onChange={e => setFormData({...formData, sales_person: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Customer' : 'Save Customer'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? (
          <div className="empty-state"><span className="loading-spinner"></span></div>
        ) : customers.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">&#128101;</div>
            <p>No customers added yet</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Name (KH)</th>
                  <th>Name (Eng)</th>
                  <th>TIN</th>
                  <th>Credit Term</th>
                  <th>Credit Limit</th>
                  <th>Sales Person</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {customers.map(cust => (
                  <tr key={cust.id}>
                    <td><strong>{cust.name_kh}</strong></td>
                    <td>{cust.name_eng}</td>
                    <td>{cust.tin || '-'}</td>
                    <td>{cust.credit_term ? `${cust.credit_term} days` : '-'}</td>
                    <td>{cust.credit_limit ? `$${cust.credit_limit}` : '-'}</td>
                    <td>{cust.sales_person || '-'}</td>
                    <td>
                      <div className="flex gap-2">
                        {canManage(user) && (
                          <>
                            <button onClick={() => handleEdit(cust)} className="btn btn-outline btn-sm">Edit</button>
                            <button onClick={() => handleDelete(cust.id)} className="btn btn-danger btn-sm">Delete</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Vendors() {
  const { user } = useAuth()
  const [vendors, setVendors] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    name_kh: '',
    name_eng: '',
    address_1: '',
    contact_person_order: '',
    address_2: '',
    contact_person_complaint: '',
    tin: '',
    credit_term: '',
    credit_limit: '',
    bank_name: '',
    account_name: '',
    account_number: ''
  })

  useEffect(() => {
    loadVendors()
  }, [])

  const loadVendors = () => {
    axios.get(`${API_BASE}/vendors`)
      .then(res => setVendors(res.data))
      .catch(() => setVendors([]))
      .finally(() => setLoading(false))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const data = {
        ...formData,
        credit_term: formData.credit_term ? parseInt(formData.credit_term) : null,
        credit_limit: formData.credit_limit ? parseFloat(formData.credit_limit) : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/vendors/${editingId}`, data)
      } else {
        await axios.post(`${API_BASE}/vendors`, data)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ name_kh: '', name_eng: '', address_1: '', contact_person_order: '', address_2: '', contact_person_complaint: '', tin: '', credit_term: '', credit_limit: '', bank_name: '', account_name: '', account_number: '' })
      loadVendors()
    } catch (err) {
      alert(editingId ? 'Failed to update vendor' : 'Failed to create vendor')
    }
  }

  const handleEdit = (vendor: any) => {
    setEditingId(vendor.id)
    setFormData({
      name_kh: vendor.name_kh || '',
      name_eng: vendor.name_eng || '',
      address_1: vendor.address_1 || '',
      contact_person_order: vendor.contact_person_order || '',
      address_2: vendor.address_2 || '',
      contact_person_complaint: vendor.contact_person_complaint || '',
      tin: vendor.tin || '',
      credit_term: vendor.credit_term?.toString() || '',
      credit_limit: vendor.credit_limit?.toString() || '',
      bank_name: vendor.bank_name || '',
      account_name: vendor.account_name || '',
      account_number: vendor.account_number || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this vendor?')) return
    try {
      await axios.delete(`${API_BASE}/vendors/${id}`)
      loadVendors()
    } catch (err) {
      alert('Failed to delete vendor')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ name_kh: '', name_eng: '', address_1: '', contact_person_order: '', address_2: '', contact_person_complaint: '', tin: '', credit_term: '', credit_limit: '', bank_name: '', account_name: '', account_number: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Vendors</h1>
          <p className="page-subtitle">Manage vendor accounts</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Vendor'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header">
            <span className="card-title">{editingId ? 'Edit Vendor' : 'Add New Vendor'}</span>
          </div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Name (Khmer) *</label>
                <input type="text" className="form-input" required
                  value={formData.name_kh}
                  onChange={e => setFormData({...formData, name_kh: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Name (English) *</label>
                <input type="text" className="form-input" required
                  value={formData.name_eng}
                  onChange={e => setFormData({...formData, name_eng: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Address 1 (Order Contact)</label>
                <input type="text" className="form-input"
                  value={formData.address_1}
                  onChange={e => setFormData({...formData, address_1: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Contact Person (Order)</label>
                <input type="text" className="form-input"
                  value={formData.contact_person_order}
                  onChange={e => setFormData({...formData, contact_person_order: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Address 2 (Complaint Contact)</label>
                <input type="text" className="form-input"
                  value={formData.address_2}
                  onChange={e => setFormData({...formData, address_2: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Contact Person (Complaint)</label>
                <input type="text" className="form-input"
                  value={formData.contact_person_complaint}
                  onChange={e => setFormData({...formData, contact_person_complaint: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">TIN</label>
                <input type="text" className="form-input"
                  value={formData.tin}
                  onChange={e => setFormData({...formData, tin: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Credit Term (days)</label>
                <input type="number" className="form-input"
                  value={formData.credit_term}
                  onChange={e => setFormData({...formData, credit_term: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Credit Limit</label>
                <input type="number" className="form-input"
                  value={formData.credit_limit}
                  onChange={e => setFormData({...formData, credit_limit: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Bank Name</label>
                <input type="text" className="form-input"
                  value={formData.bank_name}
                  onChange={e => setFormData({...formData, bank_name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Account Name</label>
                <input type="text" className="form-input"
                  value={formData.account_name}
                  onChange={e => setFormData({...formData, account_name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Account Number</label>
                <input type="text" className="form-input"
                  value={formData.account_number}
                  onChange={e => setFormData({...formData, account_number: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Vendor' : 'Save Vendor'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? (
          <div className="empty-state"><span className="loading-spinner"></span></div>
        ) : vendors.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">&#128188;</div>
            <p>No vendors added yet</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Name (KH)</th>
                  <th>Name (Eng)</th>
                  <th>TIN</th>
                  <th>Credit Term</th>
                  <th>Credit Limit</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {vendors.map(vendor => (
                  <tr key={vendor.id}>
                    <td><strong>{vendor.name_kh}</strong></td>
                    <td>{vendor.name_eng}</td>
                    <td>{vendor.tin || '-'}</td>
                    <td>{vendor.credit_term ? `${vendor.credit_term} days` : '-'}</td>
                    <td>{vendor.credit_limit ? `$${vendor.credit_limit}` : '-'}</td>
                    <td>
                      <div className="flex gap-2">
                        {canManage(user) && (
                          <>
                            <button onClick={() => handleEdit(vendor)} className="btn btn-outline btn-sm">Edit</button>
                            <button onClick={() => handleDelete(vendor.id)} className="btn btn-danger btn-sm">Delete</button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function JobDetail() {
  const { user } = useAuth()
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [trucks, setTrucks] = useState<any[]>([])
  const [trailers, setTrailers] = useState<any[]>([])
  const [drivers, setDrivers] = useState<any[]>([])
  const [locations, setLocations] = useState<any[]>([])
  const [vendors, setVendors] = useState<any[]>([])
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showDeliveryModal, setShowDeliveryModal] = useState(false)
  const [showAssignTeamModal, setShowAssignTeamModal] = useState(false)
  const [assignData, setAssignData] = useState({ truck_id: '', trailer_id: '', driver_id: '', is_outsourced: false, vendor_id: '' })
  const [deliveryData, setDeliveryData] = useState({ location_id: '', eir_number: '' })
  const [teamData, setTeamData] = useState({ team: '' })

  const jobId = window.location.pathname.split('/').pop()

  useEffect(() => {
    loadData()
  }, [jobId])

  const loadData = () => {
    Promise.all([
      axios.get(`${API_BASE}/jobs/${jobId}`),
      axios.get(`${API_BASE}/trucks`),
      axios.get(`${API_BASE}/trailers`),
      axios.get(`${API_BASE}/drivers`),
      axios.get(`${API_BASE}/locations`),
      axios.get(`${API_BASE}/vendors`)
    ]).then(([jobRes, trucksRes, trailersRes, driversRes, locationsRes, vendorsRes]) => {
      setJob(jobRes.data)
      setTrucks(trucksRes.data)
      setTrailers(trailersRes.data)
      setDrivers(driversRes.data)
      setLocations(locationsRes.data)
      setVendors(vendorsRes.data)
    }).catch(() => {
      alert('Failed to load job')
    }).finally(() => setLoading(false))
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this job? This cannot be undone.')) return
    try {
      await axios.delete(`${API_BASE}/jobs/${jobId}`)
      window.location.href = '/jobs'
    } catch (err) {
      alert('Failed to delete job')
    }
  }

  const updateJobStatus = async (action: string, data?: any) => {
    try {
      const endpoint = `${API_BASE}/jobs/${jobId}/${action}`
      if (data) {
        await axios.put(endpoint, data)
      } else {
        await axios.put(endpoint)
      }
      loadData()
    } catch (err) {
      alert(`Failed to ${action.replace('-', ' ')}`)
    }
  }

  const handleAssignTruck = async () => {
    await updateJobStatus('truck', {
      truck_id: assignData.truck_id || null,
      trailer_id: assignData.trailer_id || null,
      driver_id: assignData.driver_id || null,
      is_outsourced: assignData.is_outsourced,
      vendor_id: assignData.vendor_id || null
    })
    setShowAssignModal(false)
  }

  const handleAssignTeam = async () => {
    if (!teamData.team.trim()) {
      alert('Please enter team name')
      return
    }
    await updateJobStatus('assign-team', { team: teamData.team })
    setShowAssignTeamModal(false)
    setTeamData({ team: '' })
  }

  const handleDelivery = async () => {
    if (!deliveryData.location_id) {
      alert('Please select a delivery location')
      return
    }
    await updateJobStatus('deliver', { 
      delivery_location_id: deliveryData.location_id, 
      eir_number: deliveryData.eir_number || `EIR-${Date.now()}` 
    })
    setShowDeliveryModal(false)
    setDeliveryData({ location_id: '', eir_number: '' })
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      PENDING_APPROVAL: 'badge-pending',
      APPROVED: 'badge-approved',
      REJECTED: 'badge-rejected',
      CLOSED: 'badge-completed',
      DELIVERED: 'badge-approved'
    }
    const inProgress = ['TEAM_ASSIGNED', 'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED', 'VESSEL_ARRIVED', 'CUSTOMS_CLEARED', 'PICKED_UP']
    if (inProgress.includes(status)) return 'badge-in-progress'
    return statusMap[status] || 'badge-pending'
  }

  const workflowSteps = [
    { key: 'PENDING_APPROVAL', label: 'Pending', action: null },
    { key: 'APPROVED', label: 'Approved', action: 'approve' },
    { key: 'TEAM_ASSIGNED', label: 'Team Assigned', action: 'assign-team' },
    { key: 'PERMIT_SUBMITTED', label: 'Permit Submitted', action: 'customs-permit' },
    { key: 'TRUCK_ASSIGNED', label: 'Truck Assigned', action: null },
    { key: 'VESSEL_ARRIVED', label: 'Vessel Arrived', action: 'arrival' },
    { key: 'CUSTOMS_CLEARED', label: 'Customs Cleared', action: 'clearance' },
    { key: 'PICKED_UP', label: 'Picked Up', action: 'pickup' },
    { key: 'DELIVERED', label: 'Delivered', action: 'deliver' },
    { key: 'UNLOADED', label: 'Unloaded', action: 'unload' },
    { key: 'CONTAINER_RETURNED', label: 'Container Returned', action: 'return-container' },
    { key: 'CLOSED', label: 'Closed', action: 'close' }
  ]

  const getStepStatus = (_stepKey: string, index: number) => {
    if (!job) return ''
    const currentIndex = workflowSteps.findIndex(s => s.key === job.status)
    if (index < currentIndex) return 'completed'
    if (index === currentIndex) return 'active'
    return ''
  }

  if (loading) return <div className="empty-state"><span className="loading-spinner"></span></div>
  if (!job) return <div className="empty-state">Job not found</div>

  const assignedTrailer = trailers.find(t => t.id === job.trailer_id)
  const assignedTruck = trucks.find(t => t.id === job.truck_id)
  const assignedDriver = drivers.find(d => d.id === job.driver_id)

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">{job.job_number}</h1>
          <p className="page-subtitle">Job Details</p>
        </div>
        <span className={`badge ${getStatusBadge(job.status)}`}>{job.status.replace(/_/g, ' ')}</span>
      </div>

      <div className="card mb-4">
        <div className="card-header">
          <span className="card-title">Workflow Progress</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {workflowSteps.map((step, index) => (
            <div key={step.key} className={`status-step ${getStepStatus(step.key, index)}`}>
              {step.label}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Shipment Details</span>
          </div>
          <div className="grid grid-2">
            <div><p className="text-sm text-muted">Container</p><p>{job.container_number || '-'}</p></div>
            <div><p className="text-sm text-muted">Vessel</p><p>{job.vessel_name || '-'}</p></div>
            <div><p className="text-sm text-muted">ETA</p><p>{job.eta ? new Date(job.eta).toLocaleDateString() : '-'}</p></div>
            <div><p className="text-sm text-muted">ATA</p><p>{job.ata ? new Date(job.ata).toLocaleDateString() : '-'}</p></div>
            <div><p className="text-sm text-muted">BL Number</p><p>{job.bl_number || '-'}</p></div>
            <div><p className="text-sm text-muted">Consignee</p><p>{job.consignee || '-'}</p></div>
            <div><p className="text-sm text-muted">Quantity</p><p>{job.quantity || '-'}</p></div>
            <div><p className="text-sm text-muted">License Required</p><p>{job.license_required ? 'Yes' : 'No'}</p></div>
            {job.truck_id && <div><p className="text-sm text-muted">Assigned Truck</p><p>{assignedTruck?.plate_number || job.truck_id || '-'}</p></div>}
            {job.trailer_id && <div><p className="text-sm text-muted">Assigned Trailer</p><p>{assignedTrailer?.trailer_number || job.trailer_id || '-'}</p></div>}
            {job.driver_id && <div><p className="text-sm text-muted">Assigned Driver</p><p>{assignedDriver?.identification_card_number || job.driver_id || '-'}</p></div>}
          </div>
          <div className="mt-4">
            <p className="text-sm text-muted">Cargo Description</p>
            <p>{job.cargo_description || '-'}</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Actions</span>
          </div>
          <div className="flex flex-col gap-2">
            {job.status === 'PENDING_APPROVAL' && canManage(user) && (
              <>
                <button onClick={() => updateJobStatus('approve')} className="btn btn-success">Approve Job</button>
                <button onClick={() => updateJobStatus('reject')} className="btn btn-danger">Reject Job</button>
              </>
            )}
            {job.status === 'APPROVED' && (
              <>
                {canManage(user) && (
                  <button onClick={() => setShowAssignTeamModal(true)} className="btn btn-primary">Assign Team</button>
                )}
                {job.license_required && (
                  <button onClick={() => updateJobStatus('apply-license')} className="btn btn-outline">Apply License</button>
                )}
              </>
            )}
            {(job.status === 'TEAM_ASSIGNED' || (!job.license_required && job.status === 'APPROVED')) && (
              <button onClick={() => updateJobStatus('customs-permit', { status: 'SUBMITTED' })} className="btn btn-primary">Submit Customs Permit</button>
            )}
            {job.status === 'PERMIT_SUBMITTED' && (
              <button onClick={() => {
                setAssignData({ truck_id: job.truck_id || '', trailer_id: job.trailer_id || '', driver_id: job.driver_id || '', is_outsourced: !!job.is_outsourced, vendor_id: job.vendor_id || '' })
                setShowAssignModal(true)
              }} className="btn btn-primary">Assign Truck</button>
            )}
            {job.status === 'TRUCK_ASSIGNED' && (
              <button onClick={() => updateJobStatus('arrival', { ata: new Date().toISOString() })} className="btn btn-primary">Record Vessel Arrival</button>
            )}
            {job.status === 'VESSEL_ARRIVED' && (
              <button onClick={() => updateJobStatus('clearance', { customs_permit_status: 'CLEARED' })} className="btn btn-primary">Process Customs Clearance</button>
            )}
            {job.status === 'CUSTOMS_CLEARED' && (
              <button onClick={() => updateJobStatus('pickup')} className="btn btn-primary">Container Pick Up</button>
            )}
            {job.status === 'PICKED_UP' && (
              <button onClick={() => setShowDeliveryModal(true)} className="btn btn-primary">Deliver to Customer</button>
            )}
            {job.status === 'DELIVERED' && (
              <button onClick={() => updateJobStatus('unload')} className="btn btn-primary">Confirm Unloaded</button>
            )}
            {job.status === 'UNLOADED' && (
              <button onClick={() => updateJobStatus('return-container', { eir_number: 'EIR-' + Date.now() })} className="btn btn-primary">Return Empty Container</button>
            )}
            {job.status === 'CONTAINER_RETURNED' && canManage(user) && (
              <button onClick={() => updateJobStatus('close')} className="btn btn-success">Close Job</button>
            )}
            {isAdmin(user) && (
              <button onClick={handleDelete} className="btn btn-danger">Delete Job</button>
            )}
            <PrintJobCard job={job} />
          </div>
        </div>

        <div className="grid grid-2 mt-4">
          <ActivityLog jobId={job.id} />
          <DocumentUpload jobId={job.id} />
        </div>
      </div>

      {showAssignModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">Assign Truck</span>
              <button onClick={() => setShowAssignModal(false)} className="modal-close">&times;</button>
            </div>
            <div className="form-group">
              <label className="form-label">Use External Vendor?</label>
              <input type="checkbox" checked={assignData.is_outsourced} onChange={e => setAssignData({...assignData, is_outsourced: e.target.checked})} />
            </div>
            {assignData.is_outsourced ? (
              <div className="form-group">
                <label className="form-label">Vendor</label>
                <select className="form-select" value={assignData.vendor_id} onChange={e => setAssignData({...assignData, vendor_id: e.target.value})}>
                  <option value="">Select Vendor</option>
                  {vendors.map(v => <option key={v.id} value={v.id}>{v.name_eng}</option>)}
                </select>
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Truck</label>
                  <select className="form-select" value={assignData.truck_id} onChange={e => setAssignData({...assignData, truck_id: e.target.value})}>
                    <option value="">Select Truck</option>
                    {trucks.map(t => <option key={t.id} value={t.id}>{t.plate_number}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Driver</label>
                  <select className="form-select" value={assignData.driver_id} onChange={e => setAssignData({...assignData, driver_id: e.target.value})}>
                    <option value="">Select Driver</option>
                    {drivers.map(d => <option key={d.id} value={d.id}>{d.identification_card_number}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Trailer</label>
                  <select className="form-select" value={assignData.trailer_id} onChange={e => setAssignData({...assignData, trailer_id: e.target.value})}>
                    <option value="">Select Trailer</option>
                    {trailers.map(t => <option key={t.id} value={t.id}>{t.trailer_number}</option>)}
                  </select>
                </div>
              </>
            )}
            <button onClick={handleAssignTruck} className="btn btn-primary mt-4">Confirm Assignment</button>
          </div>
        </div>
      )}

      {showDeliveryModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">Deliver to Customer</span>
              <button onClick={() => setShowDeliveryModal(false)} className="modal-close">&times;</button>
            </div>
            <div className="form-group">
              <label className="form-label">Delivery Location <span className="required">*</span></label>
              <select className="form-select" value={deliveryData.location_id} onChange={e => setDeliveryData({...deliveryData, location_id: e.target.value})}>
                <option value="">Select Location</option>
                {locations.map(l => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">EIR Number</label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Auto-generated if empty"
                value={deliveryData.eir_number}
                onChange={e => setDeliveryData({...deliveryData, eir_number: e.target.value})}
              />
            </div>
            <button onClick={handleDelivery} className="btn btn-primary mt-4">Confirm Delivery</button>
          </div>
        </div>
      )}

      {showAssignTeamModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">Assign Team</span>
              <button onClick={() => setShowAssignTeamModal(false)} className="modal-close">&times;</button>
            </div>
            <div className="form-group">
              <label className="form-label">Team Name <span className="required">*</span></label>
              <input 
                type="text" 
                className="form-input" 
                placeholder="Enter team name"
                value={teamData.team}
                onChange={e => setTeamData({...teamData, team: e.target.value})}
              />
            </div>
            <button onClick={handleAssignTeam} className="btn btn-primary mt-4">Confirm Assignment</button>
          </div>
        </div>
      )}

      <Link to="/jobs" className="btn btn-outline">Back to Jobs</Link>
    </div>
  )
}

function ExportJobList() {
  const { user } = useAuth()
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = () => {
    axios.get(`${API_BASE}/exports`)
      .then(res => setJobs(res.data))
      .catch(() => setJobs([]))
      .finally(() => setLoading(false))
  }

  const handleApprove = async (jobId: string) => {
    try {
      await axios.put(`${API_BASE}/exports/${jobId}/approve`)
      loadJobs()
    } catch (err) {
      alert('Failed to approve export job')
    }
  }

  const handleReject = async (jobId: string) => {
    try {
      await axios.put(`${API_BASE}/exports/${jobId}/reject`)
      loadJobs()
    } catch (err) {
      alert('Failed to reject export job')
    }
  }

  const handleDelete = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this export job? This cannot be undone.')) return
    try {
      await axios.delete(`${API_BASE}/exports/${jobId}`)
      loadJobs()
    } catch (err) {
      alert('Failed to delete export job')
    }
  }

  const filteredJobs = jobs.filter(job => {
    const matchesSearch = !searchTerm ||
      job.job_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.container_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.vessel_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.shipper?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      job.consignee?.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = !statusFilter || job.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      PENDING_APPROVAL: 'badge-pending',
      APPROVED: 'badge-approved',
      REJECTED: 'badge-rejected',
      CLOSED: 'badge-completed',
      EXPORT_CLEARED: 'badge-approved'
    }
    const inProgress = ['TEAM_ASSIGNED', 'EMPTY_PICKED_UP', 'STUFFED', 'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED', 'GATE_IN', 'VESSEL_DEPARTED']
    if (inProgress.includes(status)) return 'badge-in-progress'
    return statusMap[status] || 'badge-pending'
  }

  const statusOptions = [
    'PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'TEAM_ASSIGNED',
    'EMPTY_PICKED_UP', 'STUFFED', 'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED',
    'GATE_IN', 'VESSEL_DEPARTED', 'EXPORT_CLEARED', 'CLOSED'
  ]

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Export Jobs</h1>
          <p className="page-subtitle">Manage outbound export shipments</p>
        </div>
        <Link to="/exports/new" className="btn btn-primary">+ New Export Job</Link>
      </div>

      <div className="card mb-4">
        <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
          <div className="form-group" style={{ marginBottom: 0, minWidth: '250px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search by job number, container, vessel, shipper..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0, minWidth: '200px' }}>
            <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              {statusOptions.map(s => (
                <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
              ))}
            </select>
          </div>
          <div style={{ marginLeft: 'auto', color: '#64748b', fontSize: '0.875rem' }}>
            Showing {filteredJobs.length} of {jobs.length} export jobs
          </div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <div className="empty-state"><span className="loading-spinner"></span></div>
        ) : filteredJobs.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">&#128666;</div>
            <p>{searchTerm || statusFilter ? 'No export jobs match your search criteria' : 'No export jobs found'}</p>
            {!searchTerm && !statusFilter && <Link to="/exports/new" className="btn btn-primary mt-4">Create First Export Job</Link>}
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Job Number</th>
                  <th>Container</th>
                  <th>Vessel</th>
                  <th>ETD</th>
                  <th>Shipper</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredJobs.map(job => (
                  <tr key={job.id}>
                    <td><strong>{job.job_number}</strong></td>
                    <td>{job.container_number || '-'}</td>
                    <td>{job.vessel_name || '-'}</td>
                    <td>{job.etd ? new Date(job.etd).toLocaleDateString() : '-'}</td>
                    <td>{job.shipper || '-'}</td>
                    <td>
                      <span className={`badge ${getStatusBadge(job.status)}`}>
                        {job.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        {job.status === 'PENDING_APPROVAL' && canManage(user) && (
                          <>
                            <button onClick={() => handleApprove(job.id)} className="btn btn-success btn-sm">Approve</button>
                            <button onClick={() => handleReject(job.id)} className="btn btn-danger btn-sm">Reject</button>
                          </>
                        )}
                        <Link to={`/exports/${job.id}`} className="btn btn-outline btn-sm">View</Link>
                        {isAdmin(user) && (
                          <button onClick={() => handleDelete(job.id)} className="btn btn-danger btn-sm">Delete</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function CreateExportJob() {
  const [formData, setFormData] = useState({
    container_number: '',
    vessel_name: '',
    etd: '',
    bl_number: '',
    shipper: '',
    consignee: '',
    cargo_description: '',
    quantity: '',
    license_required: false
  })
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await axios.post(`${API_BASE}/exports`, {
        ...formData,
        etd: formData.etd ? new Date(formData.etd).toISOString() : null,
        quantity: formData.quantity ? parseFloat(formData.quantity) : null
      })
      window.location.href = '/exports'
    } catch (err) {
      alert('Failed to create export job')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Create Export Job</h1>
        <p className="page-subtitle">Enter outbound shipment details</p>
      </div>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-2">
            <div className="form-group">
              <label className="form-label">Container Number</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., MAEU1234567"
                value={formData.container_number}
                onChange={e => setFormData({...formData, container_number: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Vessel Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g., Ever Given"
                value={formData.vessel_name}
                onChange={e => setFormData({...formData, vessel_name: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">ETD</label>
              <input
                type="datetime-local"
                className="form-input"
                value={formData.etd}
                onChange={e => setFormData({...formData, etd: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">BL Number</label>
              <input
                type="text"
                className="form-input"
                placeholder="Bill of Lading number"
                value={formData.bl_number}
                onChange={e => setFormData({...formData, bl_number: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Shipper</label>
              <input
                type="text"
                className="form-input"
                placeholder="Exporter / shipper name"
                value={formData.shipper}
                onChange={e => setFormData({...formData, shipper: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Consignee</label>
              <input
                type="text"
                className="form-input"
                placeholder="Overseas consignee"
                value={formData.consignee}
                onChange={e => setFormData({...formData, consignee: e.target.value})}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Quantity</label>
              <input
                type="number"
                className="form-input"
                placeholder="0.00"
                value={formData.quantity}
                onChange={e => setFormData({...formData, quantity: e.target.value})}
              />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Cargo Description</label>
            <textarea
              className="form-input"
              rows={3}
              placeholder="Describe the cargo..."
              value={formData.cargo_description}
              onChange={e => setFormData({...formData, cargo_description: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.license_required}
                onChange={e => setFormData({...formData, license_required: e.target.checked})}
                style={{ width: '18px', height: '18px' }}
              />
              <span>Export License Required</span>
            </label>
          </div>
          <div className="flex gap-4">
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? <span className="loading-spinner"></span> : 'Create Export Job'}
            </button>
            <Link to="/exports" className="btn btn-outline">Cancel</Link>
          </div>
        </form>
      </div>
    </div>
  )
}

function ExportActivityLog({ jobId }: { jobId: string }) {
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API_BASE}/exports/activities?job_id=${jobId}`)
      .then(res => setActivities(res.data))
      .catch(() => setActivities([]))
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) return <div className="empty-state"><span className="loading-spinner"></span></div>

  return (
    <div className="card">
      <div className="card-header"><span className="card-title">Activity Log</span></div>
      <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
        {activities.length === 0 ? (
          <div className="empty-state"><p>No activity recorded</p></div>
        ) : (
          <div style={{ padding: '15px' }}>
            {activities.map((a: any) => (
              <div key={a.id} style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <strong style={{ fontSize: '13px' }}>{a.action.replace(/_/g, ' ')}</strong>
                  <span style={{ fontSize: '11px', color: '#888' }}>{new Date(a.created_at).toLocaleString()}</span>
                </div>
                <p style={{ fontSize: '13px', color: '#555', margin: 0 }}>{a.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function ExportDocumentUpload({ jobId }: { jobId: string }) {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<any[]>([])
  const [uploading, setUploading] = useState(false)

  const loadDocuments = () => {
    axios.get(`${API_BASE}/exports/${jobId}/documents`)
      .then(res => setDocuments(res.data))
      .catch(() => setDocuments([]))
  }

  useEffect(() => {
    loadDocuments()
  }, [jobId])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const dataBase64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const result = reader.result as string
          resolve(result.split(',')[1] || '')
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      await axios.post(`${API_BASE}/exports/${jobId}/documents`, {
        filename: file.name,
        data_base64: dataBase64,
        file_type: file.type || 'application/octet-stream'
      })
      loadDocuments()
    } catch (err) {
      alert('Failed to upload document')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const deleteDoc = async (id: string) => {
    if (!confirm('Delete this document?')) return
    try {
      await axios.delete(`${API_BASE}/export-documents/${id}`)
      loadDocuments()
    } catch (err) {
      alert('Failed to delete document')
    }
  }

  return (
    <div className="card">
      <div className="card-header"><span className="card-title">Documents</span></div>
      <div style={{ padding: '15px' }}>
        <label className="btn btn-outline" style={{ cursor: 'pointer', display: 'inline-block', marginBottom: '15px' }}>
          {uploading ? 'Uploading...' : '+ Upload Document'}
          <input type="file" hidden onChange={handleUpload} />
        </label>
        {documents.length === 0 ? (
          <p style={{ color: '#888', fontSize: '13px' }}>No documents uploaded</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {documents.map(d => (
              <div key={d.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f5f5f5', borderRadius: '6px' }}>
                <div>
                  <strong style={{ fontSize: '13px' }}>{d.filename || d.name}</strong>
                  <div style={{ fontSize: '11px', color: '#888' }}>{new Date(d.created_at || d.date).toLocaleDateString()}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {canManage(user) && (
                    <button onClick={() => deleteDoc(d.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>&times;</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function PrintExportCard({ job }: { job: any }) {
  const [showPrint, setShowPrint] = useState(false)

  if (!showPrint) return <button onClick={() => setShowPrint(true)} className="btn btn-outline">Print Export Card</button>

  return (
    <div>
      <div className="modal-overlay" onClick={() => setShowPrint(false)}>
        <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
          <div className="modal-header">
            <span className="modal-title">Export Job Card - {job.job_number}</span>
            <button onClick={() => setShowPrint(false)} className="modal-close">&times;</button>
          </div>
          <div id="printable-export-job-card" style={{ padding: '20px', fontSize: '12px' }}>
            <div style={{ border: '2px solid #333', padding: '20px', borderRadius: '8px' }}>
              <h2 style={{ textAlign: 'center', marginBottom: '20px', borderBottom: '2px solid #333', paddingBottom: '10px' }}>CARGO FLOW - EXPORT JOB CARD</h2>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Job Number</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.job_number}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Status</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.status}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Container No</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.container_number || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Vessel Name</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.vessel_name || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>BL Number</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.bl_number || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Shipper</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.shipper || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Consignee</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.consignee || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Cargo Description</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.cargo_description || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Quantity</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.quantity || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>ETD</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.etd ? new Date(job.etd).toLocaleDateString() : '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Assigned Team</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.assigned_team || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>EIR Number</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.eir_number || '-'}</td></tr>
                </tbody>
              </table>
              <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '10px', color: '#888' }}>
                Printed on: {new Date().toLocaleString()} | CargoFlow Import Management System
              </div>
            </div>
          </div>
          <div style={{ padding: '15px', borderTop: '1px solid #eee', display: 'flex', gap: '10px' }}>
            <button onClick={() => window.print()} className="btn btn-primary">Print</button>
            <button onClick={() => setShowPrint(false)} className="btn btn-outline">Close</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function ExportJobDetail() {
  const { user } = useAuth()
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [trucks, setTrucks] = useState<any[]>([])
  const [trailers, setTrailers] = useState<any[]>([])
  const [drivers, setDrivers] = useState<any[]>([])
  const [vendors, setVendors] = useState<any[]>([])
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showAssignTeamModal, setShowAssignTeamModal] = useState(false)
  const [assignData, setAssignData] = useState({ truck_id: '', trailer_id: '', driver_id: '', is_outsourced: false, vendor_id: '' })
  const [teamData, setTeamData] = useState({ team: '' })

  const jobId = window.location.pathname.split('/').pop()

  useEffect(() => {
    loadData()
  }, [jobId])

  const loadData = () => {
    Promise.all([
      axios.get(`${API_BASE}/exports/${jobId}`),
      axios.get(`${API_BASE}/trucks`),
      axios.get(`${API_BASE}/trailers`),
      axios.get(`${API_BASE}/drivers`),
      axios.get(`${API_BASE}/vendors`)
    ]).then(([jobRes, trucksRes, trailersRes, driversRes, vendorsRes]) => {
      setJob(jobRes.data)
      setTrucks(trucksRes.data)
      setTrailers(trailersRes.data)
      setDrivers(driversRes.data)
      setVendors(vendorsRes.data)
    }).catch(() => {
      alert('Failed to load export job')
    }).finally(() => setLoading(false))
  }

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this export job? This cannot be undone.')) return
    try {
      await axios.delete(`${API_BASE}/exports/${jobId}`)
      window.location.href = '/exports'
    } catch (err) {
      alert('Failed to delete export job')
    }
  }

  const updateJobStatus = async (action: string, data?: any) => {
    try {
      const endpoint = `${API_BASE}/exports/${jobId}/${action}`
      if (data !== undefined) {
        await axios.put(endpoint, data)
      } else {
        await axios.put(endpoint)
      }
      loadData()
    } catch (err) {
      alert(`Failed to ${action.replace('-', ' ')}`)
    }
  }

  const handleAssignTruck = async () => {
    await updateJobStatus('truck', {
      truck_id: assignData.truck_id || null,
      trailer_id: assignData.trailer_id || null,
      driver_id: assignData.driver_id || null,
      is_outsourced: assignData.is_outsourced,
      vendor_id: assignData.vendor_id || null
    })
    setShowAssignModal(false)
  }

  const handleAssignTeam = async () => {
    if (!teamData.team.trim()) {
      alert('Please enter team name')
      return
    }
    await updateJobStatus('assign-team', { team: teamData.team })
    setShowAssignTeamModal(false)
    setTeamData({ team: '' })
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, string> = {
      PENDING_APPROVAL: 'badge-pending',
      APPROVED: 'badge-approved',
      REJECTED: 'badge-rejected',
      CLOSED: 'badge-completed',
      EXPORT_CLEARED: 'badge-approved'
    }
    const inProgress = ['TEAM_ASSIGNED', 'EMPTY_PICKED_UP', 'STUFFED', 'PERMIT_SUBMITTED', 'TRUCK_ASSIGNED', 'GATE_IN', 'VESSEL_DEPARTED']
    if (inProgress.includes(status)) return 'badge-in-progress'
    return statusMap[status] || 'badge-pending'
  }

  const workflowSteps = [
    { key: 'PENDING_APPROVAL', label: 'Pending', action: null },
    { key: 'APPROVED', label: 'Approved', action: 'approve' },
    { key: 'TEAM_ASSIGNED', label: 'Team Assigned', action: 'assign-team' },
    { key: 'EMPTY_PICKED_UP', label: 'Empty Picked Up', action: 'empty-pickup' },
    { key: 'STUFFED', label: 'Stuffed', action: 'stuff' },
    { key: 'PERMIT_SUBMITTED', label: 'Permit Submitted', action: 'customs-permit' },
    { key: 'TRUCK_ASSIGNED', label: 'Truck Assigned', action: 'truck' },
    { key: 'GATE_IN', label: 'Gated In', action: 'gate-in' },
    { key: 'VESSEL_DEPARTED', label: 'Vessel Departed', action: 'departure' },
    { key: 'EXPORT_CLEARED', label: 'Export Cleared', action: 'clearance' },
    { key: 'CLOSED', label: 'Closed', action: 'close' }
  ]

  const getStepStatus = (_stepKey: string, index: number) => {
    if (!job) return ''
    const currentIndex = workflowSteps.findIndex(s => s.key === job.status)
    if (index < currentIndex) return 'completed'
    if (index === currentIndex) return 'active'
    return ''
  }

  if (loading) return <div className="empty-state"><span className="loading-spinner"></span></div>
  if (!job) return <div className="empty-state">Export job not found</div>

  const assignedTrailer = trailers.find(t => t.id === job.trailer_id)
  const assignedTruck = trucks.find(t => t.id === job.truck_id)
  const assignedDriver = drivers.find(d => d.id === job.driver_id)

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">{job.job_number}</h1>
          <p className="page-subtitle">Export Job Details</p>
        </div>
        <span className={`badge ${getStatusBadge(job.status)}`}>{job.status.replace(/_/g, ' ')}</span>
      </div>

      <div className="card mb-4">
        <div className="card-header">
          <span className="card-title">Workflow Progress</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {workflowSteps.map((step, index) => (
            <div key={step.key} className={`status-step ${getStepStatus(step.key, index)}`}>
              {step.label}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-header">
            <span className="card-title">Shipment Details</span>
          </div>
          <div className="grid grid-2">
            <div><p className="text-sm text-muted">Container</p><p>{job.container_number || '-'}</p></div>
            <div><p className="text-sm text-muted">Vessel</p><p>{job.vessel_name || '-'}</p></div>
            <div><p className="text-sm text-muted">ETD</p><p>{job.etd ? new Date(job.etd).toLocaleDateString() : '-'}</p></div>
            <div><p className="text-sm text-muted">ATD</p><p>{job.atd ? new Date(job.atd).toLocaleDateString() : '-'}</p></div>
            <div><p className="text-sm text-muted">BL Number</p><p>{job.bl_number || '-'}</p></div>
            <div><p className="text-sm text-muted">Shipper</p><p>{job.shipper || '-'}</p></div>
            <div><p className="text-sm text-muted">Consignee</p><p>{job.consignee || '-'}</p></div>
            <div><p className="text-sm text-muted">Quantity</p><p>{job.quantity || '-'}</p></div>
            <div><p className="text-sm text-muted">License Required</p><p>{job.license_required ? 'Yes' : 'No'}</p></div>
            <div><p className="text-sm text-muted">Assigned Team</p><p>{job.assigned_team || '-'}</p></div>
            {job.empty_pickup_date && <div><p className="text-sm text-muted">Empty Picked Up</p><p>{new Date(job.empty_pickup_date).toLocaleDateString()}</p></div>}
            {job.gate_in_date && <div><p className="text-sm text-muted">Gated In</p><p>{new Date(job.gate_in_date).toLocaleDateString()}</p></div>}
            {job.eir_number && <div><p className="text-sm text-muted">EIR Number</p><p>{job.eir_number}</p></div>}
            {job.truck_id && <div><p className="text-sm text-muted">Assigned Truck</p><p>{assignedTruck?.plate_number || job.truck_id || '-'}</p></div>}
            {job.trailer_id && <div><p className="text-sm text-muted">Assigned Trailer</p><p>{assignedTrailer?.trailer_number || job.trailer_id || '-'}</p></div>}
            {job.driver_id && <div><p className="text-sm text-muted">Assigned Driver</p><p>{assignedDriver?.identification_card_number || job.driver_id || '-'}</p></div>}
          </div>
          <div className="mt-4">
            <p className="text-sm text-muted">Cargo Description</p>
            <p>{job.cargo_description || '-'}</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">Actions</span>
          </div>
          <div className="flex flex-col gap-2">
            {job.status === 'PENDING_APPROVAL' && canManage(user) && (
              <>
                <button onClick={() => updateJobStatus('approve')} className="btn btn-success">Approve Job</button>
                <button onClick={() => updateJobStatus('reject')} className="btn btn-danger">Reject Job</button>
              </>
            )}
            {job.status === 'APPROVED' && (
              <>
                {canManage(user) && (
                  <button onClick={() => setShowAssignTeamModal(true)} className="btn btn-primary">Assign Team</button>
                )}
                {job.license_required && !job.license_approved && (
                  <button onClick={() => updateJobStatus('apply-license')} className="btn btn-outline">Apply Export License</button>
                )}
              </>
            )}
            {job.status === 'TEAM_ASSIGNED' && (
              <button onClick={() => updateJobStatus('empty-pickup')} className="btn btn-primary">Pick Up Empty Container</button>
            )}
            {job.status === 'EMPTY_PICKED_UP' && (
              <button onClick={() => updateJobStatus('stuff')} className="btn btn-primary">Confirm Stuffing</button>
            )}
            {job.status === 'STUFFED' && (
              <>
                <button onClick={() => updateJobStatus('customs-permit', { status: 'SUBMITTED' })} className="btn btn-primary">Submit Export Permit</button>
                {job.license_required && !job.license_approved && (
                  <button onClick={() => updateJobStatus('apply-license')} className="btn btn-outline">Apply Export License</button>
                )}
              </>
            )}
            {job.status === 'PERMIT_SUBMITTED' && (
              <button onClick={() => {
                setAssignData({ truck_id: job.truck_id || '', trailer_id: job.trailer_id || '', driver_id: job.driver_id || '', is_outsourced: !!job.is_outsourced, vendor_id: job.vendor_id || '' })
                setShowAssignModal(true)
              }} className="btn btn-primary">Assign Truck</button>
            )}
            {job.status === 'TRUCK_ASSIGNED' && (
              <button onClick={() => updateJobStatus('gate-in', {})} className="btn btn-primary">Gate In Container</button>
            )}
            {job.status === 'GATE_IN' && (
              <button onClick={() => updateJobStatus('departure', { atd: new Date().toISOString() })} className="btn btn-primary">Record Vessel Departure</button>
            )}
            {job.status === 'VESSEL_DEPARTED' && (
              <button onClick={() => updateJobStatus('clearance', { customs_permit_status: 'CLEARED' })} className="btn btn-primary">Process Export Clearance</button>
            )}
            {job.status === 'EXPORT_CLEARED' && canManage(user) && (
              <button onClick={() => updateJobStatus('close')} className="btn btn-success">Close Job</button>
            )}
            {isAdmin(user) && (
              <button onClick={handleDelete} className="btn btn-danger">Delete Job</button>
            )}
            <PrintExportCard job={job} />
          </div>
        </div>

        <div className="grid grid-2 mt-4">
          <ExportActivityLog jobId={job.id} />
          <ExportDocumentUpload jobId={job.id} />
        </div>
      </div>

      {showAssignModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">Assign Truck</span>
              <button onClick={() => setShowAssignModal(false)} className="modal-close">&times;</button>
            </div>
            <div className="form-group">
              <label className="form-label">Use External Vendor?</label>
              <input type="checkbox" checked={assignData.is_outsourced} onChange={e => setAssignData({...assignData, is_outsourced: e.target.checked})} />
            </div>
            {assignData.is_outsourced ? (
              <div className="form-group">
                <label className="form-label">Vendor</label>
                <select className="form-select" value={assignData.vendor_id} onChange={e => setAssignData({...assignData, vendor_id: e.target.value})}>
                  <option value="">Select Vendor</option>
                  {vendors.map(v => <option key={v.id} value={v.id}>{v.name_eng}</option>)}
                </select>
              </div>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Truck</label>
                  <select className="form-select" value={assignData.truck_id} onChange={e => setAssignData({...assignData, truck_id: e.target.value})}>
                    <option value="">Select Truck</option>
                    {trucks.map(t => <option key={t.id} value={t.id}>{t.plate_number}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Driver</label>
                  <select className="form-select" value={assignData.driver_id} onChange={e => setAssignData({...assignData, driver_id: e.target.value})}>
                    <option value="">Select Driver</option>
                    {drivers.map(d => <option key={d.id} value={d.id}>{d.identification_card_number}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Trailer</label>
                  <select className="form-select" value={assignData.trailer_id} onChange={e => setAssignData({...assignData, trailer_id: e.target.value})}>
                    <option value="">Select Trailer</option>
                    {trailers.map(t => <option key={t.id} value={t.id}>{t.trailer_number}</option>)}
                  </select>
                </div>
              </>
            )}
            <button onClick={handleAssignTruck} className="btn btn-primary mt-4">Confirm Assignment</button>
          </div>
        </div>
      )}

      {showAssignTeamModal && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <span className="modal-title">Assign Team</span>
              <button onClick={() => setShowAssignTeamModal(false)} className="modal-close">&times;</button>
            </div>
            <div className="form-group">
              <label className="form-label">Team Name <span className="required">*</span></label>
              <input
                type="text"
                className="form-input"
                placeholder="Enter team name"
                value={teamData.team}
                onChange={e => setTeamData({...teamData, team: e.target.value})}
              />
            </div>
            <button onClick={handleAssignTeam} className="btn btn-primary mt-4">Confirm Assignment</button>
          </div>
        </div>
      )}

      <Link to="/exports" className="btn btn-outline">Back to Exports</Link>
    </div>
  )
}

function Trailers() {
  const { user } = useAuth()
  const [trailers, setTrailers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({ trailer_number: '', trailer_size: '' })

  useEffect(() => {
    loadTrailers()
  }, [])

  const loadTrailers = () => {
    axios.get(`${API_BASE}/trailers`)
      .then(res => setTrailers(res.data))
      .catch(() => setTrailers([]))
      .finally(() => setLoading(false))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingId) {
        await axios.put(`${API_BASE}/trailers/${editingId}`, formData)
      } else {
        await axios.post(`${API_BASE}/trailers`, formData)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ trailer_number: '', trailer_size: '' })
      loadTrailers()
    } catch (err) {
      alert(editingId ? 'Failed to update trailer' : 'Failed to create trailer')
    }
  }

  const handleEdit = (trailer: any) => {
    setEditingId(trailer.id)
    setFormData({ trailer_number: trailer.trailer_number || '', trailer_size: trailer.trailer_size || '' })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this trailer?')) return
    try {
      await axios.delete(`${API_BASE}/trailers/${id}`)
      loadTrailers()
    } catch (err) {
      alert('Failed to delete trailer')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ trailer_number: '', trailer_size: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Trailers</h1>
          <p className="page-subtitle">Manage trailers</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Trailer'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">{editingId ? 'Edit Trailer' : 'Add New Trailer'}</span></div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Trailer Number <span className="required">*</span></label>
                <input type="text" className="form-input" required value={formData.trailer_number}
                  onChange={e => setFormData({...formData, trailer_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Trailer Size</label>
                <input type="text" className="form-input" placeholder="e.g., 40ft" value={formData.trailer_size}
                  onChange={e => setFormData({...formData, trailer_size: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Trailer' : 'Save Trailer'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? <div className="empty-state"><span className="loading-spinner"></span></div> : trailers.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">&#128638;</div><p>No trailers added yet</p></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Trailer Number</th><th>Size</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>{trailers.map(t => (
                <tr key={t.id}><td><strong>{t.trailer_number}</strong></td><td>{t.trailer_size || '-'}</td><td><span className="badge badge-approved">{t.status}</span></td><td>{canManage(user) ? <div className="flex gap-2"><button onClick={() => handleEdit(t)} className="btn btn-outline btn-sm">Edit</button><button onClick={() => handleDelete(t.id)} className="btn btn-danger btn-sm">Delete</button></div> : null}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Drivers() {
  const { user } = useAuth()
  const [drivers, setDrivers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    identification_card_number: '',
    ic_issued_date: '',
    ic_expired_date: '',
    company_ic_number: '',
    company_ic_issued_date: '',
    company_ic_expired_date: '',
    driving_license_number: '',
    license_type: '',
    license_issued_date: '',
    license_expired_date: ''
  })

  const loadDrivers = () => {
    axios.get(`${API_BASE}/drivers`)
      .then(res => setDrivers(res.data))
      .catch(() => setDrivers([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadDrivers()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        ic_issued_date: formData.ic_issued_date ? new Date(formData.ic_issued_date).toISOString() : null,
        ic_expired_date: formData.ic_expired_date ? new Date(formData.ic_expired_date).toISOString() : null,
        company_ic_issued_date: formData.company_ic_issued_date ? new Date(formData.company_ic_issued_date).toISOString() : null,
        company_ic_expired_date: formData.company_ic_expired_date ? new Date(formData.company_ic_expired_date).toISOString() : null,
        license_issued_date: formData.license_issued_date ? new Date(formData.license_issued_date).toISOString() : null,
        license_expired_date: formData.license_expired_date ? new Date(formData.license_expired_date).toISOString() : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/drivers/${editingId}`, payload)
      } else {
        await axios.post(`${API_BASE}/drivers`, payload)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ identification_card_number: '', ic_issued_date: '', ic_expired_date: '', company_ic_number: '', company_ic_issued_date: '', company_ic_expired_date: '', driving_license_number: '', license_type: '', license_issued_date: '', license_expired_date: '' })
      loadDrivers()
    } catch (err) {
      alert(editingId ? 'Failed to update driver' : 'Failed to create driver')
    }
  }

  const handleEdit = (driver: any) => {
    setEditingId(driver.id)
    setFormData({
      identification_card_number: driver.identification_card_number || '',
      ic_issued_date: driver.ic_issued_date ? driver.ic_issued_date.split('T')[0] : '',
      ic_expired_date: driver.ic_expired_date ? driver.ic_expired_date.split('T')[0] : '',
      company_ic_number: driver.company_ic_number || '',
      company_ic_issued_date: driver.company_ic_issued_date ? driver.company_ic_issued_date.split('T')[0] : '',
      company_ic_expired_date: driver.company_ic_expired_date ? driver.company_ic_expired_date.split('T')[0] : '',
      driving_license_number: driver.driving_license_number || '',
      license_type: driver.license_type || '',
      license_issued_date: driver.license_issued_date ? driver.license_issued_date.split('T')[0] : '',
      license_expired_date: driver.license_expired_date ? driver.license_expired_date.split('T')[0] : ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this driver?')) return
    try {
      await axios.delete(`${API_BASE}/drivers/${id}`)
      loadDrivers()
    } catch (err) {
      alert('Failed to delete driver')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ identification_card_number: '', ic_issued_date: '', ic_expired_date: '', company_ic_number: '', company_ic_issued_date: '', company_ic_expired_date: '', driving_license_number: '', license_type: '', license_issued_date: '', license_expired_date: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Drivers</h1>
          <p className="page-subtitle">Manage driver information</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Driver'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">{editingId ? 'Edit Driver' : 'Add New Driver'}</span></div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">ID Card Number *</label>
                <input type="text" className="form-input" required value={formData.identification_card_number}
                  onChange={e => setFormData({...formData, identification_card_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Driving License Number *</label>
                <input type="text" className="form-input" required value={formData.driving_license_number}
                  onChange={e => setFormData({...formData, driving_license_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">License Type</label>
                <input type="text" className="form-input" placeholder="e.g., B, C, D" value={formData.license_type}
                  onChange={e => setFormData({...formData, license_type: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Company IC Number</label>
                <input type="text" className="form-input" value={formData.company_ic_number}
                  onChange={e => setFormData({...formData, company_ic_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">ID Issued Date</label>
                <input type="date" className="form-input" value={formData.ic_issued_date}
                  onChange={e => setFormData({...formData, ic_issued_date: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">ID Expired Date</label>
                <input type="date" className="form-input" value={formData.ic_expired_date}
                  onChange={e => setFormData({...formData, ic_expired_date: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">License Issued Date</label>
                <input type="date" className="form-input" value={formData.license_issued_date}
                  onChange={e => setFormData({...formData, license_issued_date: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">License Expired Date</label>
                <input type="date" className="form-input" value={formData.license_expired_date}
                  onChange={e => setFormData({...formData, license_expired_date: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Driver' : 'Save Driver'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? <div className="empty-state"><span className="loading-spinner"></span></div> : drivers.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">&#128100;</div><p>No drivers added yet</p></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>ID Card</th><th>License</th><th>License Type</th><th>ID Expiry</th><th>License Expiry</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>{drivers.map(d => (
                <tr key={d.id}>
                  <td><strong>{d.identification_card_number}</strong></td>
                  <td>{d.driving_license_number}</td>
                  <td>{d.license_type || '-'}</td>
                  <td>{d.ic_expired_date ? new Date(d.ic_expired_date).toLocaleDateString() : '-'}</td>
                  <td>{d.license_expired_date ? new Date(d.license_expired_date).toLocaleDateString() : '-'}</td>
                  <td><span className="badge badge-approved">{d.status}</span></td>
                  <td>{canManage(user) ? <div className="flex gap-2"><button onClick={() => handleEdit(d)} className="btn btn-outline btn-sm">Edit</button><button onClick={() => handleDelete(d.id)} className="btn btn-danger btn-sm">Delete</button></div> : null}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Locations() {
  const { user } = useAuth()
  const [locations, setLocations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({ name: '', coordinate_x: '', coordinate_y: '' })

  const loadLocations = () => {
    axios.get(`${API_BASE}/locations`)
      .then(res => setLocations(res.data))
      .catch(() => setLocations([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadLocations()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        coordinate_x: formData.coordinate_x ? parseFloat(formData.coordinate_x) : null,
        coordinate_y: formData.coordinate_y ? parseFloat(formData.coordinate_y) : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/locations/${editingId}`, payload)
      } else {
        await axios.post(`${API_BASE}/locations`, payload)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ name: '', coordinate_x: '', coordinate_y: '' })
      loadLocations()
    } catch (err) {
      alert(editingId ? 'Failed to update location' : 'Failed to create location')
    }
  }

  const handleEdit = (location: any) => {
    setEditingId(location.id)
    setFormData({
      name: location.name || '',
      coordinate_x: location.coordinate_x?.toString() || '',
      coordinate_y: location.coordinate_y?.toString() || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this location?')) return
    try {
      await axios.delete(`${API_BASE}/locations/${id}`)
      loadLocations()
    } catch (err) {
      alert('Failed to delete location')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ name: '', coordinate_x: '', coordinate_y: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Locations</h1>
          <p className="page-subtitle">Manage delivery locations</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Location'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">{editingId ? 'Edit Location' : 'Add New Location'}</span></div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Location Name *</label>
                <input type="text" className="form-input" required value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Google Map X (Longitude)</label>
                <input type="number" step="any" className="form-input" placeholder="e.g., 104.9285" value={formData.coordinate_x}
                  onChange={e => setFormData({...formData, coordinate_x: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Google Map Y (Latitude)</label>
                <input type="number" step="any" className="form-input" placeholder="e.g., 11.5564" value={formData.coordinate_y}
                  onChange={e => setFormData({...formData, coordinate_y: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Location' : 'Save Location'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? <div className="empty-state"><span className="loading-spinner"></span></div> : locations.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">&#128205;</div><p>No locations added yet</p></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Name</th><th>X (Longitude)</th><th>Y (Latitude)</th><th>Actions</th></tr></thead>
              <tbody>{locations.map(l => (
                <tr key={l.id}><td><strong>{l.name}</strong></td><td>{l.coordinate_x || '-'}</td><td>{l.coordinate_y || '-'}</td><td>{canManage(user) ? <div className="flex gap-2"><button onClick={() => handleEdit(l)} className="btn btn-outline btn-sm">Edit</button><button onClick={() => handleDelete(l.id)} className="btn btn-danger btn-sm">Delete</button></div> : null}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Items() {
  const { user } = useAuth()
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({ name: '', type: 'Goods', min_qty: '', delivery_lead_time: '', purchase_coa: '', sale_coa: '' })

  const loadItems = () => {
    axios.get(`${API_BASE}/items`)
      .then(res => setItems(res.data))
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadItems()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        min_qty: formData.min_qty ? parseFloat(formData.min_qty) : null,
        delivery_lead_time: formData.delivery_lead_time ? parseInt(formData.delivery_lead_time) : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/items/${editingId}`, payload)
      } else {
        await axios.post(`${API_BASE}/items`, payload)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ name: '', type: 'Goods', min_qty: '', delivery_lead_time: '', purchase_coa: '', sale_coa: '' })
      loadItems()
    } catch (err) {
      alert(editingId ? 'Failed to update item' : 'Failed to create item')
    }
  }

  const handleEdit = (item: any) => {
    setEditingId(item.id)
    setFormData({
      name: item.name || '',
      type: item.type || 'Goods',
      min_qty: item.min_qty?.toString() || '',
      delivery_lead_time: item.delivery_lead_time?.toString() || '',
      purchase_coa: item.purchase_coa || '',
      sale_coa: item.sale_coa || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this item?')) return
    try {
      await axios.delete(`${API_BASE}/items/${id}`)
      loadItems()
    } catch (err) {
      alert('Failed to delete item')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ name: '', type: 'Goods', min_qty: '', delivery_lead_time: '', purchase_coa: '', sale_coa: '' })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Items / Services</h1>
          <p className="page-subtitle">Manage products and services</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ Add Item'}
          </button>
        )}
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">{editingId ? 'Edit Item / Service' : 'Add New Item / Service'}</span></div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Name *</label>
                <input type="text" className="form-input" required value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Type *</label>
                <select className="form-select" value={formData.type} onChange={e => setFormData({...formData, type: e.target.value})}>
                  <option value="Goods">Goods</option>
                  <option value="Service">Service</option>
                </select>
              </div>
              {formData.type === 'Goods' && (
                <>
                  <div className="form-group">
                    <label className="form-label">Min Quantity</label>
                    <input type="number" step="any" className="form-input" value={formData.min_qty}
                      onChange={e => setFormData({...formData, min_qty: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Delivery Lead Time (days)</label>
                    <input type="number" className="form-input" value={formData.delivery_lead_time}
                      onChange={e => setFormData({...formData, delivery_lead_time: e.target.value})} />
                  </div>
                </>
              )}
              <div className="form-group">
                <label className="form-label">Purchase COA</label>
                <input type="text" className="form-input" placeholder="Inventory, R&M Expense, COGS" value={formData.purchase_coa}
                  onChange={e => setFormData({...formData, purchase_coa: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Sale COA</label>
                <input type="text" className="form-input" value={formData.sale_coa}
                  onChange={e => setFormData({...formData, sale_coa: e.target.value})} />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Item' : 'Save Item'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? <div className="empty-state"><span className="loading-spinner"></span></div> : items.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">&#128230;</div><p>No items added yet</p></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Name</th><th>Type</th><th>Min Qty</th><th>Lead Time</th><th>Purchase COA</th><th>Sale COA</th><th>Actions</th></tr></thead>
              <tbody>{items.map(i => (
                <tr key={i.id}><td><strong>{i.name}</strong></td><td>{i.type}</td><td>{i.min_qty || '-'}</td><td>{i.delivery_lead_time ? `${i.delivery_lead_time} days` : '-'}</td><td>{i.purchase_coa || '-'}</td><td>{i.sale_coa || '-'}</td><td>{canManage(user) ? <div className="flex gap-2"><button onClick={() => handleEdit(i)} className="btn btn-outline btn-sm">Edit</button><button onClick={() => handleDelete(i.id)} className="btn btn-danger btn-sm">Delete</button></div> : null}</td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Users() {
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({ username: '', email: '', full_name: '', role: 'staff', password: '', is_active: true })

  const loadUsers = () => {
    axios.get(`${API_BASE}/auth/users`)
      .then(res => setUsers(res.data))
      .catch(() => setUsers([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadUsers()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingId) {
        const { password, ...updateData } = formData
        const payload = password ? formData : updateData
        await axios.put(`${API_BASE}/auth/users/${editingId}`, payload)
      } else {
        await axios.post(`${API_BASE}/auth/register`, formData)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ username: '', email: '', full_name: '', role: 'staff', password: '', is_active: true })
      loadUsers()
    } catch (err: any) {
      alert(err.response?.data?.detail || (editingId ? 'Failed to update user' : 'Failed to create user'))
    }
  }

  const handleEdit = (user: any) => {
    setEditingId(user.id)
    setFormData({
      username: user.username || '',
      email: user.email || '',
      full_name: user.full_name || '',
      role: user.role || 'staff',
      password: '',
      is_active: user.is_active
    })
    setShowForm(true)
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return
    try {
      await axios.delete(`${API_BASE}/auth/users/${id}`)
      loadUsers()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete user')
    }
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ username: '', email: '', full_name: '', role: 'staff', password: '', is_active: true })
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">User Management</h1>
          <p className="page-subtitle">Manage system users and roles</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
          {showForm ? 'Cancel' : '+ Add User'}
        </button>
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">{editingId ? 'Edit User' : 'Add New User'}</span></div>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Username {!editingId && '*'}</label>
                <input type="text" className="form-input" required={!editingId} value={formData.username}
                  onChange={e => setFormData({...formData, username: e.target.value})} disabled={!!editingId} />
              </div>
              <div className="form-group">
                <label className="form-label">Email {!editingId && '*'}</label>
                <input type="email" className="form-input" required={!editingId} value={formData.email}
                  onChange={e => setFormData({...formData, email: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input type="text" className="form-input" value={formData.full_name}
                  onChange={e => setFormData({...formData, full_name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Role</label>
                <select className="form-select" value={formData.role} onChange={e => setFormData({...formData, role: e.target.value})}>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="staff">Staff</option>
                </select>
              </div>
              {!editingId && (
                <div className="form-group">
                  <label className="form-label">Password *</label>
                  <input type="password" className="form-input" required value={formData.password}
                    onChange={e => setFormData({...formData, password: e.target.value})} />
                </div>
              )}
              {editingId && (
                <div className="form-group">
                  <label className="form-label">New Password (leave blank to keep current)</label>
                  <input type="password" className="form-input" value={formData.password}
                    onChange={e => setFormData({...formData, password: e.target.value})} />
                </div>
              )}
              {editingId && (
                <div className="form-group">
                  <label className="form-label">Active</label>
                  <input type="checkbox" checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})} />
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update User' : 'Save User'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {loading ? <div className="empty-state"><span className="loading-spinner"></span></div> : users.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">&#128100;</div><p>No users added yet</p></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Username</th><th>Email</th><th>Full Name</th><th>Role</th><th>Status</th><th>Created</th><th>Actions</th></tr></thead>
              <tbody>{users.map(u => (
                <tr key={u.id}><td><strong>{u.username}</strong></td><td>{u.email}</td><td>{u.full_name || '-'}</td><td><span className={`badge ${u.role === 'admin' ? 'badge-danger' : u.role === 'manager' ? 'badge-warning' : 'badge-approved'}`}>{u.role}</span></td><td><span className={`badge ${u.is_active ? 'badge-approved' : 'badge-pending'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td><td>{new Date(u.created_at).toLocaleDateString()}</td><td><div className="flex gap-2"><button onClick={() => handleEdit(u)} className="btn btn-outline btn-sm">Edit</button><button onClick={() => handleDelete(u.id)} className="btn btn-danger btn-sm">Delete</button></div></td></tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Reports() {
  const [jobs, setJobs] = useState<any[]>([])
  const [trucks, setTrucks] = useState<any[]>([])
  const [customers, setCustomers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE}/jobs`),
      axios.get(`${API_BASE}/trucks`),
      axios.get(`${API_BASE}/customers`)
    ]).then(([jobsRes, trucksRes, customersRes]) => {
      setJobs(jobsRes.data)
      setTrucks(trucksRes.data)
      setCustomers(customersRes.data)
    }).catch(() => {})
    .finally(() => setLoading(false))
  }, [])

  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) return
    const headers = Object.keys(data[0])
    const csvContent = [
      headers.join(','),
      ...data.map(row => headers.map(h => {
        const val = row[h]
        if (val === null || val === undefined) return ''
        if (typeof val === 'object') return JSON.stringify(val)
        const str = String(val)
        return str.includes(',') || str.includes('"') ? `"${str.replace(/"/g, '""')}"` : str
      }).join(','))
    ].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`
    link.click()
  }

  const statusCounts = jobs.reduce((acc: any, job: any) => {
    acc[job.status] = (acc[job.status] || 0) + 1
    return acc
  }, {})

  const monthlyData = jobs.reduce((acc: any, job: any) => {
    const month = new Date(job.created_at).toLocaleString('default', { month: 'short', year: 'numeric' })
    acc[month] = (acc[month] || 0) + 1
    return acc
  }, {})

  const truckUtilization = trucks.reduce((acc: any, truck: any) => {
    acc[truck.status] = (acc[truck.status] || 0) + 1
    return acc
  }, {})

  if (loading) return <div className="empty-state"><span className="loading-spinner"></span></div>

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Reports & Analytics</h1>
          <p className="page-subtitle">Overview of import operations</p>
        </div>
      </div>

      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-header"><span className="card-title">Job Status Distribution</span></div>
          <div style={{ padding: '20px' }}>
            {Object.entries(statusCounts).map(([status, count]: [string, any]) => (
              <div key={status} className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
                <span>{status.replace(/_/g, ' ')}</span>
                <strong>{count}</strong>
              </div>
            ))}
            {Object.keys(statusCounts).length === 0 && <p>No data</p>}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Monthly Job Trends</span></div>
          <div style={{ padding: '20px' }}>
            {Object.entries(monthlyData).map(([month, count]: [string, any]) => (
              <div key={month} className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
                <span>{month}</span>
                <strong>{count}</strong>
              </div>
            ))}
            {Object.keys(monthlyData).length === 0 && <p>No data</p>}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Fleet Status</span></div>
          <div style={{ padding: '20px' }}>
            {Object.entries(truckUtilization).map(([status, count]: [string, any]) => (
              <div key={status} className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
                <span>{status}</span>
                <strong>{count}</strong>
              </div>
            ))}
            {trucks.length === 0 && <p>No trucks data</p>}
          </div>
        </div>

        <div className="card">
          <div className="card-header"><span className="card-title">Summary Statistics</span></div>
          <div style={{ padding: '20px' }}>
            <div className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
              <span>Total Jobs</span>
              <strong>{jobs.length}</strong>
            </div>
            <div className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
              <span>Total Trucks</span>
              <strong>{trucks.length}</strong>
            </div>
            <div className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
              <span>Total Customers</span>
              <strong>{customers.length}</strong>
            </div>
            <div className="flex justify-between mb-2" style={{ borderBottom: '1px solid #eee', padding: '8px 0' }}>
              <span>Completed Jobs</span>
              <strong>{jobs.filter((j: any) => j.status === 'CLOSED').length}</strong>
            </div>
            <div className="flex justify-between" style={{ padding: '8px 0' }}>
              <span>Pending Jobs</span>
              <strong>{jobs.filter((j: any) => j.status === 'PENDING_APPROVAL').length}</strong>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Export Data</span></div>
        <div className="flex gap-2" style={{ padding: '20px' }}>
          <button onClick={() => exportToCSV(jobs, 'jobs')} className="btn btn-outline">Export Jobs</button>
          <button onClick={() => exportToCSV(trucks, 'trucks')} className="btn btn-outline">Export Trucks</button>
          <button onClick={() => exportToCSV(customers, 'customers')} className="btn btn-outline">Export Customers</button>
        </div>
      </div>
    </div>
  )
}

function ActivityLog({ jobId }: { jobId: string }) {
  const [activities, setActivities] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API_BASE}/jobs/activities?job_id=${jobId}`)
      .then(res => setActivities(res.data))
      .catch(() => setActivities([]))
      .finally(() => setLoading(false))
  }, [jobId])

  if (loading) return <div className="empty-state"><span className="loading-spinner"></span></div>

  return (
    <div className="card">
      <div className="card-header"><span className="card-title">Activity Log</span></div>
      <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
        {activities.length === 0 ? (
          <div className="empty-state"><p>No activity recorded</p></div>
        ) : (
          <div style={{ padding: '15px' }}>
            {activities.map((a: any) => (
              <div key={a.id} style={{ padding: '10px 0', borderBottom: '1px solid #eee' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <strong style={{ fontSize: '13px' }}>{a.action.replace(/_/g, ' ')}</strong>
                  <span style={{ fontSize: '11px', color: '#888' }}>{new Date(a.created_at).toLocaleString()}</span>
                </div>
                <p style={{ fontSize: '13px', color: '#555', margin: 0 }}>{a.description}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function PrintJobCard({ job }: { job: any }) {
  const [showPrint, setShowPrint] = useState(false)

  if (!showPrint) return <button onClick={() => setShowPrint(true)} className="btn btn-outline">Print Job Card</button>

  return (
    <div>
      <div className="modal-overlay" onClick={() => setShowPrint(false)}>
        <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '800px', width: '90%' }}>
          <div className="modal-header">
            <span className="modal-title">Job Card - {job.job_number}</span>
            <button onClick={() => setShowPrint(false)} className="modal-close">&times;</button>
          </div>
          <div id="printable-job-card" style={{ padding: '20px', fontSize: '12px' }}>
            <div style={{ border: '2px solid #333', padding: '20px', borderRadius: '8px' }}>
              <h2 style={{ textAlign: 'center', marginBottom: '20px', borderBottom: '2px solid #333', paddingBottom: '10px' }}>CARGO FLOW - JOB CARD</h2>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Job Number</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.job_number}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Status</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.status}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Container No</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.container_number || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Vessel Name</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.vessel_name || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>BL Number</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.bl_number || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Consignee</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.consignee || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Cargo Description</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.cargo_description || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Quantity</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.quantity || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>ETA</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.eta ? new Date(job.eta).toLocaleDateString() : '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>Assigned Team</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.assigned_team || '-'}</td></tr>
                  <tr><td style={{ padding: '8px', borderBottom: '1px solid #ddd', fontWeight: 'bold' }}>EIR Number</td><td style={{ padding: '8px', borderBottom: '1px solid #ddd' }}>{job.eir_number || '-'}</td></tr>
                </tbody>
              </table>
              <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '10px', color: '#888' }}>
                Printed on: {new Date().toLocaleString()} | CargoFlow Import Management System
              </div>
            </div>
          </div>
          <div style={{ padding: '15px', borderTop: '1px solid #eee', display: 'flex', gap: '10px' }}>
            <button onClick={() => window.print()} className="btn btn-primary">Print</button>
            <button onClick={() => setShowPrint(false)} className="btn btn-outline">Close</button>
          </div>
        </div>
      </div>
    </div>
  )
}

function Notifications({ notifications, onDismiss }: { notifications: any[], onDismiss: (id: number) => void }) {
  if (notifications.length === 0) return null

  return (
    <div style={{ position: 'fixed', top: '20px', right: '20px', zIndex: 1000, maxWidth: '350px' }}>
      {notifications.map((n, i) => (
        <div key={i} style={{ background: 'white', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', padding: '15px', marginBottom: '10px', borderLeft: `4px solid ${n.type === 'success' ? '#10b981' : n.type === 'error' ? '#ef4444' : '#3b82f6'}` }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <strong style={{ fontSize: '13px' }}>{n.title}</strong>
              <p style={{ fontSize: '12px', color: '#666', margin: '4px 0 0' }}>{n.message}</p>
            </div>
            <button onClick={() => onDismiss(i)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', color: '#999' }}>&times;</button>
          </div>
        </div>
      ))}
    </div>
  )
}

function CompanySettings() {
  const { darkMode, setDarkMode, language, setLanguage, user } = useAuth()
  const [settings, setSettings] = useState({
    company_name: 'CargoFlow Import Management',
    company_name_kh: '',
    address: '',
    phone: '',
    email: '',
    tax_id: '',
    bank_name: '',
    bank_account: '',
    logo_url: ''
  })
  const [saved, setSaved] = useState(false)

  const handleSave = async () => {
    try {
      await axios.put(`${API_BASE}/settings`, settings)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (err) {
      alert('Failed to save settings')
    }
  }

  useEffect(() => {
    axios.get(`${API_BASE}/settings`)
      .then(res => setSettings({ ...settings, ...res.data }))
      .catch(() => {})
  }, [])

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Manage your preferences and business information</p>
        </div>
        {canManage(user) && (
          <button onClick={handleSave} className="btn btn-primary">{saved ? 'Saved!' : 'Save Settings'}</button>
        )}
      </div>

      <div className="grid grid-2 mb-4">
        <div className="card">
          <div className="card-header"><span className="card-title">Preferences</span></div>
          <div style={{ padding: '20px' }}>
            <div className="form-group">
              <label className="form-label">Language</label>
              <select className="form-select" value={language} onChange={e => setLanguage(e.target.value)}>
                <option value="en">English</option>
                <option value="kh">Khmer</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Theme</label>
              <div style={{ display: 'flex', gap: '15px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
                  <input type="radio" name="theme" checked={!darkMode} onChange={() => setDarkMode(false)} /> Light
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
                  <input type="radio" name="theme" checked={darkMode} onChange={() => setDarkMode(true)} /> Dark
                </label>
              </div>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-header"><span className="card-title">Quick Actions</span></div>
          <div style={{ padding: '20px' }}>
            <button onClick={() => { if (confirm('Clear all local data?')) { localStorage.clear(); window.location.reload() } }} className="btn btn-danger">Clear Local Data</button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">Business Information</span></div>
        <div className="grid grid-2">
          <div className="form-group">
            <label className="form-label">Company Name</label>
            <input type="text" className="form-input" value={settings.company_name} onChange={e => setSettings({...settings, company_name: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Company Name (Khmer)</label>
            <input type="text" className="form-input" value={settings.company_name_kh} onChange={e => setSettings({...settings, company_name_kh: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Address</label>
            <input type="text" className="form-input" value={settings.address} onChange={e => setSettings({...settings, address: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Phone</label>
            <input type="text" className="form-input" value={settings.phone} onChange={e => setSettings({...settings, phone: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" className="form-input" value={settings.email} onChange={e => setSettings({...settings, email: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Tax ID / TIN</label>
            <input type="text" className="form-input" value={settings.tax_id} onChange={e => setSettings({...settings, tax_id: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Bank Name</label>
            <input type="text" className="form-input" value={settings.bank_name} onChange={e => setSettings({...settings, bank_name: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Bank Account</label>
            <input type="text" className="form-input" value={settings.bank_account} onChange={e => setSettings({...settings, bank_account: e.target.value})} />
          </div>
        </div>
      </div>
    </div>
  )
}

function DocumentUpload({ jobId }: { jobId: string }) {
  const { user } = useAuth()
  const [documents, setDocuments] = useState<any[]>([])
  const [uploading, setUploading] = useState(false)

  const loadDocuments = () => {
    axios.get(`${API_BASE}/jobs/${jobId}/documents`)
      .then(res => setDocuments(res.data))
      .catch(() => setDocuments([]))
  }

  useEffect(() => {
    loadDocuments()
  }, [jobId])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const dataBase64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          const result = reader.result as string
          resolve(result.split(',')[1] || '')
        }
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
      await axios.post(`${API_BASE}/jobs/${jobId}/documents`, {
        filename: file.name,
        data_base64: dataBase64,
        file_type: file.type || 'application/octet-stream'
      })
      loadDocuments()
    } catch (err) {
      alert('Failed to upload document')
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const deleteDoc = async (id: string) => {
    if (!confirm('Delete this document?')) return
    try {
      await axios.delete(`${API_BASE}/documents/${id}`)
      loadDocuments()
    } catch (err) {
      alert('Failed to delete document')
    }
  }

  return (
    <div className="card">
      <div className="card-header"><span className="card-title">Documents</span></div>
      <div style={{ padding: '15px' }}>
        <label className="btn btn-outline" style={{ cursor: 'pointer', display: 'inline-block', marginBottom: '15px' }}>
          {uploading ? 'Uploading...' : '+ Upload Document'}
          <input type="file" hidden onChange={handleUpload} />
        </label>
        {documents.length === 0 ? (
          <p style={{ color: '#888', fontSize: '13px' }}>No documents uploaded</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {documents.map(d => (
              <div key={d.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: '#f5f5f5', borderRadius: '6px' }}>
                <div>
                  <strong style={{ fontSize: '13px' }}>{d.filename || d.name}</strong>
                  <div style={{ fontSize: '11px', color: '#888' }}>{new Date(d.created_at || d.date).toLocaleDateString()}</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {canManage(user) && (
                    <button onClick={() => deleteDoc(d.id)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>&times;</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function CalendarView() {
  const [jobs, setJobs] = useState<any[]>([])
  const [currentDate, setCurrentDate] = useState(new Date())

  useEffect(() => {
    axios.get(`${API_BASE}/jobs`)
      .then(res => setJobs(res.data))
      .catch(() => setJobs([]))
  }, [])

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const days: Date[] = []
    const startPadding = firstDay.getDay()
    for (let i = startPadding - 1; i >= 0; i--) {
      days.push(new Date(year, month, -i))
    }
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i))
    }
    const endPadding = 42 - days.length
    for (let i = 1; i <= endPadding; i++) {
      days.push(new Date(year, month + 1, i))
    }
    return days
  }

  const days = getDaysInMonth(currentDate)
  const monthName = currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })

  const getJobsForDate = (date: Date) => {
    return jobs.filter(j => {
      const jobDate = j.eta ? new Date(j.eta) : null
      return jobDate && jobDate.toDateString() === date.toDateString()
    })
  }

  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))
  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))

  const isToday = (date: Date) => date.toDateString() === new Date().toDateString()
  const isCurrentMonth = (date: Date) => date.getMonth() === currentDate.getMonth()

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Calendar</h1>
          <p className="page-subtitle">Schedule overview</p>
        </div>
        <div className="flex gap-2">
          <button onClick={prevMonth} className="btn btn-outline">&lt; Prev</button>
          <span style={{ padding: '8px 16px', fontWeight: '500' }}>{monthName}</span>
          <button onClick={nextMonth} className="btn btn-outline">Next &gt;</button>
        </div>
      </div>
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '1px', background: '#ddd' }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
            <div key={d} style={{ padding: '10px', textAlign: 'center', background: '#f9f9f9', fontWeight: '600', fontSize: '13px' }}>{d}</div>
          ))}
          {days.map((day, i) => {
            const dayJobs = getJobsForDate(day)
            return (
              <div key={i} style={{ minHeight: '100px', padding: '8px', background: isToday(day) ? '#fef3c7' : 'white', opacity: isCurrentMonth(day) ? 1 : 0.5 }}>
                <div style={{ fontSize: '14px', fontWeight: isToday(day) ? 'bold' : 'normal', marginBottom: '4px' }}>{day.getDate()}</div>
                {dayJobs.slice(0, 2).map((j: any) => (
                  <div key={j.id} style={{ fontSize: '10px', padding: '2px 4px', background: '#e0e7ff', borderRadius: '3px', marginBottom: '2px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {j.job_number}
                  </div>
                ))}
                {dayJobs.length > 2 && <div style={{ fontSize: '10px', color: '#888' }}>+{dayJobs.length - 2} more</div>}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function Invoices() {
  const { user } = useAuth()
  const [invoices, setInvoices] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [statusFilter, setStatusFilter] = useState('')
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    job_id: '',
    customer_name: '',
    issue_date: '',
    due_date: '',
    tax_rate: '',
    notes: ''
  })
  const [lines, setLines] = useState([{ description: '', quantity: '1', unit_price: '', coa: '' }])

  const loadInvoices = () => {
    axios.get(`${API_BASE}/invoices`)
      .then(res => setInvoices(res.data))
      .catch(() => setInvoices([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadInvoices()
    axios.get(`${API_BASE}/jobs`)
      .then(res => setJobs(res.data))
      .catch(() => setJobs([]))
  }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.job_id) {
      alert('Please select a job')
      return
    }
    try {
      const validLines = lines.filter(l => l.description.trim())
        .map(l => ({
          description: l.description,
          quantity: l.quantity ? parseFloat(l.quantity) : 1,
          unit_price: l.unit_price ? parseFloat(l.unit_price) : 0,
          coa: l.coa || null
        }))
      await axios.post(`${API_BASE}/jobs/${formData.job_id}/invoices`, {
        customer_name: formData.customer_name || null,
        issue_date: formData.issue_date ? new Date(formData.issue_date).toISOString() : null,
        due_date: formData.due_date ? new Date(formData.due_date).toISOString() : null,
        tax_rate: formData.tax_rate ? parseFloat(formData.tax_rate) : 0,
        notes: formData.notes || null,
        lines: validLines
      })
      setShowForm(false)
      setFormData({ job_id: '', customer_name: '', issue_date: '', due_date: '', tax_rate: '', notes: '' })
      setLines([{ description: '', quantity: '1', unit_price: '', coa: '' }])
      loadInvoices()
    } catch (err) {
      alert('Failed to create invoice')
    }
  }

  const handleStatus = async (id: string, status: string) => {
    try {
      await axios.put(`${API_BASE}/invoices/${id}/status`, { status })
      loadInvoices()
    } catch (err) {
      alert('Failed to update invoice status')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this invoice?')) return
    try {
      await axios.delete(`${API_BASE}/invoices/${id}`)
      loadInvoices()
    } catch (err) {
      alert('Failed to delete invoice')
    }
  }

  const addLineRow = () => {
    setLines([...lines, { description: '', quantity: '1', unit_price: '', coa: '' }])
  }

  const removeLineRow = (index: number) => {
    setLines(lines.filter((_, i) => i !== index))
  }

  const filteredInvoices = invoices.filter(i => !statusFilter || i.status === statusFilter)

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Invoices</h1>
          <p className="page-subtitle">Manage billing and invoicing</p>
        </div>
        {canManage(user) && (
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            {showForm ? 'Cancel' : '+ New Invoice'}
          </button>
        )}
      </div>

      <div className="card mb-4">
        <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
          <div className="form-group" style={{ marginBottom: 0, minWidth: '200px' }}>
            <select className="form-select" value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              {['DRAFT', 'ISSUED', 'PAID', 'VOID'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div style={{ marginLeft: 'auto', color: '#64748b', fontSize: '0.875rem' }}>
            Showing {filteredInvoices.length} of {invoices.length} invoices
          </div>
        </div>
      </div>

      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">Create Invoice</span></div>
          <form onSubmit={handleCreate}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Job <span className="required">*</span></label>
                <select className="form-select" required value={formData.job_id} onChange={e => {
                  const job = jobs.find(j => j.id === e.target.value)
                  setFormData({ ...formData, job_id: e.target.value, customer_name: job?.consignee || '' })
                }}>
                  <option value="">Select Job</option>
                  {jobs.map(j => <option key={j.id} value={j.id}>{j.job_number} - {j.container_number || ''}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Customer Name</label>
                <input type="text" className="form-input" value={formData.customer_name} onChange={e => setFormData({...formData, customer_name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Issue Date</label>
                <input type="date" className="form-input" value={formData.issue_date} onChange={e => setFormData({...formData, issue_date: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Due Date</label>
                <input type="date" className="form-input" value={formData.due_date} onChange={e => setFormData({...formData, due_date: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Tax Rate (%)</label>
                <input type="number" step="any" className="form-input" value={formData.tax_rate} onChange={e => setFormData({...formData, tax_rate: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Notes</label>
                <input type="text" className="form-input" value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} />
              </div>
            </div>
            <div className="card-header mt-4">
              <span className="card-title">Line Items</span>
            </div>
            {lines.map((line, index) => (
              <div key={index} className="grid grid-4" style={{ marginTop: '10px' }}>
                <div className="form-group">
                  <label className="form-label">Description *</label>
                  <input type="text" className="form-input" value={line.description} onChange={e => {
                    const updated = [...lines]
                    updated[index] = { ...line, description: e.target.value }
                    setLines(updated)
                  }} />
                </div>
                <div className="form-group">
                  <label className="form-label">Qty</label>
                  <input type="number" step="any" className="form-input" value={line.quantity} onChange={e => {
                    const updated = [...lines]
                    updated[index] = { ...line, quantity: e.target.value }
                    setLines(updated)
                  }} />
                </div>
                <div className="form-group">
                  <label className="form-label">Unit Price</label>
                  <input type="number" step="any" className="form-input" value={line.unit_price} onChange={e => {
                    const updated = [...lines]
                    updated[index] = { ...line, unit_price: e.target.value }
                    setLines(updated)
                  }} />
                </div>
                <div className="form-group">
                  <label className="form-label">COA</label>
                  <div className="flex gap-2" style={{ alignItems: 'center' }}>
                    <input type="text" className="form-input" value={line.coa} onChange={e => {
                      const updated = [...lines]
                      updated[index] = { ...line, coa: e.target.value }
                      setLines(updated)
                    }} />
                    {lines.length > 1 && <button type="button" onClick={() => removeLineRow(index)} className="btn btn-danger btn-sm">&times;</button>}
                  </div>
                </div>
              </div>
            ))}
            <button type="button" onClick={addLineRow} className="btn btn-outline btn-sm">+ Add Line</button>
            <div className="flex gap-2 mt-4">
              <button type="submit" className="btn btn-primary">Create Invoice</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-outline">Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading ? (
          <div className="empty-state"><span className="loading-spinner"></span></div>
        ) : filteredInvoices.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">&#128176;</div>
            <p>No invoices found</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Invoice #</th>
                  <th>Job</th>
                  <th>Customer</th>
                  <th>Issue Date</th>
                  <th>Due Date</th>
                  <th>Total</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map(inv => {
                  const job = jobs.find(j => j.id === inv.job_id)
                  return (
                    <tr key={inv.id}>
                      <td><strong>{inv.invoice_number}</strong></td>
                      <td>{job?.job_number || inv.job_id || '-'}</td>
                      <td>{inv.customer_name || '-'}</td>
                      <td>{inv.issue_date ? new Date(inv.issue_date).toLocaleDateString() : '-'}</td>
                      <td>{inv.due_date ? new Date(inv.due_date).toLocaleDateString() : '-'}</td>
                      <td>${Number(inv.total || 0).toFixed(2)}</td>
                      <td>
                        {canManage(user) ? (
                          <select
                            className="form-select"
                            value={inv.status}
                            onChange={e => handleStatus(inv.id, e.target.value)}
                            style={{ padding: '4px 8px', fontSize: '13px' }}
                          >
                            {['DRAFT', 'ISSUED', 'PAID', 'VOID'].map(s => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        ) : (
                          <span className={`badge ${inv.status === 'PAID' ? 'badge-approved' : inv.status === 'VOID' ? 'badge-rejected' : inv.status === 'ISSUED' ? 'badge-in-progress' : 'badge-pending'}`}>{inv.status}</span>
                        )}
                      </td>
                      <td>
                        <div className="flex gap-2">
                          <button onClick={() => setExpandedId(expandedId === inv.id ? null : inv.id)} className="btn btn-outline btn-sm">
                            {expandedId === inv.id ? 'Hide' : 'View'}
                          </button>
                          {canManage(user) && (
                            <button onClick={() => handleDelete(inv.id)} className="btn btn-danger btn-sm">Delete</button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {expandedId && (
        <div className="card mt-4">
          <div className="card-header"><span className="card-title">Invoice Details</span></div>
          <div style={{ padding: '20px' }}>
            {(() => {
              const inv = invoices.find(i => i.id === expandedId)
              if (!inv) return null
              return (
                <div>
                  <div className="grid grid-2 mb-4">
                    <div><p className="text-sm text-muted">Invoice Number</p><p><strong>{inv.invoice_number}</strong></p></div>
                    <div><p className="text-sm text-muted">Status</p><p><strong>{inv.status}</strong></p></div>
                    <div><p className="text-sm text-muted">Customer</p><p>{inv.customer_name || '-'}</p></div>
                    <div><p className="text-sm text-muted">Notes</p><p>{inv.notes || '-'}</p></div>
                  </div>
                  <div className="table-container">
                    <table className="table">
                      <thead>
                        <tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Amount</th><th>COA</th></tr>
                      </thead>
                      <tbody>
                        {inv.lines && inv.lines.map((l: any) => (
                          <tr key={l.id}>
                            <td>{l.description}</td>
                            <td>{l.quantity}</td>
                            <td>${Number(l.unit_price || 0).toFixed(2)}</td>
                            <td>${Number(l.amount || 0).toFixed(2)}</td>
                            <td>{l.coa || '-'}</td>
                          </tr>
                        ))}
                        {(!inv.lines || inv.lines.length === 0) && (
                          <tr><td colSpan={5} style={{ textAlign: 'center', color: '#888' }}>No line items</td></tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex justify-between mt-4" style={{ maxWidth: '300px', marginLeft: 'auto' }}>
                    <span>Subtotal</span><strong>${Number(inv.subtotal || 0).toFixed(2)}</strong>
                  </div>
                  <div className="flex justify-between" style={{ maxWidth: '300px', marginLeft: 'auto' }}>
                    <span>Tax ({inv.tax_rate}%)</span><strong>${Number(inv.tax || 0).toFixed(2)}</strong>
                  </div>
                  <div className="flex justify-between" style={{ maxWidth: '300px', marginLeft: 'auto', fontWeight: 'bold', fontSize: '16px' }}>
                    <span>Total</span><strong>${Number(inv.total || 0).toFixed(2)}</strong>
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      )}
    </div>
  )
}

function JobTemplates() {
  const [templates, setTemplates] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [formData, setFormData] = useState({ name: '', container_number: '', vessel_name: '', cargo_description: '', quantity: '', license_required: false })

  const loadTemplates = () => {
    axios.get(`${API_BASE}/templates`)
      .then(res => setTemplates(res.data))
      .catch(() => setTemplates([]))
  }

  useEffect(() => {
    loadTemplates()
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const payload = {
        ...formData,
        quantity: formData.quantity ? parseFloat(formData.quantity) : null
      }
      if (editingId) {
        await axios.put(`${API_BASE}/templates/${editingId}`, payload)
      } else {
        await axios.post(`${API_BASE}/templates`, payload)
      }
      setShowForm(false)
      setEditingId(null)
      setFormData({ name: '', container_number: '', vessel_name: '', cargo_description: '', quantity: '', license_required: false })
      loadTemplates()
    } catch (err) {
      alert(editingId ? 'Failed to update template' : 'Failed to create template')
    }
  }

  const handleEdit = (template: any) => {
    setEditingId(template.id)
    setFormData({
      name: template.name || '',
      container_number: template.container_number || '',
      vessel_name: template.vessel_name || '',
      cargo_description: template.cargo_description || '',
      quantity: template.quantity?.toString() || '',
      license_required: !!template.license_required
    })
    setShowForm(true)
  }

  const cancelEdit = () => {
    setShowForm(false)
    setEditingId(null)
    setFormData({ name: '', container_number: '', vessel_name: '', cargo_description: '', quantity: '', license_required: false })
  }

  const deleteTemplate = async (id: string) => {
    if (!confirm('Are you sure you want to delete this template?')) return
    try {
      await axios.delete(`${API_BASE}/templates/${id}`)
      loadTemplates()
    } catch (err) {
      alert('Failed to delete template')
    }
  }

  const useTemplate = (template: any) => {
    localStorage.setItem('selectedTemplate', JSON.stringify(template))
    window.location.href = '/jobs/new'
  }

  return (
    <div>
      <div className="page-header-row mb-4">
        <div>
          <h1 className="page-title">Job Templates</h1>
          <p className="page-subtitle">Reusable job forms</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary">{showForm ? 'Cancel' : '+ New Template'}</button>
      </div>
      {showForm && (
        <div className="card mb-4">
          <div className="card-header"><span className="card-title">{editingId ? 'Edit Template' : 'Create Template'}</span></div>
          <form onSubmit={handleSave}>
            <div className="grid grid-2">
              <div className="form-group">
                <label className="form-label">Template Name *</label>
                <input type="text" className="form-input" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Default Container Number</label>
                <input type="text" className="form-input" value={formData.container_number} onChange={e => setFormData({...formData, container_number: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Default Vessel Name</label>
                <input type="text" className="form-input" value={formData.vessel_name} onChange={e => setFormData({...formData, vessel_name: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">Default Quantity</label>
                <input type="text" className="form-input" value={formData.quantity} onChange={e => setFormData({...formData, quantity: e.target.value})} />
              </div>
              <div className="form-group" style={{ gridColumn: 'span 2' }}>
                <label className="form-label">Default Cargo Description</label>
                <textarea className="form-input" rows={2} value={formData.cargo_description} onChange={e => setFormData({...formData, cargo_description: e.target.value})} />
              </div>
              <div className="form-group">
                <label className="form-label">
                  <input type="checkbox" checked={formData.license_required} onChange={e => setFormData({...formData, license_required: e.target.checked})} /> License Required
                </label>
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">{editingId ? 'Update Template' : 'Save Template'}</button>
              {editingId && <button type="button" onClick={cancelEdit} className="btn btn-outline">Cancel</button>}
            </div>
          </form>
        </div>
      )}
      <div className="card">
        {templates.length === 0 ? (
          <div className="empty-state"><div className="empty-state-icon">&#128196;</div><p>No templates yet</p></div>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead><tr><th>Name</th><th>Container</th><th>Vessel</th><th>License Required</th><th>Actions</th></tr></thead>
              <tbody>{templates.map(t => (
                <tr key={t.id}>
                  <td><strong>{t.name}</strong></td>
                  <td>{t.container_number || '-'}</td>
                  <td>{t.vessel_name || '-'}</td>
                  <td>{t.license_required ? 'Yes' : 'No'}</td>
                  <td><div className="flex gap-2"><button onClick={() => useTemplate(t)} className="btn btn-outline btn-sm">Use</button><button onClick={() => handleEdit(t)} className="btn btn-outline btn-sm">Edit</button><button onClick={() => deleteTemplate(t.id)} className="btn btn-danger btn-sm">Delete</button></div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  const { logout, user } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [showResults, setShowResults] = useState(false)
  const [notifications, setNotifications] = useState<any[]>([])

  const dismissNotification = (index: number) => {
    setNotifications(prev => prev.filter((_, i) => i !== index))
  }

  useEffect(() => {
    Promise.all([
      axios.get(`${API_BASE}/drivers`).catch(() => ({ data: [] })),
      axios.get(`${API_BASE}/jobs`).catch(() => ({ data: [] })),
      axios.get(`${API_BASE}/exports`).catch(() => ({ data: [] }))
    ]).then(([driversRes, jobsRes, exportsRes]) => {
      const alerts: any[] = []
      const now = new Date()
      const in30Days = new Date(now.getTime() + 30 * 86400000)
      ;(driversRes.data as any[]).forEach((d: any) => {
        if (d.ic_expired_date && new Date(d.ic_expired_date) <= in30Days) {
          alerts.push({ type: 'warning', title: 'ID Expiring', message: `Driver ${d.identification_card_number} ID expires ${new Date(d.ic_expired_date).toLocaleDateString()}` })
        }
        if (d.license_expired_date && new Date(d.license_expired_date) <= in30Days) {
          alerts.push({ type: 'warning', title: 'License Expiring', message: `Driver ${d.identification_card_number} license expires ${new Date(d.license_expired_date).toLocaleDateString()}` })
        }
      })
      ;(jobsRes.data as any[]).forEach((j: any) => {
        if (j.eta && !['CLOSED', 'DELIVERED', 'REJECTED'].includes(j.status) && new Date(j.eta) < now) {
          alerts.push({ type: 'error', title: 'Past ETA', message: `${j.job_number} ETA was ${new Date(j.eta).toLocaleDateString()}` })
        }
      })
      ;(exportsRes.data as any[]).forEach((e: any) => {
        if (e.etd && !['CLOSED', 'REJECTED', 'VESSEL_DEPARTED', 'EXPORT_CLEARED'].includes(e.status) && new Date(e.etd) < now) {
          alerts.push({ type: 'error', title: 'Past ETD', message: `${e.job_number} ETD was ${new Date(e.etd).toLocaleDateString()}` })
        }
      })
      if (alerts.length > 0) {
        setNotifications(prev => [...alerts, ...prev])
      }
    })
  }, [])

  useEffect(() => {
    if (searchQuery.trim().length < 2) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(async () => {
      try {
        const [jobsRes, trucksRes, customersRes, vendorsRes] = await Promise.all([
          axios.get(`${API_BASE}/jobs?search=${searchQuery}`).catch(() => ({ data: [] })),
          axios.get(`${API_BASE}/trucks?search=${searchQuery}`).catch(() => ({ data: [] })),
          axios.get(`${API_BASE}/customers?search=${searchQuery}`).catch(() => ({ data: [] })),
          axios.get(`${API_BASE}/vendors?search=${searchQuery}`).catch(() => ({ data: [] }))
        ])
        const results: any[] = []
        jobsRes.data.slice(0, 3).forEach((j: any) => results.push({ type: 'Job', title: j.job_number || j.id, subtitle: j.status, link: `/jobs/${j.id}` }))
        trucksRes.data.slice(0, 3).forEach((t: any) => results.push({ type: 'Truck', title: t.plate_number, subtitle: t.status, link: '/trucks' }))
        customersRes.data.slice(0, 3).forEach((c: any) => results.push({ type: 'Customer', title: c.name || c.name_eng, subtitle: c.phone || '', link: '/customers' }))
        vendorsRes.data.slice(0, 3).forEach((v: any) => results.push({ type: 'Vendor', title: v.name_eng || v.name_kh, subtitle: v.phone || '', link: '/vendors' }))
        setSearchResults(results)
        setShowResults(true)
      } catch {}
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">C</div>
          <div>
            <div className="sidebar-title">CargoFlow</div>
            <div className="sidebar-subtitle">Import Management</div>
          </div>
        </div>
        <div className="sidebar-main">
        <ul className="nav-menu">
          <li className="nav-section">Overview</li>
          <li className="nav-item">
            <Link to="/" className="nav-link">
              <span className="nav-icon">&#127968;</span>
              Dashboard
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/reports" className="nav-link">
              <span className="nav-icon">&#128200;</span>
              Reports
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/calendar" className="nav-link">
              <span className="nav-icon">&#128197;</span>
              Calendar
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/templates" className="nav-link">
              <span className="nav-icon">&#128196;</span>
              Templates
            </Link>
          </li>
          <li className="nav-section">Operations</li>
          <li className="nav-item">
            <Link to="/jobs" className="nav-link">
              <span className="nav-icon">&#128196;</span>
              Import Jobs
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/exports" className="nav-link">
              <span className="nav-icon">&#128666;</span>
              Export Jobs
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/invoices" className="nav-link">
              <span className="nav-icon">&#128176;</span>
              Invoices
            </Link>
          </li>
          <li className="nav-section">Fleet Management</li>
          <li className="nav-item">
            <Link to="/trucks" className="nav-link">
              <span className="nav-icon">&#128664;</span>
              Trucks
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/trailers" className="nav-link">
              <span className="nav-icon">&#128638;</span>
              Trailers
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/drivers" className="nav-link">
              <span className="nav-icon">&#128100;</span>
              Drivers
            </Link>
          </li>
          <li className="nav-section">Master Data</li>
          <li className="nav-item">
            <Link to="/locations" className="nav-link">
              <span className="nav-icon">&#128205;</span>
              Locations
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/customers" className="nav-link">
              <span className="nav-icon">&#128101;</span>
              Customers
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/vendors" className="nav-link">
              <span className="nav-icon">&#128188;</span>
              Vendors
            </Link>
          </li>
          <li className="nav-item">
            <Link to="/items" className="nav-link">
              <span className="nav-icon">&#128230;</span>
              Items / Services
            </Link>
          </li>
          <li className="nav-section">Administration</li>
          {isAdmin(user) && (
            <li className="nav-item">
              <Link to="/users" className="nav-link">
                <span className="nav-icon">&#128100;</span>
                Users
              </Link>
            </li>
          )}
          <li className="nav-item">
            <Link to="/settings" className="nav-link">
              <span className="nav-icon">&#9881;</span>
              Settings
            </Link>
          </li>
        </ul>
        </div>
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-avatar">{(user?.full_name || user?.username || 'U').charAt(0).toUpperCase()}</div>
            <div className="user-details">
              <div className="user-name">{user?.full_name || user?.username}</div>
              <div className="user-role">{user?.role || 'Staff'}</div>
            </div>
          </div>
          <button onClick={logout} className="btn btn-outline" style={{ width: '100%', color: 'var(--sidebar-text)', borderColor: 'rgba(255,255,255,0.2)' }}>Sign Out</button>
        </div>
      </aside>
      <main className="main-content">
        <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div></div>
          <div style={{ position: 'relative', width: '300px' }}>
            <input
              type="text"
              className="form-input"
              placeholder="Search jobs, trucks, customers..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowResults(true)}
              onBlur={() => setTimeout(() => setShowResults(false), 200)}
              style={{ padding: '8px 12px 8px 35px' }}
            />
            <span style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#888' }}>&#128269;</span>
            {showResults && searchResults.length > 0 && (
              <div className="search-results" style={{ position: 'absolute', top: '100%', left: 0, right: 0, marginTop: '4px' }}>
                {searchResults.map((r, i) => (
                  <Link key={i} to={r.link} className="search-result-item" onClick={() => { setShowResults(false); setSearchQuery('') }}>
                    <span className="search-result-type">{r.type}</span>
                    <span className="search-result-title">{r.title}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
        <Notifications notifications={notifications} onDismiss={dismissNotification} />
        {children}
      </main>
    </div>
  )
}

function App() {
  const { token, user } = useAuth()

  if (!token) {
    return <Login />
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><Dashboard /></Layout>} />
        <Route path="/reports" element={<Layout><Reports /></Layout>} />
        <Route path="/jobs" element={<Layout><JobList /></Layout>} />
        <Route path="/jobs/new" element={<Layout><CreateJob /></Layout>} />
        <Route path="/jobs/:id" element={<Layout><JobDetail /></Layout>} />
        <Route path="/exports" element={<Layout><ExportJobList /></Layout>} />
        <Route path="/exports/new" element={<Layout><CreateExportJob /></Layout>} />
        <Route path="/exports/:id" element={<Layout><ExportJobDetail /></Layout>} />
        <Route path="/invoices" element={<Layout><Invoices /></Layout>} />
        <Route path="/trucks" element={<Layout><Trucks /></Layout>} />
        <Route path="/trailers" element={<Layout><Trailers /></Layout>} />
        <Route path="/drivers" element={<Layout><Drivers /></Layout>} />
        <Route path="/locations" element={<Layout><Locations /></Layout>} />
        <Route path="/customers" element={<Layout><Customers /></Layout>} />
        <Route path="/vendors" element={<Layout><Vendors /></Layout>} />
        <Route path="/items" element={<Layout><Items /></Layout>} />
        <Route path="/users" element={isAdmin(user) ? <Layout><Users /></Layout> : <Navigate to="/" />} />
        <Route path="/settings" element={<Layout><CompanySettings /></Layout>} />
        <Route path="/calendar" element={<Layout><CalendarView /></Layout>} />
        <Route path="/templates" element={<Layout><JobTemplates /></Layout>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}

export default function AppWrapper() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  )
}
