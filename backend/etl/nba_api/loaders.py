from sqlalchemy import MetaData, Table
from sqlalchemy.dialects.postgresql import insert

from db.session import engine


def upsert_dataframe(df, table_name: str, conflict_columns: list[str]) -> int:
    if df.empty:
        return 0

    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=engine)

    records = df.to_dict(orient="records")

    stmt = insert(table).values(records)

    update_columns = {
        column.name: getattr(stmt.excluded, column.name)
        for column in table.columns
        if column.name not in conflict_columns
        and column.name != "id"
        and column.name != "created_at"
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_=update_columns,
    )

    with engine.begin() as connection:
        result = connection.execute(stmt)

    return result.rowcount


def load_teams(teams_df) -> int:
    return upsert_dataframe(
        df=teams_df,
        table_name="teams",
        conflict_columns=["nba_team_id"],
    )


def load_games(games_df) -> int:
    return upsert_dataframe(
        df=games_df,
        table_name="games",
        conflict_columns=["nba_game_id"],
    )