from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from main import app
from modules.learning.domain.entities import Course, Exercise, Lesson, Media, Unit
from modules.learning.domain.exceptions import (
    CourseNotFoundError,
    ExerciseNotFoundError,
    LessonNotFoundError,
    UnitNotFoundError,
)
from modules.learning.domain.repositories import (
    CourseRepository,
    ExerciseRepository,
    LessonRepository,
    UnitRepository,
)
from modules.learning.domain.value_objects import (
    ContentStatus,
    Difficulty,
    ExerciseType,
    MediaType,
    SignLanguage,
)
from modules.learning.application.commands import (
    CreateCourseCommand,
    CreateExerciseCommand,
    CreateLessonCommand,
    CreateMediaCommand,
    CreateUnitCommand,
    ValidateAnswerCommand,
)
from modules.learning.application.services import (
    CourseApplicationServiceImpl,
    ExerciseApplicationServiceImpl,
    LessonApplicationServiceImpl,
    UnitApplicationServiceImpl,
)
from modules.learning.presentation.dependencies import (
    get_course_service,
    get_exercise_service,
    get_lesson_service,
    get_unit_service,
)


# --- IN-MEMORY REPOSITORIES FOR TESTING ---

class InMemoryCourseRepository(CourseRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Course] = {}

    async def get_by_id(self, course_id: UUID) -> Course | None:
        return self.items.get(course_id)

    async def list_all(
        self,
        language: SignLanguage | None = None,
        difficulty: Difficulty | None = None,
        status: ContentStatus | None = None,
    ) -> list[Course]:
        res = list(self.items.values())
        if language:
            res = [c for c in res if c.language == language]
        if difficulty:
            res = [c for c in res if c.difficulty == difficulty]
        if status:
            res = [c for c in res if c.status == status]
        return res

    async def save(self, course: Course) -> None:
        self.items[course.id] = course

    async def delete(self, course_id: UUID) -> None:
        self.items.pop(course_id, None)


class InMemoryUnitRepository(UnitRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Unit] = {}

    async def get_by_id(self, unit_id: UUID) -> Unit | None:
        return self.items.get(unit_id)

    async def list_by_course(self, course_id: UUID) -> list[Unit]:
        units = [u for u in self.items.values() if u.courseId == course_id]
        return sorted(units, key=lambda u: u.order)

    async def save(self, unit: Unit) -> None:
        self.items[unit.id] = unit

    async def delete(self, unit_id: UUID) -> None:
        self.items.pop(unit_id, None)


class InMemoryLessonRepository(LessonRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Lesson] = {}

    async def get_by_id(self, lesson_id: UUID) -> Lesson | None:
        return self.items.get(lesson_id)

    async def list_by_unit(self, unit_id: UUID) -> list[Lesson]:
        lessons = [l for l in self.items.values() if l.unitId == unit_id]
        return sorted(lessons, key=lambda l: l.order)

    async def save(self, lesson: Lesson) -> None:
        self.items[lesson.id] = lesson

    async def delete(self, lesson_id: UUID) -> None:
        self.items.pop(lesson_id, None)


class InMemoryExerciseRepository(ExerciseRepository):
    def __init__(self) -> None:
        self.items: dict[UUID, Exercise] = {}

    async def get_by_id(self, exercise_id: UUID) -> Exercise | None:
        return self.items.get(exercise_id)

    async def list_by_lesson(self, lesson_id: UUID) -> list[Exercise]:
        exercises = [e for e in self.items.values() if e.lessonId == lesson_id]
        return exercises

    async def save(self, exercise: Exercise) -> None:
        self.items[exercise.id] = exercise

    async def delete(self, exercise_id: UUID) -> None:
        self.items.pop(exercise_id, None)


# --- FIXTURES ---

@pytest.fixture
def repos():
    return {
        "course": InMemoryCourseRepository(),
        "unit": InMemoryUnitRepository(),
        "lesson": InMemoryLessonRepository(),
        "exercise": InMemoryExerciseRepository(),
    }


@pytest.fixture
def services(repos):
    course_svc = CourseApplicationServiceImpl(
        course_repository=repos["course"],
        unit_repository=repos["unit"],
        lesson_repository=repos["lesson"],
    )
    unit_svc = UnitApplicationServiceImpl(
        unit_repository=repos["unit"],
        course_repository=repos["course"],
    )
    lesson_svc = LessonApplicationServiceImpl(
        lesson_repository=repos["lesson"],
        unit_repository=repos["unit"],
        exercise_repository=repos["exercise"],
    )
    exercise_svc = ExerciseApplicationServiceImpl(
        exercise_repository=repos["exercise"],
        lesson_repository=repos["lesson"],
    )
    return {
        "course": course_svc,
        "unit": unit_svc,
        "lesson": lesson_svc,
        "exercise": exercise_svc,
    }


@pytest.fixture
def client(services):
    app.dependency_overrides[get_course_service] = lambda: services["course"]
    app.dependency_overrides[get_unit_service] = lambda: services["unit"]
    app.dependency_overrides[get_lesson_service] = lambda: services["lesson"]
    app.dependency_overrides[get_exercise_service] = lambda: services["exercise"]

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# --- DOMAIN TESTS ---

def test_exercise_validation_domain():
    exercise = Exercise(
        id=uuid4(),
        lessonId=uuid4(),
        type=ExerciseType.SINGLE,
        difficulty=Difficulty.BEGINNER,
        points=10,
        content="Show the sign for 'Hello'",
        answer="HELLO",
    )

    # Exact match case-insensitive with whitespace normalization
    is_correct, points = exercise.validate_answer("hello")
    assert is_correct is True
    assert points == 10

    is_correct, points = exercise.validate_answer("  hello  ")
    assert is_correct is True
    assert points == 10

    is_correct, points = exercise.validate_answer("goodbye")
    assert is_correct is False
    assert points == 0

    sentence_exercise = Exercise(
        id=uuid4(),
        lessonId=uuid4(),
        type=ExerciseType.SENTENCE,
        difficulty=Difficulty.INTERMEDIATE,
        points=20,
        content="Sign the sentence: 'Good morning friend'",
        answer="good morning friend",
    )
    is_correct, points = sentence_exercise.validate_answer("Good Morning Friend")
    assert is_correct is True
    assert points == 20

    is_correct, points = sentence_exercise.validate_answer("good night friend")
    assert is_correct is False
    assert points == 0


def test_course_status_transitions():
    course = Course(
        id=uuid4(),
        title="PJM Podstawy",
        description="Kurs podstawowy PJM",
        difficulty=Difficulty.BEGINNER,
        language=SignLanguage.PJM,
        status=ContentStatus.DRAFT,
    )
    assert course.status == ContentStatus.DRAFT

    course.publish()
    assert course.status == ContentStatus.PUBLISHED

    course.archive()
    assert course.status == ContentStatus.ARCHIVED


# --- APPLICATION SERVICE TESTS ---

@pytest.mark.asyncio
async def test_full_learning_flow_services(services):
    # 1. Create course
    course_dto = await services["course"].createCourse(
        CreateCourseCommand(
            title="ASL Beginners",
            description="Learn ASL basic signs",
            difficulty="beginner",
            language="asl",
        )
    )
    assert course_dto.title == "ASL Beginners"
    assert course_dto.language == "asl"
    assert course_dto.status == "draft"

    # 2. Create unit
    unit_dto = await services["unit"].createUnit(
        CreateUnitCommand(
            courseId=course_dto.id,
            title="Unit 1: Alphabet & Greetings",
            order=1,
        )
    )
    assert unit_dto.courseId == course_dto.id
    assert unit_dto.order == 1

    # 3. Create lesson
    lesson_dto = await services["lesson"].createLesson(
        CreateLessonCommand(
            unitId=unit_dto.id,
            title="Lesson 1: Hello & Goodbye",
            description="First signs",
            order=1,
        )
    )
    assert lesson_dto.unitId == unit_dto.id

    # 4. Create exercise
    exercise_dto = await services["exercise"].createExercise(
        CreateExerciseCommand(
            lessonId=lesson_dto.id,
            type="single",
            difficulty="beginner",
            points=10,
            content="Perform sign: Hello",
            answer="hello",
            mediaList=[
                CreateMediaCommand(
                    type="video",
                    url="https://s3.example.com/videos/hello.mp4",
                )
            ],
        )
    )
    assert exercise_dto.content == "Perform sign: Hello"
    assert exercise_dto.answer == "hello"
    assert len(exercise_dto.media) == 1
    assert exercise_dto.media[0].url == "https://s3.example.com/videos/hello.mp4"

    # 5. Public exercise query (answer MUST NOT be present)
    pub_dto = await services["exercise"].getExercisePublic(exercise_dto.id)
    assert pub_dto is not None
    assert pub_dto.id == exercise_dto.id
    assert pub_dto.content == "Perform sign: Hello"
    assert not hasattr(pub_dto, "answer")

    # 6. Validate answer
    val_correct = await services["exercise"].validateAnswer(
        ValidateAnswerCommand(exerciseId=exercise_dto.id, submittedAnswer="HELLO")
    )
    assert val_correct.isCorrect is True
    assert "Well done" in val_correct.feedback
    assert val_correct.earnedPoints == 10

    val_wrong = await services["exercise"].validateAnswer(
        ValidateAnswerCommand(exerciseId=exercise_dto.id, submittedAnswer="goodbye")
    )
    assert val_wrong.isCorrect is False
    assert val_wrong.earnedPoints == 0
    assert "did not match" in val_wrong.feedback


# --- FASTAPI ENDPOINT TESTS ---

def test_api_course_and_exercise_endpoints(client):
    # 1. Create course
    res = client.post(
        "/api/v1/courses",
        json={
            "title": "PJM dla początkujących",
            "description": "Kurs polskiego języka migowego",
            "difficulty": "beginner",
            "language": "pjm",
        },
    )
    assert res.status_code == 201, res.text
    course_data = res.json()
    course_id = course_data["id"]
    assert course_data["language"] == "pjm"

    # 2. Create unit
    res = client.post(
        f"/api/v1/units/for-course/{course_id}",
        json={
            "title": "Moduł 1",
            "order": 1,
        },
    )
    assert res.status_code == 201, res.text
    unit_data = res.json()
    unit_id = unit_data["id"]

    # 3. Create lesson
    res = client.post(
        f"/api/v1/lessons/for-unit/{unit_id}",
        json={
            "title": "Lekcja 1: Powitanie",
            "description": "Nauka gestu cześć",
            "order": 1,
        },
    )
    assert res.status_code == 201, res.text
    lesson_data = res.json()
    lesson_id = lesson_data["id"]

    # 4. Create exercise
    res = client.post(
        f"/api/v1/exercises/for-lesson/{lesson_id}",
        json={
            "type": "single",
            "difficulty": "beginner",
            "points": 10,
            "content": "Pokaż znak: Cześć",
            "answer": "cześć",
            "media": [
                {
                    "type": "video",
                    "url": "https://storage.slep.local/videos/czesc.mp4",
                }
            ],
        },
    )
    assert res.status_code == 201, res.text
    ex_data = res.json()
    ex_id = ex_data["id"]
    # Admin creation returns answer
    assert ex_data["answer"] == "cześć"

    # 5. Public GET endpoint MUST NOT expose answer
    res = client.get(f"/api/v1/exercises/{ex_id}")
    assert res.status_code == 200, res.text
    pub_data = res.json()
    assert "answer" not in pub_data
    assert pub_data["content"] == "Pokaż znak: Cześć"

    # 6. Admin GET full endpoint DOES expose answer
    res = client.get(f"/api/v1/exercises/{ex_id}/full")
    assert res.status_code == 200, res.text
    admin_data = res.json()
    assert admin_data["answer"] == "cześć"

    # 7. Validate exercise instant feedback
    res = client.post(
        f"/api/v1/exercises/{ex_id}/validate",
        json={"submittedAnswer": "cześć"},
    )
    assert res.status_code == 200, res.text
    val_data = res.json()
    assert val_data["isCorrect"] is True
    assert val_data["expectedAnswer"] == "cześć"
    assert val_data["earnedPoints"] == 10

    # Wrong answer
    res = client.post(
        f"/api/v1/exercises/{ex_id}/validate",
        json={"submittedAnswer": "do widzenia"},
    )
    assert res.status_code == 200, res.text
    val_data = res.json()
    assert val_data["isCorrect"] is False
    assert val_data["earnedPoints"] == 0
