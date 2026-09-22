from app.db.models import ActivityLog


class ActivityLogService:

    @staticmethod
    def log(
        db,
        project_id: int,
        user_id: int,
        event_type: str,
        message: str,
        agent_run_id: int | None = None,
    ):
        activity = ActivityLog(
            project_id=project_id,
            user_id=user_id,
            agent_run_id=agent_run_id,
            event_type=event_type,
            message=message,
        )

        db.add(activity)
        db.commit()
        db.refresh(activity)

        return activity