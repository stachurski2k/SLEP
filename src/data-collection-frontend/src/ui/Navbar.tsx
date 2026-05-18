import { NavLink } from 'react-router'
import { navRoutes } from '../routes'

export default function Navbar() {
  return (
    <aside
      className="border-r border-slate-400/15 bg-[#080c12]/85 px-[18px] py-6 max-[900px]:border-r-0 max-[900px]:border-b max-[900px]:px-5 max-[900px]:pt-4 max-[900px]:pb-0"
      aria-label="Primary"
    >
      <nav className="grid gap-2.5">
        {navRoutes.map((item) => (
          <NavLink
            key={item.page}
            className={({ isActive }) =>
              [
                'block w-full rounded-[14px] border px-4 py-3.5 text-left text-[#738099] no-underline transition-colors duration-150',
                isActive
                  ? 'border-emerald-300/30 bg-[linear-gradient(180deg,rgba(61,217,179,0.18),rgba(75,123,255,0.12))] text-[#f5f7fb] shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]'
                  : 'border-transparent hover:border-slate-400/20 hover:bg-slate-400/5 hover:text-[#f5f7fb]',
              ].join(' ')
            }
            end={item.end}
            to={item.path}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
