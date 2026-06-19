/// <reference types="vitest/globals" />
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { vi } from 'vitest'
import RequirementStudio from '../pages/RequirementStudio'

vi.mock('../services/requirementStudio', () => ({
  fetchStudioStatus: vi.fn(() =>
    Promise.resolve({
      project_id: 'proj-1',
      stages: [
        { stage_id: 'requirement-outline', stage_name: '概要需求', status: 'not_started', progress_percent: 0 },
        { stage_id: 'requirement-detailed', stage_name: '详细需求', status: 'locked', progress_percent: 0 },
        { stage_id: 'design-outline', stage_name: '概要设计', status: 'locked', progress_percent: 0 },
        { stage_id: 'design-detailed', stage_name: '详细设计', status: 'locked', progress_percent: 0 },
        { stage_id: 'artifacts', stage_name: '设计产物', status: 'locked', progress_percent: 0 },
        { stage_id: 'governance', stage_name: '架构治理', status: 'locked', progress_percent: 0 },
      ],
      current_stage_id: 'requirement-outline',
      overall_progress: 0,
    }),
  ),
  executeStage: vi.fn(() => Promise.resolve()),
  fetchArtifacts: vi.fn(() => Promise.resolve([])),
  createBaseline: vi.fn(() => Promise.resolve()),
  fetchStaleAnalysis: vi.fn(() => Promise.resolve({ stale_artifacts: [], summary: '' })),
  createChangeRequest: vi.fn(() => Promise.resolve()),
}))

describe('RequirementStudio', () => {
  it('renders stage nav bar', async () => {
    render(
      <MemoryRouter initialEntries={['/requirement-studio/requirement-outline?projectId=proj-1']}>
        <RequirementStudio />
      </MemoryRouter>,
    )
    await waitFor(() => {
      expect(screen.getAllByText('概要需求').length).toBeGreaterThanOrEqual(1)
    })
    expect(screen.getByText('详细需求')).toBeInTheDocument()
    expect(screen.getByText('概要设计')).toBeInTheDocument()
    expect(screen.getByText('详细设计')).toBeInTheDocument()
    expect(screen.getByText('设计产物')).toBeInTheDocument()
    expect(screen.getByText('架构治理')).toBeInTheDocument()
  })
})
