import { useCallback, useEffect, useMemo, useState } from 'react'
import { llmPolicyApi, llmProviderApi, type LlmPolicy, type LlmProvider } from '../../../services/llm'
import { type TabKey } from '../types'

interface UseLlmEntitiesOptions {
  tab: TabKey
}

interface UseLlmEntitiesResult {
  entities: LlmProvider[] | LlmPolicy[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  removeEntity: (id: string) => void
}

export function useLlmEntities({ tab }: UseLlmEntitiesOptions): UseLlmEntitiesResult {
  const [providers, setProviders] = useState<LlmProvider[]>([])
  const [policies, setPolicies] = useState<LlmPolicy[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (tab === 'provider') {
        const data = await llmProviderApi.list({ size: 1000 })
        setProviders(data.items)
      } else {
        const data = await llmPolicyApi.list({ size: 1000 })
        setPolicies(data.items)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }, [tab])

  useEffect(() => {
    refresh()
  }, [refresh])

  const removeEntity = useCallback((id: string) => {
    if (tab === 'provider') {
      setProviders((prev) => prev.filter((p) => p.id !== id))
    } else {
      setPolicies((prev) => prev.filter((p) => p.id !== id))
    }
  }, [tab])

  const entities = useMemo(() => (tab === 'provider' ? providers : policies), [tab, providers, policies])

  return { entities, loading, error, refresh, removeEntity }
}
