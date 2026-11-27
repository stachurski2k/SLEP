from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from main import app
from modules.auth.presentation.dependencies import get_current_user_id
from modules.progress.application.commands import CompleteLessonCommand
from modules.progress.application.services import ProgressApplicationServiceImpl
from modules.progress.domain.entities import LessonProgress, UserProgress
from modules.progress.domain.repositories import (
    LessonProgressRepository,
    UserProgressRepository,
)
from modules.statistics.application.commands import RecordActivityCommand
from modules.statistics.application.services import StatisticsApplicationServiceImpl
from modules.statistics.domain.entities import DailyActivity
from modules.statistics.domain.repositories import DailyActivityRepository
from modules.statistics.presentation.dependencies import get_statistics_service


# --- IN-MEMORY REPOSITORIES ---

class InMemoryDailyActivityRepository(DailyActivityRepository):
    def __init__(self) -> None:
        self.items: dict[tuple[UUID, date], DailyActivity] = {}

    async def get_by_user_and_date(
        self, user_id: UUID, activity_date: date
    ) -> DailyActivity | None:
        return self.items.get((user_id, activity_date))

    async def list_by_user_and_date_range(
        self, user_id: UUID, start_date: date, end_date: date
    ) -> list[DailyActivity]:
        res = [
            a
            for (u, d), a in self.items.items()
            if u == user_id and start_date <= d <= end_date
        ]
        return sorted(res, key=lambda x: x.date)

    async def count_active_days(self, user_id: UUID) -> int:
        return sum(
            1
            for (u, _), a in self.items.items()
            if u == user_id and (a.xpEarned > 0 or a.lessonsCompleted > 0)
        )

    async def save(self, activity: DailyActivity) -> None:
        self.items[(activity.userId, activity.date)] = activity


class InMemoryUserProgressRepository(UserProgressRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, UserProgress] = {}

    async def get_by_user_id(self, user_id: UUID) -> UserProgress | None:
        for p in self.items.values():
            if p.userId == user_id:
                return p
        return None

    async def save(self, user_progress: UserProgress) -> None:
        self.items[user_progress.id] = user_progress


class InMemoryLessonProgressRepository(LessonProgressRepository):
    def __init__(self) -> None:
        self.items: dict[tuple[UUID, UUID], LessonProgress] = {}

    async def get_by_user_and_lesson(
        self, user_id: UUID, lesson_id: UUID
    ) -> LessonProgress | None:
        return self.items.get((user_id, lesson_id))

    async def list_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        return [lp for (u, _), lp in self.items.items() if u == user_id]

    async def list_completed_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        return [
            lp for (u, _), lp in self.items.items() if u == user_id and lp.completed
        ]

    async def save(self, lesson_progress: LessonProgress) -> None:
        self.items[(lesson_progress.userId, lesson_progress.lessonId)] = lesson_progress

    async def delete(self, user_id: UUID, lesson_id: UUID) -> None:
        self.items.pop((user_id, lesson_id), None)


# --- FIXTURES ---

@pytest.fixture
def test_user_id() -> UUID:
    return uuid4()


@pytest.fixture
def repos():
    return {
        "daily": InMemoryDailyActivityRepository(),
        "user_progress": InMemoryUserProgressRepository(),
        "lesson_progress": InMemoryLessonProgressRepository(),
    }


@pytest.fixture
def stats_service(repos):
    return StatisticsApplicationServiceImpl(
        daily_activity_repository=repos["daily"],
        user_progress_repository=repos["user_progress"],
        lesson_progress_repository=repos["lesson_progress"],
    )


@pytest.fixture
def client(stats_service, test_user_id):
    app.dependency_overrides[get_statistics_service] = lambda: stats_service
    app.dependency_overrides[get_current_user_id] = lambda: test_user_id

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --- DOMAIN TESTS ---

def test_daily_activity_domain():
    act = DailyActivity(
        id=uuid4(),
        userId=uuid4(),
        date=date(2026, 10, 6),
        xpEarned=0,
        lessonsCompleted=0,
    )
    assert act.xpEarned == 0
    assert act.lessonsCompleted == 0

    act.record_progress(xp=15, lessons_completed=1)
    assert act.xpEarned == 15
    assert act.lessonsCompleted == 1


# --- APPLICATION SERVICE TESTS ---

@pytest.mark.asyncio
async def test_record_activity_only_when_actual_activity(stats_service, repos, test_user_id):
    today = date(2026, 10, 6)

    # 1. No activity if XP = 0 and lessons = 0 -> returns None and no record stored
    res_zero = await stats_service.recordActivity(
        RecordActivityCommand(userId=test_user_id, xp=0, lessonsCompleted=0, activityDate=today)
    )
    assert res_zero is None
    assert (await repos["daily"].get_by_user_and_date(test_user_id, today)) is None
    assert (await repos["daily"].count_active_days(test_user_id)) == 0

    # 2. Record real activity -> created in repository
    res_real = await stats_service.recordActivity(
        RecordActivityCommand(userId=test_user_id, xp=10, lessonsCompleted=1, activityDate=today)
    )
    assert res_real is not None
    assert res_real.xpEarned == 10
    assert res_real.lessonsCompleted == 1
    assert (await repos["daily"].count_active_days(test_user_id)) == 1

    # 3. Subsequent activity on same day increments existing record
    res_inc = await stats_service.recordActivity(
        RecordActivityCommand(userId=test_user_id, xp=20, lessonsCompleted=2, activityDate=today)
    )
    assert res_inc is not None
    assert res_inc.xpEarned == 30
    assert res_inc.lessonsCompleted == 3
    assert (await repos["daily"].count_active_days(test_user_id)) == 1


@pytest.mark.asyncio
async def test_calculate_accuracy_and_stats(stats_service, repos, test_user_id):
    # 1. When no lesson progress exists -> accuracy is 0.0
    acc_zero = await stats_service.calculateAccuracy(test_user_id)
    assert acc_zero == 0.0

    # 2. Add lesson attempts: 1 lesson completed in 2 attempts -> 50% accuracy
    lesson1 = LessonProgress(
        id=uuid4(),
        userId=test_user_id,
        lessonId=uuid4(),
        completed=True,
        attempts=2,
    )
    await repos["lesson_progress"].save(lesson1)

    acc = await stats_service.calculateAccuracy(test_user_id)
    assert acc == 50.0

    # 3. Add second lesson: completed in 1 attempt -> (2 completed / 3 attempts) = 66.67%
    lesson2 = LessonProgress(
        id=uuid4(),
        userId=test_user_id,
        lessonId=uuid4(),
        completed=True,
        attempts=1,
    )
    await repos["lesson_progress"].save(lesson2)

    acc2 = await stats_service.calculateAccuracy(test_user_id)
    assert acc2 == 66.67


@pytest.mark.asyncio
async def test_weekly_report_generation(stats_service, repos, test_user_id):
    # Fixed Tuesday
    ref_date = date(2026, 10, 6)

    # Activity only on Wednesday (2026-10-07) and Friday (2026-10-09)
    await stats_service.recordActivity(
        RecordActivityCommand(userId=test_user_id, xp=30, lessonsCompleted=2, activityDate=date(2026, 10, 7))
    )
    await stats_service.recordActivity(
        RecordActivityCommand(userId=test_user_id, xp=20, lessonsCompleted=1, activityDate=date(2026, 10, 9))
    )

    report = await stats_service.getWeeklyReport(test_user_id, reference_date=ref_date)
    assert report.totalXp == 50
    assert report.lessonsCompleted == 3
    assert report.activeDaysCount == 2
    assert len(report.dailyBreakdown) == 7

    # Check that inactive days have 0 XP and 0 lessons
    mon = report.dailyBreakdown[0]
    assert mon.dayOfWeek == "Monday"
    assert mon.xpEarned == 0
    assert mon.lessonsCompleted == 0

    # Wednesday has 30 XP
    wed = report.dailyBreakdown[2]
    assert wed.dayOfWeek == "Wednesday"
    assert wed.xpEarned == 30
    assert wed.lessonsCompleted == 2


@pytest.mark.asyncio
async def test_progress_integration_records_daily_activity(repos, test_user_id):
    # Verify that completing a lesson via progress service records daily activity
    progress_svc = ProgressApplicationServiceImpl(
        user_progress_repository=repos["user_progress"],
        lesson_progress_repository=repos["lesson_progress"],
        daily_activity_repository=repos["daily"],
    )

    lesson_id = uuid4()
    comp_res = await progress_svc.completeLesson(
        CompleteLessonCommand(userId=test_user_id, lessonId=lesson_id, xpReward=10)
    )
    assert comp_res.isFirstCompletion is True
    assert comp_res.earnedXp == 10

    # Check that daily_activity repository recorded activity today
    today = datetime.now(timezone.utc).date()
    act = await repos["daily"].get_by_user_and_date(test_user_id, today)
    assert act is not None
    assert act.xpEarned == 10
    assert act.lessonsCompleted == 1


# --- FASTAPI ENDPOINT TESTS ---

def test_statistics_endpoints(client, stats_service, repos, test_user_id):
    # 1. GET /api/v1/statistics
    res = client.get("/api/v1/statistics")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["totalXp"] == 0
    assert data["completedLessons"] == 0
    assert data["averageAccuracy"] == 0.0

    # 2. POST /api/v1/statistics/record
    res = client.post(
        "/api/v1/statistics/record",
        json={"xp": 10, "lessonsCompleted": 1, "activityDate": "2026-10-06"},
    )
    assert res.status_code == 200, res.text
    record_data = res.json()
    assert record_data["xpEarned"] == 10
    assert record_data["lessonsCompleted"] == 1

    # 3. GET /api/v1/statistics/weekly
    res = client.get("/api/v1/statistics/weekly?date=2026-10-06")
    assert res.status_code == 200, res.text
    weekly_data = res.json()
    assert weekly_data["totalXp"] == 10
    assert weekly_data["lessonsCompleted"] == 1
    assert len(weekly_data["dailyBreakdown"]) == 7

    # 4. GET /api/v1/statistics/accuracy
    res = client.get("/api/v1/statistics/accuracy")
    assert res.status_code == 200, res.text
    acc_data = res.json()
    assert "accuracy" in acc_data
