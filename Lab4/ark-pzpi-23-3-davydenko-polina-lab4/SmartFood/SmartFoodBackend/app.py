from flasgger import Swagger
from config import app
from routes.routes import init_routes
from routes.admin_routes import admin_bp

from flask_jwt_extended import JWTManager

swagger = Swagger(app, template_file="swagger.yaml")

jwt = JWTManager(app)

init_routes(app)
app.register_blueprint(admin_bp, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True)
