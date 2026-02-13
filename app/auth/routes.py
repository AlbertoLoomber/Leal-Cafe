from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging

from . import auth_bp
from .database import crear_usuario, obtener_usuario_por_email, obtener_usuario_por_id

logger = logging.getLogger(__name__)

def login_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor inicia sesión para continuar', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Pantalla de inicio de sesión"""

    # Si ya está autenticado, redirigir al dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Validación básica
        if not email or not password:
            flash('Por favor completa todos los campos', 'danger')
            return render_template('auth/login.html')

        try:
            # Buscar usuario
            user = obtener_usuario_por_email(email)

            if user and check_password_hash(user['password'], password):
                # Verificar que esté activo
                if not user['activo']:
                    flash('Tu cuenta está desactivada. Contacta al administrador', 'danger')
                    return render_template('auth/login.html')

                # Guardar en sesión
                session['user_id'] = user['id']
                session['user'] = {
                    'id': user['id'],
                    'nombre': user['nombre'],
                    'apellido': user['apellido'],
                    'email': user['email'],
                    'rol': user['rol']
                }
                session.permanent = True

                logger.info(f"Usuario {email} inició sesión exitosamente")
                flash(f'¡Bienvenido, {user["nombre"]}!', 'success')

                # Redirigir según rol
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))

            else:
                flash('Credenciales incorrectas', 'danger')
                logger.warning(f"Intento de login fallido para: {email}")

        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            flash('Error en el sistema. Por favor intenta más tarde', 'danger')

    return render_template('auth/login.html')

@auth_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Pantalla de registro de nuevos usuarios"""

    if request.method == 'POST':
        # Obtener datos del formulario
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        rol = request.form.get('rol', 'usuario')

        # Validaciones
        if not all([nombre, apellido, email, password, confirm_password]):
            flash('Por favor completa todos los campos', 'danger')
            return render_template('auth/registro.html')

        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('auth/registro.html')

        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'danger')
            return render_template('auth/registro.html')

        try:
            # Verificar si el email ya existe
            if obtener_usuario_por_email(email):
                flash('Este email ya está registrado', 'danger')
                return render_template('auth/registro.html')

            # Crear usuario
            password_hash = generate_password_hash(password)
            user_id = crear_usuario(nombre, apellido, email, password_hash, rol)

            if user_id:
                logger.info(f"Usuario registrado: {email}")
                flash('Registro exitoso. Por favor inicia sesión', 'success')
                return redirect(url_for('auth.login'))
            else:
                flash('Error al crear el usuario', 'danger')

        except Exception as e:
            logger.error(f"Error en registro: {str(e)}")
            flash('Error en el sistema. Por favor intenta más tarde', 'danger')

    return render_template('auth/registro.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    user_email = session.get('user', {}).get('email', 'Usuario')
    session.clear()
    logger.info(f"Usuario {user_email} cerró sesión")
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil de usuario"""
    user_id = session.get('user_id')
    user = obtener_usuario_por_id(user_id)

    if not user:
        flash('Usuario no encontrado', 'danger')
        return redirect(url_for('dashboard'))

    return render_template('auth/perfil.html', user=user)
