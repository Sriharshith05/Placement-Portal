from extensions import db

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(120),unique=True,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    role=db.Column(db.String(20),nullable=False)
    active=db.Column(db.Boolean,default=True)
class Student(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    name=db.Column(db.String(100))
    branch=db.Column(db.String(50))
    cgpa=db.Column(db.Float)

    resume=db.Column(db.String(200))

class Company(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    name=db.Column(db.String(100))
    contact=db.Column(db.String(50))
    approved=db.Column(db.Boolean,default=False)

class Drive(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    company_id=db.Column(db.Integer,db.ForeignKey('company.id'),nullable=False)
    title=db.Column(db.String(100))
    description=db.Column(db.Text)
    deadline=db.Column(db.String(20))
    
    closed=db.Column(db.Boolean,default=False)
    company=db.relationship(Company,backref="drives")
    approved = db.Column(db.Boolean, default=False)
    min_cgpa=db.Column(db.Float, default=0.0)
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    drive_id = db.Column(db.Integer, db.ForeignKey('drive.id'))

    status = db.Column(db.String(20), default="Pending")
    student = db.relationship("Student", backref="applications")
    drive = db.relationship("Drive", backref="applications")