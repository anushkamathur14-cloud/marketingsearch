import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from './api'

const TABS = [
  { id: 'bids', label: 'Bid Optimizer' },
  { id: 'keywords', label: 'Keyword Intelligence' },
  { id: 'budgets', label: 'Budget Allocator' },
]

const BID_FILTERS = ['all', 'increase', 'decrease', 'hold']
const KW_FILTERS = ['all', 'scale', 'pause', 'add_negative', 'add_keyword']

function formatCurrency(n) {
  return `$${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

function ChangeCell({ pct }) {
  const cls = pct > 5 ? 'change-up' : pct < -5 ? 'change-down' : 'change-neutral'
  const sign = pct > 0 ? '+' : ''
  return <span className={cls}>{sign}{pct}%</span>
}

function ActionPill({ action }) {
  return <span className={`action-pill action-${action}`}>{action.replace(/_/g, ' ')}</span>
}

function ConfidenceBar({ value }) {
  return (
    <div className="confidence-bar">
      <div className="confidence-track">
        <div className="confidence-fill" style={{ width: `${value * 100}%` }} />
      </div>
      <span className="mono">{(value * 100).toFixed(0)}%</span>
    </div>
  )
}

function BidPanel({ filter }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ limit: '25' })
    if (filter !== 'all') params.set('action', filter)
    apiFetch(`/api/recommendations/bids?${params}`)
      .then((d) => setData(d.recommendations || []))
      .finally(() => setLoading(false))
  }, [filter])

  if (loading) return <div className="loading">Loading bid recommendations…</div>

  return (
    <table>
      <thead>
        <tr>
          <th>Keyword</th>
          <th>Campaign</th>
          <th>Current Bid</th>
          <th>Recommended</th>
          <th>Change</th>
          <th>Action</th>
          <th>Confidence</th>
          <th>Conv. Rate</th>
        </tr>
      </thead>
      <tbody>
        {data.map((r, i) => (
          <tr key={i}>
            <td><strong>{r.keyword}</strong></td>
            <td className="rationale">{r.campaign}</td>
            <td className="mono">{formatCurrency(r.current_bid)}</td>
            <td className="mono">{formatCurrency(r.recommended_bid)}</td>
            <td><ChangeCell pct={r.bid_change_pct} /></td>
            <td><ActionPill action={r.action} /></td>
            <td><ConfidenceBar value={r.confidence} /></td>
            <td className="mono">{(r.metrics.conversion_rate * 100).toFixed(2)}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function KeywordPanel({ filter }) {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = new URLSearchParams({ limit: '25' })
    if (filter !== 'all') params.set('action', filter)
    apiFetch(`/api/recommendations/keywords?${params}`)
      .then((d) => setData(d.recommendations || []))
      .finally(() => setLoading(false))
  }, [filter])

  if (loading) return <div className="loading">Loading keyword recommendations…</div>

  return (
    <table>
      <thead>
        <tr>
          <th>Term</th>
          <th>Type</th>
          <th>Campaign</th>
          <th>Action</th>
          <th>Confidence</th>
          <th>Conversions</th>
          <th>Cost</th>
          <th>Rationale</th>
        </tr>
      </thead>
      <tbody>
        {data.map((r, i) => (
          <tr key={i}>
            <td><strong>{r.keyword || r.search_term}</strong></td>
            <td><span className="action-pill action-monitor">{r.type}</span></td>
            <td className="rationale">{r.campaign}</td>
            <td><ActionPill action={r.action} /></td>
            <td><ConfidenceBar value={r.confidence} /></td>
            <td className="mono">{r.metrics.conversions}</td>
            <td className="mono">{formatCurrency(r.metrics.cost)}</td>
            <td className="rationale">{r.rationale}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function BudgetPanel() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [totalBudget, setTotalBudget] = useState('1500')

  const load = useCallback((budget) => {
    setLoading(true)
    const path = budget
      ? '/api/recommendations/budgets/optimize'
      : '/api/recommendations/budgets'
    const opts = budget
      ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ total_budget: Number(budget) }) }
      : undefined
    apiFetch(path, opts)
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load(null) }, [load])

  if (loading && !data) return <div className="loading">Loading budget recommendations…</div>
  if (!data) return null

  return (
    <>
      <div className="budget-summary">
        <div className="budget-summary-item">
          <span>Current Total Budget</span>
          <strong>{formatCurrency(data.total_current_budget)}</strong>
        </div>
        <div className="budget-summary-item">
          <span>Recommended Total</span>
          <strong>{formatCurrency(data.total_recommended_budget)}</strong>
        </div>
        <div className="budget-summary-item">
          <span>Net Change</span>
          <strong>
            <ChangeCell pct={((data.total_recommended_budget - data.total_current_budget) / data.total_current_budget * 100).toFixed(1)} />
          </strong>
        </div>
      </div>
      <div className="budget-optimizer">
        <label htmlFor="total-budget">Constrain total daily budget:</label>
        <input
          id="total-budget"
          type="number"
          value={totalBudget}
          onChange={(e) => setTotalBudget(e.target.value)}
        />
        <button className="btn" onClick={() => load(totalBudget)}>Re-optimize</button>
      </div>
      <table>
        <thead>
          <tr>
            <th>Campaign</th>
            <th>Current Budget</th>
            <th>Recommended</th>
            <th>Change</th>
            <th>Priority</th>
            <th>ROAS</th>
            <th>Lost IS (Budget)</th>
            <th>Rationale</th>
          </tr>
        </thead>
        <tbody>
          {data.recommendations.map((r, i) => (
            <tr key={i}>
              <td><strong>{r.campaign}</strong></td>
              <td className="mono">{formatCurrency(r.current_budget)}</td>
              <td className="mono">{formatCurrency(r.recommended_budget)}</td>
              <td><ChangeCell pct={r.budget_change_pct} /></td>
              <td><ActionPill action={r.priority} /></td>
              <td className="mono">{r.metrics.roas}x</td>
              <td className="mono">{(r.metrics.lost_is_budget * 100).toFixed(0)}%</td>
              <td className="rationale">{r.rationale}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  )
}

export default function App() {
  const [tab, setTab] = useState('bids')
  const [bidFilter, setBidFilter] = useState('all')
  const [kwFilter, setKwFilter] = useState('all')
  const [overview, setOverview] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      apiFetch('/api/overview'),
      apiFetch('/api/health'),
    ])
      .then(([ov, health]) => {
        setOverview(ov)
        setMetrics(health.metrics)
      })
      .catch(() => setError('Cannot reach the API. Check that the backend is running and VITE_API_URL is set correctly.'))
  }, [])

  const filters = tab === 'bids' ? BID_FILTERS : tab === 'keywords' ? KW_FILTERS : []
  const activeFilter = tab === 'bids' ? bidFilter : kwFilter
  const setFilter = tab === 'bids' ? setBidFilter : setKwFilter

  const panelDescriptions = {
    bids: 'Gradient Boosting regressor predicts optimal CPC; Random Forest classifies bid actions.',
    keywords: 'Random Forest classifiers recommend scaling, pausing, or adding keywords/negatives.',
    budgets: 'Gradient Boosting regressor allocates daily budget by campaign ROAS and impression share.',
  }

  if (error) {
    return (
      <div className="app">
        <div className="error">{error}</div>
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '1rem' }}>
          Local: <code className="mono">cd backend && uvicorn main:app --reload --port 8000</code>
          {import.meta.env.VITE_API_URL && (
            <> · API: <code className="mono">{import.meta.env.VITE_API_URL}</code></>
          )}
        </p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-top">
          <div>
            <h1>Search Ads ML Automation</h1>
            <p>ML-driven recommendations for bids, keywords, and budgets — built for Google Ads-style search campaigns.</p>
          </div>
          <span className="badge"><span className="badge-dot" /> Models Active</span>
        </div>
      </header>

      {overview && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">Campaigns</div>
            <div className="stat-value">{overview.campaigns}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Keywords Tracked</div>
            <div className="stat-value">{overview.keywords.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">7d Spend</div>
            <div className="stat-value">{formatCurrency(overview.total_spend)}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Conversions</div>
            <div className="stat-value">{overview.total_conversions.toLocaleString()}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Avg ROAS</div>
            <div className="stat-value">{overview.avg_roas}x</div>
          </div>
        </div>
      )}

      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? 'active' : ''}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="panel">
        <div className="panel-header">
          <div>
            <div className="panel-title">{TABS.find((t) => t.id === tab)?.label}</div>
            <div className="panel-subtitle">{panelDescriptions[tab]}</div>
          </div>
          {filters.length > 0 && (
            <div className="filter-group">
              {filters.map((f) => (
                <button
                  key={f}
                  className={`filter-btn ${activeFilter === f ? 'active' : ''}`}
                  onClick={() => setFilter(f)}
                >
                  {f === 'all' ? 'All' : f.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          )}
        </div>
        {tab === 'bids' && <BidPanel filter={bidFilter} />}
        {tab === 'keywords' && <KeywordPanel filter={kwFilter} />}
        {tab === 'budgets' && <BudgetPanel />}
      </div>

      {metrics && (
        <div className="model-info">
          <h3>Model Performance (held-out test set)</h3>
          <div className="model-grid">
            <div className="model-card">
              <h4>Bid Optimizer</h4>
              <p>Gradient Boosting + Random Forest on keyword performance features.</p>
              <div className="model-metric">R² = {metrics.bid_r2} · Action acc = {(metrics.action_accuracy * 100).toFixed(1)}%</div>
            </div>
            <div className="model-card">
              <h4>Keyword Recommender</h4>
              <p>Random Forest on keyword + search term query reports.</p>
              <div className="model-metric">Keyword acc = {(metrics.keyword_accuracy * 100).toFixed(1)}% · Search term acc = {(metrics.search_term_accuracy * 100).toFixed(1)}%</div>
            </div>
            <div className="model-card">
              <h4>Budget Allocator</h4>
              <p>Gradient Boosting regressor on campaign ROAS and impression share.</p>
              <div className="model-metric">R² = {metrics.budget_r2}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
