async def get_resource_state(sql_registry, drone_uuid: str):
    sql_query = """
    SELECT R.drone_uuid, RS.state
    FROM Resources R
    JOIN ResourceStates RS ON R.state_id = RS.state_id
    WHERE R.drone_uuid = :drone_uuid"""
    return await sql_registry.async_execute(sql_query, dict(drone_uuid=drone_uuid))
