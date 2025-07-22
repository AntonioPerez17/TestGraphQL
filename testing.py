import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Sucursal, Empleado
from main import app


DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture
async def async_session() -> AsyncSession:
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.execute("DELETE FROM empleados")
            await session.execute("DELETE FROM sucursales")

@pytest.fixture
async def async_client(async_session: AsyncSession):
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_graphql_queries(async_session: AsyncSession, async_client: AsyncClient):
    async with async_session() as session:
        async with session.begin():
            # Create some test data
            sucursal = Sucursal(nombre="Test Sucursal", ubicacion="Test ubuicacion")
            session.add(sucursal)
            await session.commit()

    # Test query
    query = """
    query {
      sucursales {
        id
        nombre
        ubicacion
      }
    }
    """
    response = await async_client.post("/graphql", json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "sucursales" in data["data"]
    assert len(data["data"]["sucursales"]) == 1

@pytest.mark.asyncio
async def test_graphql_mutations(async_session: AsyncSession, async_client: AsyncClient):
    # Test mutation
    mutation = """
    mutation {
      crear_sucursal(nombre: "New Sucursal", ubicacion: "New Ubicacion") {
        id
        nombre
        ubicacion
      }
    }
    """
    response = await async_client.post("/graphql", json={"query": mutation})
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "crear_sucursal" in data["data"]
    assert data["data"]["crear_sucursal"]["nombre"] == "New Sucursal"
    assert data["data"]["crear_sucursal"]["ubicacion"] == "New Ubicacion"

@pytest.mark.asyncio
async def test_graphql_subscription(async_session: AsyncSession, async_client: AsyncClient):
    # Test subscription
    subscription = """
    subscription {
      empleadoCreado(sucursalId: 1) {
        id
        nombre
        edad
        sucursalId
      }
    }
    """
    async with async_client.websocket_connect("/graphql") as ws:
        await ws.send_json({"type": "connection_init"})
        await ws.send_json({"id": "1", "type": "start", "payload": {"query": subscription}})
        response = await ws.receive_json()
        assert response["type"] == "data"
        assert "empleadoCreado" in response["payload"]["data"]
        assert response["payload"]["data"]["empleadoCreado"]["id"] is not None