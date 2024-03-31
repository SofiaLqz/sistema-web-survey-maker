import functools
from flask import Blueprint, request, render_template, redirect, url_for, flash, get_flashed_messages, session, g, current_app
import datetime

bp = Blueprint('crud_encuesta', __name__)

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
        
# Vista del formulario para cargar los datos de la encuesta
@bp.route('/crear_encuesta', methods=['GET'])
@login_required
def crear_encuesta():
    tipoUsuario = session.get('tipo_user')
    if tipoUsuario != "encuestador":  
        return render_template('datos-encuesta.html') 
    else:
        return render_template('error-encuestador.html') 
    
# Guardar los datos de la encuesta
@bp.route('/add_datos_encuesta', methods=['POST'])
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
        mysql = current_app.config['MYSQL'] 
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
        return redirect(url_for('crud_preguntas_respuestas.add_preguntas', nomnbeEncuesta=session.get('nombreEncuesta')))
    # En caso que la solicitud HTTP sea GET
    return render_template('datos-encuesta.html')

# Eliminar una encuesta
@bp.route('/delete/<int:idEncuesta>', methods=['POST'])
@login_required
def delete_encuesta(idEncuesta):
    # Recibo idEncuesta de 'index.html'
    # Obtengo usuario en sesión 
    idUsuario = session.get('user_id')
    # Eliminar la encuesta seleccionada
    mysql = current_app.config['MYSQL'] 
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM encuesta WHERE ID = %s and Id_Usuario = %s', (idEncuesta, idUsuario) )
    mysql.connection.commit() 
    cursor.close()
    flash("Encuesta removida satisfactoriamente", "success")
    return redirect(url_for('vistas_principales.home'))

# Editar una encuesta
@bp.route('/edit_datos', methods=['GET'])
@login_required
def edit_encuesta_datos():
    # Recibir los datos enviados a través de la URL desde el botón 'Editar datos' en 'editar-encuesta.html'
    idEncuesta = request.args.get('idEncuesta')
    # Obtengo usuario en sesión 
    idUsuario = session.get('user_id')
    # Consulta a la base de datos, devuelve los datos del idEncuesta recibido 
    mysql = current_app.config['MYSQL'] 
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    datosEncuesta = cursor.fetchone()
    return render_template('editar-encuesta-datos.html', datosEncuesta=datosEncuesta)

# Guardar los datos editados de una encuesta   
@bp.route('/update_datos', methods=['POST'])
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
        mysql = current_app.config['MYSQL'] 
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
        flash("Datos de la encuesta actualizados satisfactoriamente", "success")
        return redirect(url_for('vistas_principales.edit_encuesta', idEncuesta=idEncuesta, nombreEncuesta=nombre))

@bp.route('/activar_encuesta/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
def activar_encuesta(idEncuesta,nombreEncuesta):
    if request.method == 'POST':
    # Actualizar el estado de la encuesta en la base de datos
        mysql = current_app.config['MYSQL'] 
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE encuesta 
            SET estado = 'activa' 
            WHERE ID = %s""", (idEncuesta,))
    mysql.connection.commit()
    cursor.close()
    # Redirigir al usuario a la página principal del encuestador
    return redirect(url_for('vistas_principales.home'))

@bp.route('/detener_encuesta/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
def detener_encuesta(idEncuesta,nombreEncuesta):
    if request.method == 'POST':
    # Actualizar el estado de la encuesta en la base de datos
        mysql = current_app.config['MYSQL'] 
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE encuesta 
            SET estado = 'inactiva' 
            WHERE ID = %s""", (idEncuesta,))
    mysql.connection.commit()
    cursor.close()
    # Redirigir al usuario a la página principal del encuestador
    return redirect(url_for('vistas_principales.home'))

# Generar el formulario según el tipo de pregunta
@bp.route('/formulario_generado', methods=['GET'])
@login_required
def generar_formulario():
    if request.method == 'GET':
        # Recibir los datos enviados a través de la URL desde el botón 'Ver' en 'index.html'
        idEncuesta = request.args.get('idEncuesta')
        nombreEncuesta = request.args.get('nombreEncuesta')
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        mysql = current_app.config['MYSQL'] 
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
@bp.route('/formulario/<int:idEncuestado>/<int:idEncuesta>/<nombreEncuesta>', methods=['GET'])
@login_required
def formulario(idEncuestado,idEncuesta,nombreEncuesta):
    if request.method == 'GET':
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        mysql = current_app.config['MYSQL'] 
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

@bp.route('/guardar_encuesta/<int:idEncuesta>/<nombreEncuesta>/<int:idEncuestado>', methods=['POST'])
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
        mysql = current_app.config['MYSQL'] 
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
        return redirect(url_for('encuestado.add_encuestado', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
