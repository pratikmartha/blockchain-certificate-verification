import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "database.db"))

# Ensure directory for database exists if custom path provided
_db_dir = os.path.dirname(DB_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Admins / Institutions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            institution_name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Certificates Table (off-chain metadata & on-chain receipt sync)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT UNIQUE NOT NULL,
            student_name TEXT NOT NULL,
            student_email TEXT,
            course TEXT NOT NULL,
            institution TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            grade TEXT DEFAULT 'Pass',
            certificate_hash TEXT NOT NULL,
            tx_hash TEXT NOT NULL,
            block_number INTEGER DEFAULT 0,
            contract_address TEXT NOT NULL,
            qr_code_path TEXT,
            status TEXT DEFAULT 'VERIFIED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Verification Audit Logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            certificate_id TEXT NOT NULL,
            verifier_ip TEXT,
            status TEXT NOT NULL,
            details TEXT,
            verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Bhubaneswar Universities and Institutions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bhubaneswar_universities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            established_year INTEGER NOT NULL,
            campus_location TEXT NOT NULL,
            website TEXT NOT NULL,
            email TEXT NOT NULL,
            specialization TEXT NOT NULL,
            description TEXT NOT NULL,
            is_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Bhubaneswar, Odisha Universities Dataset
    bhubaneswar_universities_data = [
        (
            "Utkal University (Vani Vihar)",
            "UTKAL",
            "State Public University",
            1943,
            "Vani Vihar, Saheed Nagar, Bhubaneswar, Odisha 751004",
            "https://utkaluniversity.ac.in",
            "registrar@utkaluniversity.ac.in",
            "Liberal Arts, Natural Sciences, Commerce, Law, Management, Computer Applications",
            "The oldest and mother university of Odisha, established in 1943. Ranked as the 17th oldest university in India with NAAC A+ accreditation."
        ),
        (
            "Indian Institute of Technology Bhubaneswar (IIT Bhubaneswar)",
            "IITBBS",
            "Institute of National Importance",
            2008,
            "Argul, Jatni, Bhubaneswar, Odisha 752050",
            "https://www.iitbbs.ac.in",
            "registrar@iitbbs.ac.in",
            "Computer Science, Electrical, Mechanical, Civil, Metallurgy, Climate Sciences, AI",
            "Premier autonomous technical institute of national importance established by the Ministry of Education, Govt of India on a sprawling 936-acre campus in Argul."
        ),
        (
            "All India Institute of Medical Sciences Bhubaneswar (AIIMS Bhubaneswar)",
            "AIIMS-BBS",
            "Institute of National Importance",
            2012,
            "Sijua, Patrapada, Bhubaneswar, Odisha 751019",
            "https://aiimsbhubaneswar.edu.in",
            "info@aiimsbhubaneswar.edu.in",
            "Medicine (MBBS), MD, MS, DM, M.Ch, B.Sc Nursing, Biomedical & Clinical Research",
            "Autonomous apex tertiary healthcare and research institution established under PMSSY, recognized among the top medical institutes in India."
        ),
        (
            "Kalinga Institute of Industrial Technology (KIIT Deemed to be University)",
            "KIIT",
            "Deemed to be University",
            1992,
            "Patia, Bhubaneswar, Odisha 751024",
            "https://kiit.ac.in",
            "contact@kiit.ac.in",
            "Engineering, Medicine (KIMS), Law (KLS), Management (KSOM), Biotechnology, Media",
            "Institution of Eminence (IoE) and NAAC A++ accredited multi-disciplinary university world-renowned for global academic partnerships and sports infrastructure."
        ),
        (
            "Siksha 'O' Anusandhan (SOA Deemed to be University)",
            "SOA",
            "Deemed to be University",
            2007,
            "Khandagiri Square, Bhubaneswar, Odisha 751030",
            "https://www.soa.ac.in",
            "info@soa.ac.in",
            "Engineering (ITER), Medical Sciences (IMS & SUM Hospital), Dental (IDS), Pharmacy, Nursing",
            "Top-ranked multi-disciplinary deemed university in Eastern India with NAAC A++ grade and UGC Category-I Graded Autonomy."
        ),
        (
            "National Institute of Science Education and Research (NISER Bhubaneswar)",
            "NISER",
            "Autonomous Research Institute",
            2006,
            "Jatni, Khurda, Bhubaneswar, Odisha 752050",
            "https://www.niser.ac.in",
            "director@niser.ac.in",
            "Physical, Chemical, Biological, Mathematical, Earth & Planetary Sciences",
            "Premier basic sciences research institution under the Department of Atomic Energy (DAE), Govt of India, affiliated with Homi Bhabha National Institute."
        ),
        (
            "International Institute of Information Technology Bhubaneswar (IIIT Bhubaneswar)",
            "IIIT-BH",
            "State University",
            2006,
            "Gothapatna, Malipada, Bhubaneswar, Odisha 751003",
            "https://www.iiit-bh.ac.in",
            "info@iiit-bh.ac.in",
            "Computer Science, Information Technology, Electronics & Telecommunications, Electrical",
            "Premier information technology institution established by the Government of Odisha, dedicated to excellence in software and hardware engineering."
        ),
        (
            "Odisha University of Agriculture and Technology (OUAT)",
            "OUAT",
            "State Public University",
            1962,
            "Surya Nagar, Siripur, Bhubaneswar, Odisha 751003",
            "https://ouat.ac.in",
            "registrar@ouat.ac.in",
            "Agriculture, Veterinary Science & Animal Husbandry, Horticulture, Agricultural Engineering",
            "The second oldest agricultural university in India, spearheading agricultural revolution, research, and veterinary education across Odisha."
        ),
        (
            "Rama Devi Women's University",
            "RDWU",
            "State Public University",
            2015,
            "Bhoi Nagar, Rupali Square, Bhubaneswar, Odisha 751022",
            "https://rdwu.ac.in",
            "registrar@rdwu.ac.in",
            "Liberal Arts, Life Sciences, Physical Sciences, Commerce, Gender & Women's Studies",
            "The first and only women's university in Odisha, established in honor of freedom fighter Rama Devi Choudhury, empowering female leaders in higher education."
        ),
        (
            "Odisha University of Technology and Research (OUTR - Formerly CET Bhubaneswar)",
            "OUTR",
            "Unitary State University",
            1981,
            "Ghatikia, Mahalaxmi Vihar, Bhubaneswar, Odisha 751029",
            "https://outr.ac.in",
            "registrar@outr.ac.in",
            "Engineering (CSE, EE, ME, CE), Architecture (B.Arch), Planning, MCA, Biotechnology",
            "Originally College of Engineering and Technology (CET Bhubaneswar), upgraded into a premier unitary non-affiliating state technical university in 2021."
        ),
        (
            "XIM University (Xavier Institute of Management University)",
            "XIM",
            "Private State University",
            2013,
            "Harirajpur, Jatni / Xavier Square, Jayadev Vihar, Bhubaneswar, Odisha 752050",
            "https://xim.edu.in",
            "info@xim.edu.in",
            "Management (MBA/XIMB), Business Finance, Human Resource, Rural Management, Law, Tech",
            "Prestigious Jesuit university born from the legacy of Xavier Institute of Management Bhubaneswar (est. 1987), recognized as a leading business school in Asia."
        ),
        (
            "Centurion University of Technology and Management (CUTM)",
            "CUTM",
            "Pioneering Skill University & Private State University",
            2010,
            "Ramachandrapur, P.O. Jatni, Bhubaneswar, Dist - Khurda, Odisha 752050",
            "https://cutm.ac.in",
            "info@cutm.ac.in",
            "School of Engineering & Tech (CSE, AI/ML, Data Science, Mech, Civil), M.S. Swaminathan School of Agriculture (B.Sc Ag), Paramedics & Allied Health (BMLT, Radiology, Optometry), Pharmacy (B.Pharm), Management (MBA/BBA), Forensic Science, Applied Sciences, Gram Tarang Skills",
            "Accredited with NAAC 'A+' Grade and officially recognized by the United Nations and NITI Aayog as an exemplary model for skill-integrated higher education. Features specialized Centers of Excellence in 3D Printing, Advanced Manufacturing, Electric Mobility, and Industry 4.0 at its Jatni-Bhubaneswar campus."
        ),
        (
            "C. V. Raman Global University (CGU)",
            "CGU",
            "Private State University",
            2020,
            "Bidyanagar, Mahura, Janla, Bhubaneswar, Odisha 752054",
            "https://cgu-odisha.ac.in",
            "info@cgu-odisha.ac.in",
            "Engineering, Marine Engineering, Robotics & Automation, Cloud Computing, Management",
            "Evolved from C.V. Raman College of Engineering (est. 1997), celebrated for excellence in WorldSkills championships, robotics, and maritime engineering."
        ),
        (
            "Birla Global University (BGU)",
            "BGU",
            "Private State University",
            2015,
            "IDCO Plot No. 2, Institutional Area, Gothapatna, Bhubaneswar, Odisha 751029",
            "https://www.bgu.ac.in",
            "enquiry@bgu.ac.in",
            "Management (BIMTECH Heritage), Law, Media & Communication, Commerce, Data Science",
            "Founded by the Birla Academy of Art and Culture, carrying the esteemed educational tradition of the BK Birla Group of Companies."
        ),
        (
            "Utkal University of Culture (UUC)",
            "UUC",
            "State Public University",
            1999,
            "Sanskruti Vihar, Madanpur, Bhubaneswar, Odisha 752054",
            "http://uuc.ac.in",
            "uuculture@gmail.com",
            "Odissi Dance, Hindustani & Odissi Vocal, Visual Arts, Sculpture, Temple Architecture, Tourism",
            "India's dedicated cultural university established to preserve, preserve and advance classical Indian heritage, traditional architecture, and performing arts."
        ),
        (
            "National Institute of Fashion Technology (NIFT Bhubaneswar)",
            "NIFT-BBS",
            "Institute of National Importance",
            2010,
            "IDCO Plot No. 24, Chandaka Industrial Estate, Patia, Bhubaneswar, Odisha 751024",
            "https://www.nift.ac.in/bhubaneswar",
            "nift.bhubaneswar@nift.ac.in",
            "Fashion Design, Textile Design, Fashion Communication, Apparel Production",
            "Statutory apex institute of fashion education and design excellence under the Ministry of Textiles, Government of India."
        ),
        (
            "Institute of Chemical Technology - Indian Oil Odisha Campus (ICT-IOC Bhubaneswar)",
            "ICT-IOC",
            "Deemed University Campus",
            2018,
            "Samantapuri, Mouza-Gajapati Nagar, Bhubaneswar, Odisha 751013",
            "https://www.ictmumbai.edu.in/iocbhubaneswar",
            "info@iocb.ictmumbai.edu.in",
            "Chemical Engineering, Petrochemical Engineering, Polymer Science, Energy Materials",
            "Premier energy and downstream hydrocarbon research campus created collaboratively by Indian Oil Corporation Limited and ICT Mumbai."
        ),
        (
            "Biju Patnaik University of Technology (BPUT Regional Camp Office Bhubaneswar)",
            "BPUT-BBS",
            "State Technical University",
            2002,
            "Gandamunda, Khandagiri, Bhubaneswar, Odisha 751030",
            "https://www.bput.ac.in",
            "bput@bput.ac.in",
            "Affiliating State Body for Engineering, Architecture, Pharmacy, and Computer Applications",
            "State regulatory and affiliating apex university overseeing engineering and technical curricula across colleges in Odisha, with its capital hub in Bhubaneswar."
        ),
        (
            "Institute of Physics (IOP Bhubaneswar)",
            "IOP",
            "Autonomous Research Institute",
            1972,
            "Sachivalaya Marg, P.O. Sainik School, Bhubaneswar, Odisha 751005",
            "https://www.iopb.res.in",
            "director@iopb.res.in",
            "High Energy Physics, Condensed Matter, Nuclear Physics, Quantum Information, Ph.D.",
            "Autonomous research institute of the Department of Atomic Energy (DAE), Govt of India, devoted to advanced frontier research in theoretical and experimental physics."
        ),
        (
            "Institute of Life Sciences (ILS Bhubaneswar)",
            "ILS",
            "Autonomous Research Institute",
            1989,
            "Nalco Square, Chandrasekharpur, Bhubaneswar, Odisha 751023",
            "https://www.ils.res.in",
            "director@ils.res.in",
            "Infectious Diseases, Cancer Biology, Plant Genomics, Computational Biology, Ph.D.",
            "Autonomous premier biotechnology research institute under the Department of Biotechnology (DBT), Ministry of Science and Technology, Govt of India."
        )
    ]

    for univ in bhubaneswar_universities_data:
        cursor.execute("SELECT id FROM bhubaneswar_universities WHERE short_code = ?", (univ[1],))
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO bhubaneswar_universities (
                    name, short_code, category, established_year, campus_location,
                    website, email, specialization, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, univ)
        else:
            cursor.execute("""
                UPDATE bhubaneswar_universities
                SET name = ?, category = ?, established_year = ?, campus_location = ?,
                    website = ?, email = ?, specialization = ?, description = ?
                WHERE short_code = ?
            """, (univ[0], univ[2], univ[3], univ[4], univ[5], univ[6], univ[7], univ[8], univ[1]))

    # Create default administrator if none exists
    cursor.execute("SELECT id FROM admins WHERE username = ?", ("admin",))
    if not cursor.fetchone():
        hashed_pw = generate_password_hash("admin123")
        cursor.execute("""
            INSERT INTO admins (username, password_hash, institution_name, email)
            VALUES (?, ?, ?, ?)
        """, ("admin", hashed_pw, "Utkal University (Vani Vihar)", "admin@utkaluniversity.ac.in"))
        print("[DB] Default admin initialized: admin / admin123")

    # Seed quick admin accounts for prominent Bhubaneswar universities if not present
    seed_admins = [
        ("admin_cutm", "cutm123", "Centurion University of Technology and Management (CUTM)", "admin@cutm.ac.in"),
        ("admin_utkal", "utkal123", "Utkal University (Vani Vihar)", "admin@utkaluniversity.ac.in"),
        ("admin_iitbbs", "iitbbs123", "Indian Institute of Technology Bhubaneswar (IIT Bhubaneswar)", "admin@iitbbs.ac.in"),
        ("admin_aiims", "aiims123", "All India Institute of Medical Sciences Bhubaneswar (AIIMS Bhubaneswar)", "admin@aiimsbhubaneswar.edu.in"),
        ("admin_kiit", "kiit123", "Kalinga Institute of Industrial Technology (KIIT Deemed to be University)", "admin@kiit.ac.in"),
        ("admin_soa", "soa123", "Siksha 'O' Anusandhan (SOA Deemed to be University)", "admin@soa.ac.in"),
        ("admin_outr", "outr123", "Odisha University of Technology and Research (OUTR - Formerly CET Bhubaneswar)", "admin@outr.ac.in"),
        ("admin_iiit", "iiit123", "International Institute of Information Technology Bhubaneswar (IIIT Bhubaneswar)", "admin@iiit-bh.ac.in"),
        ("admin_ouat", "ouat123", "Odisha University of Agriculture and Technology (OUAT)", "admin@ouat.ac.in")
    ]
    for usr, pwd, inst, eml in seed_admins:
        cursor.execute("SELECT id FROM admins WHERE username = ?", (usr,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO admins (username, password_hash, institution_name, email)
                VALUES (?, ?, ?, ?)
            """, (usr, generate_password_hash(pwd), inst, eml))

    conn.commit()
    conn.close()

def add_admin(username, password, institution_name, email):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        pw_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO admins (username, password_hash, institution_name, email)
            VALUES (?, ?, ?, ?)
        """, (username, pw_hash, institution_name, email))
        conn.commit()
        return True, "Institution registered successfully!"
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def verify_admin_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
    admin = cursor.fetchone()
    conn.close()

    if admin and check_password_hash(admin["password_hash"], password):
        return dict(admin)
    return None

def save_certificate(cert_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO certificates (
                certificate_id, student_name, student_email, course,
                institution, issue_date, grade, certificate_hash,
                tx_hash, block_number, contract_address, qr_code_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cert_data["certificate_id"],
            cert_data["student_name"],
            cert_data.get("student_email", ""),
            cert_data["course"],
            cert_data["institution"],
            cert_data["issue_date"],
            cert_data.get("grade", "Pass"),
            cert_data["certificate_hash"],
            cert_data["tx_hash"],
            cert_data.get("block_number", 0),
            cert_data["contract_address"],
            cert_data.get("qr_code_path", "")
        ))
        conn.commit()
        return True, "Certificate stored in database."
    except sqlite3.IntegrityError:
        return False, "Certificate ID already exists in database."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def get_certificate_by_id(cert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM certificates WHERE certificate_id = ?", (cert_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_certificates(limit=100, search_query=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if search_query:
        param = f"%{search_query}%"
        cursor.execute("""
            SELECT * FROM certificates
            WHERE certificate_id LIKE ? OR student_name LIKE ? OR course LIKE ? OR institution LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (param, param, param, param, limit))
    else:
        cursor.execute("SELECT * FROM certificates ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_verification(cert_id, status, verifier_ip="127.0.0.1", details=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO verification_logs (certificate_id, verifier_ip, status, details)
        VALUES (?, ?, ?, ?)
    """, (cert_id, verifier_ip, status, details))
    conn.commit()
    conn.close()

def get_recent_verifications(limit=10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM verification_logs ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_system_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS total_certs FROM certificates")
    total_certs = cursor.fetchone()["total_certs"]

    cursor.execute("SELECT COUNT(*) AS total_verifications FROM verification_logs")
    total_verifications = cursor.fetchone()["total_verifications"]

    cursor.execute("SELECT COUNT(*) AS successful_verifications FROM verification_logs WHERE status = 'AUTHENTIC'")
    successful_verifications = cursor.fetchone()["successful_verifications"]

    cursor.execute("SELECT COUNT(*) AS total_admins FROM admins")
    total_admins = cursor.fetchone()["total_admins"]

    conn.close()
    return {
        "total_certificates": total_certs,
        "total_verifications": total_verifications,
        "successful_verifications": successful_verifications,
        "total_institutions": total_admins
    }

def get_all_universities(search_query=None, category=None):
    """Retrieve all Bhubaneswar universities and higher education institutes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM bhubaneswar_universities WHERE 1=1"
    params = []
    
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
        
    if search_query:
        query += " AND (name LIKE ? OR short_code LIKE ? OR campus_location LIKE ? OR specialization LIKE ?)"
        s = f"%{search_query}%"
        params.extend([s, s, s, s])
        
    query += " ORDER BY established_year ASC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_university_by_id(univ_id):
    """Retrieve a single university by its database ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bhubaneswar_universities WHERE id = ?", (univ_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_university_by_code(code):
    """Retrieve a single university by its short code (e.g. IITBBS, UTKAL)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bhubaneswar_universities WHERE short_code = ?", (code.upper(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_university_by_name(name):
    """Retrieve a single university by exact or partial name"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bhubaneswar_universities WHERE name = ? OR name LIKE ?", (name, f"%{name}%"))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_university_categories():
    """Retrieve list of distinct university categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM bhubaneswar_universities ORDER BY category ASC")
    rows = cursor.fetchall()
    conn.close()
    return [r["category"] for r in rows]

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
