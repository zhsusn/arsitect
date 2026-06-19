/// <reference types="vitest/globals" />
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import ExecutionIssues from '../pages/Execution/Issues'

describe('ExecutionIssues', () => {
  it('renders filter and create button', () => {
    render(
      <MemoryRouter initialEntries={['/?projectId=proj-1']}>
        <ExecutionIssues />
      </MemoryRouter>,
    )
    expect(screen.getByText('+ 新建问题')).toBeInTheDocument()
    expect(screen.getByText('全部类型')).toBeInTheDocument()
  })
})
