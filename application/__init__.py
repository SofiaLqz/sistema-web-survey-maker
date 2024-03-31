from flask import Flask
import os

def create_app(test_config=None):
    # Creo y configuro la aplicación
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    if test_config is None:
        # Cargar la configuración de instance, si existe, cuando no se esté haciendo testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Cargar la configuración de test 
        app.config.from_mapping(test_config)
    # Asegurarse que la carpeta instance exista
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # Crear una instancia de MySQL y conectar la base de datos a la aplicación
    from .database import configure_database
    mysql = configure_database(app)
    app.config['MYSQL'] = mysql # Pasar la instancia de MySQL a la aplicación
    # Registrar blueprints
    from . import auth
    app.register_blueprint(auth.bp)

    from . import crud_encuesta
    app.register_blueprint(crud_encuesta.bp)

    from . import crud_preguntas_respuestas
    app.register_blueprint(crud_preguntas_respuestas.bp)

    from . import crud_encuestadores
    app.register_blueprint(crud_encuestadores.bp)

    from . import encuestado
    app.register_blueprint(encuestado.bp)

    from . import vistas_principales
    app.register_blueprint(vistas_principales.bp)

    return app

#if __name__ == '__main__':
    #create_app().run(debug=True)

# Configuro la aplicación usando el archivo de configuración
#app.config.from_pyfile('config.py')




