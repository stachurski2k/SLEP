from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

from modules.learning.domain.repositories import CourseRepository, LessonRepository
from modules.progress.domain.repositories import (
    LessonProgressRepository,
    UserProgressRepository,
)

from ...domain.entities import (
    DailyActivity,
    LearningStatistics,
    WeeklyDayActivity,
    WeeklyReport,
)
from ...domain.repositories import DailyActivityRepository
from ..commands import RecordActivityCommand
from ..interfaces import StatisticsApplicationService


class StatisticsApplicationServiceImpl(StatisticsApplicationService):
    """Implementation of StatisticsApplicationService returning domain entities directly."""

    def __init__(
        self,
        daily_activity_repository: DailyActivityRepository,
        user_progress_repository: UserProgressRepository,
        lesson_progress_repository: LessonProgressRepository,
        course_repository: CourseRepository | None = None,
        lesson_repository: LessonRepository | None = None,
    ) -> None:
        self._daily_activity_repo = daily_activity_repository
        self._user_progress_repo = user_progress_repository
        self._lesson_progress_repo = lesson_progress_repository
        self._course_repo = course_repository
        self._lesson_repo = lesson_repository

    async def recordActivity(
        self, command: RecordActivityCommand
    ) -> DailyActivity | None:
        if command.xp <= 0 and command.lessonsCompleted <= 0:
            return None

        act_date = command.activityDate or datetime.now(timezone.utc).date()
        activity = await self._daily_activity_repo.get_by_user_and_date(
            command.userId, act_date
        )

        if activity is None:
            activity = DailyActivity(
                id=uuid4(),
                userId=command.userId,
                date=act_date,
                xpEarned=command.xp,
                lessonsCompleted=command.lessonsCompleted,
            )
        else:
            activity.record_progress(
                xp=command.xp, lessons_completed=command.lessonsCompleted
            )

        await self._daily_activity_repo.save(activity)
        return activity

    async def calculateAccuracy(self, user_id: UUID) -> float:
        lesson_progresses = await self._lesson_progress_repo.list_by_user_id(user_id)
        if not lesson_progresses:
            return 0.0

        total_attempts = sum(lp.attempts for lp in lesson_progresses)
        if total_attempts == 0:
            return 0.0

        completed_count = sum(1 for lp in lesson_progresses if lp.completed)
        accuracy = (completed_count / total_attempts) * 100.0
        return round(min(accuracy, 100.0), 2)

    async def getLearningStatistics(self, user_id: UUID) -> LearningStatistics:
        user_progress = await self._user_progress_repo.get_by_user_id(user_id)
        total_xp = user_progress.xp if user_progress else 0

        lesson_progresses = await self._lesson_progress_repo.list_by_user_id(user_id)
        completed_lessons = [lp for lp in lesson_progresses if lp.completed]
        completed_count = len(completed_lessons)
        completed_lesson_ids = {lp.lessonId for lp in completed_lessons}

        active_days_count = await self._daily_activity_repo.count_active_days(user_id)
        accuracy = await self.calculateAccuracy(user_id)

        completed_courses_count = 0
        if self._course_repo:
            courses = await self._course_repo.list_all()
            for c in courses:
                full_course = await self._course_repo.get_by_id(c.id)
                if not full_course or not full_course.units:
                    continue

                course_lesson_ids: set[UUID] = set()
                for u in full_course.units:
                    for l in u.lessons:
                        course_lesson_ids.add(l.id)

                if course_lesson_ids and course_lesson_ids.issubset(completed_lesson_ids):
                    completed_courses_count += 1

        return LearningStatistics(
            userId=user_id,
            totalXp=total_xp,
            completedLessons=completed_count,
            completedCourses=completed_courses_count,
            averageAccuracy=accuracy,
            activeDaysCount=active_days_count,
        )

    async def getWeeklyReport(
        self, user_id: UUID, reference_date: date | None = None
    ) -> WeeklyReport:
        target_date = reference_date or datetime.now(timezone.utc).date()
        # Calculate Monday of the given week
        start_date = target_date - timedelta(days=target_date.weekday())
        end_date = start_date + timedelta(days=6)

        existing_activities = (
            await self._daily_activity_repo.list_by_user_and_date_range(
                user_id, start_date, end_date
            )
        )
        activity_map = {act.date: act for act in existing_activities}

        breakdown: list[WeeklyDayActivity] = []
        days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        total_xp = 0
        total_lessons = 0

        for i in range(7):
            current_day = start_date + timedelta(days=i)
            act = activity_map.get(current_day)
            xp = act.xpEarned if act else 0
            lessons = act.lessonsCompleted if act else 0
            total_xp += xp
            total_lessons += lessons

            breakdown.append(
                WeeklyDayActivity(
                    date=current_day,
                    xpEarned=xp,
                    lessonsCompleted=lessons,
                    dayOfWeek=days_names[i],
                )
            )

        active_days_in_week = len(existing_activities)
        avg_daily_xp = round(total_xp / 7.0, 2)

        return WeeklyReport(
            userId=user_id,
            startDate=start_date,
            endDate=end_date,
            totalXp=total_xp,
            lessonsCompleted=total_lessons,
            activeDaysCount=active_days_in_week,
            dailyBreakdown=breakdown,
            averageDailyXp=avg_daily_xp,
        )
