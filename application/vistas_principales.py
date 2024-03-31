import functools
from flask import Blueprint, request, render_template, redirect, url_for, flash, get_flashed_messages, session, g, current_app

bp = Blueprint('vistas_principales', __name__)

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
        
# Página principal
@bp.route('/home', methods=['GET'])
@login_required
def home():
    if request.method == 'GET':
        idUsuario = session.get('user_id')
        tipoUsuario = session.get('tipo_user')
        mysql = current_app.config['MYSQL']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE Id_Usuario = %s", (idUsuario,))
        encuestas = cursor.fetchall()
        cursor.close()
        if tipoUsuario != "encuestador":
            return render_template('index.html', encuestas=encuestas) 
        else:
            return render_template('error-encuestador.html') 
        
# Vista de información
@bp.route('/info_tipos_preguntas', methods=['GET'])
@login_required
def info_tipos_preguntas():
    tipoUsuario = session.get('tipo_user')
    if tipoUsuario != "encuestador":  
        return render_template('info-tipos-preguntas.html') 
    else:
        return render_template('error-encuestador.html') 
    
# Vista principal de edición
@bp.route('/edit', methods=['GET'])
@login_required
def edit_encuesta():
    # Se accede a esta vista desde el botón 'Editar' en 'index.html'
    # Recibir los datos enviados a través de la URL
    idEncuesta = request.args.get('idEncuesta')
    nombreEncuesta = request.args.get('nombreEncuesta')
    # Almacenamos en sesión los datos de la encuesta a editar
    session['idEncuesta'] = idEncuesta
    session['nombreEncuesta']= nombreEncuesta
    # Obtengo usuario en sesión 
    idUsuario = session.get('user_id')
    # Consulta JOIN tabla 'preguntas' con 'encuesta' para mostrar el nombre
    # de la encuesta seleccionada, y los nombres de las preguntas creadas para esa encuesta
    mysql = current_app.config['MYSQL']
    cursor = mysql.connection.cursor()
    cursor.execute(
                """
                SELECT preguntas.ID as Id_pregunta, Detalle as DetallePregunta, Id_Encuesta, Nombre as NombreEncuesta
                FROM preguntas
                JOIN encuesta 
                ON preguntas.Id_Encuesta = encuesta.ID
                WHERE preguntas.Id_Encuesta = %s AND encuesta.Id_Usuario = %s 
                """, (idEncuesta, idUsuario) )
    datosEncuesta = cursor.fetchall()
    cursor.close()
    # Se pasan el idEncuesta y el nombreEncuesta por separado para poder mostrar la vista 
    # aunque la variable 'datosEncuesta' este vacía porque no hay preguntas cargadas aún
    return render_template('editar-encuesta.html', encuesta = datosEncuesta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

# Página principal de un encuestador
@bp.route('/home_encuestador', methods=['GET'])
@login_required
def home_encuestador():
    idUsuarioEncuestador = session.get('user_id')
    mysql = current_app.config['MYSQL']
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT encuesta.ID as IdEncuesta, encuesta.Nombre as encuestaNombre 
        FROM encuesta
        JOIN encuestadores
        ON encuesta.ID = encuestadores.Id_Encuesta
        WHERE encuestadores.Id_Usuario = %s AND encuesta.Estado = 'activa'""", 
        (int(idUsuarioEncuestador),))
    encuestas = cursor.fetchall()
    cursor.close()
    return render_template('home-encuestador.html', encuestas=encuestas)