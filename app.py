import functools
from flask import Flask, request, render_template, redirect, url_for, flash, get_flashed_messages, session, g
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mysqldb import MySQL
import datetime
from functions.preguntas import tipoPregunta

# Inicializo la aplicación
app = Flask(__name__)

# Conecto la aplicación a una base de datos
mysql = MySQL(app)

# Configuro la aplicación usando el archivo de configuración
app.config.from_pyfile('config.py')

# Decorador personalizado para manejar errores globales
#@app.errorhandler(Exception)
#def handle_error(error):
    #return render_template("error.html", error=error), 500
 
# Página inicial
@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('login')) 

# Iniciar sesión
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Recopilar datos del formulario enviado
        email = request.form['email']
        contrasenia = request.form['contrasenia']
        # Consultar si existe el email ingresado en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuarios WHERE Email = %s', (email,)
        )
        user = cursor.fetchone()
        # Si el usuario existe verificar la contraseña ingresada
        error = None  
        if user is None or not check_password_hash(user[4], contrasenia):
            error = 'Contraseña y/o email incorrectos'
        # Si la contraseña es correcta, redirigir a la página principal
        elif email == '@encuestador':
            error = 'No tienes acceso a esta vista'
        elif error is None:
            session.clear()
            session['user_id'] = user[0]
            session['tipo_user'] = "admin"
            return redirect(url_for('home'))
        flash(error)
    # Acceder al valor enviado como parámetro desde '/register'
    registro_exitoso = request.args.get('registro_exitoso')
    return render_template('auth/login.html', registro_exitoso=registro_exitoso)
    
# Registro
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # Recopilar datos del formulario enviado
        nombreCompleto = request.form['nombreCompleto']
        nombreUsuario = request.form['nombreUsuario']
        email = request.form['email']
        contrasenia = request.form['contrasenia']
        confirmarContrasenia = request.form['confirmarContrasenia']
        # Consultar en la base de datos si el email ingresado ya existe en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s",
            (email,))
        usuario_existente = cursor.fetchone()
        error_message_email = None
        error_message_contrasenia = None  
        # Se establece un mensaje de error si se encuentra un usuario con el mismo email
        if usuario_existente != None:
            error_message_email = 'El correo ya está asociado a una cuenta. Intente con otro correo o inicie sesión.'
        # Se verifica si las contraseñas ingresadas coinciden y se establece un mensaje de error 
        elif contrasenia != confirmarContrasenia:
            error_message_contrasenia = 'Las contraseñas no coinciden'
        # Si no hay mensajes de error
        elif error_message_email is None and error_message_contrasenia is None:
            # Guardar los datos en la base de datos
            cursor.execute("INSERT INTO usuarios (NombreCompleto, NombreUsuario, Email, Contrasenia) VALUES (%s, %s, %s, %s)", 
                (nombreCompleto, nombreUsuario, email, generate_password_hash(contrasenia)))
            mysql.connection.commit()
            cursor.close()
            # Si no se encontraron errores de validación se redirige al usuario a la página de inicio de sesión
            return redirect('login?registro_exitoso=true')
        # Si se encontraron errores de validación, se muestra el formulario de registro nuevamente junto con los mensajes de error
        return render_template('auth/register.html', error_message_email=error_message_email,error_message_contrasenia=error_message_contrasenia)
    # En caso de que la solicitud HTTP sea GET
    return render_template('auth/register.html')

# Iniciar sesión del encuestador
@app.route('/login_encuestador', methods=['GET','POST'])
def login_encuestador():
    if request.method == 'POST':
        # Recopilar datos del formulario enviado
        usuario = request.form['usuario']
        contrasenia = request.form['contrasenia']
        # Consultar si existe el usuario ingresado en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuarios WHERE NombreUsuario = %s', (usuario,)
        )
        user = cursor.fetchone()
        # Si el usuario existe verificar la contraseña ingresada
        error = None
        if user is None or not check_password_hash(user[4], contrasenia):
            error = 'Contraseña y/o usuario incorrectos'
        # Si la contraseña es correcta, redirigir a la página principal
        if error is None:
            session.clear()
            session['user_id'] = user[0]
            session['tipo_user'] = "encuestador"
            return redirect(url_for('home_encuestador'))
        flash(error)
    return render_template('auth/login-encuestador.html')

@app.before_request
def load_logged_in_user():
    idUsuario= session.get('user_id')
    if idUsuario is None:
        g.user = None
    else:
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuarios WHERE ID = %s', (idUsuario,)
        )
        g.user = cursor.fetchone()
        cursor.close()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# Cerrar sesión
@app.route('/logout', methods=['GET'])
def logout():
    # Elimina la información de la sesión
    session.clear()
    return redirect(url_for('login'))

# Página principal
@app.route('/home', methods=['GET'])
@login_required
def home():
    if request.method == 'GET':
        idUsuario = session.get('user_id')
        tipoUsuario = session.get('tipo_user')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE Id_Usuario = %s", (idUsuario,))
        encuestas = cursor.fetchall()
        cursor.close()
        if tipoUsuario != "encuestador":
            return render_template('index.html', encuestas=encuestas) 
        else:
            return render_template('error-encuestador.html') 
        
# Vista del formulario para cargar los datos de la encuesta
@app.route('/crear_encuesta', methods=['GET'])
@login_required
def crear_encuesta():
    tipoUsuario = session.get('tipo_user')
    if tipoUsuario != "encuestador":  
        return render_template('datos-encuesta.html') 
    else:
        return render_template('error-encuestador.html') 

# Vista de información
@app.route('/info_tipos_preguntas', methods=['GET'])
@login_required
def info_tipos_preguntas():
    tipoUsuario = session.get('tipo_user')
    if tipoUsuario != "encuestador":  
        return render_template('info-tipos-preguntas.html') 
    else:
        return render_template('error-encuestador.html') 
    
# Guardar los datos de la encuesta
@app.route('/add_datos_encuesta', methods=['POST'])
@login_required
def add_datos_encuesta():
    if request.method == 'POST':
        # Recuperar los datos del formulario
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        objetivo = request.form['objetivo']
        cantPreguntas = request.form['cantPreguntas']
        IdUsuario = session.get('user_id')
        # Obtener la fecha actual
        fecha_actual = datetime.date.today()
        # Insertar los datos de la encuesta en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO encuesta (Nombre, Descripcion, Objetivo, CantidadPreguntas, Fecha, Id_Usuario) 
            VALUES (%s, %s, %s, %s, %s,%s)""",
            (nombre, descripcion, objetivo, cantPreguntas, fecha_actual,IdUsuario))
        mysql.connection.commit()
        cursor.execute("SELECT * FROM encuesta WHERE Id_Usuario = %s ORDER BY ID DESC", (IdUsuario,))
        ultimaEncuesta  = cursor.fetchone() # Obtiene el primer registro
        cursor.close()
        # Almacenar datos en la sesión del usuario
        session['idEncuesta'] = ultimaEncuesta[0]
        session['nombreEncuesta'] = ultimaEncuesta[1]
        # Mensaje flash
        flash('Los datos de su encuesta se guardaron correctamente. Puedes cargar las preguntas ahora o <a href="/home" class="alert-link"> después </a>', 'success')
        return redirect(url_for('add_preguntas', nomnreEncuesta=session.get('nombreEncuesta')))
    # En caso que la solicitud HTTP sea GET
    return render_template('datos-encuesta.html')

# Guardar los datos de las preguntas
@app.route('/add_preguntas', methods=['GET','POST'])
@login_required
def add_preguntas():
    # Obtengo los mensajes flash y los paso como argumento a la plantilla
    messages = get_flashed_messages()
    # Recuperar datos almacenados en sesión
    idEncuesta = session.get('idEncuesta')
    nombreEncuesta = session.get('nombreEncuesta')
    if request.method == 'POST':
        # Recuperar datos almacenados en sesión
        idEncuesta = session.get('idEncuesta')
        nombreEncuesta = session.get('nombreEncuesta')
        # Recuperar los datos del formulario
        tipo = request.form['listaDesplegable']
        pregunta = request.form['pregunta']
        cantidadOpciones = int(request.form['cantOpciones'])
        # Recuperar el ID del tipo de pregunta elegida
        idTipoPregunta = tipoPregunta(tipo)
        # Insertar los datos de la pregunta ingresada en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO preguntas (Detalle, CantidadOpciones, Id_Encuesta, Id_Tipo_Pregunta) VALUES (%s, %s, %s, %s)",
            (pregunta, cantidadOpciones, idEncuesta, idTipoPregunta))
        mysql.connection.commit()
        # Si la pregunta no es de tipo 'abierta' se redirige a la vista para cargar las opciones de respuesta
        if idTipoPregunta != 1:
            return redirect(url_for('add_respuestas', nombreEncuesta=nombreEncuesta, pregunta=pregunta, cantOpciones=cantidadOpciones))
        else:
            # Si la pregunta es de tipo 'abierta', se carga la opción de respuesta como 'respuesta abierta'
            cursor.execute("SELECT * FROM preguntas ORDER BY ID DESC")
            idPregunta = cursor.fetchone()[0]
            cursor.execute("INSERT INTO respuestas (Detalle, Valor, Id_Pregunta) VALUES (%s, %s, %s)",("-", 0, idPregunta))
            mysql.connection.commit()
            cursor.close()
            # Mensaje flash
            flash('Los datos de su pregunta se guardaron correctamente. Puedes cargar la siguiente ahora o <a href="{}" class="alert-link"> después </a>'.format(url_for('edit_encuesta', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)))
            return redirect(url_for('add_preguntas',nombreEncuesta=nombreEncuesta))
    # En caso que la solicitud HTTP sea GET
    tipoUsuario = session.get('tipo_user')
    if tipoUsuario != "encuestador":  
        return render_template('crear-formulario.html', nombreEncuesta=nombreEncuesta, messages=messages)
    else:
        return render_template('error-encuestador.html') 

# Guardar los datos de las opciones de respuestas
@app.route('/add_respuestas/<int:cantOpciones>', methods=['GET','POST'])
@login_required
def add_respuestas(cantOpciones):
    # Recuperar datos almacenados en sesión
    nombreEncuesta = session.get('nombreEncuesta')
    if request.method == 'POST':
        # Recuperar datos almacenados en sesión
        idEncuesta = session.get('idEncuesta')
        nombreEncuesta = session.get('nombreEncuesta')
        # Consultar en la base de datos el ID de la última pregunta creada para la encuesta
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM preguntas WHERE Id_Encuesta = %s ORDER BY ID DESC", (idEncuesta,))
        idPregunta = cursor.fetchone()
        # Verificar el usuario activo
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s", (idEncuesta,))
        encuesta = cursor.fetchone()
        idUsuario = encuesta[6]
        if session.get('user_id') == idUsuario:
            # Insertar las opciones en la tabla 'respuestas'
            for i in range(1, cantOpciones+1):
                detalleOpcion = request.form["opcion" + str(i)]
                cursor.execute("INSERT INTO respuestas (Detalle, Valor, Id_Pregunta) VALUES (%s, %s, %s)",
                    (detalleOpcion, i, idPregunta[0])) 
                mysql.connection.commit()
            cursor.close()
        # Mensaje flash
            flash('Los datos de su pregunta se guardaron correctamente. Puedes cargar la siguiente ahora o <a href="{}" class="alert-link"> después </a>'.format(url_for('edit_encuesta', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)))
            return redirect(url_for('add_preguntas', nombreEncuesta=nombreEncuesta))
        else:
            return render_template('error.html')
    # En caso que la solicitud HTTP sea GET
    return render_template('crear-formulario-paso2.html', nombreEncuesta=nombreEncuesta, pregunta=request.args.get('pregunta'),cantOpciones=cantOpciones)

# Vista principal de edición
@app.route('/edit', methods=['GET'])
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
    
# Eliminar una encuesta
@app.route('/delete/<int:idEncuesta>', methods=['POST'])
@login_required
def delete_encuesta(idEncuesta):
    # Recibo idEncuesta de 'index.html'
    # Obtengo usuario en sesión 
    idUsuario = session.get('user_id')
    # Eliminar la encuesta seleccionada
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM encuesta WHERE ID = %s and Id_Usuario = %s', (idEncuesta, idUsuario) )
    mysql.connection.commit() 
    cursor.close()
    flash("Encuesta removida satisfactoriamente")
    return redirect(url_for('home'))

# Editar una encuesta
@app.route('/edit_datos', methods=['GET'])
@login_required
def edit_encuesta_datos():
    # Recibir los datos enviados a través de la URL desde el botón 'Editar datos' en 'editar-encuesta.html'
    idEncuesta = request.args.get('idEncuesta')
    # Obtengo usuario en sesión 
    idUsuario = session.get('user_id')
    # Consulta a la base de datos, devuelve los datos del idEncuesta recibido 
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    datosEncuesta = cursor.fetchone()
    return render_template('editar-encuesta-datos.html', datosEncuesta=datosEncuesta)

# Guardar los datos editados de una encuesta   
@app.route('/update_datos', methods=['POST'])
@login_required
def update_encuesta_datos():
    if request.method == 'POST':
        # Recuperar los datos del formulario 'editar-encuesta.html' 
        idEncuesta = request.form['idEncuesta']
        nombre = request.form['nombre']
        descripcion = request.form['descripcion']
        objetivo = request.form['objetivo']
        cantPreguntas = request.form['cantPreguntas']
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        # Actualizar los datos de la encuesta con el idEncuesta recibido
        cursor.execute("""
                UPDATE encuesta
                SET Nombre = %s,
                    Descripcion = %s,
                    Objetivo = %s,
                    CantidadPreguntas = %s
                WHERE ID = %s 
                AND Id_Usuario = %s 
        """, (nombre,descripcion,objetivo,cantPreguntas,idEncuesta,idUsuario))
        mysql.connection.commit() 
        flash("Datos de la encuesta actualizados satisfactoriamente")
        return redirect(url_for('edit_encuesta', idEncuesta=idEncuesta, nombreEncuesta=nombre))

# Editar preguntas
@app.route('/edit_preguntas', methods=['GET'])
@login_required
def edit_encuesta_preguntas():
    if request.method == 'GET':
        # Recibir los datos enviados a través de la URL desde el botón "Editar pregunta" en 'editar-encuesta.html' 
        idPregunta = request.args.get('idPregunta')
        idEncuesta = request.args.get('idEncuesta')
        nombreEncuesta = request.args.get('nombreEncuesta')
        # Verificar el usuario en sesión para dar acceso a la vista solicitad
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        if cursor.fetchone() != None:
            # Consulta JOIN tabla 'preguntas' con 'tipos_preguntas' para mostrar los datos
            # de la pregunta seleccionada
            cursor.execute(""" 
                        SELECT preguntas.Detalle as DetallePregunta, CantidadOpciones, 
                        Id_Encuesta, Id_Tipo_Pregunta, Tipo, respuestas.ID, respuestas.Detalle as DetalleRespuesta
                        FROM preguntas 
                        JOIN tipos_preguntas
                        ON preguntas.Id_Tipo_Pregunta = tipos_preguntas.ID
                        JOIN respuestas 
                        ON preguntas.ID = respuestas.Id_Pregunta
                        WHERE preguntas.ID = %s
                        """, (idPregunta,))
            datosPreguntas = cursor.fetchall()
        else: 
            return render_template('error.html')
        return render_template('editar-encuesta-preguntas.html', datosPreguntas = datosPreguntas, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, idPregunta= idPregunta)

# Actualizar una pregunta con los datos editados  
@app.route('/update_pregunta/<int:idPregunta>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def update_encuesta_pregunta(idPregunta, idEncuesta, nombreEncuesta):
    if request.method == 'POST':
        # Recibo idPregunta, idEncuesta, nombre de la encuesta de 'editar-encuesta-preguntas.html' 
        # Recuperar los datos del formulario
        tipo = request.form['listaDesplegable']
        pregunta = request.form['pregunta']
        cantidadOpciones = int(request.form['cantOpciones'])
        # Recuperar el ID del tipo de pregunta elegida
        idTipoPregunta = tipoPregunta(tipo)
        # Obtener el ID del usuario en sesión y verificar si tiene asignada una encuesta igual a idEncuesta
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Actualizar la pregunta con el idPregunta recibido
        if cursor.fetchone() != None:
            cursor.execute("""
                    UPDATE preguntas
                    SET Detalle = %s,
                        CantidadOpciones = %s,
                        Id_Encuesta = %s,
                        Id_Tipo_Pregunta = %s
                    WHERE ID = %s 
            """, (pregunta,cantidadOpciones,idEncuesta,idTipoPregunta,idPregunta))
            mysql.connection.commit()
            if idTipoPregunta == 1:
                cursor.execute("""
                    SELECT * FROM preguntas
                    JOIN respuestas
                    ON preguntas.ID = respuestas.Id_Pregunta
                    WHERE preguntas.ID = %s""", (idPregunta,))
                respuestas = cursor.fetchall()
                if len(respuestas) > 1:
                    cursor.execute("""
                    DELETE FROM respuestas WHERE id_Pregunta = %s""", (idPregunta,))
                    mysql.connection.commit()
                    cursor.execute("""
                    INSERT INTO respuestas (Detalle, Valor, Id_Pregunta) 
                    VALUES (%s, %s, %s)""",("-", 0, idPregunta))
                    mysql.connection.commit()
            flash('Los datos de su pregunta se actualizaron correctamente')
            return redirect(url_for('edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
        cursor.close()
        return render_template("error.html")
    
# Eliminar una pregunta
@app.route('/delete_pregunta/<int:idPregunta>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_encuesta_pregunta(idPregunta,idEncuesta,nombreEncuesta):
    # Recibo idPregunta, idEncuesta, nombre de la encuesta de 'editar-encuesta.html'
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
    if cursor.fetchone() != None:
        # Eliminar la pregunta con el idPregunta recibido
        cursor.execute('DELETE FROM preguntas WHERE ID = %s', (idPregunta,))
        mysql.connection.commit() 
        cursor.close()
        flash("Pregunta removida satisfactoriamente")
        return redirect(url_for('edit_encuesta',idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Eliminar una opción de respuesta
@app.route('/delete_respuesta/<int:idPregunta>/<int:idRespuesta>/<int:cantOpciones>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_encuesta_respuesta(idPregunta,idRespuesta,cantOpciones,idEncuesta,nombreEncuesta):
    # Recibo parámetros de 'editar-encuesta-preguntas.html' 
    # Determinar la cantidad de opciones como una unidad menos de la recibida
    cantOpcionesActual = cantOpciones-1
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
    if cursor.fetchone() != None:
        # Eliminar la opción de respuesta seleccionada
        cursor.execute('DELETE FROM respuestas WHERE ID = %s', (idRespuesta,) )
        mysql.connection.commit() 
        # Actualizar cantidad de opciones de respuesta
        cursor.execute(
                    """UPDATE preguntas
                    SET CantidadOpciones = %s
                    WHERE ID = %s """, (cantOpcionesActual,idPregunta))
        mysql.connection.commit()
        cursor.close()
        flash("Opción de respuesta removida satisfactoriamente")
        return redirect(url_for('edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Agregar una nueva opción de respuesta
@app.route('/add_respuesta_nueva', methods=['GET'])
@login_required
def add_encuesta_respuesta_nueva():
    # Recibo parámetros de 'editar-encuesta-preguntas.html' 
    if request.method == 'GET':
        # Obtengo las variables en sesión
        idUsuario = session.get('user_id')
        idEncuesta=session.get('idEncuesta')
        nombreEncuesta=session.get('nombreEncuesta')
        idPregunta = request.args.get('idPregunta')
        pregunta = request.args.get('pregunta')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
        if cursor.fetchone() != None:
            # Obtener la cantidad de respuestas cargadas en la base de datos para la pregunta con el idPregunta recibido
            cursor.execute("SELECT * FROM respuestas WHERE Id_Pregunta = %s", (idPregunta,))
            datosRespuestas =cursor.fetchall()
            cursor.close()
            cantOpciones= len(datosRespuestas)
            return render_template('editar-encuesta-opciones.html', idPregunta=idPregunta, pregunta=pregunta, cantOpciones= cantOpciones)
        else:
            return render_template("error.html") 
        
# Agregar una nueva opción de respuesta
@app.route('/save_respuesta_nueva/<int:idPregunta>/<pregunta>', methods=['POST'])
@login_required
def save_encuesta_respuesta_nueva(idPregunta,pregunta):
    if request.method == 'POST':
        # Obtengo las variables en sesión
        idUsuario = session.get('user_id')
        idEncuesta=session.get('idEncuesta')
        nombreEncuesta=session.get('nombreEncuesta')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
        if cursor.fetchone() != None:
            # Obtener la cantidad de respuestas cargadas en la base de datos para la pregunta con el idPregunta recibido
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM respuestas WHERE Id_Pregunta = %s", (idPregunta,))
            datosRespuestas =cursor.fetchall()
            cantOpciones= len(datosRespuestas)
            respuestaDetalle=request.form['opcion'+str(cantOpciones+1)]
            # Insertar en la base de datos la nueva opción de respuesta ingresada
            cursor.execute("INSERT INTO respuestas (Detalle, Valor, Id_Pregunta) VALUES (%s, %s, %s)",
                    (respuestaDetalle, cantOpciones+1, idPregunta))
            mysql.connection.commit()
            # Actualizar la cantidad de opciones de la pregunta
            cursor.execute(
                        """UPDATE preguntas
                        SET CantidadOpciones = %s
                        WHERE ID = %s """, (cantOpciones+1,idPregunta))
            mysql.connection.commit()
            cursor.close()
            flash("Opción de respuesta agregada satisfactoriamente")
            return redirect(url_for('edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
        else:
            return render_template("error.html")
        
# Actualizar datos de las opciones de respuesta editadas
@app.route('/update_respuestas/<int:idEncuesta>/<nombreEncuesta>/<int:idPregunta>', methods=['POST'])
@login_required
def update_encuesta_respuestas(idEncuesta, nombreEncuesta, idPregunta):
    # Recibo parámetros de 'editar-encuesta-preguntas.html' 
    if request.method == 'POST':
        # Actualizar las opciones de respuesta
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM respuestas WHERE Id_Pregunta = %s", (idPregunta,))
        respuestas=cursor.fetchall()
        for i in range(len(request.form)):
            detalleOpcion = request.form["opcion" + str(i+1)]
            cursor.execute("""
                UPDATE respuestas
                SET Detalle = %s, 
                    Valor = %s, 
                    Id_Pregunta = %s
                WHERE ID = %s""",
                    (detalleOpcion, i+1, idPregunta, respuestas[i][0])) 
            mysql.connection.commit()
        cursor.close()
        flash("Opciones de respuesta actualizadas satisfactoriamente")
        return redirect(url_for('edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Encuestadores de cada encuesta
@app.route('/encuestadores', methods=['GET'])
@login_required
def encuestadores():
    # Recibir los datos enviados a través de la URL desde el botón 'Encuestadores' en 'index.html' 
    idEncuesta = request.args.get('idEncuesta') 
    nombreEncuesta = request.args.get('nombreEncuesta')
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
    if cursor.fetchone() != None:
    # Consulto los encuestadores cargados en la BD para el idEncuesta recibido
        cursor.execute("SELECT * FROM encuestadores WHERE Id_Encuesta = %s",(idEncuesta,))
        encuestadores=cursor.fetchall()
        cursor.close()
        return render_template('encuestadores.html', datosEncuestadores=encuestadores, idEncuesta= idEncuesta, nombreEncuesta=nombreEncuesta)
    else:
        return render_template("error.html")
    
# Agregar encuestador a una encuesta
@app.route('/add_encuestador', methods=['GET','POST'])
@login_required
def add_encuestadores():
    # Recibir los datos enviados a través de la URL desde el botón 'Agregar encuestador ' en 'encuestadores.html' 
    idEncuesta = request.args.get('idEncuesta') 
    nombreEncuesta = request.args.get('nombreEncuesta')
    if request.method == 'POST':
        # Recuperar los datos del formulario
        idEncuesta = request.form['idEncuesta']
        nombreEncuesta = request.form['nombreEncuesta']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        dni = request.form['dni']
        numTramiteDNI = request.form['numTramiteDNI']
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
        if cursor.fetchone() != None:
            # Insertar datos de encuestador en la base de datos
            if edad == '':
                cursor.execute("""
                    INSERT INTO encuestadores (Nombre,Apellido,DNI,NumTramiteDNI,Id_Encuesta)
                    VALUES (%s,%s,%s,%s,%s)
                    """, (nombre,apellido,dni,numTramiteDNI,idEncuesta))
                mysql.connection.commit()
            else: 
                cursor.execute("""
                    INSERT INTO encuestadores (Nombre,Apellido,Edad,DNI,NumTramiteDNI,Id_Encuesta)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """, (nombre,apellido,edad,dni,numTramiteDNI,idEncuesta))
                mysql.connection.commit()
                cursor.close()
            return redirect(url_for('encuestadores', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
    return render_template('datos-encuestadores.html', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

# Eliminar un encuestador
@app.route('/delete_encuestador/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_encuestador(idEncuesta,nombreEncuesta,idEncuestador):
    if request.method == 'POST':
        # Recibo parámetros de 'encuestadores.html'
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
        if cursor.fetchone() != None:
            # Eliminar el encuestador seleccionado
            cursor.execute('DELETE FROM encuestadores WHERE ID = %s', (idEncuestador,) )
            mysql.connection.commit() 
            cursor.close()
            flash("Encuestador removido satisfactoriamente")
            return redirect(url_for('encuestadores',idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Editar un encuestador
@app.route('/edit_encuestador', methods=['GET'])
@login_required
def edit_encuestador():
    # Recibir los datos enviados a través de la URL desde el botón 'Editar' en 'encuestadores.html'
    idEncuestador = request.args.get('idEncuestador')
    nombre = request.args.get('nombre')
    apellido = request.args.get('apellido')
    idEncuesta = request.args.get('idEncuesta')
    nombreEncuesta = request.args.get('nombreEncuesta')
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
    if cursor.fetchone() != None:
        # Consulta a la base de datos, devuelve los datos del IdEncuestador recibido
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuestadores WHERE ID = %s", (idEncuestador,))
        datosEncuestador = cursor.fetchone()
        cursor.close()
        return render_template('editar-encuestadores.html', datosEncuestador=datosEncuestador, idEncuestador=idEncuestador, nombre=nombre, apellido=apellido, idEncuesta=idEncuesta,nombreEncuesta=nombreEncuesta)

# Actualizar un encuestador
@app.route('/update_encuestador/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def update_encuestador(idEncuestador, idEncuesta, nombreEncuesta):
    if request.method == 'POST':
        # Recibo parámetros de 'editar-encuestadores.html' 
        # Recuperar los datos del formulario
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        dni = request.form['dni']
        numTramiteDNI = request.form['numTramiteDNI']
        # Obtener el ID del usuario en sesión y verificar si tiene asignada una encuesta igual a idEncuesta
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        if cursor.fetchone() != None:
            # Actualizar datos del encuestador
            # Si el campo edad está vacío no se actualiza porque no puede ser un campo vacío
            if edad == '':
                cursor.execute("""
                        UPDATE encuestadores
                        SET Nombre = %s,
                            Apellido = %s,
                            DNI = %s,
                            NumTramiteDNI = %s
                        WHERE ID = %s 
                """, (nombre,apellido,dni,numTramiteDNI,idEncuestador))
                mysql.connection.commit()
            else:
                cursor.execute("""
                        UPDATE encuestadores
                        SET Nombre = %s,
                            Apellido = %s,
                            Edad = %s,
                            DNI = %s,
                            NumTramiteDNI = %s
                        WHERE ID = %s 
                """, (nombre,apellido,edad,dni,numTramiteDNI,idEncuestador))
                mysql.connection.commit()
            cursor.close()
            flash('Los datos de su encuestador se actualizaron correctamente')
            return redirect(url_for('encuestadores', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta,))

# Crear un accceso de usuario para un encuestador
@app.route('/usuario_encuestador', methods=['GET'])
@login_required
def usuario_encuestador():
    # Recibir los datos enviados a través de la URL desde el botón 'Usuario' en 'encuestadores.html'
    idEncuestador = request.args.get('idEncuestador')
    idEncuesta = request.args.get('idEncuesta')
    nombreEncuesta = request.args.get('nombreEncuesta')
    nombreEncuestador = request.args.get('nombreEncuestador')
    apellidoEncuestador = request.args.get('apellidoEncuestador')
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    if cursor.fetchone() != None:
        # Obtener el DNI del encuestador al que se le desea crear usuario
        cursor.execute("SELECT * FROM encuestadores WHERE ID = %s AND Id_Encuesta = %s", (idEncuestador,idEncuesta))
        encuestadorCargado = cursor.fetchone()
        dniEncuestador = encuestadorCargado[4]
        # Consultar en la base de datos si ya existe en la base de datos un usuario con el dni obtenido 
        cursor.execute("SELECT NombreUsuario FROM usuarios WHERE NombreUsuario = %s",
                (dniEncuestador,))
        usuarioExistente = cursor.fetchone()
        cursor.execute("""
            SELECT encuestadores.ID as idEncuestador, NombreUsuario, usuarios.ID as idUsuario
            FROM encuestadores
            JOIN usuarios
            ON usuarios.ID = encuestadores.Id_Usuario
            WHERE encuestadores.Id_Encuesta = %s AND encuestadores.ID = %s""",(idEncuesta,idEncuestador))
        encuestador= cursor.fetchone()
        cursor.close()
        return render_template("usuario-encuestador.html", idEncuestador=idEncuestador, encuestador=encuestador, 
        idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, usuarioExistente=usuarioExistente,
        nombreEncuestador=nombreEncuestador,apellidoEncuestador=apellidoEncuestador)

# Agregar un acceso de encuestador
@app.route('/add_usuario_encuestador', methods=['GET','POST'])
@login_required
def add_usuario_encuestador ():
    # Recibir los datos enviados a través de la URL desde el botón 'Usuario' en 'encuestadores.html'
    idEncuesta = request.args.get('idEncuesta')
    nombreEncuesta = request.args.get('nombreEncuesta')
    idEncuestador = request.args.get('idEncuestador')
    if request.method == 'POST':
        # Recuperar datos del formulario en 'crear-usuario-encuestador.html'
        nombreEncuesta = request.form['nombreEncuesta']
        idEncuesta = request.form['idEncuesta']
        contrasenia = request.form['contrasenia']
        idEncuestador= request.form['idEncuestador']
        # Se ingresa un falso mail por defecto para todos los encuestadores para evitar que puedan ingresar
        # a la vista de administrador
        email ='@encuestador'
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
        if cursor.fetchone() != None:
            # Obtener el DNI del encuestador al que se le desea crear usuario
            cursor.execute("SELECT * FROM encuestadores WHERE ID = %s", (idEncuestador,))
            encuestador = cursor.fetchone()
            dniEncuestador = encuestador[4]
            nombreCompleto = encuestador[1]+" "+encuestador[2]
            cursor.execute("INSERT INTO usuarios (NombreCompleto, NombreUsuario, Email, Contrasenia) VALUES (%s, %s, %s, %s)", 
                            (nombreCompleto,dniEncuestador,email,generate_password_hash(contrasenia)))
            mysql.connection.commit()
            # Consulto el último registro ingresado para el usuario con NombreUsuario 
            # igual al cargado en el paso anterior
            cursor.execute("""
                        SELECT * FROM usuarios 
                        WHERE NombreUsuario = %s """,
                        (dniEncuestador,))
            encuestador = cursor.fetchone()
            if encuestador is not None:
                # Se verifica que la contraseña de ese usuario obtenido sea igual a la ingresada
                contraseniaGuardada = encuestador[4]
                if check_password_hash(contraseniaGuardada, contrasenia):
                    # Se le asigna al encuestador el usuario
                    cursor.execute("""
                            UPDATE encuestadores
                            SET Id_Usuario = %s
                            WHERE ID = %s
                        """, (encuestador[0],int(idEncuestador)))
                    mysql.connection.commit()
                    cursor.close()
                    flash("Se ha creado un usuario para "+nombreCompleto+'. Accede a través de <a href="{}" class="alert-link"> login_encuestador </a>'.format(url_for('login_encuestador')))
                    return redirect(url_for('encuestadores', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
    # Si la solicitud es 'GET'
    return render_template("crear-usuario-encuestador.html", idEncuestador=idEncuestador,idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

# Eliminar el acceso de un encuestador a una encuesta en particular
@app.route('/delete_usuario_encuestador/<int:idUsuarioEncuestador>/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_usuario_encuestador(idUsuarioEncuestador,idEncuestador,idEncuesta,nombreEncuesta):
    # Recibir los datos enviados a través de la URL desde el botón 'Desactivar' en 'usuario-encuestador.html'
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    if cursor.fetchone() != None:
        cursor.execute("""
                UPDATE encuestadores 
                SET Id_Usuario = NULL 
                WHERE Id_Usuario = %s""",(idUsuarioEncuestador,))
        mysql.connection.commit()
        cursor.close()
        flash("Se ha desvinculado el encuestador de esta encuesta")
        return redirect(url_for('usuario_encuestador', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, idEncuestador=idEncuestador))

# Reactivar el acceso de un encuestador a una encuesta en particular
@app.route('/update_usuario_encuestador/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def update_usuario_encuestador(idEncuestador,idEncuesta,nombreEncuesta):
    # Recibir los datos enviados a través de la URL desde el botón 'Sí' en el botón 'Eliminar' en 'usuario-encuestador.html'
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    if cursor.fetchone() != None:
        cursor.execute("SELECT * FROM encuestadores WHERE ID = %s", (idEncuestador,))
        encuestador=cursor.fetchone()
        dni = encuestador[4]
        cursor.execute("SELECT * FROM usuarios WHERE NombreUsuario = %s", (dni,))
        usuarioEncuestador = cursor.fetchone()
        idUsuarioEncuestador = usuarioEncuestador[0]
        cursor.execute("""
                UPDATE encuestadores 
                SET Id_Usuario = %s 
                WHERE ID = %s""",(idUsuarioEncuestador,idEncuestador))
        mysql.connection.commit()
        cursor.close()
        flash("Se ha vinculado nuevamente el encuestador a esta encuesta")
        return redirect(url_for('usuario_encuestador', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, idEncuestador=idEncuestador))

# Página principal de un encuestador
@app.route('/home_encuestador', methods=['GET'])
@login_required
def home_encuestador():
    idUsuarioEncuestador = session.get('user_id')
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

@app.route('/activar_encuesta/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
def activar_encuesta(idEncuesta,nombreEncuesta):
    if request.method == 'POST':
    # Actualizar el estado de la encuesta en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE encuesta 
            SET estado = 'activa' 
            WHERE ID = %s""", (idEncuesta,))
    mysql.connection.commit()
    cursor.close()
    # Redirigir al usuario a la página principal del encuestador
    return redirect(url_for('home'))

@app.route('/detener_encuesta/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
def detener_encuesta(idEncuesta,nombreEncuesta):
    if request.method == 'POST':
    # Actualizar el estado de la encuesta en la base de datos
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE encuesta 
            SET estado = 'inactiva' 
            WHERE ID = %s""", (idEncuesta,))
    mysql.connection.commit()
    cursor.close()
    # Redirigir al usuario a la página principal del encuestador
    return redirect(url_for('home'))

# Cargar datos del encuestado
@app.route('/add_encuestado', methods=['GET','POST'])
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
                flash("Ya se registraron respuestas para el DNI ingresado")
                redirect(url_for('add_encuestado',idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
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
                flash("Los datos se guardaron correctamente")
                return redirect(url_for('formulario', idEncuestado=idEncuestado, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
        cursor.close()
    return render_template('datos-encuestado.html', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

# Generar el formulario según el tipo de pregunta
@app.route('/formulario_generado', methods=['GET'])
@login_required
def generar_formulario():
    if request.method == 'GET':
        # Recibir los datos enviados a través de la URL desde el botón 'Ver' en 'index.html'
        idEncuesta = request.args.get('idEncuesta')
        nombreEncuesta = request.args.get('nombreEncuesta')
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        encuesta=cursor.fetchone()
        if encuesta != None:
            descripcion = encuesta[2]
            objetivo = encuesta[3]
        # Consulta JOIN entre la tabla 'preguntas' y la tabla 'respuestas' para obtener los datos
        # de las preguntas ingresadas y los datos de sus correspondientes opciones de respuesta
            cursor.execute("""
                SELECT preguntas.ID, preguntas.Detalle as DetallePregunta, CantidadOpciones, 
                Id_Tipo_Pregunta, respuestas.Detalle as DetalleRespuesta, respuestas.ID as Id_Respuesta
                FROM preguntas
                INNER JOIN respuestas
                WHERE preguntas.ID = respuestas.Id_Pregunta AND preguntas.Id_Encuesta = %s
                """, (idEncuesta,))
            preguntas=cursor.fetchall()
            cursor.close()
            # Creo un diccionario para almacenar cada una de las preguntas como diccionarios,
            # con la ID de la pregunta como clave y un diccionario asociado como valor.
            preguntas_dict = {}
            for pregunta in preguntas:
                pregunta_id = pregunta[0]
                pregunta_detalle = pregunta[1]
                cantidad_opciones = pregunta[2]
                pregunta_tipo = pregunta[3]
                respuesta_detalle = pregunta[4]
                id_respuesta = pregunta[5]
                
                if pregunta_id in preguntas_dict:
                    preguntas_dict[pregunta_id]['respuestas'].append({
                        'detalle': respuesta_detalle,
                        'id_respuesta': id_respuesta
                    })
                else:
                    preguntas_dict[pregunta_id] = {
                        'detalle': pregunta_detalle,
                        'cantidad_opciones': cantidad_opciones,
                        'tipo': pregunta_tipo,
                        'respuestas': [{
                            'detalle': respuesta_detalle,
                            'id_respuesta': id_respuesta
                        }]
                    }
        return render_template('generar-formulario.html', preguntas_dict=preguntas_dict, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, descripcion=descripcion, objetivo=objetivo)

# Formulario generado que utiliza el encuestador
@app.route('/formulario/<int:idEncuestado>/<int:idEncuesta>/<nombreEncuesta>', methods=['GET'])
@login_required
def formulario(idEncuestado,idEncuesta,nombreEncuesta):
    if request.method == 'GET':
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuestadores WHERE Id_Encuesta = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        if cursor.fetchone()!= None:
            cursor.execute("SELECT * FROM encuesta WHERE ID = %s", (idEncuesta,))
            encuesta = cursor.fetchone()
            descripcion = encuesta[2]
            objetivo = encuesta[3]
        # Consulta JOIN entre la tabla 'preguntas' y la tabla 'respuestas' para obtener los datos
        # de las preguntas ingresadas y los datos de sus correspondientes opciones de respuesta
            cursor.execute("""
                SELECT preguntas.ID, preguntas.Detalle as DetallePregunta, CantidadOpciones, 
                Id_Tipo_Pregunta, respuestas.Detalle as DetalleRespuesta, respuestas.ID as Id_Respuesta
                FROM preguntas
                INNER JOIN respuestas
                WHERE preguntas.ID = respuestas.Id_Pregunta AND preguntas.Id_Encuesta = %s
                """, (idEncuesta,))
            preguntas=cursor.fetchall()
            cursor.close()
            # Creo un diccionario para almacenar cada una de las preguntas como diccionarios,
            # con la ID de la pregunta como clave y un diccionario asociado como valor.
            preguntas_dict = {}
            for pregunta in preguntas:
                pregunta_id = pregunta[0]
                pregunta_detalle = pregunta[1]
                cantidad_opciones = pregunta[2]
                pregunta_tipo = pregunta[3]
                respuesta_detalle = pregunta[4]
                id_respuesta = pregunta[5]
                
                if pregunta_id in preguntas_dict:
                    preguntas_dict[pregunta_id]['respuestas'].append({
                        'detalle': respuesta_detalle,
                        'id_respuesta': id_respuesta
                    })
                else:
                    preguntas_dict[pregunta_id] = {
                        'detalle': pregunta_detalle,
                        'cantidad_opciones': cantidad_opciones,
                        'tipo': pregunta_tipo,
                        'respuestas': [{
                            'detalle': respuesta_detalle,
                            'id_respuesta': id_respuesta
                        }]
                    }
            return render_template('formulario-encuestador.html', preguntas_dict=preguntas_dict, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, descripcion=descripcion, objetivo=objetivo, idEncuestado=idEncuestado)
        else:
            return  render_template('error.html')

@app.route('/guardar_encuesta/<int:idEncuesta>/<nombreEncuesta>/<int:idEncuestado>', methods=['POST'])
@login_required
def guardar_encuesta(idEncuesta,nombreEncuesta,idEncuestado):
    if request.method == 'POST':
        # Recuperar datos del formulario
        diccionario = request.form
        respuestas = []
        detalles= []
        # Las respuestas a preguntas con elecciones definidas se obtienen como tuplas donde el valor es el id_respuesta
        # de la opción elegida y la clave es 'respuesta_<el numero de pregunta>'
        # Si la respuesta es un input de texto se guarda el id_respuesta como clave y el texto ingresado por el usuario
        # como valor.
        for key, value in diccionario.items():
            # Para el primer caso guardamos los id en la lista respuesta      
            if key.startswith('respuesta'):
                respuestas.append(diccionario.getlist(key))
            # Para el segundo caso guardamos los id en la lista detalles
            else:
                detalles.append((key,value))
        dict_respuestas = {}
        contador = 1
        # Para cada respuesta en la lista 'respuestas', si es única se agega al diccionario 
        for clave_respuesta in respuestas:
            longitud = len(clave_respuesta)
            if longitud == 1:
                dict_respuestas[contador] = {
                    'id_respuesta': clave_respuesta[0],
                    'detalle': ''
                }
                contador += 1
            # Si es una lista de respuestas quiere decir que son de una pregunta donde se hicieron múltiples elecciones
            # y se guarda cada respuesta en el diccionario
            else:
                for valor in clave_respuesta:
                    dict_respuestas[contador] = {
                        'id_respuesta': valor,
                        'detalle': ''
                    }
                    contador += 1
        # En cada iteración, obtenemos el id_respuesta del diccionario y recorreremos cada tupla en la lista detalles. 
        # Si el id_respuesta coincide con la clave de la tupla, actualizamos el valor del detalle en el diccionario 
        # dict_respuestas con el valor de la tupla y luego rompemos el bucle interno.
        for id, respuesta in dict_respuestas.items():
            id_respuesta = respuesta['id_respuesta']
            for clave_tupla, detalle in detalles:
                if id_respuesta == clave_tupla:
                    dict_respuestas[id]['detalle'] = detalle
                    break
        # Insertar en la tabla encuestados_respuestas
        cursor = mysql.connection.cursor()
        for id, respuesta in dict_respuestas.items():
            id_respuesta = respuesta['id_respuesta']
            detalle = respuesta['detalle']
            # Obtener la fecha actual
            fecha_actual = datetime.date.today()
            cursor.execute(
                    """
                    INSERT INTO encuestados_respuestas (Fecha, Id_Encuestado, Id_Respuesta, Detalle)
                    VALUES (%s, %s, %s, %s)
                    """, (fecha_actual, idEncuestado, id_respuesta, detalle))
            mysql.connection.commit()
        cursor.close()
        return redirect(url_for('add_encuestado', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

@app.route('/prueba', methods=['GET'])
def prueba():
    return render_template('prueba.html')

if __name__ == '__main__':
    app.run(debug=True)
