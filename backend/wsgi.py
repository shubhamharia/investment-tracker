from app import create_app
from app.config import Config

app = create_app()

# Create the database if it doesn't exist
with app.app_context():
    Config.create_database(app)

if __name__ == "__main__":
    app.run()