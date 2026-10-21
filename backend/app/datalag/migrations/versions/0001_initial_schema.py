"""Initial schema: incidents, segment_scores, reports, users.

Revision ID: 0001
Revises:
Create Date: 2026-08-26
"""
import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("risk_profile", sa.String(20), server_default="balanced"),
        sa.Column("emergency_contacts", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("location", geoalchemy2.Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=False),
        sa.Column("verified", sa.Boolean, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "segment_scores",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("segment_id", sa.String(64), nullable=False, index=True),
        sa.Column("geom", geoalchemy2.Geography(geometry_type="LINESTRING", srid=4326), nullable=False),
        sa.Column("safety_score", sa.Numeric(4, 2), nullable=False),
        sa.Column("time_bucket", sa.String(20), nullable=False),
        sa.Column("shap_summary", postgresql.JSONB),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("location", geoalchemy2.Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("confirmations", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("reports")
    op.drop_table("segment_scores")
    op.drop_table("incidents")
    op.drop_table("users")
