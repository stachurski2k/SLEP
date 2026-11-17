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
    toast.success(`Zaktualizowano listę gestów: ${res.poses.length} gestów (${res.source}).`)
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
      toast.error(err instanceof Error ? err.message : 'Błąd ładowania lekcji.')
    }
  }, [])

  // Load exercises for a specific lesson
  const loadExercises = useCallback(async (lessonId: string) => {
    try {
      const data = await fetchExercisesByLesson(lessonId)
      setExercises(data)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Błąd ładowania zadań.')
    }
  }, [])

  // Load units and sync
  const loadUnits = useCallback(async () => {
    try {
      const data = await fetchUnits()
      setUnits(data)
      if (data.length > 0) {
        const targetUnitId = activeUnitId && data.some((u) => u.id === activeUnitId)
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
      toast.error(err instanceof Error ? err.message : 'Błąd ładowania unitów.')
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
        if (isMounted) toast.error(err instanceof Error ? err.message : 'Błąd inicjalizacji danych.')
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
        title: 'Jednostka 1: Podstawy języka migowego',
        order: 1,
      })

      for (let i = 0; i < staticLessons.length; i++) {
        const item = staticLessons[i]
        const createdLesson = await createLesson(newUnit.id, {
          title: item.title,
          description: `Ćwiczenie gestów: ${item.signs.join(', ')}`,
          order: i + 1,
        })
        await publishLesson(createdLesson.id)

        for (const sign of item.signs) {
          await createExercise(createdLesson.id, {
            type: 'single',
            difficulty: 'beginner',
            points: 10,
            content: `Wykonaj znak dla: ${sign}`,
            answer: sign,
          })
        }
      }

      toast.success('Pomyślnie zainicjalizowano unity i lekcje z bazy lessons.ts!')
      await loadUnits()
      setActiveUnitId(newUnit.id)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Błąd importowania danych.')
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
      toast.error('Tytuł unitu jest wymagany.')
      return
    }

    try {
      if (editingUnitId) {
        await updateUnit(editingUnitId, unitForm)
        toast.success('Zaktualizowano unit.')
      } else {
        const created = await createUnit(unitForm)
        toast.success('Utworzono nowy unit.')
        setActiveUnitId(created.id)
      }
      setShowUnitModal(false)
      await loadUnits()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Wystąpił błąd zapisu unitu.')
    }
  }

  const handleDeleteUnit = async (unitId: string) => {
    if (!confirm('Czy na pewno chcesz usunąć ten unit wraz ze wszystkimi jego lekcjami?')) return
    try {
      await deleteUnit(unitId)
      toast.success('Unit został usunięty.')
      if (activeUnitId === unitId) {
        setActiveUnitId(null)
      }
      await loadUnits()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Błąd podczas usuwania unitu.')
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
      toast.error('Tytuł lekcji jest wymagany.')
      return
    }

    try {
      if (editingLessonId) {
        await updateLesson(editingLessonId, lessonForm)
        toast.success('Zaktualizowano lekcję.')
      } else {
        const created = await createLesson(activeUnitId, lessonForm)
        toast.success('Utworzono nową lekcję.')
        setActiveLessonId(created.id)
      }
      setShowLessonModal(false)
      await loadLessons(activeUnitId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Wystąpił błąd zapisu lekcji.')
    }
  }

  const handlePublishLesson = async (lessonId: string) => {
    try {
      await publishLesson(lessonId)
      toast.success('Lekcja została opublikowana!')
      if (activeUnitId) await loadLessons(activeUnitId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Błąd podczas publikacji lekcji.')
    }
  }

  const handleDeleteLesson = async (lessonId: string) => {
    if (!confirm('Czy na pewno chcesz usunąć tę lekcję i jej zadania?')) return
    try {
      await deleteLesson(lessonId)
      toast.success('Lekcja została usunięta.')
      if (activeLessonId === lessonId) {
        setActiveLessonId(null)
      }
      if (activeUnitId) await loadLessons(activeUnitId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Błąd podczas usuwania lekcji.')
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
      content: `Wykonaj znak dla: ${defaultPose}`,
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
        prev.content.startsWith('Wykonaj znak dla:') || !prev.content
          ? `Wykonaj znak dla: ${selectedPose}`
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
      toast.error('Docelowy gest (odpowiedź) jest wymagany.')
      return
    }
    if (!exerciseForm.content.trim()) {
      toast.error('Treść zadania jest wymagana.')
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
        toast.success('Zaktualizowano zadanie.')
      } else {
        await createExercise(activeLessonId, {
          type: exerciseForm.type,
          difficulty: exerciseForm.difficulty,
          points: exerciseForm.points,
          content: exerciseForm.content.trim(),
          answer: exerciseForm.answer.trim().toUpperCase(),
          media: cleanMedia,
        })
        toast.success('Utworzono zadanie.')
      }
      setShowExerciseModal(false)
      await loadExercises(activeLessonId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Wystąpił błąd zapisu zadania.')
    }
  }

  const handleDeleteExercise = async (exerciseId: string) => {
    if (!confirm('Czy na pewno chcesz usunąć to zadanie?')) return
    try {
      await deleteExercise(exerciseId)
      toast.success('Zadanie zostało usunięte.')
      if (activeLessonId) await loadExercises(activeLessonId)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Błąd podczas usuwania zadania.')
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
            Panel Administratora · Zarządzanie Kursem
          </h2>
          <p className="mt-1 mb-0 text-sm text-[#a8b0c3]">
            Twórz i konfiguruj unity, lekcje oraz interaktywne zadania bazujące na gestach modelu.
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
            title="Kliknij, aby przejrzeć dostępne gesty"
          >
            <span
              className={`size-2 rounded-full ${
                posesInfo.source === 'model-service' ? 'bg-emerald-400 animate-pulse' : 'bg-sky-400'
              }`}
            />
            <span>
              {posesInfo.source === 'model-service' ? 'Model Service (live)' : 'Baza z lessons.ts'} ·{' '}
              {posesInfo.poses.length} gestów
            </span>
            <span className="text-white/40">👁</span>
          </button>

          {units.length === 0 && (
            <button
              type="button"
              onClick={() => void handleSeedFromLessons()}
              className="cursor-pointer rounded-xl border border-emerald-400/30 bg-emerald-400/15 px-3.5 py-2 text-xs font-semibold text-emerald-300 transition hover:bg-emerald-400/25"
            >
              ⚡ Zaimportuj dane z lessons.ts
            </button>
          )}

          <button
            type="button"
            onClick={handleOpenCreateUnit}
            className={`${primaryButtonClass} !min-h-10 text-sm`}
          >
            + Nowy Unit
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="mt-12 flex justify-center text-slate-400">
          Ładowanie struktury kursu...
        </div>
      ) : (
        /* 3-Column Manager Layout */
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Column 1: Unity (Units) - 3 cols */}
          <div className="flex flex-col gap-3 lg:col-span-3">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-semibold text-white">
                1. Unity ({units.length})
              </h3>
              <button
                type="button"
                onClick={handleOpenCreateUnit}
                className="text-xs text-emerald-400 hover:underline"
              >
                + Dodaj
              </button>
            </div>

            {units.length === 0 ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Brak unitów. Kliknij &quot;+ Nowy Unit&quot; lub zaimportuj dane demonstracyjne.
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
                          title="Edytuj unit"
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
                          title="Usuń unit"
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

          {/* Column 2: Lekcje (Lessons) - 4 cols */}
          <div className="flex flex-col gap-3 lg:col-span-4">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-semibold text-white">
                2. Lekcje {activeUnit ? `w: ${activeUnit.title}` : ''} ({lessons.length})
              </h3>
              {activeUnit && (
                <button
                  type="button"
                  onClick={handleOpenCreateLesson}
                  className="text-xs text-emerald-400 hover:underline"
                >
                  + Dodaj lekcję
                </button>
              )}
            </div>

            {!activeUnit ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Wybierz unit z lewej strony, aby zarządzać jego lekcjami.
              </div>
            ) : lessons.length === 0 ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Brak lekcji w tym unicie. Kliknij &quot;+ Dodaj lekcję&quot;.
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
                              Lekcja #{lesson.order}
                            </span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[0.62rem] font-bold uppercase tracking-wider ${
                                isPublished
                                  ? 'bg-emerald-400/15 text-emerald-300 border border-emerald-400/30'
                                  : 'bg-amber-400/15 text-amber-300 border border-amber-400/30'
                              }`}
                            >
                              {lesson.status}
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
                              className="rounded bg-emerald-500/20 px-2 py-0.5 text-[0.68rem] font-semibold text-emerald-300 hover:bg-emerald-500/30"
                              title="Publikuj lekcję dla użytkowników"
                            >
                              Publikuj
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleOpenEditLesson(lesson)
                            }}
                            className="rounded p-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white"
                            title="Edytuj lekcję"
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
                            title="Usuń lekcję"
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

          {/* Column 3: Zadania (Exercises) - 5 cols */}
          <div className="flex flex-col gap-3 lg:col-span-5">
            <div className="flex items-center justify-between">
              <h3 className="m-0 text-base font-semibold text-white">
                3. Zadania {activeLesson ? `w: ${activeLesson.title}` : ''} ({exercises.length})
              </h3>
              {activeLesson && (
                <button
                  type="button"
                  onClick={handleOpenCreateExercise}
                  className="text-xs text-emerald-400 hover:underline"
                >
                  + Dodaj zadanie
                </button>
              )}
            </div>

            {!activeLesson ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Wybierz lekcję, aby przeglądać lub dodawać do niej zadania gestów.
              </div>
            ) : exercises.length === 0 ? (
              <div className={`${panelClass} p-5 text-center text-sm text-[#738099]`}>
                Ta lekcja nie ma jeszcze żadnych zadań. Kliknij &quot;+ Dodaj zadanie&quot;, aby
                stworzyć ćwiczenie rozpoznawania znaku.
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
                          GEST: {exercise.answer}
                        </span>
                        <span className="rounded-md border border-slate-400/20 bg-slate-400/10 px-2 py-0.5 text-[0.68rem] text-[#a8b0c3]">
                          {exercise.difficulty}
                        </span>
                        <span className="rounded-md border border-slate-400/20 bg-slate-400/10 px-2 py-0.5 text-[0.68rem] text-[#a8b0c3]">
                          {exercise.points} pkt
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleOpenEditExercise(exercise)}
                          className="rounded p-1 text-xs text-slate-400 hover:bg-white/10 hover:text-white"
                          title="Edytuj zadanie"
                        >
                          ✎
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleDeleteExercise(exercise.id)}
                          className="rounded p-1 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-300"
                          title="Usuń zadanie"
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
                            title={`Otwórz materiał: ${m.url}`}
                          >
                            <span>{m.type === 'video' ? '🎥' : '🖼️'}</span>
                            <span className="max-w-[130px] truncate">{m.type}: {m.url.split('/').pop() || 'link'}</span>
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

      {/* MODAL: Podgląd Dostępnych Póz */}
      {showPosesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} max-h-[85vh] w-full max-w-2xl overflow-hidden p-6`}>
            <div className="flex items-center justify-between border-b border-slate-400/15 pb-4">
              <div>
                <h3 className="m-0 text-xl font-bold text-white">Dostępne gesty i pozy</h3>
                <p className="mt-1 mb-0 text-xs text-[#a8b0c3]">
                  Źródło:{' '}
                  <span className="font-semibold text-emerald-400">
                    {posesInfo.source === 'model-service'
                      ? 'Model Service API'
                      : 'Lokalne definicje lessons.ts'}
                  </span>{' '}
                  · Łącznie {posesInfo.poses.length} gestów
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => void handleRefreshPoses()}
                  className="cursor-pointer rounded-lg border border-slate-400/20 bg-slate-400/10 px-2.5 py-1 text-xs text-slate-300 transition hover:bg-slate-400/20 hover:text-white"
                >
                  ↻ Odśwież
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
                placeholder="Szukaj gestu (np. YES, NO, MORNING)..."
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
                Zamknij
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Tworzenie / Edycja Unitu */}
      {showUnitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} w-full max-w-md p-6`}>
            <h3 className="m-0 text-xl font-bold text-white">
              {editingUnitId ? 'Edytuj Unit' : 'Nowy Unit'}
            </h3>
            <form onSubmit={(e) => void handleSaveUnit(e)} className="mt-5 flex flex-col gap-4">
              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Tytuł unitu</label>
                <input
                  type="text"
                  required
                  placeholder="np. Podstawowe gesty powitalne"
                  value={unitForm.title}
                  onChange={(e) => setUnitForm({ ...unitForm, title: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Kolejność (Order)</label>
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
                  Anuluj
                </button>
                <button type="submit" className={`${primaryButtonClass} !min-h-10 text-sm`}>
                  Zapisz Unit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Tworzenie / Edycja Lekcji */}
      {showLessonModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} w-full max-w-md p-6`}>
            <h3 className="m-0 text-xl font-bold text-white">
              {editingLessonId ? 'Edytuj Lekcję' : 'Nowa Lekcja'}
            </h3>
            <p className="mt-1 text-xs text-emerald-400">Unit: {activeUnit?.title}</p>
            <form onSubmit={(e) => void handleSaveLesson(e)} className="mt-5 flex flex-col gap-4">
              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Tytuł lekcji</label>
                <input
                  type="text"
                  required
                  placeholder="np. Powitania i zwroty grzecznościowe"
                  value={lessonForm.title}
                  onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Opis lekcji</label>
                <textarea
                  rows={3}
                  placeholder="Krótki opis czego użytkownik się nauczy..."
                  value={lessonForm.description}
                  onChange={(e) => setLessonForm({ ...lessonForm, description: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Kolejność (Order)</label>
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
                  Anuluj
                </button>
                <button type="submit" className={`${primaryButtonClass} !min-h-10 text-sm`}>
                  Zapisz Lekcję
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: Tworzenie / Edycja Zadania (Exercise) */}
      {showExerciseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
          <div className={`${panelClass} max-h-[90vh] w-full max-w-lg overflow-y-auto p-6`}>
            <h3 className="m-0 text-xl font-bold text-white">
              {editingExerciseId ? 'Edytuj Zadanie w Lekcji' : 'Nowe Zadanie w Lekcji'}
            </h3>
            <p className="mt-1 text-xs text-emerald-400">Lekcja: {activeLesson?.title}</p>

            <form
              onSubmit={(e) => void handleSaveExercise(e)}
              className="mt-5 flex flex-col gap-4"
            >
              {/* Wybór pozy docelowej (Answer) */}
              <div>
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-[#a8b0c3]">
                    Oczekiwany gest / poza (Answer) *
                  </label>
                  <span className="text-[0.7rem] text-slate-400">
                    Źródło: {posesInfo.source}
                  </span>
                </div>

                {/* Dropdown z dostępnych póz */}
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
                  Możesz też wpisać niestandardowy gest w polu poniżej:
                </p>
                <input
                  type="text"
                  required
                  placeholder="np. YES, SMILE, MAN"
                  value={exerciseForm.answer}
                  onChange={(e) => handlePoseSelect(e.target.value.toUpperCase())}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              {/* Treść polecenia (Content) */}
              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">
                  Treść polecenia dla ucznia *
                </label>
                <input
                  type="text"
                  required
                  placeholder="np. Wykonaj znak dla: YES"
                  value={exerciseForm.content}
                  onChange={(e) => setExerciseForm({ ...exerciseForm, content: e.target.value })}
                  className={`${inputClass} mt-1 w-full`}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-[#a8b0c3]">Typ zadania</label>
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
                    <option value="single">Single (pojedynczy gest)</option>
                    <option value="sentence">Sentence (sekwencja)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#a8b0c3]">Trudność</label>
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
                    <option value="beginner">Beginner (początkujący)</option>
                    <option value="intermediate">Intermediate (średni)</option>
                    <option value="advanced">Advanced (zaawansowany)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-[#a8b0c3]">Punkty za wykonanie</label>
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

              {/* Materiały pomocnicze (Zdjęcia / Wideo) */}
              <div className="rounded-xl border border-slate-400/20 bg-slate-900/50 p-3.5">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold text-white">
                      Materiały pomocnicze (Media)
                    </span>
                    <p className="mt-0.5 mb-0 text-[0.72rem] text-[#a8b0c3]">
                      Przypnij zdjęcia lub nagrania wideo jako materiały referencyjne.
                    </p>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleAddMedia('image')}
                      className="cursor-pointer rounded-lg border border-sky-400/30 bg-sky-500/10 px-2.5 py-1 text-xs font-medium text-sky-300 transition hover:bg-sky-500/20"
                    >
                      + Zdjęcie
                    </button>
                    <button
                      type="button"
                      onClick={() => handleAddMedia('video')}
                      className="cursor-pointer rounded-lg border border-purple-400/30 bg-purple-500/10 px-2.5 py-1 text-xs font-medium text-purple-300 transition hover:bg-purple-500/20"
                    >
                      + Wideo
                    </button>
                  </div>
                </div>

                {(!exerciseForm.media || exerciseForm.media.length === 0) ? (
                  <p className="mt-3 mb-1 text-center text-xs text-[#738099]">
                    Brak załączonych materiałów pomocniczych. Kliknij powyżej, aby dodać link.
                  </p>
                ) : (
                  <div className="mt-3 flex flex-col gap-2.5">
                    {exerciseForm.media.map((m, idx) => (
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
                            <option value="image">Zdjęcie</option>
                            <option value="video">Wideo</option>
                          </select>
                          <input
                            type="url"
                            placeholder="Wklej URL zdjęcia lub wideo (https://...)"
                            value={m.url}
                            onChange={(e) => handleUpdateMedia(idx, 'url', e.target.value)}
                            className="flex-1 rounded-lg border border-slate-400/20 bg-[#0d1420] px-2.5 py-1.5 text-xs text-white placeholder-slate-500"
                          />
                          <button
                            type="button"
                            onClick={() => handleRemoveMedia(idx)}
                            className="rounded-lg p-1.5 text-xs text-rose-400 hover:bg-rose-500/20 hover:text-rose-300"
                            title="Usuń materiał"
                          >
                            ✕
                          </button>
                        </div>

                        {/* Podgląd live jeśli podano URL */}
                        {m.url.trim().length > 8 && (
                          <div className="mt-2 overflow-hidden rounded-md border border-slate-700/50 bg-black/40 p-1.5 text-center">
                            {m.type === 'image' ? (
                              <img
                                src={m.url}
                                alt={`Podgląd ${idx + 1}`}
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
                    ))}
                  </div>
                )}
              </div>

              <div className="mt-3 flex justify-end gap-2.5">
                <button
                  type="button"
                  onClick={() => setShowExerciseModal(false)}
                  className="cursor-pointer rounded-xl border border-slate-400/20 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white"
                >
                  Anuluj
                </button>
                <button type="submit" className={`${primaryButtonClass} !min-h-10 text-sm`}>
                  {editingExerciseId ? 'Zaktualizuj Zadanie' : 'Zapisz Zadanie'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  )
}
