import functools
from flask import Blueprint, redirect, render_template, url_for, request, flash, get_flashed_messages, g, session, current_app
from application.functions.preguntas import tipoPregunta

bp = Blueprint('crud_preguntas_respuestas', __name__)

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
        
# Guardar los datos de las preguntas
@bp.route('/add_preguntas', methods=['GET','POST'])
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
        mysql = current_app.config['MYSQL']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO preguntas (Detalle, CantidadOpciones, Id_Encuesta, Id_Tipo_Pregunta) VALUES (%s, %s, %s, %s)",
            (pregunta, cantidadOpciones, idEncuesta, idTipoPregunta))
        mysql.connection.commit()
        # Si la pregunta no es de tipo 'abierta' se redirige a la vista para cargar las opciones de respuesta
        if idTipoPregunta != 1:
            return redirect(url_for('crud_preguntas_respuestas.add_respuestas', nombreEncuesta=nombreEncuesta, pregunta=pregunta, cantOpciones=cantidadOpciones))
        else:
            # Si la pregunta es de tipo 'abierta', se carga la opción de respuesta como 'respuesta abierta'
            cursor.execute("SELECT * FROM preguntas ORDER BY ID DESC")
            idPregunta = cursor.fetchone()[0]
            cursor.execute("INSERT INTO respuestas (Detalle, Valor, Id_Pregunta) VALUES (%s, %s, %s)",("-", 0, idPregunta))
            mysql.connection.commit()
            cursor.close()
            # Mensaje flash
            flash('Los datos de su pregunta se guardaron correctamente. Puedes cargar la siguiente ahora o <a href="{}" class="alert-link"> después </a>'.format(url_for('vistas_principales.edit_encuesta', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)), "success")
            return redirect(url_for('crud_preguntas_respuestas.add_preguntas',nombreEncuesta=nombreEncuesta))
    # En caso que la solicitud HTTP sea GET
    tipoUsuario = session.get('tipo_user')
    if tipoUsuario != "encuestador":  
        return render_template('crear-formulario.html', nombreEncuesta=nombreEncuesta, messages=messages)
    else:
        return render_template('error-encuestador.html') 

# Guardar los datos de las opciones de respuestas
@bp.route('/add_respuestas/<int:cantOpciones>', methods=['GET','POST'])
@login_required
def add_respuestas(cantOpciones):
    # Recuperar datos almacenados en sesión
    nombreEncuesta = session.get('nombreEncuesta')
    if request.method == 'POST':
        # Recuperar datos almacenados en sesión
        idEncuesta = session.get('idEncuesta')
        nombreEncuesta = session.get('nombreEncuesta')
        # Consultar en la base de datos el ID de la última pregunta creada para la encuesta
        mysql = current_app.config['MYSQL']
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
            flash('Los datos de su pregunta se guardaron correctamente. Puedes cargar la siguiente ahora o <a href="{}" class="alert-link"> después </a>'.format(url_for('vistas_principales.edit_encuesta', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)), "success")
            return redirect(url_for('crud_preguntas_respuestas.add_preguntas', nombreEncuesta=nombreEncuesta))
        else:
            return render_template('error.html')
    # En caso que la solicitud HTTP sea GET
    return render_template('crear-formulario-paso2.html', nombreEncuesta=nombreEncuesta, pregunta=request.args.get('pregunta'),cantOpciones=cantOpciones)

# Editar preguntas
@bp.route('/edit_preguntas', methods=['GET'])
@login_required
def edit_encuesta_preguntas():
    if request.method == 'GET':
        # Recibir los datos enviados a través de la URL desde el botón "Editar pregunta" en 'editar-encuesta.html' 
        idPregunta = request.args.get('idPregunta')
        idEncuesta = request.args.get('idEncuesta')
        nombreEncuesta = request.args.get('nombreEncuesta')
        # Verificar el usuario en sesión para dar acceso a la vista solicitad
        idUsuario = session.get('user_id')
        mysql = current_app.config['MYSQL']
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
@bp.route('/update_pregunta/<int:idPregunta>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
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
        mysql = current_app.config['MYSQL']
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
            flash('Los datos de su pregunta se actualizaron correctamente', 'success')
            return redirect(url_for('crud_preguntas_respuestas.edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
        cursor.close()
        return render_template("error.html")
    
# Eliminar una pregunta
@bp.route('/delete_pregunta/<int:idPregunta>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_encuesta_pregunta(idPregunta,idEncuesta,nombreEncuesta):
    # Recibo idPregunta, idEncuesta, nombre de la encuesta de 'editar-encuesta.html'
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    mysql = current_app.config['MYSQL']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
    if cursor.fetchone() != None:
        # Eliminar la pregunta con el idPregunta recibido
        cursor.execute('DELETE FROM preguntas WHERE ID = %s', (idPregunta,))
        mysql.connection.commit() 
        cursor.close()
        flash("Pregunta removida satisfactoriamente", "success")
        return redirect(url_for('vistas_principales.edit_encuesta',idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Eliminar una opción de respuesta
@bp.route('/delete_respuesta/<int:idPregunta>/<int:idRespuesta>/<int:cantOpciones>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_encuesta_respuesta(idPregunta,idRespuesta,cantOpciones,idEncuesta,nombreEncuesta):
    # Recibo parámetros de 'editar-encuesta-preguntas.html' 
    # Determinar la cantidad de opciones como una unidad menos de la recibida
    cantOpcionesActual = cantOpciones-1
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    mysql = current_app.config['MYSQL']
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
        flash("Opción de respuesta removida satisfactoriamente", "success")
        return redirect(url_for('crud_preguntas_respuestas.edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Agregar una nueva opción de respuesta
@bp.route('/add_respuesta_nueva', methods=['GET'])
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
        mysql = current_app.config['MYSQL']
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
        
# Guardar nueva opción de respuesta
@bp.route('/save_respuesta_nueva/<int:idPregunta>/<pregunta>', methods=['POST'])
@login_required
def save_encuesta_respuesta_nueva(idPregunta,pregunta):
    if request.method == 'POST':
        # Obtengo las variables en sesión
        idUsuario = session.get('user_id')
        idEncuesta=session.get('idEncuesta')
        nombreEncuesta=session.get('nombreEncuesta')
        mysql = current_app.config['MYSQL']
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
            flash("Opción de respuesta agregada satisfactoriamente", "success")
            return redirect(url_for('crud_preguntas_respuestas.edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
        else:
            return render_template("error.html")
        
# Actualizar datos de las opciones de respuesta editadas
@bp.route('/update_respuestas/<int:idEncuesta>/<nombreEncuesta>/<int:idPregunta>', methods=['POST'])
@login_required
def update_encuesta_respuestas(idEncuesta, nombreEncuesta, idPregunta):
    # Recibo parámetros de 'editar-encuesta-preguntas.html' 
    if request.method == 'POST':
        # Actualizar las opciones de respuesta
        mysql = current_app.config['MYSQL']
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
        flash("Opciones de respuesta actualizadas satisfactoriamente", "success")
        return redirect(url_for('crud_preguntas_respuestas.edit_encuesta_preguntas', idPregunta= idPregunta, idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

