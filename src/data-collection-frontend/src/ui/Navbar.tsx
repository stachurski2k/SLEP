import type { Page } from '../App'

type NavbarProps = {
  activePage: Page
  onPageChange: (page: Page) => void
}

const navItems: Array<{ page: Page; label: string }> = [
  { page: 'editor', label: 'Video editor' },
  { page: 'dataset-manager', label: 'Dataset Manager' },
]

export default function Navbar({ activePage, onPageChange }: NavbarProps) {
  return (
    <aside className="navbar" aria-label="Primary">
      <nav className="nav-panel">
        {navItems.map((item) => (
          <button
            key={item.page}
            className={`nav-item${
              activePage === item.page ? ' nav-item-active' : ''
            }`}
            type="button"
            onClick={() => onPageChange(item.page)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
