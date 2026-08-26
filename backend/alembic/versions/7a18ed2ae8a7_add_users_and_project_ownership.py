"""add users and project ownership

Revision ID: 7a18ed2ae8a7
Revises:
Create Date: 2026-08-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a18ed2ae8a7"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ---------------------------------------
    # 1. Create users table
    # ---------------------------------------

    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "hashed_password",
            sa.String(length=255),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ---------------------------------------
    # 2. Create indexes
    # ---------------------------------------

    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # ---------------------------------------
    # 3. Create a temporary migration user
    # ---------------------------------------

    op.execute(
        """
        INSERT INTO users (email, hashed_password)
        VALUES (
            'migration@syntra.local',
            'MIGRATION_USER'
        )
        """
    )

    # ---------------------------------------
    # 4. Add owner_id temporarily nullable
    # ---------------------------------------

    op.add_column(
        "projects",
        sa.Column(
            "owner_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # ---------------------------------------
    # 5. Assign existing projects
    #    to migration user
    # ---------------------------------------

    op.execute(
        """
        UPDATE projects
        SET owner_id = (
            SELECT id
            FROM users
            WHERE email = 'migration@syntra.local'
        )
        WHERE owner_id IS NULL
        """
    )

    # ---------------------------------------
    # 6. Make owner_id NOT NULL
    # ---------------------------------------

    op.alter_column(
        "projects",
        "owner_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # ---------------------------------------
    # 7. Add foreign key
    # ---------------------------------------

    op.create_foreign_key(
        "fk_projects_owner_id_users",
        "projects",
        "users",
        ["owner_id"],
        ["id"],
    )


def downgrade() -> None:

    # Remove foreign key
    op.drop_constraint(
        "fk_projects_owner_id_users",
        "projects",
        type_="foreignkey",
    )

    # Remove owner_id
    op.drop_column(
        "projects",
        "owner_id",
    )

    # Remove user indexes
    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.drop_index(
        "ix_users_id",
        table_name="users",
    )

    # Remove users table
    op.drop_table("users")