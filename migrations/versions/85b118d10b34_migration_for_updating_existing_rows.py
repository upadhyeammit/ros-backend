"""Update top_candidate and top_candidate_price for existing records of PerformanceProfile

Revision ID: 85b118d10b34
Revises: 5f72a9f8b2d2
Create Date: 2023-07-19 19:31:53.519338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '85b118d10b34'
down_revision = '5f72a9f8b2d2'
branch_labels = None
depends_on = None


def upgrade():
    try:
        print('Updating top_candidate and top_candidate_price for existing PerformanceProfile records!')
        op.execute(
            "update performance_profile set top_candidate = subquery.top_candidate, top_candidate_price = cast("
            "subquery.top_candidate_price as double precision) from (select rule_hit_details #> '{0,details,"
            "candidates,0,0}' as top_candidate, rule_hit_details #> '{0,details,candidates,0,"
            "1}' as top_candidate_price, system_id from performance_profile) as subquery where "
            "performance_profile.system_id = subquery.system_id")
    except sa.exc.SQLAlchemyError as err:
        print(f"Failed to update table with error {err}!")
    else:
        print('Successfully updated top_candidate and top_candidate_price for existing PerformanceProfile records!')