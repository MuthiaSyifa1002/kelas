import uuid
from datetime import datetime

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.kelas_diikuti = []

class Kelas:
    def __init__(self, nama, matkul, jadwal_dt, pertemuan, creator):
        self.id = str(uuid.uuid4())
        self.nama = nama
        self.matkul = matkul
        self.jadwal_dt = jadwal_dt
        self.pertemuan = pertemuan
        self.creator = creator
        self.anggota = []
        self.komentar = []
        self.status_dosen = None
        self.mode_dosen = None
        self.dosen_jadwal = None
        self.status = 'aktif'
        self.token_dosen = str(uuid.uuid4())

class Komentar:
    def __init__(self, pengirim, pesan):
        self.pengirim = pengirim
        self.pesan = pesan
        self.waktu = datetime.now()
