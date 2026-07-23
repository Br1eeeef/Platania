import { Search } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function MarketPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const { data, loading, error, retry } = useAsync(() => api.instruments(page, search), [page, search])
  const values = data?.items ?? []
  return <div className="page"><div className="page-header"><div><p className="eyebrow">A-SHARE MARKET</p><h1>A股行情</h1><p>{data?.pagination.total ? `全市场 ${data.pagination.total.toLocaleString('zh-CN')} 个标的，目录每日缓存` : '全市场目录、实时 K 线与策略入口'}</p></div></div>
    <div className="market-tabs" role="tablist"><button className="active">A股</button><button disabled>港股 · 即将支持</button><button disabled>美股 · 即将支持</button><button disabled>加密货币 · 即将支持</button></div>
    <label className="search-field"><Search size={17} /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="搜索全部 A 股代码、名称或行业" aria-label="搜索全市场 A股" /></label>
    {loading ? <LoadingState /> : error ? <ErrorState error={error} retry={retry} /> : <><div className="data-table-wrap"><table className="data-table"><thead><tr><th>标的</th><th>市场</th><th>行业</th><th>状态</th><th aria-label="操作" /></tr></thead><tbody>{values.map((item) => <tr key={item.symbol}><td><strong>{item.name}</strong><small>{item.symbol}</small></td><td>{item.market}</td><td>{item.sector}</td><td><span className="state-tag active">正常</span></td><td><Link className="button small secondary" to={`/stocks/${item.symbol}`}>研究</Link></td></tr>)}</tbody></table></div><div className="pagination"><button className="button secondary" disabled={page <= 1} onClick={() => setPage(page - 1)}>上一页</button><span>{data?.pagination.page} / {Math.max(1, Math.ceil((data?.pagination.total ?? 0) / (data?.pagination.page_size ?? 50)))}</span><button className="button secondary" disabled={values.length < (data?.pagination.page_size ?? 50)} onClick={() => setPage(page + 1)}>下一页</button></div></>}
  </div>
}
