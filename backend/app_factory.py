"""Small integration helper used by deployments that import the service routers."""
from .api_services import router as service_router

def register_service_routes(app):
    app.include_router(service_router)
    return app
