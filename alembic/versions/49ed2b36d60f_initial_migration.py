"""Initial migration

Revision ID: 49ed2b36d60f
Revises:
Create Date: 2024-09-19 17:53:29.583440

"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "49ed2b36d60f"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "criterion",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("evidence", sa.String(), nullable=False),
        sa.Column(
            "created_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "criterion_gate",
            postgresql.ENUM(
                "GATE_0",
                "GATE_1",
                "GATE_2",
                "GATE_3",
                "GATE_4",
                "IPA_GUIDANCE",
                "CUSTOM",
                name="criterion_gate_enum",
            ),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("results_summary", sa.String(), nullable=True),
        sa.Column(
            "created_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "user",
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "file",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("clean_name", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("published_date", sa.String(), nullable=True),
        sa.Column("s3_bucket", sa.String(), nullable=True),
        sa.Column("s3_key", sa.String(), nullable=True),
        sa.Column("storage_kind", sa.String(), nullable=True),
        sa.Column(
            "created_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "project_criterions",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("criterion_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["criterion_id"],
            ["criterion.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.PrimaryKeyConstraint("project_id", "criterion_id"),
    )
    op.create_table(
        "project_users",
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )
    op.create_table(
        "result",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("answer", sa.String(), nullable=False),
        sa.Column("full_text", sa.String(), nullable=False),
        sa.Column(
            "created_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("criterion_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["criterion_id"],
            ["criterion.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chunk",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("idx", sa.Integer(), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("page_num", sa.Integer(), nullable=False),
        sa.Column(
            "created_datetime",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("updated_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("file_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["file_id"],
            ["file.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "result_chunks",
        sa.Column("chunk_id", sa.UUID(), nullable=False),
        sa.Column("result_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["chunk.id"],
        ),
        sa.ForeignKeyConstraint(
            ["result_id"],
            ["result.id"],
        ),
        sa.PrimaryKeyConstraint("chunk_id", "result_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("result_chunks")
    op.drop_table("chunk")
    op.drop_table("result")
    op.drop_table("project_users")
    op.drop_table("project_criterions")
    op.drop_table("file")
    op.drop_table("user")
    op.drop_table("project")
    op.drop_table("criterion")
    # ### end Alembic commands ###
