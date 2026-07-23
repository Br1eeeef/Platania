import { ExternalLink, Newspaper } from 'lucide-react'
import { Disclaimer } from '../components/Disclaimer'

const EXTERNAL_NEWS_URL = 'https://opi48web.haofanw.com/mydata/newss/summary.html'

export function FeedPage() {
  return (
    <div className="page feed-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">QUANT FEED</p>
          <h1>量化信息流</h1>
          <p>聚合市场资讯与量化研究线索</p>
        </div>
      </div>

      <Disclaimer />

      <section className="external-feed" aria-labelledby="external-feed-title">
        <div className="external-feed-icon" aria-hidden="true">
          <Newspaper size={24} />
        </div>
        <div className="external-feed-content">
          <span className="state-tag">临时外部资讯源</span>
          <h2 id="external-feed-title">前往外部量化资讯页面</h2>
          <p>
            Platania 自有信息流正在建设中。为避免用演示内容冒充真实资讯，当前暂时引导至外部页面查看市场信息。
          </p>
          <dl>
            <div>
              <dt>内容来源</dt>
              <dd>opi48web.haofanw.com</dd>
            </div>
            <div>
              <dt>打开方式</dt>
              <dd>将在新标签页中打开</dd>
            </div>
          </dl>
          <a
            className="button primary external-feed-action"
            href={EXTERNAL_NEWS_URL}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="前往外部量化资讯页面（新标签页打开）"
          >
            前往查看量化资讯
            <ExternalLink size={14} aria-hidden="true" />
          </a>
          <small>外部页面内容由第三方提供，Platania 不对其准确性、及时性或可用性作保证。</small>
        </div>
      </section>
    </div>
  )
}
