from flasgger import Swagger
from config import app
from routes.routes import init_routes

swagger = Swagger(app, template_file="swagger.yaml")

init_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
