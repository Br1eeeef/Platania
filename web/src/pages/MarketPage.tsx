import { Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function MarketPage() {
  const [search, setSearch] = useState('')
  const { data, loading, error, retry } = useAsync(api.instruments, [])
  const values = useMemo(() => data?.items.filter((item) => `${item.symbol}${item.name}${item.sector}`.toLowerCase().includes(search.toLowerCase())) ?? [], [data, search])
  return <div className="page"><div className="page-header"><div><p className="eyebrow">A-SHARE MARKET</p><h1>A股行情</h1><p>研究池行情、行业与策略入口</p></div></div>
    <div className="market-tabs" role="tablist"><button className="active">A股</button><button disabled>港股 · 即将支持</button><button disabled>美股 · 即将支持</button><button disabled>加密货币 · 即将支持</button></div>
    <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索代码、名称或行业" aria-label="搜索研究池" /></label>
    {loading ? <LoadingState /> : error ? <ErrorState error={error} retry={retry} /> : <div className="data-table-wrap"><table className="data-table"><thead><tr><th>标的</th><th>市场</th><th>行业</th><th>状态</th><th aria-label="操作" /></tr></thead><tbody>{values.map((item) => <tr key={item.symbol}><td><strong>{item.name}</strong><small>{item.symbol}</small></td><td>{item.market}</td><td>{item.sector}</td><td><span className="state-tag active">正常</span></td><td><Link className="button small secondary" to={`/stocks/${item.symbol}`}>研究</Link></td></tr>)}</tbody></table></div>}
  </div>
}

