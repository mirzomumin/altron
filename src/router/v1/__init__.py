from fastapi import APIRouter

from src.router.v1.roles import router as role_router
from src.router.v1.users import router as user_router

router_v1 = APIRouter(prefix="/v1")
router_v1.include_router(user_router)
router_v1.include_router(role_router)
