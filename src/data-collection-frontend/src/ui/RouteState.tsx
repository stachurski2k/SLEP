type RouteStateProps = {
  title: string
  description?: string
  variant?: 'default' | 'error'
}

export default function RouteState({
  title,
  description,
  variant = 'default',
}: RouteStateProps) {
  return (
    <section className="grid min-h-full place-items-center">
      <div
        className={`w-full max-w-[420px] rounded-lg border border-slate-400/15 bg-slate-900/55 p-6 text-[#f5f7fb]${
          variant === 'error' ? ' border-rose-400/35' : ''
        }`}
      >
        <p className="m-0 text-[0.72rem] tracking-[0.14em] text-[#738099] uppercase">
          Status
        </p>
        <h2 className="mt-2 mb-0 text-[1.35rem] font-semibold tracking-normal text-[#f5f7fb]">
          {title}
        </h2>
        {description ? (
          <p className="mt-4 mb-0 text-[#738099]">{description}</p>
        ) : null}
      </div>
    </section>
  )
}
