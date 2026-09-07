import { useNavigate } from 'react-router'
import { routes } from '../routes'
import { panelClass, primaryButtonClass } from '../ui/classes'

export default function LessonsPage() {
  const navigate = useNavigate()
  return (
    <section className="mx-auto flex min-h-full max-w-3xl flex-col justify-center py-6">
      <div className="mb-8 text-center"><p className="m-0 text-xs font-semibold tracking-[0.16em] text-[#64d7bd] uppercase">Your learning path</p><h2 className="mt-3 mb-0 text-3xl font-semibold tracking-tight text-white">Ready to keep signing?</h2><p className="mt-3 text-[#a8b0c3]">A small step today helps build fluent communication.</p></div>
      <article className={`${panelClass} overflow-hidden`}>
        <div className="flex items-start justify-between border-b border-slate-400/15 px-7 py-5 max-[520px]:px-5"><div><p className="m-0 text-xs tracking-[0.14em] text-[#738099] uppercase">Next lesson</p><p className="mt-2 text-sm text-[#a8b0c3]">Lesson 1 of 8 · Basics</p></div><span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs font-semibold text-[#75dfc9]">5 min</span></div>
        <div className="grid gap-7 px-7 py-8 max-[520px]:px-5"><div className="flex items-center gap-5"><div className="grid size-18 shrink-0 place-items-center rounded-2xl bg-[linear-gradient(135deg,rgba(61,217,179,0.25),rgba(75,123,255,0.22))] text-3xl" aria-hidden="true">🤟</div><div><h3 className="m-0 text-2xl font-semibold text-white">The alphabet: A</h3><p className="mt-2 mb-0 leading-6 text-[#a8b0c3]">Learn your first sign and practise its hand shape.</p></div></div><button type="button" className={`${primaryButtonClass} w-fit max-[520px]:w-full`} onClick={() => navigate(routes.lesson)}>Start lesson</button></div>
      </article>
    </section>
  )
}
