import os
import time
import uuid
import hashlib
from datetime import datetime, timezone
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, send_from_directory
)
import qrcode
from blockchain import get_blockchain_manager
import database as db

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "blockchain-certificate-secret-key-2026")

# Directory for generated QR codes (supports custom mount path in Docker/persistent volumes)
QR_FOLDER = os.environ.get("QR_FOLDER", os.path.join(app.root_path, "static", "qr_codes"))
os.makedirs(QR_FOLDER, exist_ok=True)

# Initialize database
db.init_db()

# Initialize Blockchain Manager (compiles and deploys Solidity contract if needed)
blockchain_mgr = get_blockchain_manager()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please sign in to access the institution portal.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_data():
    """Make blockchain status and current year available to all templates"""
    status = blockchain_mgr.get_blockchain_status()
    return {
        "blockchain_status": status,
        "current_year": datetime.now().year,
        "current_admin": session.get("admin_name"),
        "admin_institution": session.get("admin_institution")
    }


def generate_certificate_qr(cert_id, request_host_url):
    """Generate and save QR code linking directly to certificate verification"""
    verify_url = f"{request_host_url.rstrip('/')}/verify/{cert_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1e1b4b", back_color="white")
    
    filename = f"{cert_id}.png"
    filepath = os.path.join(QR_FOLDER, filename)
    img.save(filepath)
    return f"qr_codes/{filename}"


# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route("/")
def index():
    stats = db.get_system_stats()
    blockchain_info = blockchain_mgr.get_blockchain_status()
    recent_certs = db.get_all_certificates(limit=5)
    return render_template(
        "index.html",
        stats=stats,
        blockchain_info=blockchain_info,
        recent_certs=recent_certs
    )


@app.route("/verify", methods=["GET", "POST"])
def verify():
    if request.method == "POST":
        cert_id = request.form.get("certificate_id", "").strip()
        if cert_id:
            return redirect(url_for("verify_result", cert_id=cert_id))
        flash("Please enter a valid Certificate ID.", "danger")
        return redirect(url_for("verify"))

    query_id = request.args.get("id", "").strip()
    if query_id:
        return redirect(url_for("verify_result", cert_id=query_id))

    return render_template("verify.html")


@app.route("/verify/<cert_id>")
def verify_result(cert_id):
    cert_id = cert_id.strip()
    
    # 1. Query Solidity Smart Contract on Blockchain
    on_chain_data = blockchain_mgr.verify_certificate(cert_id)
    
    # 2. Query Local Database for enriched metadata
    db_data = db.get_certificate_by_id(cert_id)

    # 3. Determine Authenticity Status
    is_valid = on_chain_data.get("exists", False)
    tampered = False
    
    if is_valid and db_data:
        # Check cryptographic hash match
        if on_chain_data.get("certificate_hash") != db_data.get("certificate_hash"):
            tampered = True
            is_valid = False

    # Log verification attempt in database
    status_label = "AUTHENTIC" if is_valid else ("TAMPERED" if tampered else "NOT_FOUND")
    client_ip = request.remote_addr or "127.0.0.1"
    db.log_verification(
        cert_id=cert_id,
        status=status_label,
        verifier_ip=client_ip,
        details=f"Verification query via web portal for {cert_id}"
    )

    return render_template(
        "verify_result.html",
        cert_id=cert_id,
        on_chain=on_chain_data,
        db_cert=db_data,
        is_valid=is_valid,
        tampered=tampered
    )


@app.route("/certificate/<cert_id>")
def view_certificate(cert_id):
    cert_id = cert_id.strip()
    db_cert = db.get_certificate_by_id(cert_id)
    on_chain = blockchain_mgr.verify_certificate(cert_id)

    if not db_cert and not on_chain.get("exists"):
        flash("Certificate not found.", "danger")
        return redirect(url_for("verify"))

    return render_template(
        "certificate_view.html",
        cert_id=cert_id,
        cert=db_cert,
        on_chain=on_chain
    )


@app.route("/explorer")
def explorer():
    status = blockchain_mgr.get_blockchain_status()
    all_certs = db.get_all_certificates(limit=50)
    verifications = db.get_recent_verifications(limit=15)
    return render_template(
        "explorer.html",
        status=status,
        certificates=all_certs,
        verifications=verifications
    )


@app.route("/demo/tamper", methods=["GET", "POST"])
def tamper_demo():
    certs = db.get_all_certificates(limit=10)
    selected_cert = certs[0] if certs else None
    
    tampered_hash = None
    original_hash = None
    tamper_result = None

    if request.method == "POST":
        cert_id = request.form.get("certificate_id")
        student_name = request.form.get("student_name")
        course = request.form.get("course")
        institution = request.form.get("institution")
        issue_date = request.form.get("issue_date")

        selected_cert = db.get_certificate_by_id(cert_id)
        if selected_cert:
            original_hash = selected_cert["certificate_hash"]
            # Recalculate hash with potentially tampered fields
            tampered_data = {
                "certificate_id": cert_id,
                "student_name": student_name,
                "course": course,
                "institution": institution,
                "issue_date": issue_date
            }
            tampered_hash = blockchain_mgr.calculate_hash(tampered_data)
            
            # Compare against on-chain record
            on_chain = blockchain_mgr.verify_certificate(cert_id)
            on_chain_hash = on_chain.get("certificate_hash", "")
            
            is_match = (tampered_hash == on_chain_hash)
            tamper_result = {
                "original_hash": original_hash,
                "calculated_hash": tampered_hash,
                "on_chain_hash": on_chain_hash,
                "is_match": is_match
            }

    return render_template(
        "tamper_demo.html",
        certificates=certs,
        selected_cert=selected_cert,
        tamper_result=tamper_result
    )


@app.route("/universities")
def universities():
    """Directory of all universities and premier institutions in Bhubaneswar, Odisha"""
    category = request.args.get("category", "All")
    search_query = request.args.get("q", "").strip()
    univ_list = db.get_all_universities(search_query=search_query, category=category)
    categories = db.get_university_categories()
    return render_template(
        "universities.html",
        universities=univ_list,
        categories=categories,
        selected_category=category,
        search_query=search_query,
        total_count=len(univ_list)
    )


@app.route("/api/universities")
def api_universities():
    """REST API endpoint for Bhubaneswar universities"""
    category = request.args.get("category", "All")
    search_query = request.args.get("q", "").strip()
    univ_list = db.get_all_universities(search_query=search_query, category=category)
    return jsonify({
        "success": True,
        "count": len(univ_list),
        "city": "Bhubaneswar",
        "state": "Odisha",
        "universities": univ_list
    })


# ==========================================
# INSTITUTION / ADMIN PORTAL
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin = db.verify_admin_login(username, password)
        if admin:
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["username"]
            session["admin_institution"] = admin["institution_name"]
            flash(f"Welcome back, {admin['username']} ({admin['institution_name']})!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials. Try username: 'admin' and password: 'admin123'.", "danger")

    return render_template("login.html")


@app.route("/admin/register", methods=["GET", "POST"])
def register():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        institution = request.form.get("institution_name", "").strip()
        email = request.form.get("email", "").strip()

        if not username or not password or not institution:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        success, msg = db.add_admin(username, password, institution, email)
        if success:
            flash("Institution registered successfully! Please log in.", "success")
            return redirect(url_for("login"))
        else:
            flash(msg, "danger")

    bhubaneswar_universities = db.get_all_universities()
    return render_template("register.html", bhubaneswar_universities=bhubaneswar_universities)


@app.route("/admin/logout")
def logout():
    session.clear()
    flash("You have logged out.", "info")
    return redirect(url_for("index"))


@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    stats = db.get_system_stats()
    blockchain_info = blockchain_mgr.get_blockchain_status()
    recent_certs = db.get_all_certificates(limit=10)
    verifications = db.get_recent_verifications(limit=8)
    return render_template(
        "admin_dashboard.html",
        stats=stats,
        blockchain_info=blockchain_info,
        recent_certs=recent_certs,
        verifications=verifications
    )


@app.route("/admin/issue", methods=["GET", "POST"])
@login_required
def issue_certificate():
    bhubaneswar_universities = db.get_all_universities()
    if request.method == "POST":
        cert_id = request.form.get("certificate_id", "").strip()
        student_name = request.form.get("student_name", "").strip()
        student_email = request.form.get("student_email", "").strip()
        course = request.form.get("course", "").strip()
        institution = request.form.get("institution", "").strip() or session.get("admin_institution", "Authority")
        issue_date = request.form.get("issue_date", "").strip() or datetime.now().strftime("%Y-%m-%d")
        grade = request.form.get("grade", "Pass").strip()

        if not cert_id:
            cert_id = f"CERT-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"

        if not student_name or not course:
            flash("Student Name and Course are required.", "danger")
            return render_template("issue_certificate.html", default_institution=institution, bhubaneswar_universities=bhubaneswar_universities)

        # 1. Compute SHA-256 Cryptographic Hash
        cert_payload = {
            "certificate_id": cert_id,
            "student_name": student_name,
            "course": course,
            "institution": institution,
            "issue_date": issue_date
        }
        cert_hash = blockchain_mgr.calculate_hash(cert_payload)

        # 2. Transact on Solidity Smart Contract on Ethereum
        tx_result = blockchain_mgr.issue_certificate(
            cert_id=cert_id,
            student_name=student_name,
            course=course,
            institution=institution,
            cert_hash=cert_hash
        )

        if not tx_result["success"]:
            flash(f"Blockchain Transaction Failed: {tx_result.get('error')}", "danger")
            return render_template("issue_certificate.html", default_institution=institution, bhubaneswar_universities=bhubaneswar_universities)

        # 3. Generate QR Code linking to verification URL
        qr_rel_path = generate_certificate_qr(cert_id, request.host_url)

        # 4. Save metadata in Database
        db_record = {
            "certificate_id": cert_id,
            "student_name": student_name,
            "student_email": student_email,
            "course": course,
            "institution": institution,
            "issue_date": issue_date,
            "grade": grade,
            "certificate_hash": cert_hash,
            "tx_hash": tx_result["tx_hash"],
            "block_number": tx_result["block_number"],
            "contract_address": tx_result["contract_address"],
            "qr_code_path": qr_rel_path
        }
        db.save_certificate(db_record)

        flash(f"Certificate {cert_id} successfully issued on the Ethereum blockchain! (Tx: {tx_result['tx_hash'][:16]}...)", "success")
        return redirect(url_for("view_certificate", cert_id=cert_id))

    suggested_id = f"CERT-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
    selected_univ = request.args.get("univ", "").strip()
    default_institution = selected_univ or session.get("admin_institution", "Utkal University (Vani Vihar)")
    return render_template(
        "issue_certificate.html",
        suggested_id=suggested_id,
        default_institution=default_institution,
        bhubaneswar_universities=bhubaneswar_universities,
        today=datetime.now().strftime("%Y-%m-%d")
    )


@app.route("/admin/certificates")
@login_required
def admin_certificates():
    search = request.args.get("search", "").strip()
    certificates = db.get_all_certificates(limit=100, search_query=search)
    return render_template("admin_certificates.html", certificates=certificates, search=search)


@app.route("/admin/redeploy-contract", methods=["POST"])
@login_required
def redeploy_contract():
    try:
        new_details = blockchain_mgr.deploy_contract()
        flash(f"Smart contract successfully redeployed at {new_details['address']}!", "success")
    except Exception as e:
        flash(f"Deployment error: {e}", "danger")
    return redirect(url_for("admin_dashboard"))


# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.route("/api/verify/<cert_id>")
def api_verify(cert_id):
    """Public JSON API for third-party verification"""
    on_chain = blockchain_mgr.verify_certificate(cert_id)
    db_cert = db.get_certificate_by_id(cert_id)
    
    is_valid = on_chain.get("exists", False)
    if is_valid and db_cert:
        if on_chain.get("certificate_hash") != db_cert.get("certificate_hash"):
            is_valid = False

    return jsonify({
        "certificate_id": cert_id,
        "valid": is_valid,
        "on_chain": on_chain,
        "metadata": db_cert
    })


@app.route("/api/calculate-hash", methods=["POST"])
def api_calculate_hash():
    """Calculate SHA-256 for arbitrary payload or uploaded file"""
    if "file" in request.files:
        uploaded_file = request.files["file"]
        content = uploaded_file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        return jsonify({"sha256": file_hash})
    
    data = request.get_json(silent=True) or request.form
    calculated = blockchain_mgr.calculate_hash(dict(data))
    return jsonify({"sha256": calculated})


@app.route("/health")
def health_check():
    """Liveness probe for container orchestrators and cloud load balancers"""
    return jsonify({
        "status": "healthy",
        "service": "certchain-blockchain-verification",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@app.route("/api/status")
def api_status():
    return jsonify(blockchain_mgr.get_blockchain_status())


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    
    print("\n" + "=" * 60)
    print(" Blockchain-Based Certificate Verification System")
    print(" Smart Contract: CertificateVerification.sol")
    print(f" Running on: http://{host}:{port}")
    print(" Default Admin: admin / admin123")
    print("=" * 60 + "\n")
    app.run(debug=debug, host=host, port=port)
