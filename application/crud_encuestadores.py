import functools
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, g, current_app
from werkzeug.security import check_password_hash, generate_password_hash

# Decorador personalizado para manejar errores globales
#@app.errorhandler(Exception)
#def handle_error(error):
    #return render_template("error.html", error=error), 500
bp = Blueprint('crud_encuestadores', __name__)

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
        
# Encuestadores de cada encuesta
@bp.route('/encuestadores', methods=['GET'])
@login_required
def encuestadores():
    # Recibir los datos enviados a través de la URL desde el botón 'Encuestadores' en 'index.html' 
    idEncuesta = request.args.get('idEncuesta') 
    nombreEncuesta = request.args.get('nombreEncuesta')
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    mysql = current_app.config['MYSQL']
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
@bp.route('/add_encuestador', methods=['GET','POST'])
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
        mysql = current_app.config['MYSQL']
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
            return redirect(url_for('crud_encuestadores.encuestadores', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
    return render_template('datos-encuestadores.html', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

# Eliminar un encuestador
@bp.route('/delete_encuestador/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_encuestador(idEncuesta,nombreEncuesta,idEncuestador):
    if request.method == 'POST':
        # Recibo parámetros de 'encuestadores.html'
        # Verificar el usuario en sesión para dar acceso a la vista solicitada
        idUsuario = session.get('user_id')
        mysql = current_app.config['MYSQL']
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
        # Si el usuario en sesión tiene encuesta con el idEncuesta recibido
        if cursor.fetchone() != None:
            # Eliminar el encuestador seleccionado
            cursor.execute('DELETE FROM encuestadores WHERE ID = %s', (idEncuestador,) )
            mysql.connection.commit() 
            cursor.close()
            flash("Encuestador removido satisfactoriamente", "success")
            return redirect(url_for('crud_encuestadores.encuestadores',idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))

# Editar un encuestador
@bp.route('/edit_encuestador', methods=['GET'])
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
    mysql = current_app.config['MYSQL']
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
@bp.route('/update_encuestador/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
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
        mysql = current_app.config['MYSQL']
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
            flash('Los datos de su encuestador se actualizaron correctamente', 'success')
            return redirect(url_for('crud_encuestadores.encuestadores', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta,))

# Crear un accceso de usuario para un encuestador
@bp.route('/usuario_encuestador', methods=['GET'])
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
    mysql = current_app.config['MYSQL']
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
@bp.route('/add_usuario_encuestador', methods=['GET','POST'])
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
        mysql = current_app.config['MYSQL']
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
                    flash("Se ha creado un usuario para "+nombreCompleto+'. Accede a través de <a href="{}" class="alert-link"> login_encuestador </a>'.format(url_for('auth.login_encuestador')), "success")
                    return redirect(url_for('crud_encuestadores.encuestadores', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta))
    # Si la solicitud es 'GET'
    return render_template("crear-usuario-encuestador.html", idEncuestador=idEncuestador,idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta)

# Eliminar el acceso de un encuestador a una encuesta en particular
@bp.route('/delete_usuario_encuestador/<int:idUsuarioEncuestador>/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def delete_usuario_encuestador(idUsuarioEncuestador,idEncuestador,idEncuesta,nombreEncuesta):
    # Recibir los datos enviados a través de la URL desde el botón 'Desactivar' en 'usuario-encuestador.html'
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    mysql = current_app.config['MYSQL']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM encuesta WHERE ID = %s AND Id_Usuario = %s", (idEncuesta,idUsuario))
    if cursor.fetchone() != None:
        cursor.execute("""
                UPDATE encuestadores 
                SET Id_Usuario = NULL 
                WHERE Id_Usuario = %s""",(idUsuarioEncuestador,))
        mysql.connection.commit()
        cursor.close()
        flash("Se ha desvinculado el encuestador de esta encuesta", "success")
        return redirect(url_for('crud_encuestadores.usuario_encuestador', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, idEncuestador=idEncuestador))

# Reactivar el acceso de un encuestador a una encuesta en particular
@bp.route('/update_usuario_encuestador/<int:idEncuestador>/<int:idEncuesta>/<nombreEncuesta>', methods=['POST'])
@login_required
def update_usuario_encuestador(idEncuestador,idEncuesta,nombreEncuesta):
    # Recibir los datos enviados a través de la URL desde el botón 'Sí' en el botón 'Eliminar' en 'usuario-encuestador.html'
    # Verificar el usuario en sesión para dar acceso a la vista solicitada
    idUsuario = session.get('user_id')
    mysql = current_app.config['MYSQL']
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
        flash("Se ha vinculado nuevamente el encuestador a esta encuesta", "success")
        return redirect(url_for('crud_encuestadores.usuario_encuestador', idEncuesta=idEncuesta, nombreEncuesta=nombreEncuesta, idEncuestador=idEncuestador))
