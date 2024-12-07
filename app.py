from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Asegúrate de que esta clave esté definida

def init_db():
    # Conectar a la base de datos (se crea si no existe)
    conn = sqlite3.connect('models/database.db')
    cursor = conn.cursor()
    
    # Crear la tabla de usuarios
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT
        )
    ''')
    
    # Crear la tabla de perfiles de empleados (con la columna first_name)
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS employee_profiles (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            middle_name TEXT,
            birth_date TEXT,
            age INTEGER,
            gender TEXT,
            phone TEXT,
            department TEXT,
            position TEXT,
            modality TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Crear tabla para registrar asistencias
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Confirmar los cambios y cerrar la conexión
    conn.commit()

    # Insertar usuarios predeterminados si no existen
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)", 
                   ('admin', 'admin123', 'admin', 'Administrador Sistema'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)", 
                   ('employee', 'employee123', 'employee', 'Empleado Ejemplo'))
    conn.commit()

    conn.close()
    
# Ruta inicial: Login
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['username'] = user[1]
            session['role'] = user[3]
            session['user_id'] = user[0]  # Guardar el ID del usuario en la sesión
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user[3] == 'employee':
                return redirect(url_for('employee_dashboard'))
        else:
            flash("Usuario o contraseña incorrectos.")
    return render_template('login.html')

# Ruta para registro de usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()
        
        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            flash("El usuario ya existe.")
        else:
            # Insertar el nuevo usuario con el rol 'employee'
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           (username, password, 'employee'))
            conn.commit()
            flash("Usuario registrado exitosamente. Ahora puedes iniciar sesión.")
            return redirect(url_for('index'))
        
        conn.close()

    return render_template('register.html')

# Dashboard Administrador
@app.route('/admin')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    return redirect(url_for('index'))

# Dashboard Empleado
@app.route('/employee')
def employee_dashboard():
    if 'role' in session and session['role'] == 'employee':
        return render_template('employee_dashboard.html')
    return redirect(url_for('index'))

# Perfil del empleado
@app.route('/employee/perfil', methods=['GET', 'POST'])
def perfil():
    if 'user_id' not in session:
        return redirect(url_for('index'))  # Si no hay 'user_id' en la sesión, redirigir al login
    
    conn = sqlite3.connect('models/database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        birth_date = request.form['birth_date']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        department = request.form['department']
        position = request.form['position']
        modality = request.form['modality']

        cursor.execute('''INSERT OR REPLACE INTO employee_profiles (user_id, first_name, last_name, middle_name, birth_date, age, gender, phone, department, position, modality)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                       (session['user_id'], first_name, last_name, middle_name, birth_date, age, gender, phone, department, position, modality))
        conn.commit()

    cursor.execute('SELECT * FROM employee_profiles WHERE user_id = ?', (session['user_id'],))
    profile = cursor.fetchone()
    conn.close()
    
    return render_template('perfil.html', profile=profile)

# Rutas específicas para el administrador
@app.route('/admin/empleados')
def empleados():
    if 'role' in session and session['role'] == 'admin':
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM employee_profiles')
        employees = cursor.fetchall()
        conn.close()
        return render_template('empleados.html', employees=employees)
    return redirect(url_for('index'))

@app.route('/asistencia', methods=['GET', 'POST'])
def registrar_asistencia():
    attendance_records = []  # Inicializa la lista vacía para evitar errores si algo falla

    if request.method == 'POST':
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        user_id = session.get('user_id')  # Asegúrate de que el usuario esté autenticado
        
        if not check_in:
            flash("Por favor, ingresa la hora de entrada.")
            return redirect('/asistencia')

        # Registrar asistencia
        try:
            conn = sqlite3.connect('models/database.db')
            cursor = conn.cursor()
            
            # Registrar la asistencia con la fecha actual
            current_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                '''
                INSERT INTO attendance (user_id, date, check_in, check_out)
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, current_date, check_in, check_out)
            )
            conn.commit()
            flash("Asistencia registrada exitosamente.")
        except sqlite3.Error as e:
            flash(f"Error al registrar asistencia: {e}")
        finally:
            conn.close()

    # Recuperar registros de asistencia para el usuario autenticado
    try:
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()
        user_id = session.get('user_id')  # Asegúrate de obtener el ID del usuario desde la sesión
        
        cursor.execute(
            '''
            SELECT date, check_in, check_out
            FROM attendance
            WHERE user_id = ?
            ORDER BY date DESC
            ''',
            (user_id,)
        )
        attendance_records = cursor.fetchall()
    except sqlite3.Error as e:
        flash(f"Error al cargar los registros de asistencia: {e}")
    finally:
        conn.close()

    # Renderiza la plantilla y pasa los registros de asistencia
    return render_template('asistencia.html', attendance_records=attendance_records)

def get_attendance_data():
    # Conectar a la base de datos
    conn = sqlite3.connect('models/database.db')
    cursor = conn.cursor()
    
    # Consulta SQL para obtener los datos
    query = '''
    SELECT 
        p.first_name,
        p.department,
        p.position,
        a.date,
        a.check_in,
        a.check_out
    FROM attendance a
    INNER JOIN users u ON a.user_id = u.id
    LEFT JOIN employee_profiles p ON u.id = p.user_id
    '''
    
    cursor.execute(query)
    records = cursor.fetchall()  # Obtener todos los resultados de la consulta
    conn.close()
    
    return records

@app.route('/admin/asistencia')
def admin_asistencia():
    if 'role' in session and session['role'] == 'admin':
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()

        page = request.args.get('page', 1, type=int)  # Obtener página de los parámetros
        month_filter = request.args.get('month')

        query = '''
        SELECT 
            COALESCE(p.first_name, '') || ' ' || COALESCE(p.middle_name, '') || ' ' || COALESCE(p.last_name, '') AS full_name,
            p.department,
            p.position,
            a.date,
            a.check_in,
            a.check_out
        FROM attendance a
        INNER JOIN users u ON a.user_id = u.id
        LEFT JOIN employee_profiles p ON u.id = p.user_id
'''

        if month_filter:
            query += ' WHERE strftime("%m", a.date) = ? ORDER BY a.date DESC LIMIT 10 OFFSET ?'
            cursor.execute(query, (month_filter, (page - 1) * 10))
        else:
            query += ' ORDER BY a.date DESC LIMIT 10 OFFSET ?'
            cursor.execute(query, ((page - 1) * 10,))

        attendance_data = cursor.fetchall()
        conn.close()

        return render_template('admin_asistencia.html', attendance_data=attendance_data, page=page)

@app.route('/admin/asistencia/<int:employee_id>', methods=['GET', 'POST'])
def asistencia_empleado(employee_id):
    if 'role' in session and session['role'] == 'admin':
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()

        # Si se seleccionó un mes, filtramos por ese mes
        month_filter = request.args.get('month')  # El mes seleccionado en el filtro (opcional)
        if month_filter:
            query = '''
                SELECT a.date, a.check_in, a.check_out 
                FROM attendance a
                WHERE a.user_id = ? AND strftime('%m', a.date) = ?
                ORDER BY a.date DESC
            '''
            cursor.execute(query, (employee_id, month_filter))
        else:
            query = '''
                SELECT a.date, a.check_in, a.check_out 
                FROM attendance a
                WHERE a.user_id = ?
                ORDER BY a.date DESC
            '''
            cursor.execute(query, (employee_id,))

        attendance_data = cursor.fetchall()
        conn.close()

        # Obtener el nombre completo del empleado para mostrarlo en la vista
        conn = sqlite3.connect('models/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT full_name FROM users WHERE id = ?', (employee_id,))
        employee_name = cursor.fetchone()[0]
        conn.close()

        return render_template('asistencia_empleado.html', attendance_data=attendance_data, employee_name=employee_name)
    return redirect(url_for('index'))

def add_full_name_column():
    conn = sqlite3.connect('models/database.db')  # Asegúrate de usar la ruta correcta
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
        conn.commit()
        print("Columna 'full_name' agregada correctamente.")
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

add_full_name_column()


# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()  # Limpiar la sesión
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Llamar a la función para inicializar la base de datos
    app.run(debug=True)
