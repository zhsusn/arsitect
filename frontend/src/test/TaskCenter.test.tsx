/// <reference types="vitest/globals" />
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import TaskCenter from '../pages/Execution/TaskCenter'

describe('TaskCenter', () => {
  it('renders tab labels', () => {
    render(
      <MemoryRouter initialEntries={['/?projectId=proj-1']}>
        <TaskCenter />
      </MemoryRouter>,
    )
    expect(screen.getByText('任务执行')).toBeInTheDocument()
    expect(screen.getByText('任务拆解')).toBeInTheDocument()
    expect(screen.getByText('Bug 修复')).toBeInTheDocument()
  })
})
