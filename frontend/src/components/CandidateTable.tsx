import type { Candidate } from '../types'
import { formatPercent, priceClass } from '../utils'

interface CandidateTableProps {
  candidates: Candidate[]
  selectedSymbol: string
  onSelect: (symbol: string) => void
}

export function CandidateTable({ candidates, selectedSymbol, onSelect }: CandidateTableProps) {
  return (
    <div className="table-wrap">
      <table className="candidate-table">
        <thead>
          <tr>
            <th>标的</th>
            <th>最新价</th>
            <th>涨跌</th>
            <th>量化分</th>
            <th>信号</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate) => (
            <tr
              key={candidate.symbol}
              className={candidate.symbol === selectedSymbol ? 'selected' : ''}
              onClick={() => onSelect(candidate.symbol)}
            >
              <td>
                <strong>{candidate.name}</strong>
                <span>{candidate.symbol}.{candidate.exchange}</span>
              </td>
              <td>{candidate.close.toFixed(2)}</td>
              <td className={priceClass(candidate.change)}>{formatPercent(candidate.change)}</td>
              <td><span className="score-cell">{candidate.score}</span></td>
              <td><span className={`signal-tag ${candidate.position === '持有' ? 'active' : ''}`}>{candidate.position}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

