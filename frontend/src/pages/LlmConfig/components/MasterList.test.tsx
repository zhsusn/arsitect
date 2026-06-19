/// <reference types="vitest/globals" />
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MasterList from './MasterList'
import type { LlmProvider } from '../../../services/llm'

const providers: LlmProvider[] = [
  {
    id: 'p1',
    key: 'default',
    name: '默认 Kimi CLI',
    scope: 'global',
    scope_target: null,
    description: '',
    is_enabled: true,
    is_default: true,
    priority: 10,
    provider_type: 'kimi-cli',
    config_json: { provider: 'kimi-cli' },
    has_api_key: false,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: 'p2',
    key: 'openai',
    name: 'OpenAI Provider',
    scope: 'project',
    scope_target: 'proj-1',
    description: '',
    is_enabled: true,
    is_default: false,
    priority: 5,
    provider_type: 'openai',
    config_json: { provider: 'openai' },
    has_api_key: false,
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
  },
]

describe('MasterList', () => {
  it('renders all nodes by default', () => {
    render(
      <MasterList
        tab="provider"
        entities={providers}
        selectedId={null}
        loading={false}
        onSelect={vi.fn()}
        onAdd={vi.fn()}
      />,
    )
    expect(screen.getByText('默认 Kimi CLI')).toBeInTheDocument()
    expect(screen.getByText('OpenAI Provider')).toBeInTheDocument()
  })

  it('filters nodes by search term', async () => {
    render(
      <MasterList
        tab="provider"
        entities={providers}
        selectedId={null}
        loading={false}
        onSelect={vi.fn()}
        onAdd={vi.fn()}
      />,
    )
    const search = screen.getByPlaceholderText('搜索节点名称、key...')
    await userEvent.type(search, 'openai')
    expect(screen.queryByText('默认 Kimi CLI')).not.toBeInTheDocument()
    expect(screen.getByText('OpenAI Provider')).toBeInTheDocument()
  })

  it('filters nodes by scope', async () => {
    render(
      <MasterList
        tab="provider"
        entities={providers}
        selectedId={null}
        loading={false}
        onSelect={vi.fn()}
        onAdd={vi.fn()}
      />,
    )
    const scopeSelect = screen.getByRole('combobox')
    await userEvent.selectOptions(scopeSelect, 'project')
    expect(screen.queryByText('默认 Kimi CLI')).not.toBeInTheDocument()
    expect(screen.getByText('OpenAI Provider')).toBeInTheDocument()
  })

  it('calls onSelect when a card is clicked', async () => {
    const onSelect = vi.fn()
    render(
      <MasterList
        tab="provider"
        entities={providers}
        selectedId={null}
        loading={false}
        onSelect={onSelect}
        onAdd={vi.fn()}
      />,
    )
    await userEvent.click(screen.getByText('OpenAI Provider'))
    expect(onSelect).toHaveBeenCalledWith('p2')
  })

  it('calls onAdd when the add button is clicked', async () => {
    const onAdd = vi.fn()
    render(
      <MasterList
        tab="provider"
        entities={providers}
        selectedId={null}
        loading={false}
        onSelect={vi.fn()}
        onAdd={onAdd}
      />,
    )
    await userEvent.click(screen.getByRole('button', { name: /新增 Provider/i }))
    expect(onAdd).toHaveBeenCalled()
  })
})
