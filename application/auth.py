from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
from werkzeug.security import check_password_hash, generate_password_hash

bp = Blueprint('auth', __name__)

@bp.before_request
def before_request():
    mysql = current_app.config['MYSQL']

# Página inicial
@bp.route('/', methods=['GET'])
def index():
    return redirect(url_for('auth.login')) 

# Iniciar sesión
@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Recopilar datos del formulario enviado
        email = request.form['email']
        contrasenia = request.form['contrasenia']
        # Consultar si existe el email ingresado en la base de datos
        mysql = current_app.config['MYSQL']
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
            return redirect(url_for('vistas_principales.home'))
        flash(error,"danger")
    # Acceder al valor enviado como parámetro desde '/register'
    registro_exitoso = request.args.get('registro_exitoso')
    return render_template('auth/login.html', registro_exitoso=registro_exitoso)
    
# Registro
@bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # Recopilar datos del formulario enviado
        nombreCompleto = request.form['nombreCompleto']
        nombreUsuario = request.form['nombreUsuario']
        email = request.form['email']
        contrasenia = request.form['contrasenia']
        confirmarContrasenia = request.form['confirmarContrasenia']
        # Consultar en la base de datos si el email ingresado ya existe en la base de datos
        mysql = current_app.config['MYSQL']
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
            return redirect('auth.login?registro_exitoso=true')
        # Si se encontraron errores de validación, se muestra el formulario de registro nuevamente junto con los mensajes de error
        return render_template('auth/register.html', error_message_email=error_message_email,error_message_contrasenia=error_message_contrasenia)
    # En caso de que la solicitud HTTP sea GET
    return render_template('auth/register.html')

# Iniciar sesión del encuestador
@bp.route('/login_encuestador', methods=['GET','POST'])
def login_encuestador():
    if request.method == 'POST':
        # Recopilar datos del formulario enviado
        usuario = request.form['usuario']
        contrasenia = request.form['contrasenia']
        # Consultar si existe el usuario ingresado en la base de datos
        mysql = current_app.config['MYSQL']
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
            return redirect(url_for('vistas_principales.home_encuestador'))
        flash(error, "danger")
    return render_template('auth/login-encuestador.html')

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

# Cerrar sesión
@bp.route('/logout', methods=['GET'])
def logout():
    # Elimina la información de la sesión
    session.clear()
    return redirect(url_for('auth.login'))