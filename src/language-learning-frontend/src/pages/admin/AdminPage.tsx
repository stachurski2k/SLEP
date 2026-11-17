import { useCallback, useEffect, useMemo, useState } from 'react'
import { toast } from 'sonner'
import {
  createExercise,
  createLesson,
  createUnit,
  deleteExercise,
  deleteLesson,
  deleteUnit,
  fetchExercisesByLesson,
  fetchLessonsByUnit,
  fetchUnits,
  getAvailablePoses,
  publishLesson,
  updateExercise,
  updateLesson,
  updateUnit,
} from '../../api/learning'
import { inputClass, panelClass, primaryButtonClass } from '../../components/ui/classes'
import { lessons as staticLessons } from '../../data/lessons'
import { parseMediaUrl } from '../../utils/media'
import type {
  AvailablePosesResponse,
  Difficulty,
  ExerciseCreateInput,
  ExerciseEntity,
  ExerciseType,
  LessonCreateInput,
  LessonEntity,
  UnitCreateInput,
  UnitEntity,
} from '../../types/learning'

export default function AdminPage() {
  const [posesInfo, setPosesInfo] = useState<AvailablePosesResponse>({
    poses: [],
    source: 'lessons.ts',
  })
  const [units, setUnits] = useState<UnitEntity[]>([])
  const [activeUnitId, setActiveUnitId] = useState<string | null>(null)
  const [lessons, setLessons] = useState<LessonEntity[]>([])
  const [activeLessonId, setActiveLessonId] = useState<string | null>(null)
  const [exercises, setExercises] = useState<ExerciseEntity[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Modals state
  const [showPosesModal, setShowPosesModal] = useState(false)
  const [posesSearch, setPosesSearch] = useState('')

  const [showUnitModal, setShowUnitModal] = useState(false)
  const [unitForm, setUnitForm] = useState<UnitCreateInput>({ title: '', order: 1 })
  const [editingUnitId, setEditingUnitId] = useState<string | null>(null)

  const [showLessonModal, setShowLessonModal] = useState(false)
  const [lessonForm, setLessonForm] = useState<LessonCreateInput>({
    title: '',
    description: '',
    order: 1,
  })
  const [editingLessonId, setEditingLessonId] = useState<string | null>(null)

  const [showExerciseModal, setShowExerciseModal] = useState(false)
  const [editingExerciseId, setEditingExerciseId] = useState<string | null>(null)
  const [exerciseForm, setExerciseForm] = useState<ExerciseCreateInput>({
    type: 'single',
    difficulty: 'beginner',
    points: 10,
    content: '',
    answer: '',
    media: [],
  })

  // Refresh available poses
  const handleRefreshPoses = async () => {
    const res = await getAvailablePoses()
    setPosesInfo(res)
    toast.success(`Updated gestures list: ${res.poses.length} gestures (${res.source}).`)
  }

  // Load lessons for a specific unit
  const loadLessons = useCallback(async (unitId: string) => {
    try {
      const data = await fetchLessonsByUnit(unitId)
      setLessons(data)
      if (data.length > 0) {
        const firstLessonId = data[0].id
        setActiveLessonId(firstLessonId)
        const exercisesData = await fetchExercisesByLesson(firstLessonId)
        setExercises(exercisesData)
      } else {
        setActiveLessonId(null)
        setExercises([])
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load lessons.')
    }
  }, [])

  // Load exercises for a specific lesson
  const loadExercises = useCallback(async (lessonId: string) => {
    try {
      const data = await fetchExercisesByLesson(lessonId)
      setExercises(data)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load exercises.')
    }
  }, [])

  // Load units and sync
  const loadUnits = useCallback(async () => {
    try {
      const data = await fetchUnits()
      setUnits(data)
      if (data.length > 0) {
        const targetUnitId =
          activeUnitId && data.some((u) => u.id === activeUnitId)
            ? activeUnitId
            : data[0].id
        setActiveUnitId(targetUnitId)
        await loadLessons(targetUnitId)
      } else {
        setActiveUnitId(null)
        setLessons([])
        setActiveLessonId(null)
        setExercises([])
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load units.')
    } finally {
      setIsLoading(false)
    }
  }, [activeUnitId, loadLessons])

  // Single mount effect to initialize data
  useEffect(() => {
    let isMounted = true
    const initData = async () => {
      const poses = await getAvailablePoses()
      if (!isMounted) return
      setPosesInfo(poses)

      try {
        const unitsData = await fetchUnits()
        if (!isMounted) return
        setUnits(unitsData)
        if (unitsData.length > 0) {
          const firstUnitId = unitsData[0].id
          setActiveUnitId(firstUnitId)
          const lessonsData = await fetchLessonsByUnit(firstUnitId)
          if (!isMounted) return
          setLessons(lessonsData)
          if (lessonsData.length > 0) {
            const firstLessonId = lessonsData[0].id
            setActiveLessonId(firstLessonId)
            const exercisesData = await fetchExercisesByLesson(firstLessonId)
            if (!isMounted) return
            setExercises(exercisesData)
          }
        }
      } catch (err) {
        if (isMounted) toast.error(err instanceof Error ? err.message : 'Failed to initialize data.')
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void initData()
    return () => {
      isMounted = false
    }
  }, [])

  const handleSelectUnit = async (unitId: string) => {
    setActiveUnitId(unitId)
    await loadLessons(unitId)
  }

  const handleSelectLesson = async (lessonId: string) => {
    setActiveLessonId(lessonId)
    await loadExercises(lessonId)
  }

  // Active items
  const activeUnit = useMemo(() => units.find((u) => u.id === activeUnitId), [units, activeUnitId])
  const activeLesson = useMemo(
    () => lessons.find((l) => l.id === activeLessonId),
    [lessons, activeLessonId],
  )

  // Seed initial demo data from lessons.ts
  const handleSeedFromLessons = async () => {
    try {
      setIsLoading(true)
      const newUnit = await createUnit({
        title: 'Unit 1: Sign Language Fundamentals',
        order: 1,
      })

      for (let i = 0; i < staticLessons.length; i++) {
        const item = staticLessons[i]
        const createdLesson = await createLesson(newUnit.id, {
          title: item.title,
          description: `Practice signs: ${item.signs.join(', ')}`,
          order: i + 1,
        })
        await publishLesson(createdLesson.id)

        for (const sign of item.signs) {
          await createExercise(createdLesson.id, {
            type: 'single',
            difficulty: 'beginner',
            points: 10,
            content: `Show the sign for: ${sign}`,
            answer: sign,
          })
        }
      }

      toast.success('Successfully initialized units and lessons from lessons.ts!')
      await loadUnits()
      setActiveUnitId(newUnit.id)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Data import failed.')
    } finally {
      setIsLoading(false)
    }
  }

  // Unit handlers
  const handleOpenCreateUnit = () => {
    setEditingUnitId(null)
    setUnitForm({ title: '', order: units.length + 1 })
    setShowUnitModal(true)
  }

  const handleOpenEditUnit = (unit: UnitEntity) => {
    setEditingUnitId(unit.id)
    setUnitForm({ title: unit.title, order: unit.order })
    setShowUnitModal(true)
  }

  const handleSaveUnit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!unitForm.title.trim()) {
      toast.error('Unit title is required.')
      return
    }

    try {
      if (editingUnitId) {
        await updateUnit(editingUnitId, unitForm)
        toast.success('Unit updated.')
      } else {
        const created = await createUnit(unitForm)
        toast.success('New unit created.')
        setActiveUnitId(created.id)
      }
      setShowUnitModal(false)
      await loadUnits()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save unit.')
    }
  }

  const handleDeleteUnit = async (unitId: string) => {
    if (!confirm('Are you sure you want to delete this unit along with all its lessons?')) return
    try {
      await deleteUnit(unitId)
      toast.success('Unit deleted.')
      if (activeUnitId === unitId) {
        setActiveUnitId(null)
      }
      await loadUnits()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete unit.')
    }
  }

  // Lesson handlers
  const handleOpenCreateLesson = () => {
    if (!activeUnitId) return
    setEditingLessonId(null)
    setLessonForm({ title: '', description: '', order: lessons.length + 1 })
    setShowLessonModal(true)
  }

  const handleOpenEditLesson = (lesson: LessonEntity) => {
    setEditingLessonId(lesson.id)
    setLessonForm({
      title: lesson.title,
      description: lesson.description,
      order: lesson.order,
    })
    setShowLessonModal(true)
  }

  const handleSaveLesson = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeUnitId) return
    if (!lessonForm.title.trim()) {
      toast.error('Lesson title is required.')
      return
    }

    try {
      if (editingLessonId) {
        await updateLesson(editingLessonId, lessonForm)
        toast.success('Lesson updated.')
      } else {
        const created = await createLesson(activeUnitId, lessonForm)
        toast.success('New lesson created.')
        setActiveLessonId(created.id)
      }
      setShowLessonModal(false)
      await loadLessons(activeUnitId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save lesson.')
    }
  }

  const handlePublishLesson = async (lessonId: string) => {
    try {
      await publishLesson(lessonId)
      toast.success('Lesson published!')
      if (activeUnitId) await loadLessons(activeUnitId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to publish lesson.')
    }
  }

  const handleDeleteLesson = async (lessonId: string) => {
    if (!confirm('Are you sure you want to delete this lesson and its exercises?')) return
    try {
      await deleteLesson(lessonId)
      toast.success('Lesson deleted.')
      if (activeLessonId === lessonId) {
        setActiveLessonId(null)
      }
      if (activeUnitId) await loadLessons(activeUnitId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete lesson.')
    }
  }

  // Exercise handlers
  const handleOpenCreateExercise = () => {
    if (!activeLessonId) return
    setEditingExerciseId(null)
    const defaultPose = posesInfo.poses[0] || 'YES'
    setExerciseForm({
      type: 'single',
      difficulty: 'beginner',
      points: 10,
      content: `Show the sign for: ${defaultPose}`,
      answer: defaultPose,
      media: [],
    })
    setShowExerciseModal(true)
  }

  const handleOpenEditExercise = (exercise: ExerciseEntity) => {
    setEditingExerciseId(exercise.id)
    setExerciseForm({
      type: exercise.type,
      difficulty: exercise.difficulty,
      points: exercise.points,
      content: exercise.content,
      answer: exercise.answer,
      media: exercise.media ? exercise.media.map((m) => ({ type: m.type, url: m.url })) : [],
    })
    setShowExerciseModal(true)
  }

  const handlePoseSelect = (selectedPose: string) => {
    setExerciseForm((prev) => ({
      ...prev,
      answer: selectedPose,
      content:
        prev.content.startsWith('Show the sign for:') ||
        prev.content.startsWith('Wykonaj znak dla:') ||
        !prev.content
          ? `Show the sign for: ${selectedPose}`
          : prev.content,
    }))
  }

  const handleAddMedia = (type: 'image' | 'video' = 'image') => {
    setExerciseForm((prev) => ({
      ...prev,
      media: [...(prev.media || []), { type, url: '' }],
    }))
  }

  const handleUpdateMedia = (index: number, field: 'type' | 'url', value: string) => {
    setExerciseForm((prev) => {
      const nextMedia = [...(prev.media || [])]
      nextMedia[index] = { ...nextMedia[index], [field]: value }
      return { ...prev, media: nextMedia }
    })
  }

  const handleRemoveMedia = (index: number) => {
    setExerciseForm((prev) => ({
      ...prev,
      media: (prev.media || []).filter((_, i) => i !== index),
    }))
  }

  const handleSaveExercise = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeLessonId) return
    if (!exerciseForm.answer.trim()) {
      toast.error('Target sign (answer) is required.')
      return
    }
    if (!exerciseForm.content.trim()) {
      toast.error('Exercise prompt content is required.')
      return
    }

    const cleanMedia = (exerciseForm.media || [])
      .filter((m) => m.url.trim().length > 0)
      .map((m) => ({ type: m.type, url: m.url.trim() }))

    try {
      if (editingExerciseId) {
        await updateExercise(editingExerciseId, {
          type: exerciseForm.type,
          difficulty: exerciseForm.difficulty,
          points: exerciseForm.points,
          content: exerciseForm.content.trim(),
          answer: exerciseForm.answer.trim().toUpperCase(),
          media: cleanMedia,
        })
        toast.success('Exercise updated.')
      } else {
        await createExercise(activeLessonId, {
          type: exerciseForm.type,
          difficulty: exerciseForm.difficulty,
          points: exerciseForm.points,
          content: exerciseForm.content.trim(),
          answer: exerciseForm.answer.trim().toUpperCase(),
          media: cleanMedia,
        })
        toast.success('Exercise created.')
      }
      setShowExerciseModal(false)
      await loadExercises(activeLessonId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save exercise.')
    }
  }

  const handleDeleteExercise = async (exerciseId: string) => {
    if (!confirm('Are you sure you want to delete this exercise?')) return
    try {
      await deleteExercise(exerciseId)
      toast.success('Exercise deleted.')
      if (activeLessonId) await loadExercises(activeLessonId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete exercise.')
    }
  }

  // Filtered poses for search
  const filteredPoses = useMemo(() => {
    if (!posesSearch.trim()) return posesInfo.poses
    return posesInfo.poses.filter((p) => p.toLowerCase().includes(posesSearch.toLowerCase()))
  }, [posesInfo.poses, posesSearch])

  return (
    <section className="mx-auto w-full max-w-7xl py-2">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="m-0 text-3xl font-semibold tracking-tight text-white">
            Admin Panel · Course Management
          </h2>
          <p className="mt-1 mb-0 text-sm text-[#a8b0c3]">
            Create and configure units, lessons, and interactive exercises based on model gestures.
          </p>
        </div>

        {/* Poses status indicator badge */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setShowPosesModal(true)}
            className={`inline-flex cursor-pointer items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-semibold tracking-wide transition hover:brightness-110 ${
              posesInfo.source === 'model-service'
                ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-300'
                : 'border-sky-400/30 bg-sky-500/10 text-sky-300'
            }`}
            title="Click to view all available gestures"
          >
            <span
              className={`size-2 rounded-full ${
                posesInfo.source === 'model-service' ? 'bg-emerald-400 animate-pulse' : 'bg-sky-400'
              }`}
            />
            <span>
              {posesInfo.source === 'model-service' ? 'Model Service (live)' : 'lessons.ts database'} ·{' '}
              {posesInfo.poses.length} gestures
            </span>
            <span className="text-white/40">👁</span>
          </button>

          {units.length === 0 && (
            <button
              type="button"
              onClick={() => void handleSeedFromLessons()}
              className="cursor-pointer rounded-xl border border-emerald-400/30 bg-emerald-400/15 px-3.5 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-400/25"
            >
              ⚡ Import data from lessons.ts
            </button>
          )}

          <button
            type="button"
            onClick={handleOpenCreateUnit}
            className={`${primaryButtonClass} !min-h-10 text-sm`}
          >
            + New Unit
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="mt-12 flex justify-center text-slate-400">
          Loading course structure...
        </div>
      ) : (
        /* 3-Column Manager Layout */
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Column 1: Units - 3 cols */}
          <div className="flex flex-col gap-3 lg:col-span-3">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-semibold text-white">
                1. Units ({units.length})
              </h3>
              <button
                type="button"
                onClick={handleOpenCreateUnit}
                className="cursor-pointer text-xs text-emerald-400 hover:underline"
              >
                + Add Unit
              </button>
            </div>

            {units.length === 0 ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                No units found. Click &quot;+ New Unit&quot; or import demo data.
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {units.map((unit) => {
                  const isSelected = unit.id === activeUnitId
                  return (
                    <div
                      key={unit.id}
                      onClick={() => void handleSelectUnit(unit.id)}
                      className={`group flex cursor-pointer items-center justify-between rounded-xl border p-3.5 transition-colors ${
                        isSelected
                          ? 'border-emerald-300/40 bg-[linear-gradient(135deg,rgba(61,217,179,0.15),rgba(75,123,255,0.08))] text-white'
                          : 'border-slate-400/15 bg-[#0a0f18]/80 text-[#a8b0c3] hover:border-slate-400/30 hover:bg-white/5'
                      }`}
                    >
                      <div className="min-w-0 pr-2">
                        <span className="text-[0.7rem] font-bold tracking-wider text-emerald-400 uppercase">
                          Unit #{unit.order}
                        </span>
                        <h4 className="m-0 truncate text-sm font-semibold text-white">
                          {unit.title}
                        </h4>
                      </div>
                      <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleOpenEditUnit(unit)
                          }}
                          className="rounded p-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white"
                          title="Edit unit"
                        >
                          ✎
                        </button>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            void handleDeleteUnit(unit.id)
                          }}
                          className="rounded p-1 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-300"
                          title="Delete unit"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Column 2: Lessons - 4 cols */}
          <div className="flex flex-col gap-3 lg:col-span-4">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-semibold text-white">
                2. Lessons {activeUnit ? `in: ${activeUnit.title}` : ''} ({lessons.length})
              </h3>
              {activeUnit && (
                <button
                  type="button"
                  onClick={handleOpenCreateLesson}
                  className="cursor-pointer text-xs text-emerald-400 hover:underline"
                >
                  + Add Lesson
                </button>
              )}
            </div>

            {!activeUnit ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Select a unit on the left to manage its lessons.
              </div>
            ) : lessons.length === 0 ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                No lessons in this unit yet. Click &quot;+ Add Lesson&quot;.
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {lessons.map((lesson) => {
                  const isSelected = lesson.id === activeLessonId
                  const isPublished = lesson.status === 'published'
                  return (
                    <div
                      key={lesson.id}
                      onClick={() => void handleSelectLesson(lesson.id)}
                      className={`group flex cursor-pointer flex-col gap-2 rounded-xl border p-3.5 transition-colors ${
                        isSelected
                          ? 'border-emerald-300/40 bg-[linear-gradient(135deg,rgba(61,217,179,0.15),rgba(75,123,255,0.08))] text-white'
                          : 'border-slate-400/15 bg-[#0a0f18]/80 text-[#a8b0c3] hover:border-slate-400/30 hover:bg-white/5'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-[0.68rem] font-bold text-[#64d7bd] uppercase">
                              Lesson #{lesson.order}
                            </span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[0.62rem] font-bold uppercase tracking-wider ${
                                isPublished
                                  ? 'bg-emerald-400/15 text-emerald-300 border border-emerald-400/30'
                                  : 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                              }`}
                            >
                              {isPublished ? 'Published' : 'Draft'}
                            </span>
                          </div>
                          <h4 className="mt-1 mb-0 text-sm font-semibold text-white">
                            {lesson.title}
                          </h4>
                        </div>

                        <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100">
                          {!isPublished && (
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation()
                                void handlePublishLesson(lesson.id)
                              }}
                              className="cursor-pointer rounded bg-emerald-500/20 px-2 py-0.5 text-[0.68rem] font-semibold text-emerald-300 hover:bg-emerald-500/30"
                              title="Publish lesson for all learners"
                            >
                              Publish
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleOpenEditLesson(lesson)
                            }}
                            className="rounded p-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white"
                            title="Edit lesson"
                          >
                            ✎
                          </button>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              void handleDeleteLesson(lesson.id)
                            }}
                            className="rounded p-1 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-300"
                            title="Delete lesson"
                          >
                            ✕
                          </button>
                        </div>
                      </div>

                      {lesson.description && (
                        <p className="m-0 text-xs text-[#738099] line-clamp-2">
                          {lesson.description}
                        </p>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Column 3: Exercises - 5 cols */}
          <div className="flex flex-col gap-3 lg:col-span-5">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-semibold text-white">
                3. Exercises {activeLesson ? `in: ${activeLesson.title}` : ''} ({exercises.length})
              </h3>
              {activeLesson && (
                <button
                  type="button"
                  onClick={handleOpenCreateExercise}
                  className="cursor-pointer text-xs text-emerald-400 hover:underline"
                >
                  + Add Exercise
                </button>
              )}
            </div>

            {!activeLesson ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Select a lesson to view or create gesture exercises.
              </div>
            ) : exercises.length === 0 ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                This lesson does not have any exercises yet. Click &quot;+ Add Exercise&quot; to
                create a sign recognition task.
              </div>
            ) : (
              <div className="flex flex-col gap-2.5">
                {exercises.map((exercise, index) => (
                  <div
                    key={exercise.id}
                    className={`${panelClass} flex flex-col gap-2.5 p-4`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold text-slate-400">#{index + 1}</span>
                        <span className="rounded-md border border-emerald-400/40 bg-emerald-500/15 px-2.5 py-0.5 text-xs font-bold tracking-wider text-emerald-300">
                          SIGN: {exercise.answer}
                        </span>
                        <span className="rounded-md border border-slate-400/20 bg-slate-400/10 px-2 py-0.5 text-[0.68rem] text-[#a8b0c3]">
                          {exercise.difficulty}
                        </span>
                        <span className="rounded-md border border-slate-400/20 bg-slate-400/10 px-2 py-0.5 text-[0.68rem] text-[#a8b0c3]">
                          {exercise.points} pts
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleOpenEditExercise(exercise)}
                          className="rounded p-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white"
                          title="Edit exercise"
                        >
                          ✎
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDeleteExercise(exercise.id)}
                          className="rounded p-1 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-300"
                          title="Delete exercise"
                        >
                          ✕
                        </button>
                      </div>
                    </div>

                    <p className="m-0 text-sm font-medium text-white">{exercise.content}</p>

                    {exercise.media && exercise.media.length > 0 && (
                      <div className="mt-1 flex flex-wrap items-center gap-1.5">
                        {exercise.media.map((m, mIdx) => (
                          <a
                            key={m.id || mIdx}
                            href={m.url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 rounded-md border border-slate-700/60 bg-black/40 px-2 py-0.5 text-[0.7rem] text-slate-300 hover:border-emerald-500/40 hover:text-emerald-300"
                            title={`Open media: ${m.url}`}
                          >
                            <span>{m.type === 'video' ? '🎥' : '🖼️'}</span>
                            <span className="max-w-[130px] truncate">
                              {m.type}: {m.url.split('/').pop() || 'link'}
                            </span>
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL: Available Gestures & Poses Preview */}
      {showPosesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} max-h-[85vh] w-full max-w-2xl overflow-hidden p-6`}>
            <div className="flex items-center justify-between border-b border-slate-400/15 pb-4">
              <div>
                <h3 className="m-0 text-xl font-bold text-white">Available Gestures & Poses</h3>
                <p className="mt-1 mb-0 text-xs text-[#a8b0c3]">
                  Source:{' '}
                  <span className="font-semibold text-emerald-400">
                    {posesInfo.source === 'model-service'
                      ? 'Model Service API'
                      : 'Local lessons.ts definitions'}
                  </span>{' '}
                  · Total {posesInfo.poses.length} gestures
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => void handleRefreshPoses()}
                  className="cursor-pointer rounded-lg border border-slate-400/20 bg-slate-400/10 px-2.5 py-1 text-xs text-slate-300 transition hover:bg-slate-400/20 hover:text-white"
                >
                  ↻ Refresh
                </button>
                <button
                  type="button"
                  onClick={() => setShowPosesModal(false)}
                  className="rounded-lg p-1 text-slate-400 hover:bg-white/10 hover:text-white"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="mt-4">
              <input
                type="text"
                placeholder="Search gesture (e.g. YES, NO, MORNING)..."
                value={posesSearch}
                onChange={(e) => setPosesSearch(e.target.value)}
                className={`${inputClass} w-full`}
              />
            </div>

            <div className="mt-4 max-h-[50vh] overflow-y-auto pr-1">
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4">
                {filteredPoses.map((pose) => (
                  <div
                    key={pose}
                    className="flex items-center justify-between rounded-xl border border-slate-400/15 bg-white/5 px-3 py-2 text-xs font-semibold text-white"
                  >
                    <span>{pose}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setShowPosesModal(false)}
                className="cursor-pointer rounded-xl border border-slate-400/20 bg-slate-400/10 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-400/20"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Create / Edit Unit */}
      {showUnitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} w-full max-w-md p-6`}>
            <h3 className="m-0 text-xl font-bold text-white">
              {editingUnitId ? 'Edit Unit' : 'New Unit'}
            </h3>
            <form onSubmit={(e) => void handleSaveUnit(e)} className="mt-5 flex flex-col gap-4">
              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Unit title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Basic Greeting Signs"
                  value={unitForm.title}
                  onChange={(e) => setUnitForm({ ...unitForm, title: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Order</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={unitForm.order}
                  onChange={(e) =>
                    setUnitForm({ ...unitForm, order: parseInt(e.target.value, 10) || 1 })
                  }
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div className="mt-3 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowUnitModal(false)}
                  className="cursor-pointer rounded-xl border border-slate-400/20 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button type="submit" className={`${primaryButtonClass} !min-h-10 text-sm`}>
                  Save Unit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Create / Edit Lesson */}
      {showLessonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} w-full max-w-md p-6`}>
            <h3 className="m-0 text-xl font-bold text-white">
              {editingLessonId ? 'Edit Lesson' : 'New Lesson'}
            </h3>
            <p className="mt-1 text-xs text-emerald-400">Unit: {activeUnit?.title}</p>
            <form onSubmit={(e) => void handleSaveLesson(e)} className="mt-5 flex flex-col gap-4">
              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Lesson title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Greetings and Polite Phrases"
                  value={lessonForm.title}
                  onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Lesson description</label>
                <textarea
                  rows={3}
                  placeholder="Short description of what learners will practice..."
                  value={lessonForm.description}
                  onChange={(e) => setLessonForm({ ...lessonForm, description: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Order</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={lessonForm.order}
                  onChange={(e) =>
                    setLessonForm({ ...lessonForm, order: parseInt(e.target.value, 10) || 1 })
                  }
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div className="mt-3 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowLessonModal(false)}
                  className="cursor-pointer rounded-xl border border-slate-400/20 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button type="submit" className={`${primaryButtonClass} !min-h-10 text-sm`}>
                  Save Lesson
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Create / Edit Exercise */}
      {showExerciseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} max-h-[90vh] w-full max-w-lg overflow-y-auto p-6`}>
            <h3 className="m-0 text-xl font-bold text-white">
              {editingExerciseId ? 'Edit Exercise' : 'New Exercise'}
            </h3>
            <p className="mt-1 text-xs text-emerald-400">Lesson: {activeLesson?.title}</p>

            <form
              onSubmit={(e) => void handleSaveExercise(e)}
              className="mt-5 flex flex-col gap-4"
            >
              {/* Target pose selection (Answer) */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-[#a8b0c3]">
                    Target sign / gesture (Answer) *
                  </label>
                  <span className="text-[0.7rem] text-slate-400">
                    Source: {posesInfo.source}
                  </span>
                </div>

                {/* Dropdown of available poses */}
                <select
                  value={exerciseForm.answer}
                  onChange={(e) => handlePoseSelect(e.target.value)}
                  className={`${inputClass} mt-1 w-full bg-[#0d1420] text-white`}
                >
                  {posesInfo.poses.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>

                <p className="mt-1 text-[0.72rem] text-slate-400">
                  You can also type a custom sign in the field below:
                </p>
                <input
                  type="text"
                  required
                  placeholder="e.g. YES, SMILE, MAN"
                  value={exerciseForm.answer}
                  onChange={(e) => handlePoseSelect(e.target.value.toUpperCase())}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              {/* Prompt instruction for learner */}
              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">
                  Prompt instruction for learner *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Show the sign for: YES"
                  value={exerciseForm.content}
                  onChange={(e) => setExerciseForm({ ...exerciseForm, content: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#a8b0c3]">Exercise type</label>
                  <select
                    value={exerciseForm.type}
                    onChange={(e) =>
                      setExerciseForm({
                        ...exerciseForm,
                        type: e.target.value as ExerciseType,
                      })
                    }
                    className={`${inputClass} mt-1 w-full bg-[#0d1420] text-white`}
                  >
                    <option value="single">Single (single gesture)</option>
                    <option value="sentence">Sentence (sequence)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#a8b0c3]">Difficulty</label>
                  <select
                    value={exerciseForm.difficulty}
                    onChange={(e) =>
                      setExerciseForm({
                        ...exerciseForm,
                        difficulty: e.target.value as Difficulty,
                      })
                    }
                    className={`${inputClass} mt-1 w-full bg-[#0d1420] text-white`}
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Reward points</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  required
                  value={exerciseForm.points}
                  onChange={(e) =>
                    setExerciseForm({
                      ...exerciseForm,
                      points: parseInt(e.target.value, 10) || 10,
                    })
                  }
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              {/* Auxiliary reference media (Photos / Videos) */}
              <div className="rounded-xl border border-slate-400/20 bg-slate-900/50 p-3.5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-white">
                      Auxiliary Media (Photos / Videos)
                    </span>
                    <p className="mt-0.5 mb-0 text-[0.72rem] text-[#a8b0c3]">
                      Attach reference photos or video clips for learners.
                    </p>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleAddMedia('image')}
                      className="cursor-pointer rounded-lg border border-sky-400/30 bg-sky-500/10 px-2.5 py-1 text-xs font-medium text-sky-300 transition hover:bg-sky-500/20"
                    >
                      + Image
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAddMedia('video')}
                      className="cursor-pointer rounded-lg border border-purple-400/30 bg-purple-500/10 px-2.5 py-1 text-xs font-medium text-purple-300 transition hover:bg-purple-500/20"
                    >
                      + Video
                    </button>
                  </div>
                </div>

                {(!exerciseForm.media || exerciseForm.media.length === 0) ? (
                  <p className="mt-3 mb-1 text-center text-xs text-[#738099]">
                    No auxiliary media attached. Click above to add a media link.
                  </p>
                ) : (
                  <div className="mt-3 flex flex-col gap-2.5">
                    {exerciseForm.media.map((m, idx) => {
                      const parsed = parseMediaUrl(m.url)
                      return (
                        <div
                          key={idx}
                          className="rounded-lg border border-slate-400/15 bg-white/5 p-2.5"
                        >
                          <div className="flex items-center gap-2">
                            <select
                              value={m.type}
                              onChange={(e) => handleUpdateMedia(idx, 'type', e.target.value)}
                              className="rounded-lg border border-slate-400/20 bg-[#0d1420] px-2 py-1.5 text-xs text-white"
                            >
                              <option value="image">Image</option>
                              <option value="video">Video</option>
                            </select>
                            <input
                              type="url"
                              placeholder="Paste image or video URL (https://... or YouTube)"
                              value={m.url}
                              onChange={(e) => handleUpdateMedia(idx, 'url', e.target.value)}
                              className="flex-1 rounded-lg border border-slate-400/20 bg-[#0d1420] px-2.5 py-1.5 text-xs text-white placeholder-slate-500"
                            />
                            <button
                              type="button"
                              onClick={() => handleRemoveMedia(idx)}
                              className="cursor-pointer rounded-lg p-1.5 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-300"
                              title="Delete media"
                            >
                              ✕
                            </button>
                          </div>

                          {/* Live preview */}
                          {m.url.trim().length > 8 && (
                            <div className="mt-2 overflow-hidden rounded-md border border-slate-700/50 bg-black/40 p-1.5 text-center">
                              {parsed.isYouTube || parsed.isVimeo ? (
                                <iframe
                                  src={parsed.embedUrl}
                                  title={`Preview ${idx + 1}`}
                                  className="mx-auto aspect-video max-h-36 w-full rounded border-0"
                                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                  allowFullScreen
                                />
                              ) : m.type === 'image' || parsed.isImage ? (
                                <img
                                  src={m.url}
                                  alt={`Preview ${idx + 1}`}
                                  className="mx-auto max-h-32 rounded object-contain"
                                  onError={(e) => {
                                    ;(e.target as HTMLElement).style.display = 'none'
                                  }}
                                />
                              ) : (
                                <video
                                  src={m.url}
                                  controls
                                  className="mx-auto max-h-32 rounded"
                                />
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>

              <div className="mt-3 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowExerciseModal(false)}
                  className="cursor-pointer rounded-xl border border-slate-400/20 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white"
                >
                  Cancel
                </button>
                <button type="submit" className={`${primaryButtonClass} !min-h-10 text-sm`}>
                  {editingExerciseId ? 'Update Exercise' : 'Save Exercise'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
