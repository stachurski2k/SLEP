import type { Video } from '../actions'
import {
  fieldControlClass,
  fieldLabelClass,
  panelClass,
  panelLabelClass,
  primaryButtonClass,
  secondaryButtonClass,
} from '../ui/classes'
import {
  MAX_ZOOM,
  MIN_ZOOM,
  TIMELINE_PADDING,
  useVideoEditor,
} from './VideoEditor.hook'
import NextFrameIcon from './icons/NextFrameIcon'
import PauseIcon from './icons/PauseIcon'
import PlayIcon from './icons/PlayIcon'
import PreviousFrameIcon from './icons/PreviousFrameIcon'

const readoutPillClass =
  'inline-flex min-h-[34px] items-center rounded-full border border-slate-400/15 bg-slate-400/5 px-3 text-sm text-[#a8b0c3]'
const primaryIconButtonClass =
  'inline-flex h-[42px] w-[42px] items-center justify-center rounded-[14px] border border-emerald-300/20 bg-[linear-gradient(180deg,rgba(61,217,179,0.18),rgba(75,123,255,0.14))] text-[#f5f7fb] transition duration-150 hover:-translate-y-px hover:border-emerald-300/40 disabled:cursor-not-allowed disabled:opacity-40 [&_svg]:h-[18px] [&_svg]:w-[18px]'
const secondaryIconButtonClass =
  'inline-flex h-[42px] w-[42px] items-center justify-center rounded-[14px] border border-slate-400/15 bg-slate-400/10 text-[#a8b0c3] transition duration-150 hover:-translate-y-px hover:border-emerald-300/40 disabled:cursor-not-allowed disabled:opacity-40 [&_svg]:h-[18px] [&_svg]:w-[18px]'

type VideoEditorProps = {
  video: Video | null
}

export default function VideoEditor({ video }: VideoEditorProps) {
  const {
    asset,
    clipPointMarkers,
    clipSelection,
    clipWidth,
    currentFrameTimeLabel,
    endFrameLabel,
    fps,
    gestureClasses,
    gestureTypes,
    handleLoadedMetadata,
    handleSaveClip,
    handleTimeUpdate,
    handleTimelineSeek,
    isPlaying,
    isSavingClip,
    isVideoLoading,
    markerOffset,
    rulerMarks,
    selectedGestureClassId,
    selectedGestureTypeId,
    setClipPoint,
    setIsPlaying,
    setSelectedGestureClassId,
    setSelectedGestureTypeId,
    setZoom,
    startFrameLabel,
    stepFrame,
    timelineRef,
    timelineWidth,
    togglePlayback,
    videoRef,
    zoom,
  } = useVideoEditor(video)

  return (
    <>
      <div className={`${panelClass} min-h-0 overflow-hidden`}>
        {asset ? (
          <div className="grid p-[18px] max-[720px]:p-3.5">
            <video
              key={asset.filepath}
              ref={videoRef}
              className="block min-h-[750px] max-h-[40vh] w-full rounded-[18px] border border-slate-400/10 bg-[radial-gradient(circle_at_top,rgba(61,217,179,0.14),transparent_22%),#05070b] object-contain max-[720px]:min-h-60"
              src={asset.url}
              controls={false}
              onLoadedMetadata={handleLoadedMetadata}
              onTimeUpdate={handleTimeUpdate}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              onEnded={() => setIsPlaying(false)}
            />
          </div>
        ) : (
          <div className="grid min-h-[750px] place-items-center rounded-[22px] border border-slate-400/10 bg-[linear-gradient(135deg,rgba(61,217,179,0.08),transparent_36%),linear-gradient(225deg,rgba(75,123,255,0.1),transparent_30%),rgba(7,11,18,0.86)] p-9 max-[720px]:min-h-60">
            <div className="max-w-[520px] text-center">
              <p className={panelLabelClass}>
                {isVideoLoading ? 'Opening video' : 'Video editor'}
              </p>
              <h3 className="my-3 text-[1.6rem] font-semibold tracking-normal text-[#f5f7fb]">
                {isVideoLoading
                  ? 'Loading editor asset'
                  : 'Select a server video'}
              </h3>
              <p className="mb-0 text-[#a8b0c3]">
                {isVideoLoading
                  ? 'Fetching the selected video from object storage.'
                  : 'Open a dataset below, then select a video from its table.'}
              </p>
            </div>
          </div>
        )}
      </div>

      <section className={`${panelClass} grid gap-4 p-4 max-[720px]:p-3.5`}>
        <div className="flex items-center justify-between gap-3.5 max-[720px]:flex-col max-[720px]:items-start">
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex items-center gap-2.5">
              <button
                className={primaryIconButtonClass}
                type="button"
                onClick={togglePlayback}
                disabled={!asset}
                aria-label={isPlaying ? 'Pause video' : 'Play video'}
              >
                {isPlaying ? <PauseIcon /> : <PlayIcon />}
              </button>

              <button
                className={secondaryIconButtonClass}
                type="button"
                onClick={() => stepFrame(-1)}
                disabled={!asset}
                aria-label="Previous frame"
                title="Previous frame (A)"
              >
                <PreviousFrameIcon />
              </button>

              <button
                className={secondaryIconButtonClass}
                type="button"
                onClick={() => stepFrame(1)}
                disabled={!asset}
                aria-label="Next frame"
                title="Next frame (D)"
              >
                <NextFrameIcon />
              </button>
            </div>

            <div className="h-8 w-px bg-slate-400/15 max-[720px]:hidden" />

            <div className="flex items-center gap-2">
              <button
                className={secondaryButtonClass}
                type="button"
                onClick={() => setClipPoint('start')}
                disabled={!asset}
                title="Set start point (Q)"
              >
                Set Start
              </button>

              <button
                className={secondaryButtonClass}
                type="button"
                onClick={() => setClipPoint('end')}
                disabled={!asset}
                title="Set end point (E)"
              >
                Set End
              </button>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            <span className={readoutPillClass}>{currentFrameTimeLabel}</span>
            <span className={readoutPillClass}>{fps} fps step</span>
            <span className={readoutPillClass}>Start {startFrameLabel}</span>
            <span className={readoutPillClass}>End {endFrameLabel}</span>
          </div>
        </div>

        <div className="grid min-h-56 grid-cols-[188px_minmax(0,1fr)] gap-3.5 max-[1080px]:grid-cols-1">
          <div className="grid grid-rows-[56px_1fr] overflow-hidden rounded-[18px] border border-slate-400/10 bg-[#070b12]/80 max-[1080px]:grid-cols-[96px_1fr] max-[1080px]:grid-rows-1">
            <div className="flex items-center border-b border-slate-400/10 px-4 text-xs tracking-[0.12em] text-[#738099] uppercase max-[1080px]:border-r max-[1080px]:border-b-0">
              V1
            </div>
            <div className="flex items-center px-4 text-[#a8b0c3]">
              {asset?.name ?? 'No clip loaded'}
            </div>
          </div>

          <div className="grid min-w-0 grid-rows-[minmax(0,1fr)_auto] overflow-hidden rounded-[18px] border border-slate-400/10 bg-[#070b12]/80">
            <div className="min-w-0 overflow-hidden">
              <div
                ref={timelineRef}
                className="relative h-full min-w-0 cursor-pointer overflow-x-auto overflow-y-hidden [scrollbar-color:rgba(148,163,184,0.45)_transparent]"
                onClick={handleTimelineSeek}
              >
                <div
                  className="relative min-h-44 bg-[linear-gradient(rgba(255,255,255,0.04)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.035)_1px,transparent_1px),linear-gradient(180deg,rgba(11,17,25,0.94),rgba(8,12,18,1))] bg-[length:100%_44px,48px_100%,100%_100%]"
                  style={{ width: timelineWidth }}
                >
                  {rulerMarks.map((mark) => (
                    <div
                      key={mark.second}
                      className="absolute top-0 bottom-0 w-px bg-white/10"
                      style={{ left: mark.left }}
                    >
                      <span className="absolute top-2.5 left-2 whitespace-nowrap text-[0.72rem] text-[#738099]">
                        {mark.label}
                      </span>
                    </div>
                  ))}

                  {asset ? (
                    <div
                      className="absolute top-[62px] h-[70px] overflow-hidden rounded-[14px] border border-emerald-300/30 bg-[linear-gradient(180deg,rgba(61,217,179,0.22),rgba(75,123,255,0.18)),rgba(16,24,34,0.94)] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
                      style={{
                        width: clipWidth,
                        left: TIMELINE_PADDING,
                      }}
                      aria-hidden="true"
                    />
                  ) : (
                    <div className="absolute inset-[62px_24px_24px] grid place-items-center rounded-2xl border border-dashed border-slate-400/20 text-[#738099]">
                      Select a video to build the timeline.
                    </div>
                  )}

                  {asset && clipSelection ? (
                    <div
                      className="pointer-events-none absolute top-[62px] h-[70px] rounded-[14px] border border-amber-200/45 bg-amber-300/12"
                      style={{
                        left: clipSelection.left,
                        width: clipSelection.width,
                      }}
                      aria-hidden="true"
                    />
                  ) : null}

                  {asset
                    ? clipPointMarkers.map((point) => (
                        <div
                          key={point.id}
                          className={`pointer-events-none absolute top-0 bottom-0 z-10 w-0.5 ${
                            point.id === 'start'
                              ? 'bg-emerald-300 shadow-[0_0_0_1px_rgba(110,231,183,0.2)]'
                              : 'bg-sky-300 shadow-[0_0_0_1px_rgba(125,211,252,0.2)]'
                          }`}
                          style={{ left: point.left }}
                          aria-hidden="true"
                        >
                          <span
                            className={`absolute left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 rounded-[3px] ${
                              point.id === 'start'
                                ? 'top-6 bg-emerald-300'
                                : 'top-11 bg-sky-300'
                            }`}
                          />
                          <span
                            className={`absolute left-2 whitespace-nowrap rounded-full border px-2 py-0.5 text-[0.68rem] font-semibold tracking-[0.1em] uppercase ${
                              point.id === 'start'
                                ? 'top-5 border-emerald-300/30 bg-emerald-300/10 text-emerald-100'
                                : 'top-10 border-sky-300/30 bg-sky-300/10 text-sky-100'
                            }`}
                          >
                            {point.label} {point.frameIndex}
                          </span>
                        </div>
                      ))
                    : null}

                  {asset ? (
                    <div
                      className="pointer-events-none absolute top-0 bottom-0 w-0.5 bg-orange-500 shadow-[0_0_0_1px_rgba(249,115,22,0.18)]"
                      style={{ left: markerOffset }}
                      aria-hidden="true"
                    >
                      <span className="absolute top-2 left-1/2 h-3.5 w-3.5 -translate-x-1/2 rotate-45 rounded bg-orange-500" />
                    </div>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 border-t border-slate-400/10 px-3.5 pt-3 pb-3.5">
              <span className="text-xs tracking-[0.12em] text-[#738099] uppercase">
                Zoom
              </span>
              <input
                className="h-1.5 flex-1 appearance-none rounded-full bg-[linear-gradient(90deg,rgba(61,217,179,0.65),rgba(75,123,255,0.65))] outline-none [&::-moz-range-thumb]:h-[18px] [&::-moz-range-thumb]:w-[18px] [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-[#0a0e16]/90 [&::-moz-range-thumb]:bg-[#f5f7fb] [&::-moz-range-thumb]:shadow-[0_0_16px_rgba(75,123,255,0.28)] [&::-webkit-slider-thumb]:h-[18px] [&::-webkit-slider-thumb]:w-[18px] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[#0a0e16]/90 [&::-webkit-slider-thumb]:bg-[#f5f7fb] [&::-webkit-slider-thumb]:shadow-[0_0_16px_rgba(75,123,255,0.28)]"
                type="range"
                min={MIN_ZOOM}
                max={MAX_ZOOM}
                step={10}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
                aria-label="Timeline zoom"
              />
            </div>
          </div>
        </div>

        <form
          className="grid gap-3.5 border-t border-slate-400/10 pt-4"
          onSubmit={handleSaveClip}
        >
          <div className="grid grid-cols-2 gap-3.5 max-[720px]:grid-cols-1">
            <label className="grid gap-2">
              <span className={fieldLabelClass}>Gesture Class</span>
              <select
                className={fieldControlClass}
                value={selectedGestureClassId}
                onChange={(event) =>
                  setSelectedGestureClassId(event.target.value)
                }
                disabled={isSavingClip || gestureClasses.length === 0}
              >
                <option value="">Select gesture class</option>
                {gestureClasses.map((gestureClass) => (
                  <option key={gestureClass.id} value={gestureClass.id}>
                    {gestureClass.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2">
              <span className={fieldLabelClass}>Gesture Type</span>
              <select
                className={fieldControlClass}
                value={selectedGestureTypeId}
                onChange={(event) =>
                  setSelectedGestureTypeId(event.target.value)
                }
                disabled={isSavingClip || gestureTypes.length === 0}
              >
                <option value="">Select gesture type</option>
                {gestureTypes.map((gestureType) => (
                  <option key={gestureType.id} value={gestureType.id}>
                    {gestureType.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="flex justify-end max-[720px]:justify-stretch">
            <button
              className={`${primaryButtonClass} max-[720px]:w-full`}
              type="submit"
              disabled={isSavingClip}
            >
              {isSavingClip ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </section>
    </>
  )
}
