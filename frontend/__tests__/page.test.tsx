import '@testing-library/jest-dom'
import { render, screen } from '@testing-library/react'
import Page from '@/app/page'

describe('Landing Page', () => {
  it('renders a heading', () => {
    render(<Page />)
    const heading = screen.getByRole('heading', { level: 1 })
    expect(heading).toBeInTheDocument()
  })

  it('contains call to action links', () => {
    render(<Page />)
    const links = screen.queryAllByRole('link')
    expect(links.length).toBeGreaterThan(0)
  })
})
