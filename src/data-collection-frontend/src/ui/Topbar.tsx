export default function Topbar() {
  return (
    <header className="flex min-h-[76px] items-center border-b border-slate-400/15 bg-[#070b12]/70 px-7 backdrop-blur-[18px] max-[640px]:px-5">
      <div className="flex items-center gap-3.5">
        <span
          className="h-3.5 w-3.5 rounded bg-linear-135 from-[#3dd9b3] to-[#4b7bff] shadow-[0_0_24px_rgba(75,123,255,0.45)]"
          aria-hidden="true"
        />
        <div>
          <p className="m-0 text-[0.72rem] tracking-[0.14em] text-[#738099] uppercase">
            Editing workspace
          </p>
          <h1 className="m-0 text-2xl font-semibold tracking-normal text-[#f5f7fb]">
            SLEP video
          </h1>
        </div>
      </div>
    </header>
  )
}
