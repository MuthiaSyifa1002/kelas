from flask import Flask, render_template, request, redirect, session, url_for, flash
from models import User, Kelas, Komentar
from datetime import datetime, timedelta
import babel.dates

app = Flask(__name__, template_folder='views')
app.secret_key = 'tubes2025'

all_users = []
all_kelas = []

LOCALE = 'id_ID'

def tambah_user(username, password):
    user = User(username, password)
    all_users.append(user)
    return user

def cari_user(username):
    for user in all_users:
        if user.username == username:
            return user
    return None

def valid_login(username, password):
    u = cari_user(username)
    return u if u and u.password == password else None

def cari_kelas_by_id(kid):
    for k in all_kelas:
        if k.id == kid:
            return k
    return None

def cari_kelas_by_token(token):
    for k in all_kelas:
        if k.token_dosen == token:
            return k
    return None

def update_riwayat_kelas():
    now = datetime.now()
    for k in all_kelas:
        try:
            kelas_awal = datetime.strptime(k.jadwal_dt, "%Y-%m-%dT%H:%M")
            if now > kelas_awal + timedelta(hours=24) and k.status == 'aktif':
                k.status = 'selesai'
        except Exception:
            pass

def to_jam_indo(dt_str):
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
        return babel.dates.format_datetime(dt, "EEEE, d MMMM yyyy, HH:mm", locale=LOCALE)
    except Exception:
        return dt_str

@app.template_filter('indo')
def indo(value):
    return to_jam_indo(value)

@app.template_filter('komentar_indo')
def komentar_indo(dt):
    return babel.dates.format_datetime(dt, "EEEE, d MMM yyyy, HH:mm", locale=LOCALE)

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uname, pw = request.form['username'], request.form['password']
        if cari_user(uname):
            flash("Username sudah terdaftar!")
        else:
            tambah_user(uname, pw)
            flash("Registrasi berhasil, silakan login.")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        uname = request.form['username']
        new_pw = request.form['new_password']
        user = cari_user(uname)
        if not user:
            flash("Akun dengan username tersebut tidak ditemukan!")
        else:
            user.password = new_pw
            flash("Password berhasil di-reset! Silakan login.")
            return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname, pw = request.form['username'], request.form['password']
        user = valid_login(uname, pw)
        if user:
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash('Login gagal.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Sukses logout!')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    user = cari_user(session['user'])
    update_riwayat_kelas()
    host = request.host_url.rstrip('/')
    return render_template('dashboard.html', user=user, all_kelas=all_kelas, host=host)

@app.route('/kelas/buat', methods=['GET', 'POST'])
def kelas_form():
    if 'user' not in session: return redirect(url_for('login'))
    if request.method == "POST":
        nama = request.form['nama']
        matkul = request.form['matkul']
        jadwal_dt = request.form['jadwal_dt']
        pertemuan = request.form['pertemuan']
        user = cari_user(session['user'])
        kelas_baru = Kelas(nama, matkul, jadwal_dt, pertemuan, user.username)
        kelas_baru.anggota.append(user)
        user.kelas_diikuti.append(kelas_baru)
        all_kelas.append(kelas_baru)
        # Tampilkan link dosen sebagai hyperlink klik
        flash(
          f"Kelas berhasil dibuat.<br>"
          f"<b>Link Dosen: <a href='{request.host_url}kelas/dosen/{kelas_baru.token_dosen}' "
          f"target='_blank' style='color:#2366a8;'>{request.host_url}kelas/dosen/{kelas_baru.token_dosen}</a></b>",
          "msg-success"
        )
        return redirect(url_for('dashboard'))
    return render_template('kelas_form.html')

@app.route('/kelas/join/<kelas_id>')
def join_kelas(kelas_id):
    if 'user' not in session: return redirect(url_for('login'))
    user = cari_user(session['user'])
    kelas = cari_kelas_by_id(kelas_id)
    if kelas and user not in kelas.anggota:
        kelas.anggota.append(user)
        user.kelas_diikuti.append(kelas)
        flash("Berhasil masuk ke kelas.")
    return redirect(url_for('kelas_detail', kelas_id=kelas_id))

@app.route('/kelas/<kelas_id>')
def kelas_detail(kelas_id):
    if 'user' not in session: return redirect(url_for('login'))
    user = cari_user(session['user'])
    kelas = cari_kelas_by_id(kelas_id)
    update_riwayat_kelas()
    host = request.host_url.rstrip('/')
    return render_template('kelas_detail.html', kelas=kelas, user=user, host=host)

@app.route('/kelas/<kelas_id>/komentar', methods=['POST'])
def komentar_route(kelas_id):
    if 'user' not in session: return redirect(url_for('login'))
    user = cari_user(session['user'])
    kelas = cari_kelas_by_id(kelas_id)
    pesan = request.form['pesan']
    kelas.komentar.append(Komentar(user.username, pesan))
    return redirect(url_for('kelas_detail', kelas_id=kelas_id))

@app.route('/kelas/dosen/<token>', methods=['GET', 'POST'])
def dosen_link(token):
    kelas = cari_kelas_by_token(token)
    if not kelas:
        flash('Link dosen tidak valid.')
        return redirect(url_for('login'))
    if request.method == "POST":
        status = request.form['status']
        kelas.status_dosen = status
        if status == 'Setuju':
            kelas.mode_dosen = request.form.get('mode')
            kelas.dosen_jadwal = request.form.get('jadwal_dosen')
        else:
            kelas.mode_dosen = None
            kelas.dosen_jadwal = None
        komentar = request.form.get('komentar', '')
        if komentar:
            kelas.komentar.append(Komentar('DOSEN', komentar))
        flash("Dosen update berhasil.")
    update_riwayat_kelas()
    return render_template('dosen_link.html', kelas=kelas)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
