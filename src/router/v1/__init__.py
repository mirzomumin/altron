from fastapi import APIRouter

from src.router.v1.applications import router as application_router
from src.router.v1.customers import router as customer_router
from src.router.v1.norm_documents import router as norm_document_router
from src.router.v1.permissions import router as permission_router
from src.router.v1.roles import router as role_router
from src.router.v1.users import router as user_router

router_v1 = APIRouter(prefix="/v1")
router_v1.include_router(user_router)
router_v1.include_router(role_router)
router_v1.include_router(permission_router)
router_v1.include_router(customer_router)
router_v1.include_router(application_router)
router_v1.include_router(norm_document_router)
