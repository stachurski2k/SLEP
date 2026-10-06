from datetime import datetime, timezone
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from main import app
from modules.auth.presentation.dependencies import get_current_user_id
from modules.progress.application.commands import (
    CompleteLessonCommand,
    ResetLessonCommand,
    StartLessonCommand,
)
from modules.progress.application.services import ProgressApplicationServiceImpl
from modules.progress.domain.entities import LessonProgress, UserProgress
from modules.progress.domain.repositories import (
    LessonProgressRepository,
    UserProgressRepository,
)
from modules.progress.presentation.dependencies import get_progress_service


# --- IN-MEMORY REPOSITORIES FOR TESTING ---

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
        self.items: dict[UUID, LessonProgress] = {}

    async def get_by_user_and_lesson(
        self, user_id: UUID, lesson_id: UUID
    ) -> LessonProgress | None:
        for lp in self.items.values():
            if lp.userId == user_id and lp.lessonId == lesson_id:
                return lp
        return None

    async def list_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        return [lp for lp in self.items.values() if lp.userId == user_id]

    async def list_completed_by_user_id(self, user_id: UUID) -> list[LessonProgress]:
        return [
            lp for lp in self.items.values() if lp.userId == user_id and lp.completed
        ]

    async def save(self, lesson_progress: LessonProgress) -> None:
        self.items[lesson_progress.id] = lesson_progress

    async def delete(self, user_id: UUID, lesson_id: UUID) -> None:
        to_del = [
            k
            for k, v in self.items.items()
            if v.userId == user_id and v.lessonId == lesson_id
        ]
        for k in to_del:
            self.items.pop(k, None)


# --- FIXTURES ---

@pytest.fixture
def test_user_id() -> UUID:
    return uuid4()


@pytest.fixture
def service():
    user_repo = InMemoryUserProgressRepository()
    lesson_repo = InMemoryLessonProgressRepository()
    return ProgressApplicationServiceImpl(
        user_progress_repository=user_repo,
        lesson_progress_repository=lesson_repo,
    )


@pytest.fixture
def client(service, test_user_id):
    app.dependency_overrides[get_progress_service] = lambda: service
    app.dependency_overrides[get_current_user_id] = lambda: test_user_id

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --- DOMAIN TESTS ---

def test_user_progress_domain():
    user_id = uuid4()
    progress = UserProgress(id=uuid4(), userId=user_id, xp=0)
    assert progress.xp == 0

    progress.add_xp(10)
    assert progress.xp == 10

    progress.add_xp(0)
    assert progress.xp == 10


def test_lesson_progress_domain():
    user_id = uuid4()
    lesson_id = uuid4()
    lp = LessonProgress(id=uuid4(), userId=user_id, lessonId=lesson_id)
    assert lp.completed is False
    assert lp.attempts == 0

    lp.start_attempt()
    assert lp.attempts == 1
    assert lp.lastAttemptAt is not None

    # First completion grants XP
    is_first, earned_xp = lp.complete(xp_reward=10)
    assert is_first is True
    assert earned_xp == 10
    assert lp.completed is True
    assert lp.completedAt is not None

    # Second completion grants 0 XP
    is_first_second, earned_xp_second = lp.complete(xp_reward=10)
    assert is_first_second is False
    assert earned_xp_second == 0


def test_lesson_progress_reset():
    user_id = uuid4()
    lesson_id = uuid4()
    lp = LessonProgress(id=uuid4(), userId=user_id, lessonId=lesson_id)
    lp.start_attempt()
    lp.complete(xp_reward=10)
    assert lp.completed is True
    assert lp.attempts == 1

    lp.reset()
    assert lp.completed is False
    assert lp.attempts == 0
    assert lp.completedAt is None


# --- APPLICATION SERVICE TESTS ---

@pytest.mark.asyncio
async def test_progress_application_service_flow(service, test_user_id):
    lesson1_id = uuid4()
    lesson2_id = uuid4()

    # 1. Initial progress summary
    summary = await service.getProgressSummary(test_user_id)
    assert summary.totalXp == 0
    assert summary.completedLessonsCount == 0

    # 2. Start lesson 1
    lp1 = await service.startLesson(
        StartLessonCommand(userId=test_user_id, lessonId=lesson1_id)
    )
    assert lp1.attempts == 1
    assert lp1.completed is False

    # 3. Complete lesson 1 (first time -> 10 XP)
    res1 = await service.completeLesson(
        CompleteLessonCommand(userId=test_user_id, lessonId=lesson1_id, xpReward=10)
    )
    assert res1.isFirstCompletion is True
    assert res1.earnedXp == 10
    assert res1.totalXp == 10

    # 4. Complete lesson 1 again (subsequent -> 0 XP)
    res1_repeat = await service.completeLesson(
        CompleteLessonCommand(userId=test_user_id, lessonId=lesson1_id, xpReward=10)
    )
    assert res1_repeat.isFirstCompletion is False
    assert res1_repeat.earnedXp == 0
    assert res1_repeat.totalXp == 10

    # 5. Complete lesson 2 (first time -> another 10 XP)
    res2 = await service.completeLesson(
        CompleteLessonCommand(userId=test_user_id, lessonId=lesson2_id, xpReward=10)
    )
    assert res2.isFirstCompletion is True
    assert res2.earnedXp == 10
    assert res2.totalXp == 20

    # 6. Check summary
    summary_after = await service.getProgressSummary(test_user_id)
    assert summary_after.totalXp == 20
    assert summary_after.completedLessonsCount == 2
    assert lesson1_id in summary_after.completedLessonIds
    assert lesson2_id in summary_after.completedLessonIds


# --- FASTAPI ENDPOINT TESTS ---

def test_progress_api_endpoints(client, test_user_id):
    lesson_id = uuid4()

    # 1. GET /api/v1/progress/summary
    res = client.get("/api/v1/progress/summary")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["totalXp"] == 0
    assert data["completedLessonsCount"] == 0

    # 2. POST /api/v1/progress/lessons/{id}/start
    res = client.post(f"/api/v1/progress/lessons/{lesson_id}/start")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["lessonId"] == str(lesson_id)
    assert data["attempts"] == 1
    assert data["completed"] is False

    # 3. POST /api/v1/progress/lessons/{id}/complete
    res = client.post(f"/api/v1/progress/lessons/{lesson_id}/complete")
    assert res.status_code == 200, res.text
    comp_data = res.json()
    assert comp_data["isFirstCompletion"] is True
    assert comp_data["earnedXp"] == 10
    assert comp_data["totalXp"] == 10

    # 4. Repeat POST /api/v1/progress/lessons/{id}/complete -> no extra XP
    res = client.post(f"/api/v1/progress/lessons/{lesson_id}/complete")
    assert res.status_code == 200, res.text
    comp_data_repeat = res.json()
    assert comp_data_repeat["isFirstCompletion"] is False
    assert comp_data_repeat["earnedXp"] == 0
    assert comp_data_repeat["totalXp"] == 10

    # 5. GET /api/v1/progress/lessons/{id}
    res = client.get(f"/api/v1/progress/lessons/{lesson_id}")
    assert res.status_code == 200, res.text
    lesson_progress = res.json()
    assert lesson_progress["completed"] is True

    # 6. GET /api/v1/progress (UserProgress)
    res = client.get("/api/v1/progress")
    assert res.status_code == 200, res.text
    user_prog = res.json()
    assert user_prog["xp"] == 10

    # 7. POST /api/v1/progress/lessons/{id}/reset
    res = client.post(f"/api/v1/progress/lessons/{lesson_id}/reset")
    assert res.status_code == 200, res.text
    reset_data = res.json()
    assert reset_data["completed"] is False
    assert reset_data["attempts"] == 0
