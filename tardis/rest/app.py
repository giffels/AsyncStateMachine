from . import crud
from ..plugins.sqliteregistry import SqliteRegistry
from fastapi import Depends, FastAPI, HTTPException, Query

app = FastAPI()


def get_sql_registry():
    sql_registry = SqliteRegistry()
    return lambda: sql_registry


@app.get("/state/{drone_uuid}")
async def get_state(
    drone_uuid: str = Query(..., regex=r"^\S+-[A-Fa-f0-9]{10}$"),
    sql_registry: SqliteRegistry = Depends(get_sql_registry()),
):
    query_result = await crud.get_resource_state(sql_registry, drone_uuid)
    try:
        query_result = query_result[0]
    except IndexError:
        raise HTTPException(status_code=404, detail="Drone not found")
    return query_result
