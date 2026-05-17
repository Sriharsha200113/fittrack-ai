import uuid
from datetime import datetime, date
from sqlalchemy import String, DateTime, Boolean, Integer, Float, Text, Date, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from backend.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False)

    meal_logs: Mapped[list["MealLog"]] = relationship(back_populates="user")
    exercise_logs: Mapped[list["ExerciseLog"]] = relationship(back_populates="user")
    squad_memberships: Mapped[list["SquadMember"]] = relationship(back_populates="user")
    daily_points: Mapped[list["DailyPoints"]] = relationship(back_populates="user")
    goals: Mapped["UserGoals | None"] = relationship(back_populates="user", uselist=False)
    body_metrics: Mapped[list["BodyMetrics"]] = relationship(back_populates="user")
    streak: Mapped["UserStreak | None"] = relationship(back_populates="user", uselist=False)
    badges: Mapped[list["UserBadge"]] = relationship(back_populates="user")
    device_tokens: Mapped[list["DeviceToken"]] = relationship(back_populates="user")


class Squad(Base):
    __tablename__ = "squads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    wa_group_id: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    members: Mapped[list["SquadMember"]] = relationship(back_populates="squad")
    daily_points: Mapped[list["DailyPoints"]] = relationship(back_populates="squad")


class SquadMember(Base):
    __tablename__ = "squad_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    role: Mapped[str] = mapped_column(String(20), default="member")

    squad: Mapped["Squad"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="squad_memberships")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    meal_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    food_items: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    log_date: Mapped[date] = mapped_column(Date, default=date.today)

    user: Mapped["User"] = relationship(back_populates="meal_logs")


class ExerciseLog(Base):
    __tablename__ = "exercise_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    workout_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sets_reps: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    calories_burned: Mapped[float | None] = mapped_column(Float, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    log_date: Mapped[date] = mapped_column(Date, default=date.today)

    user: Mapped["User"] = relationship(back_populates="exercise_logs")


class DailyPoints(Base):
    __tablename__ = "daily_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    squad_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, default=date.today)
    points: Mapped[int] = mapped_column(Integer, default=0)
    meals_logged: Mapped[int] = mapped_column(Integer, default=0)
    workouts_logged: Mapped[int] = mapped_column(Integer, default=0)
    protein_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    calorie_target_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    weight_logged: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="daily_points")
    squad: Mapped["Squad"] = relationship(back_populates="daily_points")


class UserGoals(Base):
    __tablename__ = "user_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    daily_calories: Mapped[int] = mapped_column(Integer, default=2000)
    protein_g: Mapped[int] = mapped_column(Integer, default=150)
    carbs_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fat_g: Mapped[int | None] = mapped_column(Integer, nullable=True)

    goal_type: Mapped[str] = mapped_column(String(20), default="maintain")
    target_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_level: Mapped[str] = mapped_column(String(20), default="moderate")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="goals")


class BodyMetrics(Base):
    __tablename__ = "body_metrics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    muscle_mass_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    arms_cm: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    log_date: Mapped[date] = mapped_column(Date, default=date.today)

    user: Mapped["User"] = relationship(back_populates="body_metrics")


class UserStreak(Base):
    __tablename__ = "user_streaks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="streak")


class UserBadge(Base):
    __tablename__ = "user_badges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    badge_slug: Mapped[str] = mapped_column(String(50), nullable=False)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="badges")

    __table_args__ = (
        UniqueConstraint("user_id", "badge_slug", name="uq_user_badge"),
    )


class WeeklySnapshot(Base):
    __tablename__ = "weekly_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    rankings: Mapped[dict] = mapped_column(JSON, nullable=False)
    winner_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeviceToken(Base):
    __tablename__ = "device_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token: Mapped[str] = mapped_column(String(500), nullable=False)
    platform: Mapped[str] = mapped_column(String(20), default="ios")
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship(back_populates="device_tokens")


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
