import { Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function WatchlistPage() {
  const [selected, setSelected] = useState('600519.SH')
  const { data, loading, error, retry, setData } = useAsync(() => Promise.all([api.watchlist(), api.instruments()]), [])
  const add = async () => { await api.addWatchlist(selected); setData(await Promise.all([api.watchlist(), api.instruments()])) }
  const remove = async (symbol: string) => { await api.removeWatchlist(symbol); setData(await Promise.all([api.watchlist(), api.instruments()])) }
  return <div className="page"><div className="page-header"><div><p className="eyebrow">WATCHLIST</p><h1>自选股</h1><p>免费会员最多 10 个标的，额度由后端校验</p></div></div>{loading ? <LoadingState /> : error || !data ? <ErrorState error={error ?? new Error('无法加载')} retry={retry} /> : <><div className="inline-form"><select value={selected} onChange={(event) => setSelected(event.target.value)} aria-label="选择要加入自选的股票">{data[1].items.map((item) => <option key={item.symbol} value={item.symbol}>{item.symbol} {item.name}</option>)}</select><button className="button primary" onClick={() => void add()}><Plus size={15} />加入自选</button></div><div className="data-table-wrap"><table className="data-table"><thead><tr><th>标的</th><th>加入时间</th><th aria-label="操作" /></tr></thead><tbody>{data[0].length ? data[0].map((item) => { const instrument = data[1].items.find((value) => value.symbol === item.symbol); return <tr key={item.symbol}><td><Link to={`/stocks/${item.symbol}`}><strong>{instrument?.name ?? item.symbol}</strong><small>{item.symbol}</small></Link></td><td>{new Date(item.added_at).toLocaleString('zh-CN')}</td><td><button className="icon-button danger" aria-label={`删除 ${item.symbol}`} onClick={() => void remove(item.symbol)}><Trash2 size={15} /></button></td></tr> }) : <tr><td colSpan={3}>暂无自选股，请从上方添加</td></tr>}</tbody></table></div></>}</div>
}

