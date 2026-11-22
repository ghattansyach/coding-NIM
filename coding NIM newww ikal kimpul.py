
import sqlite3
import hashlib

db = sqlite3.connect("evote_mahasiswa.db")
db.row_factory = sqlite3.Row
cur = db.cursor()

ADMIN = "admin"
PASSWORD = hashlib.sha256("abcde".encode()).hexdigest()
PREFIX = "2610631140"



# DATABASE 

def buat_database():
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS pemilih (
        nim TEXT PRIMARY KEY,
        nama TEXT,
        sudah_memilih INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS kandidat (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama TEXT,
        visi TEXT,
        misi TEXT,
        suara INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS admin (
        username TEXT PRIMARY KEY,
        password TEXT
    );

    CREATE TABLE IF NOT EXISTS pengaturan (
        status TEXT DEFAULT 'BUKA'
    );
    """)

    cur.execute(
        "INSERT OR IGNORE INTO admin VALUES (?, ?)",
        (ADMIN, PASSWORD)
    )

    cur.execute("SELECT COUNT(*) FROM pemilih")
    if cur.fetchone()[0] == 0:
        for i in range(10, 157):
            nim = PREFIX + str(i).zfill(3)
            cur.execute(
                "INSERT INTO pemilih VALUES (?, ?, 0)",
                (nim, "Mahasiswa " + nim)
            )

    cur.execute("SELECT COUNT(*) FROM kandidat")
    if cur.fetchone()[0] == 0:
        data = [
            ("Nabila Asma Noor",
            "Mewujudkan himpunan yang inklusif, kolaboratif, dan berdaya saing.",
            "Mempererat kekeluargaan; Membuka ruang aspirasi; Meningkatkan kolaborasi"),

            ("Ghattan Syach Al Ghofari",
            "Membangun himpunan yang profesional dan berorientasi pada pengembangan kompetensi.",
            "Mengadakan pelatihan; Menjalin kerja sama dengan alumni; Mendorong keikutsertaan lomba"),

            ("Muhammad Haikal Albani",
            "Menciptakan himpunan yang aktif, inovatif, dan berprestasi.",
            "Menghadirkan program kreatif; Memanfaatkan media digital; Meningkatkan prestasi")
        ]

        cur.executemany(
            "INSERT INTO kandidat (nama, visi, misi) VALUES (?, ?, ?)",
            data
        )

    cur.execute("SELECT COUNT(*) FROM pengaturan")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO pengaturan VALUES ('BUKA')")

    db.commit()


# TAMPILAN

def tampilkan_kandidat():
    data = cur.execute("SELECT * FROM kandidat").fetchall()

    print("\n== DAFTAR KANDIDAT ==")
    for k in data:
        print(f"\nNomor {k['id']}: {k['nama']}")
        print("Visi:", k["visi"])
        print("Misi:", k["misi"])


def cek_status():
    return cur.execute(
        "SELECT status FROM pengaturan"
    ).fetchone()["status"]
    
    return hasil["status"]


# LOGIN

def login_admin():
    user = input("Username: ")
    pw = hashlib.sha256(input("Password: ").encode()).hexdigest()

    data = cur.execute(
        "SELECT * FROM admin WHERE username=? AND password=?",
        (user, pw)
    ).fetchone()

    if data:
        menu_admin()
    else:
        print("Login admin gagal!")


def login_mahasiswa():
    nim = input("Masukkan NIM:")
    nim = PREFIX + nim.zfill(3)
    data = cur.execute(
        "SELECT * FROM pemilih WHERE nim=?", (nim,)
    ).fetchone()

    if data:
        menu_mahasiswa(data)
    else:
        print("NIM tidak terdaftar!")


# VOTING

def proses_voting(mahasiswa):
    if cek_status() != "BUKA":
        print("Pemilihan sudah ditutup!")
        return

    if mahasiswa["sudah_memilih"]:
        print("Anda sudah melakukan voting!")
        return

    tampilkan_kandidat()

    try:
        pilihan = int(input("\nPilih nomor kandidat: "))
    except ValueError:
        print("Masukkan angka yang benar!")
        return

    kandidat = cur.execute(
        "SELECT * FROM kandidat WHERE id=?", (pilihan,)
    ).fetchone()

    if not kandidat:
        print("Nomor kandidat tidak tersedia!")
        return

    yakin = input("Yakin memilih kandidat ini? (y/n): ").lower()

    if yakin == "y":
        cur.execute(
            "UPDATE kandidat SET suara=suara+1 WHERE id=?",
            (pilihan,)
        )
        cur.execute(
            "UPDATE pemilih SET sudah_memilih=1 WHERE nim=? AND sudah_memilih=0",
            (mahasiswa["nim"],)
        )

        if cur.rowcount == 0:
            db.rollback()
            print("Anda sudah melakukan voting!")
            return

        db.commit()
        print("Voting berhasil!")


# HASIL PEMILIHAN

def hasil_voting():
    data = cur.execute(
        "SELECT * FROM kandidat ORDER BY suara DESC"
    ).fetchall()

    total = sum(k["suara"] for k in data)

    print("\n== HASIL PEMILIHAN ==")
    for k in data:
        persen = (k["suara"] / total * 100) if total else 0
        print(f"{k['nama']} : {k['suara']} suara ({persen:.1f}%)")

    print("Total suara:", total)


def statistik():
    pemilih = cur.execute(
        "SELECT COUNT(*) FROM pemilih"
    ).fetchone()[0]

    sudah = cur.execute(
        "SELECT COUNT(*) FROM pemilih WHERE sudah_memilih=1"
    ).fetchone()[0]

    print("\nTotal mahasiswa:", pemilih)
    print("Sudah memilih:", sudah)
    print("Belum memilih:", pemilih - sudah)


# ADMIN

def tambah_kandidat():
    nama = input("Nama kandidat: ")
    visi = input("Visi: ")
    misi = input("Misi: ")

    cur.execute(
        "INSERT INTO kandidat (nama, visi, misi) VALUES (?, ?, ?)",
        (nama, visi, misi)
    )
    db.commit()
    print("Kandidat berhasil ditambahkan!")


def hapus_kandidat():
    tampilkan_kandidat()

    try:
        nomor = int(input("Nomor kandidat yang dihapus: "))
    except ValueError:
        print("Nomor tidak valid!")
        return

    data = cur.execute(
        "SELECT suara FROM kandidat WHERE id=?", (nomor,)
    ).fetchone()

    if data and data["suara"] == 0:
        cur.execute("DELETE FROM kandidat WHERE id=?", (nomor,))
        db.commit()
        print("Kandidat berhasil dihapus!")
    else:
        print("Kandidat tidak ditemukan atau sudah memiliki suara.")


def tutup_pemilihan():
    cur.execute("UPDATE pengaturan SET status='TUTUP'")
    db.commit()
    print("Pemilihan berhasil ditutup!")


def menu_admin():
    while True:
        print("""
== MENU ADMIN ==
1. Lihat kandidat
2. Tambah kandidat
3. Hapus kandidat
4. Hasil voting
5. Statistik pemilih
6. Tutup pemilihan
0. Logout
""")

        pilih = input("Pilih menu: ")

        if pilih == "1":
            tampilkan_kandidat()
        elif pilih == "2":
            tambah_kandidat()
        elif pilih == "3":
            hapus_kandidat()
        elif pilih == "4":
            hasil_voting()
        elif pilih == "5":
            statistik()
        elif pilih == "6":
            tutup_pemilihan()
        elif pilih == "0":
            break
        else:
            print("Pilihan tidak tersedia!")


# MAHASISWA 

def menu_mahasiswa(mahasiswa):
    while True:
        print(f"""
===== MENU MAHASISWA =====
NIM: {mahasiswa['nim']}
Status: {"Sudah memilih" if mahasiswa['sudah_memilih'] else "Belum memilih"}

1. Lihat kandidat
2. Lakukan voting
0. Logout
""")

        pilih = input("Pilih menu: ")

        if pilih == "1":
            tampilkan_kandidat()
        elif pilih == "2":
            proses_voting(mahasiswa)
            mahasiswa = cur.execute(
                "SELECT * FROM pemilih WHERE nim=?",
                (mahasiswa["nim"],)
            ).fetchone()
        elif pilih == "0":
            break
        else:
            print("Pilihan tidak tersedia!")


# PROGRAM UTAMA 

def main():
    buat_database()

    while True:
        print("""
== E-VOTE MAHASISWA == 
1. Login Admin
2. Login Mahasiswa
0. Keluar
""")

        pilih = input("Pilih menu: ")

        if pilih == "1":
            login_admin()
        elif pilih == "2":
            login_mahasiswa()
        elif pilih == "0":
            print("Terima kasih!")
            break
        else:
            print("Pilihan tidak tersedia!")


main()
db.close()
