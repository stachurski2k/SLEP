from datetime import datetime, timezone
from uuid import UUID, uuid4

from modules.statistics.domain.entities import DailyActivity
from modules.statistics.domain.repositories import DailyActivityRepository

from ...domain.entities import LessonProgress, UserProgress
from ...domain.repositories import LessonProgressRepository, UserProgressRepository
from ..commands import CompleteLessonCommand, ResetLessonCommand, StartLessonCommand
from ..dtos import LessonCompletionResultDTO, ProgressSummaryDTO
from ..interfaces import ProgressApplicationService


class ProgressApplicationServiceImpl(ProgressApplicationService):
    """Implementation of ProgressApplicationService handling user learning progression."""

    def __init__(
        self,
        user_progress_repository: UserProgressRepository,
        lesson_progress_repository: LessonProgressRepository,
        daily_activity_repository: DailyActivityRepository | None = None,
    ) -> None:
        self._user_progress_repo = user_progress_repository
        self._lesson_progress_repo = lesson_progress_repository
        self._daily_activity_repo = daily_activity_repository

    async def _get_or_create_user_progress(self, user_id: UUID) -> UserProgress:
        user_progress = await self._user_progress_repo.get_by_user_id(user_id)
        if user_progress is None:
            now = datetime.now(timezone.utc)
            user_progress = UserProgress(
                id=uuid4(),
                userId=user_id,
                xp=0,
                createdAt=now,
                updatedAt=now,
            )
            await self._user_progress_repo.save(user_progress)
        return user_progress

    async def getUserProgress(self, user_id: UUID) -> UserProgress:
        return await self._get_or_create_user_progress(user_id)

    async def getProgressSummary(self, user_id: UUID) -> ProgressSummaryDTO:
        user_progress = await self._get_or_create_user_progress(user_id)
        completed_lessons = await self._lesson_progress_repo.list_completed_by_user_id(
            user_id
        )
        completed_ids = [lp.lessonId for lp in completed_lessons]
        return ProgressSummaryDTO(
            userId=user_id,
            totalXp=user_progress.xp,
            completedLessonsCount=len(completed_ids),
            completedLessonIds=completed_ids,
        )

    async def getLessonProgress(
        self, user_id: UUID, lesson_id: UUID
    ) -> LessonProgress:
        lp = await self._lesson_progress_repo.get_by_user_and_lesson(user_id, lesson_id)
        if lp is None:
            return LessonProgress(
                id=uuid4(),
                userId=user_id,
                lessonId=lesson_id,
                completed=False,
                attempts=0,
                completedAt=None,
                lastAttemptAt=None,
            )
        return lp

    async def startLesson(self, command: StartLessonCommand) -> LessonProgress:
        lp = await self._lesson_progress_repo.get_by_user_and_lesson(
            command.userId, command.lessonId
        )
        if lp is None:
            lp = LessonProgress(
                id=uuid4(),
                userId=command.userId,
                lessonId=command.lessonId,
                completed=False,
                attempts=0,
            )

        lp.start_attempt()
        await self._lesson_progress_repo.save(lp)
        return lp

    async def completeLesson(
        self, command: CompleteLessonCommand
    ) -> LessonCompletionResultDTO:
        lp = await self._lesson_progress_repo.get_by_user_and_lesson(
            command.userId, command.lessonId
        )
        if lp is None:
            lp = LessonProgress(
                id=uuid4(),
                userId=command.userId,
                lessonId=command.lessonId,
                completed=False,
                attempts=1,
            )

        is_first_completion, earned_xp = lp.complete(xp_reward=command.xpReward)
        await self._lesson_progress_repo.save(lp)

        user_progress = await self._get_or_create_user_progress(command.userId)
        if is_first_completion and earned_xp > 0:
            user_progress.add_xp(earned_xp)
            await self._user_progress_repo.save(user_progress)

            if self._daily_activity_repo:
                today = datetime.now(timezone.utc).date()
                act = await self._daily_activity_repo.get_by_user_and_date(
                    command.userId, today
                )
                if act is None:
                    act = DailyActivity(
                        id=uuid4(),
                        userId=command.userId,
                        date=today,
                        xpEarned=earned_xp,
                        lessonsCompleted=1,
                    )
                else:
                    act.record_progress(xp=earned_xp, lessons_completed=1)
                await self._daily_activity_repo.save(act)

        return LessonCompletionResultDTO(
            lessonId=command.lessonId,
            isFirstCompletion=is_first_completion,
            earnedXp=earned_xp,
            totalXp=user_progress.xp,
            completedAt=lp.completedAt or datetime.now(timezone.utc),
        )

    async def resetLesson(self, command: ResetLessonCommand) -> LessonProgress:
        lp = await self._lesson_progress_repo.get_by_user_and_lesson(
            command.userId, command.lessonId
        )
        if lp is None:
            lp = LessonProgress(
                id=uuid4(),
                userId=command.userId,
                lessonId=command.lessonId,
                completed=False,
                attempts=0,
            )
        else:
            lp.reset()

        await self._lesson_progress_repo.save(lp)
        return lp
