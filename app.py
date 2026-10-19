from datetime import datetime
import os
from flask import Flask, flash, redirect, render_template_string, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'physics_secret_key_123'

# Database Configuration (Auto-switches to Render PostgreSQL if present, else SQLite)
database_url = os.environ.get('DATABASE_URL')

if database_url:
  if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
  app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///physics_class.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---


class ClassRoom(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  # Automatically sorts all students in this class alphabetically by name (A to Z)
  students = db.relationship(
      'Student', backref='classroom', lazy=True, order_by='Student.name'
  )
  assignments = db.relationship(
      'Assignment', backref='classroom', lazy=True, cascade='all, delete-orphan'
  )
  groups = db.relationship(
      'ProjectGroup',
      backref='classroom',
      lazy=True,
      cascade='all, delete-orphan',
  )


class ProjectGroup(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  class_id = db.Column(
      db.Integer, db.ForeignKey('class_room.id'), nullable=False
  )
  members = db.relationship('Student', backref='project_group', lazy=True)


class Student(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), nullable=False)
  email = db.Column(db.String(100), nullable=True)  # Optional Email Field
  guardian_name = db.Column(db.String(100), nullable=True)
  guardian_phone = db.Column(db.String(50), nullable=True)
  class_id = db.Column(
      db.Integer, db.ForeignKey('class_room.id'), nullable=False
  )
  group_id = db.Column(
      db.Integer, db.ForeignKey('project_group.id'), nullable=True
  )
  is_leader = db.Column(db.Boolean, default=False)
  is_secretary = db.Column(db.Boolean, default=False)
  grades = db.relationship(
      'Grade', backref='student', lazy=True, cascade='all, delete-orphan'
  )
  attendance = db.relationship(
      'Attendance', backref='student', lazy=True, cascade='all, delete-orphan'
  )


class Assignment(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(150), nullable=False)
  category = db.Column(db.String(50), nullable=False)
  class_id = db.Column(
      db.Integer, db.ForeignKey('class_room.id'), nullable=False
  )
  grades = db.relationship(
      'Grade', backref='assignment', lazy=True, cascade='all, delete-orphan'
  )


class Grade(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  score = db.Column(db.Float, nullable=False, default=0.0)
  student_id = db.Column(
      db.Integer, db.ForeignKey('student.id'), nullable=False
  )
  assignment_id = db.Column(
      db.Integer, db.ForeignKey('assignment.id'), nullable=False
  )


class Attendance(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(
      db.String(20), nullable=False, default=datetime.utcnow().strftime('%Y-%m-%d')
  )
  status = db.Column(db.String(20), nullable=False)
  student_id = db.Column(
      db.Integer, db.ForeignKey('student.id'), nullable=False
  )


# --- HTML TEMPLATE ---
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quantum Physics CMS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(12px); border: 1px solid rgba(51, 65, 85, 0.8); }
        .glow-cyan { box-shadow: 0 0 25px -5px rgba(6, 182, 212, 0.15); }
        @media print {
            body { background: white !important; color: black !important; }
            aside, header, .no-print { display: none !important; }
            .print-container { width: 100% !important; margin: 0 !important; padding: 0 !important; background: white !important; border: none !important; box-shadow: none !important; color: black !important; }
            .print-text { color: black !important; }
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex font-sans antialiased">
    
    <!-- Sidebar Navigation -->
    <aside class="w-72 bg-slate-900 border-r border-slate-800 flex flex-col justify-between hidden md:flex sticky top-0 h-screen">
        <div>
            <div class="p-6 border-b border-slate-800/80 flex items-center space-x-3">
                <div class="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-teal-400 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-xl font-bold">⚛️</div>
                <div>
                    <h1 class="font-bold text-sm tracking-wide text-white">Quantum CMS</h1>
                    <p class="text-[11px] text-cyan-400 font-medium">Physics Department</p>
                </div>
            </div>

            <nav class="p-4 space-y-1.5">
                <a href="/" class="flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition {% if active_tab == 'dashboard' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 glow-cyan{% else %}text-slate-400 hover:bg-slate-800/60 hover:text-slate-200{% endif %}">
                    <span>📊</span><span>Dashboard</span>
                </a>
                <a href="/classes" class="flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition {% if active_tab == 'classes' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 glow-cyan{% else %}text-slate-400 hover:bg-slate-800/60 hover:text-slate-200{% endif %}">
                    <span>🏫</span><span>My Classes</span>
                </a>
                <a href="/reports_hub" class="flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition {% if active_tab == 'reports_hub' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 glow-cyan{% else %}text-slate-400 hover:bg-slate-800/60 hover:text-slate-200{% endif %}">
                    <span>📄</span><span>Academic Reports</span>
                </a>
                <a href="/communication" class="flex items-center space-x-3 px-4 py-3 rounded-xl text-sm font-medium transition {% if active_tab == 'communication' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 glow-cyan{% else %}text-slate-400 hover:bg-slate-800/60 hover:text-slate-200{% endif %}">
                    <span>💬</span><span>Communication Hub</span>
                </a>
            </nav>
        </div>

        <div class="p-4 border-t border-slate-800/80 m-4 rounded-xl bg-slate-950/50 border border-slate-800/60">
            <div class="flex items-center space-x-2 text-xs font-medium text-emerald-400">
                <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>SQLite Database Active</span>
            </div>
            <p class="text-[10px] text-slate-500 mt-1">Laptop & Tablet Ready</p>
        </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0">
        <header class="bg-slate-900/60 backdrop-blur border-b border-slate-800 py-4 px-6 md:hidden flex justify-between items-center sticky top-0 z-20">
            <div class="flex items-center space-x-2"><span class="text-xl">⚛️</span><span class="font-bold text-sm text-white">Quantum CMS</span></div>
            <div class="flex space-x-2 text-xs">
                <a href="/" class="p-2 bg-slate-800 rounded-lg">Home</a>
                <a href="/classes" class="p-2 bg-slate-800 rounded-lg">Classes</a>
                <a href="/reports_hub" class="p-2 bg-slate-800 rounded-lg">Reports</a>
            </div>
        </header>

        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            <div class="max-w-6xl mx-auto px-6 mt-6 w-full no-print">
              {% for category, message in messages %}
                <div class="p-4 mb-3 rounded-xl text-sm flex items-center space-x-3 shadow-lg {% if category == 'error' %}bg-red-950/80 text-red-300 border border-red-800/80{% else %}bg-emerald-950/80 text-emerald-300 border border-emerald-800/80{% endif %}">
                    <span>{% if category == 'error' %}⚠️{% else %}✅{% endif %}</span>
                    <span>{{ message }}</span>
                </div>
              {% endfor %}
            </div>
          {% endif %}
        {% endwith %}

        <main class="flex-grow p-6 md:p-10 max-w-6xl w-full mx-auto">
            {% if active_tab == 'dashboard' %}
                <div class="mb-8">
                    <h2 class="text-2xl font-bold tracking-tight text-white">Dashboard Overview</h2>
                    <p class="text-sm text-slate-400 mt-1">Welcome back, Professor. Select a class below to manage its students, groups, grades, and attendance.</p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-8">
                    <div class="glass-card p-6 rounded-2xl"><p class="text-slate-400 text-xs font-semibold uppercase">Total Classes</p><p class="text-3xl font-extrabold text-cyan-400 mt-2">{{ total_classes }}</p></div>
                    <div class="glass-card p-6 rounded-2xl"><p class="text-slate-400 text-xs font-semibold uppercase">Total Students</p><p class="text-3xl font-extrabold text-teal-400 mt-2">{{ total_students }}</p></div>
                    <div class="glass-card p-6 rounded-2xl"><p class="text-slate-400 text-xs font-semibold uppercase">System Status</p><p class="text-lg font-bold text-emerald-400 mt-3">Ready</p></div>
                </div>

                <div class="glass-card p-6 rounded-2xl">
                    <div class="flex justify-between items-center mb-4"><h3 class="font-bold text-base text-white">Your Physics Classes</h3><a href="/classes" class="text-xs text-cyan-400 hover:underline">View All &rarr;</a></div>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {% for c in classes %}
                            <div class="bg-slate-950/60 border border-slate-800 p-5 rounded-xl flex justify-between items-center">
                                <div>
                                    <h4 class="font-bold text-cyan-300 text-base">{{ c.name }}</h4>
                                    <p class="text-xs text-slate-400 mt-1">🗓️ {{ c.schedule }} | 📍 {{ c.room }}</p>
                                    <p class="text-xs text-slate-300 mt-2">👥 {{ c.students|length }} students &bull; 📂 {{ c.groups|length }} groups</p>
                                </div>
                                <a href="/class/{{ c.id }}" class="bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs px-4 py-2.5 rounded-xl shadow transition">Open Workspace</a>
                            </div>
                        {% else %}
                            <p class="text-slate-400 text-sm col-span-2 text-center py-4">No classes created yet.</p>
                        {% endfor %}
                    </div>
                </div>

            {% elif active_tab == 'classes' %}
                <div class="mb-8"><h2 class="text-2xl font-bold tracking-tight text-white">Classrooms & Laboratories</h2></div>
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div class="glass-card p-6 rounded-2xl h-fit">
                        <h3 class="font-bold text-base text-white mb-4">Add New Class</h3>
                        <form action="/classes/add" method="POST" class="space-y-4">
                            <div><label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Class Name</label><input type="text" name="name" required class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100"></div>
                            <div><label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Schedule</label><input type="text" name="schedule" required class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100"></div>
                            <div><label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Room</label><input type="text" name="room" required class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100"></div>
                            <button type="submit" class="w-full bg-cyan-600 text-white font-semibold py-3 rounded-xl text-sm">Create Class</button>
                        </form>
                    </div>
                    <div class="lg:col-span-2 glass-card p-6 rounded-2xl">
                        <h3 class="font-bold text-base text-white mb-4">Class Directory</h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {% for c in classes %}
                                <div class="bg-slate-950/60 border border-slate-800 p-5 rounded-xl flex flex-col justify-between">
                                    <div>
                                        <h4 class="font-bold text-base text-cyan-300">{{ c.name }}</h4>
                                        <p class="text-xs text-slate-400 mt-1">🗓️ {{ c.schedule }} | 📍 {{ c.room }}</p>
                                        <p class="text-xs text-slate-300 mt-2 font-medium">👥 Students Enrolled: {{ c.students|length }}</p>
                                    </div>
                                    <div class="mt-5 pt-4 border-t border-slate-900 flex justify-between items-center">
                                        <a href="/classes/delete/{{ c.id }}" onclick="return confirm('Delete class?')" class="text-xs text-red-400">Delete</a>
                                        <a href="/class/{{ c.id }}" class="bg-cyan-600 text-white text-xs font-semibold px-4 py-2 rounded-xl">Workspace &rarr;</a>
                                    </div>
                                </div>
                            {% else %}
                                <p class="text-slate-400 text-sm col-span-2 text-center py-6">No classes created yet.</p>
                            {% endfor %}
                        </div>
                    </div>
                </div>

            {% elif active_tab == 'reports_hub' %}
                <div class="mb-8">
                    <h2 class="text-2xl font-bold tracking-tight text-white">Academic Reports & Analytics Hub</h2>
                    <p class="text-sm text-slate-400 mt-1">Switch modes to view class-wide performance analytics or generate individual student report cards.</p>
                </div>

                <!-- Mode Selection Form -->
                <div class="glass-card p-6 rounded-2xl mb-8">
                    <form method="GET" action="/reports_hub" class="grid grid-cols-1 {% if report_type == 'student' %}md:grid-cols-3{% else %}md:grid-cols-2{% endif %} gap-4 items-end">
                        <div>
                            <label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Report Mode</label>
                            <select name="report_type" onchange="this.form.submit()" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 focus:outline-none focus:border-cyan-500">
                                <option value="class" {% if report_type == 'class' %}selected{% endif %}>🏫 Class Load Analytics & Batch Print</option>
                                <option value="student" {% if report_type == 'student' %}selected{% endif %}>👤 Individual Student Report Card</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Select Class</label>
                            <select name="class_id" onchange="this.form.submit()" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 focus:outline-none focus:border-cyan-500">
                                {% for c in classes %}
                                    <option value="{{ c.id }}" {% if selected_class and selected_class.id == c.id %}selected{% endif %}>{{ c.name }}</option>
                                {% endfor %}
                            </select>
                        </div>

                        {% if report_type == 'student' %}
                            <div>
                                <label class="block text-xs font-semibold uppercase text-slate-400 mb-1.5">Select Student</label>
                                <div class="flex gap-2">
                                    <select name="student_id" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100 focus:outline-none focus:border-cyan-500">
                                        {% if selected_class %}
                                            {% for s in selected_class.students %}
                                                <option value="{{ s.id }}" {% if selected_student and selected_student.id == s.id %}selected{% endif %}>{{ s.name }}</option>
                                            {% endfor %}
                                        {% endif %}
                                    </select>
                                    <button type="submit" class="bg-cyan-600 hover:bg-cyan-500 text-white font-semibold px-5 rounded-xl text-sm transition">Load</button>
                                </div>
                            </div>
                        {% endif %}
                    </form>
                </div>

                <!-- MODE A: Class Load Analytics & Batch Print -->
                {% if report_type == 'class' %}
                    {% if selected_class %}
                        <div class="space-y-6">
                            <!-- Top Analytics Cards -->
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div class="glass-card p-5 rounded-2xl border border-cyan-500/20"><p class="text-[11px] uppercase font-semibold text-slate-400">Class Average</p><p class="text-3xl font-black text-cyan-400 mt-1">{{ class_stats.avg }}%</p></div>
                                <div class="glass-card p-5 rounded-2xl border border-emerald-500/20"><p class="text-[11px] uppercase font-semibold text-slate-400">Pass Rate (&ge;50%)</p><p class="text-3xl font-black text-emerald-400 mt-1">{{ class_stats.pass_rate }}%</p></div>
                                <div class="glass-card p-5 rounded-2xl border border-teal-500/20"><p class="text-[11px] uppercase font-semibold text-slate-400">Highest Score</p><p class="text-3xl font-black text-teal-400 mt-1">{{ class_stats.high }}%</p></div>
                                <div class="glass-card p-5 rounded-2xl border border-red-500/20"><p class="text-[11px] uppercase font-semibold text-slate-400">Lowest Score</p><p class="text-3xl font-black text-red-400 mt-1">{{ class_stats.low }}%</p></div>
                            </div>

                            <!-- Analytics Distribution Bar -->
                            <div class="glass-card p-6 rounded-2xl">
                                <h3 class="font-bold text-white text-base mb-4">Performance Distribution Analytics</h3>
                                <div class="space-y-3">
                                    <div>
                                        <div class="flex justify-between text-xs text-slate-300 mb-1"><span>Excellent (80% - 100%)</span><span class="font-bold">{{ class_stats.dist.exc }} Students ({{ class_stats.dist.exc_pct }}%)</span></div>
                                        <div class="w-full bg-slate-950 h-3 rounded-full overflow-hidden"><div class="bg-cyan-500 h-full" style="width: {{ class_stats.dist.exc_pct }}%"></div></div>
                                    </div>
                                    <div>
                                        <div class="flex justify-between text-xs text-slate-300 mb-1"><span>Proficient (60% - 79%)</span><span class="font-bold">{{ class_stats.dist.prof }} Students ({{ class_stats.dist.prof_pct }}%)</span></div>
                                        <div class="w-full bg-slate-950 h-3 rounded-full overflow-hidden"><div class="bg-emerald-500 h-full" style="width: {{ class_stats.dist.prof_pct }}%"></div></div>
                                    </div>
                                    <div>
                                        <div class="flex justify-between text-xs text-slate-300 mb-1"><span>Passing (50% - 59%)</span><span class="font-bold">{{ class_stats.dist.pass }} Students ({{ class_stats.dist.pass_pct }}%)</span></div>
                                        <div class="w-full bg-slate-950 h-3 rounded-full overflow-hidden"><div class="bg-amber-500 h-full" style="width: {{ class_stats.dist.pass_pct }}%"></div></div>
                                    </div>
                                    <div>
                                        <div class="flex justify-between text-xs text-slate-300 mb-1"><span>At Risk (&lt; 50%)</span><span class="font-bold">{{ class_stats.dist.risk }} Students ({{ class_stats.dist.risk_pct }}%)</span></div>
                                        <div class="w-full bg-slate-950 h-3 rounded-full overflow-hidden"><div class="bg-red-500 h-full" style="width: {{ class_stats.dist.risk_pct }}%"></div></div>
                                    </div>
                                </div>
                            </div>

                            <!-- Batch Print CTA -->
                            <div class="glass-card p-6 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-4">
                                <div>
                                    <h3 class="font-bold text-white text-base">Batch Reports Printing</h3>
                                    <p class="text-xs text-slate-400 mt-0.5">Generate printable PDF report cards for all {{ selected_class.students|length }} students in {{ selected_class.name }}.</p>
                                </div>
                                <a href="/class/{{ selected_class.id }}/reports/batch_print" target="_blank" class="bg-gradient-to-r from-emerald-600 to-teal-500 text-white font-semibold px-6 py-3 rounded-xl text-sm shadow transition whitespace-nowrap">🖨️ Batch Print (PDF)</a>
                            </div>
                        </div>
                    {% else %}
                        <div class="glass-card p-8 text-center text-slate-400 text-sm rounded-2xl">Please select or create a class to view analytics.</div>
                    {% endif %}

                <!-- MODE B: Individual Student Report Card -->
                {% elif report_type == 'student' %}
                    {% if selected_student %}
                        <div class="glass-card p-8 rounded-2xl print-container bg-slate-900 border border-slate-700 space-y-6">
                            <div class="border-b border-slate-700 pb-6 flex justify-between items-start">
                                <div>
                                    <span class="bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 text-xs px-3 py-1 rounded-full font-bold">Individual Report Card</span>
                                    <h3 class="text-2xl font-black text-white mt-2 print-text">{{ selected_student.name }}</h3>
                                    <p class="text-xs text-slate-400 mt-1">Class: {{ selected_class.name }} {% if selected_student.email %}&bull; Email: {{ selected_student.email }}{% endif %}</p>
                                </div>
                                <button onclick="window.print()" class="no-print bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2.5 rounded-xl shadow transition">🖨️ Print Report Card</button>
                            </div>

                            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800"><p class="text-xs text-slate-400 font-semibold uppercase">Overall Average</p><p class="text-2xl font-black text-cyan-400 mt-1 print-text">{{ student_report.avg }}%</p></div>
                                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800"><p class="text-xs text-slate-400 font-semibold uppercase">Project Group & Role</p><p class="text-sm font-bold text-teal-300 mt-2 print-text">{{ selected_student.project_group.name if selected_student.project_group else 'Unassigned' }} {% if selected_student.is_leader %}(Leader){% elif selected_student.is_secretary %}(Secretary){% endif %}</p></div>
                                <div class="bg-slate-950 p-4 rounded-xl border border-slate-800"><p class="text-xs text-slate-400 font-semibold uppercase">Guardian Contact</p><p class="text-xs font-bold text-slate-300 mt-2 print-text">{{ selected_student.guardian_name or 'N/A' }} ({{ selected_student.guardian_phone or 'N/A' }})</p></div>
                            </div>

                            <div>
                                <h4 class="font-bold text-sm text-slate-300 uppercase mb-3">Assessment Breakdown</h4>
                                <table class="w-full text-left text-sm border-collapse">
                                    <thead><tr class="border-b border-slate-700 text-xs text-slate-400 uppercase"><th class="py-3">Assessment Title</th><th class="py-3">Category</th><th class="py-3 text-right">Score</th></tr></thead>
                                    <tbody class="divide-y divide-slate-800">
                                        {% for g in student_report.grades %}
                                            <tr><td class="py-3 font-semibold text-slate-200 print-text">{{ g.title }}</td><td class="py-3 text-xs text-slate-400">{{ g.category }}</td><td class="py-3 text-right font-bold text-cyan-300 print-text">{{ g.score }} / 100</td></tr>
                                        {% else %}
                                            <tr><td colspan="3" class="py-4 text-center text-slate-500 text-xs">No grades recorded for this student yet.</td></tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    {% else %}
                        <div class="glass-card p-8 text-center text-slate-400 text-sm rounded-2xl">No student selected or no students enrolled in this class yet.</div>
                    {% endif %}
                {% endif %}

            {% elif active_tab == 'class_workspace' %}
                <div class="mb-6">
                    <a href="/classes" class="text-xs text-slate-400 hover:text-cyan-400">&larr; Back to Classes</a>
                    <h2 class="text-2xl font-bold text-white mt-1">{{ current_class.name }}</h2>
                </div>

                <div class="flex space-x-2 border-b border-slate-800 pb-4 mb-6 overflow-x-auto">
                    <a href="/class/{{ current_class.id }}?tab=students" class="px-4 py-2 rounded-xl text-sm font-semibold {% if sub_tab == 'students' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20{% else %}text-slate-400{% endif %}">Student Roster</a>
                    <a href="/class/{{ current_class.id }}?tab=groups" class="px-4 py-2 rounded-xl text-sm font-semibold {% if sub_tab == 'groups' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20{% else %}text-slate-400{% endif %}">👥 Project Groups</a>
                    <a href="/class/{{ current_class.id }}?tab=gradebook" class="px-4 py-2 rounded-xl text-sm font-semibold {% if sub_tab == 'gradebook' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20{% else %}text-slate-400{% endif %}">Gradebook Matrix</a>
                    <a href="/class/{{ current_class.id }}?tab=group_grading" class="px-4 py-2 rounded-xl text-sm font-semibold {% if sub_tab == 'group_grading' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20{% else %}text-slate-400{% endif %}">🏆 Group Grading</a>
                    <a href="/class/{{ current_class.id }}?tab=attendance" class="px-4 py-2 rounded-xl text-sm font-semibold {% if sub_tab == 'attendance' %}bg-cyan-500/10 text-cyan-400 border border-cyan-500/20{% else %}text-slate-400{% endif %}">Attendance Roll</a>
                </div>

                {% if sub_tab == 'students' %}
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="glass-card p-6 rounded-2xl h-fit">
                            <h3 class="font-bold text-white mb-4 text-base">Enroll Student</h3>
                            <form action="/class/{{ current_class.id }}/student/add" method="POST" class="space-y-4">
                                <input type="text" name="name" required placeholder="Full Name *" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                <input type="email" name="email" placeholder="Email Address (Optional)" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                <input type="text" name="guardian_name" placeholder="Guardian Name (Optional)" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                <input type="text" name="guardian_phone" placeholder="Guardian Phone (Optional)" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                <button type="submit" class="w-full bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-3 rounded-xl text-sm">Enroll Student</button>
                            </form>
                        </div>
                        <div class="lg:col-span-2 glass-card p-6 rounded-2xl overflow-x-auto">
                            <h3 class="font-bold text-white mb-4 text-base">Enrolled Students ({{ current_class.students|length }})</h3>
                            <table class="w-full text-left text-sm">
                                <thead><tr class="border-b border-slate-800 text-xs text-slate-400 uppercase"><th class="p-3">Name</th><th class="p-3">Group</th><th class="p-3 text-right">Action</th></tr></thead>
                                <tbody class="divide-y divide-slate-800">
                                    {% for s in current_class.students %}
                                        <tr>
                                            <td class="p-3 font-semibold text-slate-200">
                                                {{ s.name }}
                                                {% if s.is_leader %}<span class="ml-2 text-[10px] bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded-full font-bold">Leader</span>{% endif %}
                                                {% if s.is_secretary %}<span class="ml-2 text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full font-bold">Secretary</span>{% endif %}
                                            </td>
                                            <td class="p-3 text-xs text-cyan-300">{{ s.project_group.name if s.project_group else 'Unassigned' }}</td>
                                            <td class="p-3 text-right"><a href="/student/delete/{{ s.id }}" onclick="return confirm('Remove?')" class="text-xs text-red-400">Remove</a></td>
                                        </tr>
                                    {% else %}
                                        <tr><td colspan="3" class="p-6 text-center text-slate-400">No students enrolled.</td></tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>

                {% elif sub_tab == 'groups' %}
                    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div class="glass-card p-6 rounded-2xl h-fit">
                            <h3 class="font-bold text-white mb-4 text-base">Create Project Group</h3>
                            <form action="/class/{{ current_class.id }}/group/add" method="POST" class="space-y-4">
                                <input type="text" name="group_name" required placeholder="Group Name (e.g. Group A)" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                <button type="submit" class="w-full bg-cyan-600 text-white font-semibold py-3 rounded-xl text-sm">Create Group</button>
                            </form>
                        </div>
                        <div class="lg:col-span-2 space-y-4">
                            {% for g in current_class.groups %}
                                <div class="glass-card p-5 rounded-2xl">
                                    <div class="flex justify-between items-center pb-3 border-b border-slate-800">
                                        <h4 class="font-bold text-cyan-300 text-base">{{ g.name }}</h4>
                                        <a href="/group/delete/{{ g.id }}" onclick="return confirm('Delete group?')" class="text-xs text-red-400">Delete</a>
                                    </div>
                                    <form action="/group/{{ g.id }}/member/add" method="POST" class="grid grid-cols-1 sm:grid-cols-4 gap-2 py-3 border-b border-slate-800 items-end">
                                        <div class="sm:col-span-2">
                                            <select name="student_id" required class="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100">
                                                {% for s in current_class.students %}{% if not s.group_id %}<option value="{{ s.id }}">{{ s.name }}</option>{% endif %}{% endfor %}
                                            </select>
                                        </div>
                                        <div>
                                            <select name="role" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-slate-100">
                                                <option value="member">Member</option>
                                                <option value="leader">Leader</option>
                                                <option value="secretary">Secretary</option>
                                            </select>
                                        </div>
                                        <button type="submit" class="bg-teal-600 text-white py-2.5 px-3 rounded-xl text-xs font-semibold">Add</button>
                                    </form>
                                    <div class="pt-3 space-y-2">
                                        {% for m in g.members %}
                                            <div class="flex justify-between items-center text-xs text-slate-300">
                                                <span>{{ m.name }} {% if m.is_leader %}(Leader){% elif m.is_secretary %}(Secretary){% endif %}</span>
                                                <a href="/group/member/remove/{{ m.id }}" class="text-red-400">Remove</a>
                                            </div>
                                        {% else %}
                                            <p class="text-xs text-slate-500">No members assigned.</p>
                                        {% endfor %}
                                    </div>
                                </div>
                            {% else %}
                                <div class="glass-card p-8 text-center text-slate-400 text-sm">No project groups created yet.</div>
                            {% endfor %}
                        </div>
                    </div>

                {% elif sub_tab == 'group_grading' %}
                    <div class="glass-card p-6 rounded-2xl max-w-xl mx-auto">
                        <h3 class="font-bold text-lg text-cyan-300 mb-1">Award Group Project Score</h3>
                        <p class="text-xs text-slate-400 mb-6">Enter a title for this group task or project, select the group, and assign their score.</p>
                        <form action="/class/{{ current_class.id }}/group/grade/apply" method="POST" class="space-y-4">
                            <div>
                                <label class="block text-xs uppercase text-slate-400 font-semibold mb-1">Assessment / Task Title</label>
                                <input type="text" name="custom_title" required placeholder="e.g. Optics Lab Group Project" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                            </div>
                            <div>
                                <label class="block text-xs uppercase text-slate-400 font-semibold mb-1">Select Group</label>
                                <select name="group_id" required class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                    {% for g in current_class.groups %}
                                        <option value="{{ g.id }}">{{ g.name }} ({{ g.members|length }} Members)</option>
                                    {% endfor %}
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs uppercase text-slate-400 font-semibold mb-1">Group Score (0 - 100)</label>
                                <input type="number" step="0.1" name="score" required placeholder="e.g. 88.5" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                            </div>
                            <button type="submit" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-3 rounded-xl shadow transition text-sm">Apply Grade to Group Members</button>
                        </form>
                    </div>

                {% elif sub_tab == 'gradebook' %}
                    <div class="space-y-6">
                        <div class="glass-card p-6 rounded-2xl">
                            <form action="/class/{{ current_class.id }}/assignment/add" method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
                                <input type="text" name="title" required placeholder="Assessment Title" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                <select name="category" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                                    <option value="Homework">Homework</option>
                                    <option value="Lab Report">Lab Report</option>
                                    <option value="Quiz">Quiz</option>
                                    <option value="Exam">Exam</option>
                                    <option value="Group Project">Group Project</option>
                                </select>
                                <button type="submit" class="bg-cyan-600 text-white font-semibold py-3 rounded-xl text-sm">Add Assessment</button>
                            </form>
                        </div>
                        <div class="glass-card p-6 rounded-2xl overflow-x-auto">
                            <form action="/class/{{ current_class.id }}/grades/update" method="POST">
                                <table class="w-full text-left">
                                    <thead><tr class="border-b border-slate-800 text-xs text-slate-400 uppercase"><th class="p-3">Student</th>{% for a in current_class.assignments %}<th class="p-3">{{ a.title }}</th>{% endfor %}</tr></thead>
                                    <tbody class="divide-y divide-slate-800 text-sm">
                                        {% for s in current_class.students %}
                                            <tr>
                                                <td class="p-3 font-semibold text-slate-200">{{ s.name }}</td>
                                                {% for a in current_class.assignments %}
                                                    {% set ns = namespace(score='') %}
                                                    {% for g in s.grades %}{% if g.assignment_id == a.id %}{% set ns.score = g.score %}{% endif %}{% endfor %}
                                                    <td class="p-3"><input type="number" step="0.1" name="grade_{{ s.id }}_{{ a.id }}" value="{{ ns.score }}" class="w-20 bg-slate-950 border border-slate-700 rounded-xl p-2 text-center text-slate-100"></td>
                                                {% endfor %}
                                            </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                                {% if current_class.students and current_class.assignments %}
                                    <div class="mt-4 flex justify-end"><button type="submit" class="bg-emerald-600 text-white font-semibold px-6 py-2.5 rounded-xl text-sm">Save Grades</button></div>
                                {% endif %}
                            </form>
                        </div>
                    </div>

                {% elif sub_tab == 'attendance' %}
                    <div class="glass-card p-6 rounded-2xl max-w-xl">
                        <form action="/class/{{ current_class.id }}/attendance/save" method="POST" class="space-y-4">
                            <input type="date" name="date" value="{{ today }}" class="bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                            <table class="w-full text-left">
                                <thead><tr class="border-b border-slate-800 text-xs text-slate-400 uppercase"><th class="p-3">Student</th><th class="p-3 text-center">Status</th></tr></thead>
                                <tbody class="divide-y divide-slate-800 text-sm">
                                    {% for s in current_class.students %}
                                        {% set ns = namespace(status='Present') %}
                                        {% for att in s.attendance %}{% if att.date == today %}{% set ns.status = att.status %}{% endif %}{% endfor %}
                                        <tr>
                                            <td class="p-3 font-semibold text-slate-200">{{ s.name }}</td>
                                            <td class="p-3 text-center">
                                                <input type="hidden" name="status_{{ s.id }}" id="input_status_{{ s.id }}" value="{{ ns.status }}">
                                                <button type="button" onclick="toggleStatus({{ s.id }})" id="btn_status_{{ s.id }}" class="px-5 py-2 rounded-xl font-bold text-xs {% if ns.status == 'Present' %}bg-emerald-950 text-emerald-400 border border-emerald-700{% else %}bg-red-950 text-red-400 border border-red-700{% endif %}">
                                                    <span id="text_status_{{ s.id }}">{{ ns.status }}</span>
                                                </button>
                                            </td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                            {% if current_class.students %}
                                <div class="flex justify-end pt-4"><button type="submit" class="bg-cyan-600 text-white font-semibold px-6 py-2.5 rounded-xl text-sm">Save Roll Call</button></div>
                            {% endif %}
                        </form>
                        <script>
                            function toggleStatus(id) {
                                const inp = document.getElementById('input_status_' + id);
                                const btn = document.getElementById('btn_status_' + id);
                                const txt = document.getElementById('text_status_' + id);
                                if (inp.value === 'Present') {
                                    inp.value = 'Absent'; txt.innerText = 'Absent';
                                    btn.className = "px-5 py-2 rounded-xl font-bold text-xs bg-red-950 text-red-400 border border-red-700";
                                } else {
                                    inp.value = 'Present'; txt.innerText = 'Present';
                                    btn.className = "px-5 py-2 rounded-xl font-bold text-xs bg-emerald-950 text-emerald-400 border border-emerald-700";
                                }
                            }
                        </script>
                    </div>
                {% endif %}

            {% elif active_tab == 'communication' %}
                <div class="glass-card p-6 rounded-2xl max-w-xl mx-auto">
                    <h3 class="font-bold text-lg text-white mb-4">Communication Hub</h3>
                    <div class="space-y-4">
                        <select id="comm_student" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                            {% for s in all_students %}
                                {% if s.email %}
                                    <option value="{{ s.email }}">{{ s.name }} ({{ s.classroom.name }})</option>
                                {% endif %}
                            {% endfor %}
                        </select>
                        <input type="text" id="comm_subject" value="Physics Feedback" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">
                        <textarea id="comm_body" rows="4" class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-sm text-slate-100">Please review your latest assignment.</textarea>
                        <button onclick="window.location.href=`mailto:${document.getElementById('comm_student').value}?subject=${encodeURIComponent(document.getElementById('comm_subject').value)}&body=${encodeURIComponent(document.getElementById('comm_body').value)}`" class="w-full bg-cyan-600 text-white py-3 rounded-xl text-sm font-semibold">Open Email Client</button>
                    </div>
                </div>
            {% endif %}
        </main>
    </div>
</body>
</html>
"""

# --- ROUTES ---


@app.route('/')
def dashboard():
  classes = ClassRoom.query.all()
  return render_template_string(
      TEMPLATE,
      active_tab='dashboard',
      classes=classes,
      total_classes=len(classes),
      total_students=Student.query.count(),
  )


@app.route('/classes')
def classes():
  return render_template_string(
      TEMPLATE, active_tab='classes', classes=ClassRoom.query.all()
  )


@app.route('/classes/add', methods=['POST'])
def add_class():
  if request.form.get('name'):
    db.session.add(
        ClassRoom(
            name=request.form.get('name'),
            schedule=request.form.get('schedule'),
            room=request.form.get('room'),
        )
    )
    db.session.commit()
    flash('Class created successfully!', 'success')
  return redirect(url_for('classes'))


@app.route('/classes/delete/<int:id>')
def delete_class(id):
  db.session.delete(ClassRoom.query.get_or_404(id))
  db.session.commit()
  flash('Class deleted.', 'success')
  return redirect(url_for('classes'))


@app.route('/reports_hub')
def reports_hub():
  all_classes = ClassRoom.query.all()
  report_type = request.args.get('report_type', 'class')

  selected_class = ClassRoom.query.get(request.args.get('class_id', type=int)) or (
      all_classes[0] if all_classes else None
  )

  selected_student = None
  if selected_class and selected_class.students:
    student_id = request.args.get('student_id', type=int)
    if student_id:
      selected_student = Student.query.get(student_id)
    if not selected_student:
      selected_student = selected_class.students[0]

  class_stats = {
      'avg': 0,
      'pass_rate': 0,
      'high': 0,
      'low': 0,
      'dist': {
          'exc': 0,
          'prof': 0,
          'pass': 0,
          'risk': 0,
          'exc_pct': 0,
          'prof_pct': 0,
          'pass_pct': 0,
          'risk_pct': 0,
      },
  }

  if selected_class and selected_class.students:
    class_scores = []
    exc, prof, pass_count, risk = 0, 0, 0, 0
    for student in selected_class.students:
      s_total, s_count = 0, 0
      for assignment in selected_class.assignments:
        for g in student.grades:
          if g.assignment_id == assignment.id:
            s_total += g.score
            s_count += 1
            break
      if s_count > 0:
        avg_score = s_total / s_count
        class_scores.append(avg_score)
        if avg_score >= 80:
          exc += 1
        elif avg_score >= 60:
          prof += 1
        elif avg_score >= 50:
          pass_count += 1
        else:
          risk += 1

    total_graded = len(class_scores)
    if total_graded > 0:
      class_stats = {
          'avg': round(sum(class_scores) / total_graded, 1),
          'high': round(max(class_scores), 1),
          'low': round(min(class_scores), 1),
          'pass_rate': round(
              ((exc + prof + pass_count) / total_graded) * 100, 1
          ),
          'dist': {
              'exc': exc,
              'prof': prof,
              'pass': pass_count,
              'risk': risk,
              'exc_pct': round((exc / total_graded) * 100, 1),
              'prof_pct': round((prof / total_graded) * 100, 1),
              'pass_pct': round((pass_count / total_graded) * 100, 1),
              'risk_pct': round((risk / total_graded) * 100, 1),
          },
      }

  student_report = {'grades': [], 'avg': 0}
  if selected_student and selected_class:
    total, count = 0, 0
    s_grades = []
    for a in selected_class.assignments:
      score_val = 0
      for g in selected_student.grades:
        if g.assignment_id == a.id:
          score_val = g.score
          break
      s_grades.append(
          {'title': a.title, 'category': a.category, 'score': score_val}
      )
      total += score_val
      count += 1
    student_report = {
        'grades': s_grades,
        'avg': round(total / count, 1) if count > 0 else 0,
    }

  return render_template_string(
      TEMPLATE,
      active_tab='reports_hub',
      classes=all_classes,
      selected_class=selected_class,
      selected_student=selected_student,
      report_type=report_type,
      class_stats=class_stats,
      student_report=student_report,
  )


@app.route('/class/<int:class_id>')
def class_workspace(class_id):
  classroom = ClassRoom.query.get_or_404(class_id)

  # Query students and sort them alphabetically from A to Z
  sorted_students = (
      Student.query.filter_by(class_id=class_id)
      .order_by(Student.name.asc())
      .all()
  )

  return render_template_string(
      TEMPLATE,
      active_tab='class_workspace',
      current_class=classroom,
      students=sorted_students,  # Passes the alphabetically sorted list
      sub_tab=request.args.get('tab', 'students'),
      today=datetime.utcnow().strftime('%Y-%m-%d'),
  )


@app.route('/class/<int:class_id>/group/add', methods=['POST'])
def add_group(class_id):
  if request.form.get('group_name'):
    db.session.add(
        ProjectGroup(name=request.form.get('group_name'), class_id=class_id)
    )
    db.session.commit()
    flash('Project group created!', 'success')
  return redirect(url_for('class_workspace', class_id=class_id, tab='groups'))


@app.route('/group/delete/<int:id>')
def delete_group(id):
  g = ProjectGroup.query.get_or_404(id)
  c_id = g.class_id
  for m in g.members:
    m.group_id = None
    m.is_leader = False
    m.is_secretary = False
  db.session.delete(g)
  db.session.commit()
  flash('Group deleted.', 'success')
  return redirect(url_for('class_workspace', class_id=c_id, tab='groups'))


@app.route('/group/<int:group_id>/member/add', methods=['POST'])
def add_group_member(group_id):
  group = ProjectGroup.query.get_or_404(group_id)
  student = Student.query.get_or_404(int(request.form.get('student_id')))
  student.group_id = group.id
  role = request.form.get('role')
  if role == 'leader':
    for m in group.members:
      m.is_leader = False
    student.is_leader = True
    student.is_secretary = False
  elif role == 'secretary':
    for m in group.members:
      m.is_secretary = False
    student.is_secretary = True
    student.is_leader = False
  db.session.commit()
  flash(f'Assigned {student.name} to {group.name}!', 'success')
  return redirect(
      url_for('class_workspace', class_id=group.class_id, tab='groups')
  )


@app.route('/group/member/remove/<int:student_id>')
def remove_group_member(student_id):
  student = Student.query.get_or_404(student_id)
  c_id = student.class_id
  student.group_id = None
  student.is_leader = False
  student.is_secretary = False
  db.session.commit()
  flash('Member removed from group.', 'success')
  return redirect(url_for('class_workspace', class_id=c_id, tab='groups'))


@app.route('/class/<int:class_id>/group/grade/apply', methods=['POST'])
def apply_group_grade(class_id):
  custom_title = request.form.get('custom_title')
  group_id = request.form.get('group_id')
  score = request.form.get('score')

  if custom_title and group_id and score != '':
    group = ProjectGroup.query.get_or_404(int(group_id))
    score_val = float(score)

    assignment = Assignment.query.filter_by(
        title=custom_title, class_id=class_id
    ).first()
    if not assignment:
      assignment = Assignment(
          title=custom_title, category='Group Project', class_id=class_id
      )
      db.session.add(assignment)
      db.session.commit()

    for member in group.members:
      g_entry = Grade.query.filter_by(
          student_id=member.id, assignment_id=assignment.id
      ).first()
      if g_entry:
        g_entry.score = score_val
      else:
        db.session.add(
            Grade(
                student_id=member.id,
                assignment_id=assignment.id,
                score=score_val,
            )
        )

    db.session.commit()
    flash(
        f'Score of {score_val}% for "{custom_title}" applied to {group.name}!',
        'success',
    )

  return redirect(
      url_for('class_workspace', class_id=class_id, tab='group_grading')
  )


@app.route('/class/<int:class_id>/reports/batch_print')
def batch_print_reports(class_id):
  current_class = ClassRoom.query.get_or_404(class_id)
  today_date = datetime.utcnow().strftime('%Y-%m-%d')
  batch_reports = []
  for student in current_class.students:
    s_grades = []
    total_score, count = 0, 0
    for a in current_class.assignments:
      score_val = 0
      for g in student.grades:
        if g.assignment_id == a.id:
          score_val = g.score
          break
      s_grades.append(
          {'title': a.title, 'category': a.category, 'score': score_val}
      )
      total_score += score_val
      count += 1
    avg = round(total_score / count, 1) if count > 0 else 0
    batch_reports.append({
        'student': student,
        'grades': s_grades,
        'avg': avg,
        'attendance': student.attendance,
    })

  BATCH_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Batch Reports - {{ current_class.name }}</title><script src="https://cdn.tailwindcss.com"></script>
    <style>@media print { .page-break { page-break-after: always; } .no-print { display: none !important; } }</style></head>
    <body class="bg-white text-black p-8">
        <div class="no-print mb-6 p-4 bg-slate-100 rounded-xl flex justify-between items-center">
            <p class="font-bold text-slate-800">Batch Print Preview ({{ batch_reports|length }} Students)</p>
            <button onclick="window.print()" class="bg-emerald-600 text-white px-5 py-2.5 rounded-lg font-semibold text-sm">🖨️ Print / Save All as PDF</button>
        </div>
        {% for r in batch_reports %}
            <div class="border-2 border-slate-300 p-8 rounded-2xl mb-8 page-break">
                <div class="border-b-2 border-slate-300 pb-4 flex justify-between items-start">
                    <div>
                        <h1 class="text-2xl font-black text-slate-900">OFFICIAL ACADEMIC REPORT CARD</h1>
                        <p class="text-sm font-semibold text-slate-700">Physics Department &bull; {{ current_class.name }}</p>
                    </div>
                    <div class="text-right text-xs text-slate-500"><p>Date: {{ today }}</p></div>
                </div>
                <div class="grid grid-cols-4 gap-4 py-4 border-b border-slate-200 text-sm">
                    <div><span class="text-xs text-slate-500 uppercase font-bold">Student Name</span><p class="font-bold text-slate-900">{{ r.student.name }}</p></div>
                    <div><span class="text-xs text-slate-500 uppercase font-bold">Email</span><p class="text-medium text-slate-800 text-xs">{{ r.student.email or 'N/A' }}</p></div>
                    <div><span class="text-xs text-slate-500 uppercase font-bold">Group & Role</span><p class="text-medium text-slate-800 text-xs">{{ r.student.project_group.name if r.student.project_group else 'Unassigned' }} {% if r.student.is_leader %}(Leader){% elif r.student.is_secretary %}(Secretary){% endif %}</p></div>
                    <div><span class="text-xs text-slate-500 uppercase font-bold">Overall Average</span><p class="font-black text-emerald-600 text-lg">{{ r.avg }}%</p></div>
                </div>
                <div class="py-4">
                    <h3 class="font-bold text-xs uppercase tracking-wider text-slate-600 mb-2">Assessments</h3>
                    <table class="w-full text-left border-collapse text-sm">
                        <thead><tr class="border-b border-slate-300 text-xs uppercase text-slate-500"><th class="py-2">Title</th><th class="py-2">Category</th><th class="py-2 text-right">Score</th></tr></thead>
                        <tbody class="divide-y divide-slate-200">
                            {% for g in r.grades %}
                                <tr><td class="py-2 font-semibold text-slate-800">{{ g.title }}</td><td class="py-2 text-xs text-slate-600">{{ g.category }}</td><td class="py-2 text-right font-bold text-slate-900">{{ g.score }} / 100</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        {% endfor %}
    </body>
    </html>
    """
  return render_template_string(
      BATCH_TEMPLATE,
      current_class=current_class,
      batch_reports=batch_reports,
      today=today_date,
  )


@app.route('/class/<int:class_id>/student/add', methods=['POST'])
def add_student_to_class(class_id):
  if request.form.get('name'):
    db.session.add(
        Student(
            name=request.form.get('name'),
            email=request.form.get('email'),
            class_id=class_id,
            guardian_name=request.form.get('guardian_name'),
            guardian_phone=request.form.get('guardian_phone'),
        )
    )
    db.session.commit()
    flash('Student enrolled!', 'success')
  return redirect(url_for('class_workspace', class_id=class_id, tab='students'))


@app.route('/student/delete/<int:id>')
def delete_student(id):
  s = Student.query.get_or_404(id)
  c_id = s.class_id
  db.session.delete(s)
  db.session.commit()
  flash('Student removed.', 'success')
  return redirect(url_for('class_workspace', class_id=c_id, tab='students'))


@app.route('/class/<int:class_id>/assignment/add', methods=['POST'])
def add_assignment_to_class(class_id):
  if request.form.get('title'):
    db.session.add(
        Assignment(
            title=request.form.get('title'),
            category=request.form.get('category'),
            class_id=class_id,
        )
    )
    db.session.commit()
    flash('Assessment added!', 'success')
  return redirect(
      url_for('class_workspace', class_id=class_id, tab='gradebook')
  )


@app.route('/class/<int:class_id>/grades/update', methods=['POST'])
def update_class_grades(class_id):
  for key, value in request.form.items():
    if key.startswith('grade_') and value != '':
      parts = key.split('_')
      s_id, a_id = int(parts[1]), int(parts[2])
      try:
        val = float(value)
        g_entry = Grade.query.filter_by(
            student_id=s_id, assignment_id=a_id
        ).first()
        if g_entry:
          g_entry.score = val
        else:
          db.session.add(Grade(student_id=s_id, assignment_id=a_id, score=val))
      except ValueError:
        pass
  db.session.commit()
  flash('Grades saved!', 'success')
  return redirect(
      url_for('class_workspace', class_id=class_id, tab='gradebook')
  )


@app.route('/class/<int:class_id>/attendance/save', methods=['POST'])
def save_class_attendance(class_id):
  date = request.form.get('date')
  for key, value in request.form.items():
    if key.startswith('status_'):
      s_id = int(key.split('_')[1])
      existing = Attendance.query.filter_by(student_id=s_id, date=date).first()
      if existing:
        existing.status = value
      else:
        db.session.add(Attendance(student_id=s_id, date=date, status=value))
  db.session.commit()
  flash('Attendance saved!', 'success')
  return redirect(
      url_for('class_workspace', class_id=class_id, tab='attendance')
  )


@app.route('/communication')
def communication():
  return render_template_string(
      TEMPLATE, active_tab='communication', all_students=Student.query.all()
  )
# Create database tables at global scope so Gunicorn initializes SQLite on Render startup
with app.app_context():
  db.create_all()

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 5000))
  app.run(host='0.0.0.0', port=port, debug=True)
