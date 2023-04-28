from app import create_app
from instance.config import PORT

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False, port=PORT)
