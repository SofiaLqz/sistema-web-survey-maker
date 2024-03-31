import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app

bp = Blueprint('encuestado', __name__)

@bp.before_request
def before_request():
    mysql = current_app.config['MYSQL']

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view 

@bp.before_request
def load_logged_in_user():
    idUsuario= session.get('user_id')
    if idUsuario is None:
        g.user = None
    else:
        mysql = current_app.config['MYSQL']
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuarios WHERE ID = %s', (idUsuario,)
        )
        g.user = cursor.fetchone()
        cursor.close()
        
# Cargar datos del encuestado
@bp.route('/add_encuestado', methods=['GET','POST'])
@login_required
def add_encuestado():
    # Recibir los datos enviados a través de la URL desde el enlace de la encuesta en 'home-encuestador.html'
    idEncuesta = request.args.get('idEncuesta')
    nombreEncuesta = request.args.get('nombreEncuesta')
    if request.method == 'POST':
        # Recuperar los datos del formulario
        idEncuesta = int(request.form['idEncuesta'])
        nombreEncuesta = request.form['nombreEncuesta']
        idUsuarioEncuestador = session.get('user_id')
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        dni = request.form['dni']
        numTramiteDNI = request.form['numTramiteDNI']
        # Consultar el ID del encuestador en sesión
        mysql = current_app.config['MYSQL'] 
        cursor = mysql.connection.cursor()
        cursor.execute("""
                SELECT * FROM encuestadores 
                WHERE Id_Usuario = %s AND Id_Encuesta = %s""", (idUsuarioEncuestador,idEncuesta))
        encuestador = cursor.fetchone()
        if encuestador != None:
            idEncuestador = encuestador[0]
            # Consultar en la base de datos si el dni ingresado ya existe en la base de datos
            cursor.execute("SELECT * FROM encuestados WHERE dni = %s",
                (dni,))
            encuestado_existente = cursor.fetchone()
            if encuestado_existente != None:
                flash("Ya se registraron respuestas para el DNI ingresado", "danger")
                redirect(url_for('encuestado.add_encuestado',idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
            else:
                # Consideramos el ingreso de datos según cuáles se obtenienen desde el formulario
                if edad == '':
                    cursor.execute("""INSERT INTO encuestados (Nombre, Apellido, DNI, NumTramiteDNI,Id_Encuestador,Id_Encuesta) 
                            VALUES (%s, %s, %s, %s, %s, %s)""",(nombre,apellido,dni,numTramiteDNI,idEncuestador,idEncuesta))
                    mysql.connection.commit()
                else:
                    cursor.execute("""INSERT INTO encuestados (Nombre, Apellido, Edad, DNI, NumTramiteDNI,Id_Encuestador,Id_Encuesta) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""",(nombre,apellido,edad,dni,numTramiteDNI,idEncuestador,idEncuesta)) 
                    mysql.connection.commit()
                cursor.execute("""
                            SELECT * FROM encuestados 
                            WHERE Id_Encuestador = %s AND Id_Encuesta = %s ORDER BY ID DESC""", (idEncuestador, idEncuesta))
                encuestadoIngresado = cursor.fetchone()
                idEncuestado = encuestadoIngresado[0]
                cursor.close()
                flash("Los datos se guardaron correctamente", "success")
                return redirect(url_for('crud_encuesta.formulario', idEncuestado=idEncuestado, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
        cursor.close()
    return render_template('datos-encuestado.html', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

