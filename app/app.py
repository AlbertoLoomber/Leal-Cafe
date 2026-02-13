from flask import Flask, redirect, url_for
from config import Config
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Factory para crear la aplicación Flask"""

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar configuración
    config_class.init_app(app)

    # Importar y registrar Blueprints
    from auth import auth_bp
    from ventas import ventas_bp
    from reportes import reportes_bp
    from contabilidad import contabilidad_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(ventas_bp, url_prefix='/ventas')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(contabilidad_bp, url_prefix='/contabilidad')

    # Ruta raíz
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Ruta de dashboard principal
    @app.route('/dashboard')
    def dashboard():
        from flask import render_template, session
        from auth import login_required

        @login_required
        def dashboard_view():
            return render_template('dashboard.html', user=session.get('user'))

        return dashboard_view()

    # Rutas de módulos principales
    @app.route('/modulo/ventas')
    def modulo_ventas():
        from flask import render_template, session
        from auth import login_required

        @login_required
        def modulo_ventas_view():
            return render_template('modulos/ventas.html', user=session.get('user'))

        return modulo_ventas_view()

    @app.route('/modulo/contabilidad')
    def modulo_contabilidad():
        from flask import render_template, session
        from auth import login_required

        @login_required
        def modulo_contabilidad_view():
            return render_template('modulos/contabilidad.html', user=session.get('user'))

        return modulo_contabilidad_view()

    @app.route('/modulo/operativo')
    def modulo_operativo():
        from flask import render_template, session
        from auth import login_required

        @login_required
        def modulo_operativo_view():
            return render_template('modulos/operativo.html', user=session.get('user'))

        return modulo_operativo_view()

    @app.route('/modulo/operativo/tareas')
    def modulo_operativo_tareas():
        from flask import render_template, session
        from auth import login_required

        @login_required
        def modulo_operativo_tareas_view():
            return render_template('modulos/tareas.html', user=session.get('user'))

        return modulo_operativo_tareas_view()

    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found(error):
        from flask import render_template
        return render_template('404.html'), 404

    # Manejador de errores 500
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        logger.error(f"Error 500: {str(error)}")
        return render_template('500.html'), 500

    logger.info(f"Aplicación {Config.APP_NAME} v{Config.APP_VERSION} iniciada")

    return app

if __name__ == '__main__':
    app = create_app()

    # Inicializar base de datos
    try:
        from database import init_database
        init_database()
        logger.info("Base de datos inicializada")
    except Exception as e:
        logger.warning(f"No se pudo inicializar la BD (puede que ya exista): {str(e)}")

    # Ejecutar aplicación
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
