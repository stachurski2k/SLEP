import { useState } from 'react'
import { useNavigate } from 'react-router'
import { routes } from '../routes'
import { primaryButtonClass } from '../ui/classes'

export default function LessonPage() {
  const navigate = useNavigate()
  const [isComplete, setIsComplete] = useState(false)

  if (isComplete) {
    return <section className="mx-auto grid min-h-full max-w-xl place-items-center py-10 text-center"><div><div className="mx-auto grid size-20 place-items-center rounded-full bg-emerald-300/15 text-4xl">✓</div><p className="mt-6 text-xs font-semibold tracking-[0.16em] text-[#64d7bd] uppercase">Lesson complete</p><h2 className="mt-3 mb-0 text-3xl font-semibold text-white">Nice work!</h2><p className="mt-3 text-[#a8b0c3]">You completed your first sign language exercise.</p><button type="button" className={`${primaryButtonClass} mt-8`} onClick={() => navigate(routes.lessons)}>Back to lessons</button></div></section>
  }

  return (
    <section className="mx-auto max-w-3xl py-2">
      <div className="flex items-center gap-4"><button type="button" className="grid size-10 cursor-pointer place-items-center rounded-xl border border-slate-400/15 bg-slate-400/5 text-xl text-[#a8b0c3] transition hover:text-white" onClick={() => navigate(routes.lessons)} aria-label="Back to lessons">×</button><div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-400/10"><div className="h-full w-1/3 rounded-full bg-[linear-gradient(90deg,#38c8a6,#4c78ff)]" /></div><span className="text-xs font-medium text-[#738099]">1 / 3</span></div>
      <div className="mx-auto mt-14 max-w-xl text-center"><p className="m-0 text-xs font-semibold tracking-[0.16em] text-[#64d7bd] uppercase">Alphabet basics</p><h2 className="mt-3 mb-0 text-3xl font-semibold tracking-tight text-white">Show “A”</h2><p className="mt-3 text-[#a8b0c3]">Make the sign for the letter A in front of your camera.</p><div className="mt-9 aspect-video rounded-[28px] border border-dashed border-slate-400/30 bg-[radial-gradient(circle_at_center,rgba(74,119,255,0.16),transparent_45%),#0a1018] p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]"><div className="grid h-full place-items-center rounded-[20px] border border-white/5 bg-[#070b12]/40"><div><div className="text-7xl font-bold text-white">A</div><p className="mt-3 text-sm text-[#738099]">Camera preview will appear here</p></div></div></div><p className="mt-5 text-sm text-[#738099]">Recognition is not enabled in this demo yet.</p><button type="button" className={`${primaryButtonClass} mt-8 min-w-48`} onClick={() => setIsComplete(true)}>Continue</button></div>
    </section>
  )
}
