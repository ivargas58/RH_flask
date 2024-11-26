from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Asegúrate de que esta clave esté definida

# Configuración inicial de la base de datos
def init_db():
    conn = sqlite3.connect('models/database.db')
    cursor = conn.cursor()
    
    # Crear la tabla de usuarios
    cursor.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
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
    
    conn.commit()
    
    # Insertar usuarios predeterminados si no existen
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('admin', 'admin123', 'admin'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)", 
                   ('employee', 'employee123', 'employee'))
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

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()  # Limpiar la sesión
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()  # Llamar a la función para inicializar la base de datos
    app.run(debug=True)
