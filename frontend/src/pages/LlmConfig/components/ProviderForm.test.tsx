/// <reference types="vitest/globals" />
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import ProviderForm from './ProviderForm'
import type { LlmProvider } from '../../../services/llm'

const baseProvider: LlmProvider = {
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
  config_json: { provider: 'kimi-cli', kimi_cli_path: 'kimi', timeout: 120 },
  has_api_key: false,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
}

describe('ProviderForm', () => {
  it('submits the expected payload for a kimi-cli provider', async () => {
    const onSave = vi.fn()
    render(
      <ProviderForm
        provider={baseProvider}
        isNew={false}
        saving={false}
        error={null}
        onSave={onSave}
        onCancel={vi.fn()}
      />,
    )

    await userEvent.clear(screen.getByTestId('provider-name-input'))
    await userEvent.type(screen.getByTestId('provider-name-input'), 'Renamed Provider')
    await userEvent.click(screen.getByRole('button', { name: '保存' }))

    expect(onSave).toHaveBeenCalledWith({
      name: 'Renamed Provider',
      description: undefined,
      priority: 10,
      config_json: {
        timeout: 120,
        kimi_cli_path: 'kimi',
      },
    })
  })

  it('shows a validation error when the name is empty', async () => {
    const onSave = vi.fn()
    render(
      <ProviderForm
        provider={baseProvider}
        isNew={false}
        saving={false}
        error={null}
        onSave={onSave}
        onCancel={vi.fn()}
      />,
    )

    await userEvent.clear(screen.getByTestId('provider-name-input'))
    await userEvent.click(screen.getByRole('button', { name: '保存' }))

    expect(screen.getByText('名称不能为空')).toBeInTheDocument()
    expect(onSave).not.toHaveBeenCalled()
  })

  it('calls onCancel when cancel is clicked', async () => {
    const onCancel = vi.fn()
    render(
      <ProviderForm
        provider={baseProvider}
        isNew={false}
        saving={false}
        error={null}
        onSave={vi.fn()}
        onCancel={onCancel}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: '取消' }))
    expect(onCancel).toHaveBeenCalled()
  })

  it('notifies parent on every input change', async () => {
    const onChange = vi.fn()
    render(
      <ProviderForm
        provider={baseProvider}
        isNew={false}
        saving={false}
        error={null}
        onSave={vi.fn()}
        onCancel={vi.fn()}
        onChange={onChange}
      />,
    )

    await userEvent.type(screen.getByTestId('provider-name-input'), 'x')
    expect(onChange).toHaveBeenCalled()
  })
})
