import asyncio
from typing import List, AsyncGenerator
import strawberry
from strawberry import Schema

from models import Sucursal, Empleado
from database import get_db

@strawberry.type
class SucursalType:
    id: int
    nombre: str
    ubicacion: str

    @strawberry.field
    def empleados(self) -> List["EmpleadoType"]:
        db = get_db()
        empleados = db.query(Empleado).filter(Empleado.sucursal_id == self.id).all()
        return [
            EmpleadoType(
                id=empleado.id,
                nombre=empleado.nombre,
                edad=empleado.edad,
                sucursal_id=empleado.sucursal_id
            )
            for empleado in empleados
        ]

@strawberry.type
class EmpleadoType:
    id: int
    nombre: str
    edad: int
    sucursal_id: int

    @strawberry.field
    def sucursal(self) -> "SucursalType":
        db = get_db()
        sucursal = db.query(Sucursal).filter(Sucursal.id == self.sucursal_id).first()
        return SucursalType(
            id=sucursal.id,
            nombre=sucursal.nombre,
            ubicacion=sucursal.ubicacion
        ) if sucursal else None

@strawberry.type
class Query:
    @strawberry.field
    async def sucursales(self) -> List[SucursalType]:
            db=get_db()
            sucursales = db.query(Sucursal).all()
            return [SucursalType(id=sucursal.id, nombre=sucursal.nombre, ubicacion=sucursal.ubicacion) for sucursal in sucursales]

    @strawberry.field
    async def empleados(self) -> List[EmpleadoType]:
            db=get_db()
            empleados = db.query(Empleado).all()
            return [EmpleadoType(id=empleado.id, nombre=empleado.nombre, edad=empleado.edad, sucursal_id=empleado.sucursal_id) for empleado in empleados]
    
@strawberry.type
class Mutation:
    @strawberry.mutation
    async def crear_sucursal(self, nombre: str, ubicacion: str) -> SucursalType:
            db=get_db() 
            sucursal = Sucursal(nombre=nombre, ubicacion=ubicacion)
            db.add(sucursal)
            db.commit()
            db.refresh(sucursal)
            return SucursalType(id=sucursal.id, nombre=sucursal.nombre, ubicacion=sucursal.ubicacion)

    @strawberry.mutation
    async def crear_empleado(self, nombre: str, edad: int, sucursal_id: int) -> EmpleadoType:
            db=get_db()
            sucursal = db.query(Sucursal).filter(Sucursal.id == sucursal_id).first()
            if not sucursal:
                raise ValueError("Sucursal not found")
            empleado = Empleado(nombre=nombre, edad=edad, sucursal_id=sucursal_id)
            db.add(empleado)
            db.commit()
            db.refresh(empleado)
            return EmpleadoType(id=empleado.id, nombre=empleado.nombre, edad=empleado.edad, sucursal_id=empleado.sucursal_id)
    
@strawberry.type
class Subscription:
    @strawberry.subscription
    async def empleado_creado(self, sucursal_id: int) -> AsyncGenerator[EmpleadoType, None]:
        try:
            async for empleado in empleado_stream(sucursal_id):
                yield empleado
        except Exception as e:
            print(f"Error en la suscripción empleado_creado: {e}")
            return

async def empleado_stream(sucursal_id: int) -> AsyncGenerator[EmpleadoType, None]:
    while True:
        try:
            await asyncio.sleep(5)  # Simulate real-time updates
            db=get_db()
            empleado = db.query(Empleado).filter(Empleado.sucursal_id == sucursal_id).order_by(Empleado.id.desc()).first()
            if empleado:
                yield EmpleadoType(id=empleado.id, nombre=empleado.nombre, edad=empleado.edad, sucursal_id=empleado.sucursal_id)
        except Exception as e:
            print(f"Error en empleado_stream: {e}")
            break


schema = Schema(query=Query, mutation=Mutation, subscription=Subscription)