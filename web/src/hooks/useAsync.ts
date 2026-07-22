import { useCallback, useEffect, useState } from 'react'

export function useAsync<T>(loader: () => Promise<T>, dependencies: readonly unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const execute = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setData(await loader())
    } catch (reason) {
      setError(reason instanceof Error ? reason : new Error('未知错误'))
    } finally {
      setLoading(false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  useEffect(() => { void execute() }, [execute])
  return { data, loading, error, retry: execute, setData }
}

