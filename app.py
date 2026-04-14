# Placement Portal - Full Stack Web Application
# Built with Flask, SQLAlchemy, SQLite
# Features: Role-based auth, 18+ REST endpoints, 
# CGPA filtering, resume upload, application tracking

from flask import Flask,render_template,request,redirect,url_for,session,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash,check_password_hash
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from extensions import db
import models

app=Flask(__name__)

UPLOAD_FOLDER = os.path.join(app.root_path, "static", "resumes")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['SECRET_KEY']='placement123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

UPLOAD_FOLDER = "static/resumes"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)

@app.route('/')
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] == "admin":
        return redirect(url_for("admin_dashboard"))

    elif session["role"] == "student":
        return redirect(url_for("student_dashboard"))

    elif session["role"] == "company":
        return redirect(url_for("company_dashboard"))

    return redirect(url_for("login"))

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email:
            email = email.strip()        
        print("\n--- DEBUGGING LOGIN ---")
        print(f"1. Email from form: '{email}'")
        print(f"2. Password from form: '{password}'")

        user = models.User.query.filter_by(email=email).first()
        
        print(f"3. User found in database: {user}")

        if not user:
            flash("Email not found")
            print("-> FAILED: Redirecting because user is None\n")
            return redirect(url_for("login"))
        if not user.active:
            flash("Your account is deactivated. Contact admin.")
            return redirect(url_for("login"))
        if not check_password_hash(user.password, password):
            flash("Wrong password")
            print("-> FAILED: Password mismatch\n")
            return redirect(url_for("login"))

        print("-> SUCCESS: Passwords match, redirecting to dashboard!\n")

        session["user_id"] = user.id
        session["role"] = user.role

        if user.role == "admin":
            return redirect('/admin/dashboard')
        elif user.role == "student":
             return redirect('/student/dashboard')
        elif user.role == "company":
             return redirect('/company/dashboard')
             
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/register/student',methods=["GET","POST"])
def register_student():
    if request.method=="POST":
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        branch = request.form.get("branch")
        cgpa = request.form.get("cgpa")


        existing = models.User.query.filter_by(email=email).first()

        if existing:
            flash("Email already registered. Please login.")
            return redirect(url_for("register_student"))
        
        hashed=generate_password_hash(password)

        user=models.User(email=email,password=hashed,role="student")
        db.session.add(user)
        db.session.commit()

        student=models.Student(
            user_id=user.id,
            name=name,
            branch=branch,
            cgpa=cgpa
        )
        db.session.add(student)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template('register_student.html')

@app.route('/register/company',methods=["GET","POST"])
def register_company():

    if request.method=="POST":

        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")
        contact = request.form.get("contact")

        existing = models.User.query.filter_by(email=email).first()

        if existing:
            flash("Email already registered. Please login.")
            return redirect(url_for("register_company"))
        hashed=generate_password_hash(password)

        user=models.User(email=email,password=hashed,role="company")
        db.session.add(user)
        db.session.commit()

        company=models.Company(

            user_id=user.id,
            name=name,
            contact=contact
            )
        db.session.add(company)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template("register_company.html")


@app.route("/student/dashboard")
def student_dashboard():

    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))
    student=models.Student.query.filter_by(user_id=session["user_id"]).first()
    return render_template("student_dashboard.html",student=student)

@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():

    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    student = models.Student.query.filter_by(
        user_id=session["user_id"]
    ).first()

    if request.method == "POST":

        student.name = request.form.get("name")
        student.branch = request.form.get("branch")
        student.cgpa = request.form.get("cgpa")

        db.session.commit()

        flash("Profile updated successfully!")
        return redirect(url_for("student_dashboard"))

    return render_template("student_profile.html", student=student)

@app.route("/company/dashboard")
def company_dashboard():

    if "user_id" not in session or session["role"] != "company":
        return redirect(url_for("login"))
    
    user_id=session["user_id"]

    company = models.Company.query.filter_by(user_id=session["user_id"]).first()

    if not company.approved:
        return "<h3>Your account is waiting for admin approval. </h3>"
    drives = models.Drive.query.filter_by(company_id=company.id).all()

    return render_template("company_dashboard.html",drives=drives)

@app.route('/company/create-drive',methods=["GET","POST"])

def create_drive():
    if "user_id" not in session or session["role"]!="company":
        return redirect(url_for('login'))
    
    if request.method=="POST":


        title = request.form.get("title")
        description = request.form.get("description")
        deadline = request.form.get("deadline")
        min_cgpa = request.form.get("min_cgpa")

        company = models.Company.query.filter_by(user_id=session["user_id"]).first()

        drive = models.Drive(

            company_id = company.id,
            title = title,
            description = description,
            deadline = deadline,
            min_cgpa = float(min_cgpa)

        )

        db.session.add(drive)
        db.session.commit()

        flash("Drive created successfully! Waiting for admin approval.")

        return redirect(url_for("company_dashboard"))

    return render_template("create_drive.html")

@app.route("/student/drives")
def student_drives():

    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    student = models.Student.query.filter_by(user_id=session["user_id"]).first()

    today = datetime.today().date()

    all_drives = models.Drive.query.join(models.Company).join(models.User).filter(
        models.Drive.approved == True,
        models.Drive.closed == False,
        models.User.active == True
    ).all()

    drives = []

    for drive in all_drives:
        drive_deadline = datetime.strptime(drive.deadline, "%Y-%m-%d").date()
        if drive_deadline >= today:
            drives.append(drive)

    student = models.Student.query.filter_by(user_id=session["user_id"]).first()

    applied_drive_ids = [
        app.drive_id for app in models.Application.query.filter_by(student_id=student.id).all()
    ]
    return render_template(
        "student_drives.html",
        drives=drives,
        applied_drive_ids=applied_drive_ids
    )

@app.route('/student/apply/<int:drive_id>')
def apply_drive(drive_id):

    if "user_id" not in session or session["role"] != "student":
        return redirect("/login")

   
    drive = models.Drive.query.get(drive_id)

    
    if not drive:
        flash("Drive not found.")
        return redirect("/student/drives")

    
    if drive.closed:
        flash("This drive is closed.")
        return redirect("/student/drives")

    today = datetime.today().date()
    drive_deadline = datetime.strptime(drive.deadline, "%Y-%m-%d").date()
    if today > drive_deadline:
        flash("This drive deadline has passed. You cannot apply.")
        return redirect("/student/drives")
    
    company = models.Company.query.get(drive.company_id)
    company_user = models.User.query.get(company.user_id)

    if not company_user.active:
        flash("This company is currently inactive.")
        return redirect("/student/drives")
    
    student = models.Student.query.filter_by(
        user_id=session["user_id"]
    ).first()

    
    if student.cgpa < drive.min_cgpa:
        flash("You are not eligible for this drive (CGPA requirement not met).")
        return redirect("/student/drives")

   
    old = models.Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()

    if old:
        flash("Already Applied")
        return redirect("/student/drives")

    
    app = models.Application(
        student_id=student.id,
        drive_id=drive_id
    )

    db.session.add(app)
    db.session.commit()

    flash("Applied Successfully!")
    return redirect("/student/drives")

@app.route('/student/upload-resume', methods=["GET","POST"])
def upload_resume():
    if "user_id" not in session or session["role"] != "student":
        return redirect(url_for("login"))

    student = models.Student.query.filter_by(user_id=session["user_id"]).first()

    if request.method == "POST":

        file = request.files.get("resume")

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            file.save(path)

            student.resume = filename
            db.session.commit()

            flash("Resume uploaded successfully!")
            return redirect("/student/dashboard")

        flash("Please select a file")

    return render_template("upload_resume.html")


@app.route('/student/applications')
def student_applications():
    if "user_id" not in session or session["role"]!='student':
        return redirect(url_for('login'))
    student=models.Student.query.filter_by(user_id=session["user_id"]).first()

    applications=models.Application.query.filter_by(student_id=student.id).all()
    
    return render_template("student_applications.html",applications=applications) 
    




@app.route('/company/applicants/<int:drive_id>')
def company_applicants(drive_id):

    if "user_id" not in session or session["role"] != "company":
        return redirect("/login")

    apps = models.Application.query.filter_by(drive_id=drive_id).all()

    drive = models.Drive.query.get(drive_id)

    return render_template("company_applicants.html", apps=apps,drive=drive)
    

@app.route('/company/update-status/<int:app_id>/<status>')
def update_status(app_id,status):
    if "user_id" not in session or session["role"] != "company":
        return redirect(url_for("login"))

    application = models.Application.query.get(app_id)

    if application:
        application.status = status
        db.session.commit()

    return redirect(request.referrer)
@app.route("/company/drives")
def company_drives():

    if "user_id" not in session or session["role"] != "company":
        return redirect(url_for("login"))

    company = models.Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

   
    drives = models.Drive.query.filter_by(
        company_id=company.id
    ).all()

    return render_template(
        "company_drives.html",
        drives=drives
    )

@app.route("/company/close-drive/<int:drive_id>")
def close_drive(drive_id):

    if "user_id" not in session or session["role"] != "company":
        return redirect(url_for("login"))

    company = models.Company.query.filter_by(
        user_id=session["user_id"]
    ).first()

    drive = models.Drive.query.get(drive_id)

    
    if drive and drive.company_id == company.id:

        drive.closed = True
        db.session.commit()

        flash("Drive closed successfully!")

    return redirect(url_for("company_drives"))


@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))
    total_students=models.Student.query.count()
    total_companies=models.Company.query.count()
    total_drives = models.Drive.query.count()
    total_apps = models.Application.query.count()

    pending_companies = models.Company.query.filter_by(approved=False).all()
    pending_drives = models.Drive.query.filter_by(approved=False).all()

    return render_template(
        "admin_dashboard.html",
        students=total_students,
        companies=total_companies,
        drives=total_drives,
        apps=total_apps,
        pending_companies=pending_companies,
        pending_drives=pending_drives
    )

@app.route('/admin/applications')
def admin_applications():

    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    apps = models.Application.query.all()

    return render_template("admin_applications.html", apps=apps)

    

@app.route('/admin/approve-drive/<int:drive_id>')
def approve_id(drive_id):

    if session["role"]!="admin":
        return redirect(url_for("login"))
    drive=models.Drive.query.get(drive_id)

    if drive:
        drive.approved=True
        db.session.commit()

    return redirect('/admin/dashboard')

@app.route('/admin/reject-drive/<int:drive_id>')
def reject_drive(drive_id):
    if session["role"]!="admin":
        return redirect('/login')
    drive=models.Drive.query.get(drive_id)

    if drive:
        db.session.delete(drive)
        db.session.commit()

    return redirect('/admin/dashboard')

@app.route('/admin/approve-company/<int:company_id>')
def approve_company(company_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    company = models.Company.query.get(company_id)

    if company:
        company.approved = True
        db.session.commit()

    return redirect("/admin/dashboard")

@app.route('/admin/reject-company/<int:company_id>')
def reject_company(company_id):
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    company = models.Company.query.get(company_id)

    if company:
        db.session.delete(company)
        db.session.commit()

    return redirect("/admin/dashboard")
    

@app.route('/admin/search-student',methods=["GET","POST"])
def search_student():
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    students = []

    if request.method == "POST":
        keyword = request.form.get("keyword")

        students = models.Student.query.filter(
            models.Student.name.contains(keyword)
        ).all()

        if not students:
            flash("No student found with that name.")

    return render_template(
        "search_student.html",
        students=students
    )

@app.route('/admin/toggle-user/<int:user_id>')
def toggle_user(user_id):

    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    user = models.User.query.get(user_id)

    
    if user.role == "admin":
        flash("Admin account cannot be deactivated.")
        return redirect("/admin/users")

    if user:
        user.active = not user.active
        db.session.commit()

        if user.active:
            flash("User activated successfully!")
        else:
            flash("User deactivated successfully!")

    return redirect("/admin/users")
@app.route('/admin/search-company', methods=["GET","POST"])
def search_company():

    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    companies = []

    if request.method == "POST":
        keyword = request.form.get("keyword")

        companies = models.Company.query.filter(
            models.Company.name.contains(keyword)
        ).all()

        if not companies:
            flash("No company found with that name.")


    return render_template(
        "search_company.html",
        companies=companies
    )


@app.route('/admin/users')
def admin_users():
    if "user_id" not in session or session["role"] != "admin":
        return redirect("/login")

    users = models.User.query.all()

    return render_template(
        "admin_users.html",
        users=users
    )


if __name__=="__main__":

    with app.app_context():

        db.create_all()
        admin = models.User.query.filter_by(role="admin").first()

        if not admin:
            from werkzeug.security import generate_password_hash

            default_admin = models.User(
                email="admin@portal.com",
                password=generate_password_hash("admin@123"),
                role="admin",
            )

            db.session.add(default_admin)
            db.session.commit()

            print("Default Admin Created!")

    app.run(debug=False)
