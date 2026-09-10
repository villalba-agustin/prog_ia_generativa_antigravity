from fastapi import APIRouter, Header, HTTPException, status
from app.schemas import AdminLoginRequest, AdminLoginResponse

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])

ADMIN_PASSWORD = "admin"
ADMIN_TOKEN = "admin-session-token-secret-2026"

def require_admin(x_admin_token: str = Header(None, alias="X-Admin-Token")):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Debes iniciar sesión como Administrador para realizar esta acción."
        )

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(req: AdminLoginRequest):
    if req.password == ADMIN_PASSWORD:
        return AdminLoginResponse(
            success=True,
            token=ADMIN_TOKEN,
            message="Autenticado con éxito como Administrador."
        )
    return AdminLoginResponse(
        success=False,
        token=None,
        message="Contraseña incorrecta. Intente de nuevo."
    )
