import { Heart, MessageSquare } from 'lucide-react'
import { Disclaimer } from '../components/Disclaimer'
import { ErrorState, LoadingState } from '../components/PageState'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export function FeedPage() {
  const { data, loading, error, retry } = useAsync(api.feed, [])
  return <div className="page feed-page"><div className="page-header"><div><p className="eyebrow">QUANT FEED</p><h1>量化信息流</h1><p>策略信号、研究笔记、公开回测与版本更新</p></div></div><Disclaimer />{loading ? <LoadingState /> : error ? <ErrorState error={error} retry={retry} /> : <div className="feed-list">{data?.items.map((item) => <article className="feed-item" key={item.id}><header><span className="feed-kind">{item.kind}</span><span>{item.author_name}</span><time>{new Date(item.created_at).toLocaleString('zh-CN')}</time>{item.is_demo && <span className="state-tag">演示内容</span>}</header><h2>{item.title}</h2><p>{item.excerpt}</p><footer>{item.symbol && <span>{item.symbol}</span>}<span><Heart size={14} />{item.likes}</span><span><MessageSquare size={14} />{item.comments}</span></footer></article>)}</div>}</div>
}

