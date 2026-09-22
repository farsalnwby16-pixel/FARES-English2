from flask import Flask, render_template_string, request, redirect, url_for, session, send_file
import json
import os
import sqlite3
from gtts import gTTS
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "fares_super_secret_key_change_this"

DB_FILE = "lessons.json"
USERS_DB = "users.db"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# إيميل وكلمة مرور الأدمن الخاصة بك يا مايسترو
ADMIN_EMAIL = "farsalnwby16@gmail.com"
ADMIN_PASSWORD = "farsalnwby16@gmail.com"

# إعداد قاعدة بيانات الطلاب
def init_db():
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        password TEXT,
                        progress TEXT DEFAULT '[]'
                    )''')
    conn.commit()
    conn.close()

init_db()

default_lessons = [
    {"id": 1, "level": "Level 1 (A1)", "order": 1, "title": "الدرس الأول: الحروف والتحيات", "description": "تعلم أساسيات نطق الحروف والتحيات اليومية.", "youtube_id": "tgbNymZ7vqY", "file": "", "transcript": [{"title": "التحية الصباحية", "en": "Hello, how are you?", "ar": "أهلاً، كيف حالك؟", "audio_type": "tts", "audio_val": "Hello, how are you?", "yt_url": ""}]},
    {"id": 2, "level": "Level 1 (A1)", "order": 2, "title": "الدرس الثاني: الأرقام والألوان", "description": "تعلم الأرقام وكيفية وصف الأشياء بالألوان.", "youtube_id": "tgbNymZ7vqY", "file": "", "transcript": [{"title": "الأرقام الأولى", "en": "One, two, three.", "ar": "واحد، اثنان، ثلاثة.", "audio_type": "tts", "audio_val": "One, two, three.", "yt_url": ""}]},
    {"id": 3, "level": "Level 2 (A2)", "order": 1, "title": "الدرس الأول: تكوين الجمل البسيطة", "description": "كيف تكون جملة مفيدة في المضارع البسيط.", "youtube_id": "tgbNymZ7vqY", "file": "", "transcript": [{"title": "جملة بسيطة", "en": "I speak English.", "ar": "أنا أتحدث الإنجليزية.", "audio_type": "tts", "audio_val": "I speak English.", "yt_url": ""}]}
]

def load_lessons():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default_lessons
    return default_lessons

def save_lessons(lessons):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(lessons, f, ensure_ascii=False, indent=4)

lessons_db = load_lessons()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>FARES ELNOBY Academy - منصة فارس النوبي</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; font-family: Tahoma, sans-serif; overflow-x: hidden; color: #333; }
        
        /* القائمة الجانبية بالوضع الدارك المطور والمنظم */
        .sidebar { background: #212529; color: #f8f9fa; min-height: 100vh; padding: 20px; border-left: 1px solid #343a40; transition: all 0.3s ease; box-shadow: 2px 0 5px rgba(0,0,0,0.2); }
        .sidebar.hidden { display: none; }
        .sidebar h3, .sidebar h5 { color: #f8f9fa !important; }
        .sidebar p.text-muted { color: #adb5bd !important; }
        .sidebar a { color: #ced4da; text-decoration: none; display: block; padding: 6px 12px; border-radius: 4px; margin-bottom: 4px; background: #343a40; border: 1px solid #495057; }
        .sidebar a:hover, .sidebar a.active { background: #d4af37; color: #000; border-color: #d4af37; font-weight: bold; }
        .sidebar .badge.bg-secondary { background-color: #495057 !important; color: #fff; }
        
        .video-container { position: relative; width: 100%; padding-bottom: 56.25%; height: 0; background: #000; border-radius: 8px; overflow: hidden; }
        .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
    </style>
</head>
<body>
<div class="container-fluid">
    <div class="row">
        {% if session.get('user_email') or session.get('is_admin') %}
        <!-- القائمة الجانبية (Dark Mode) -->
        <div id="sidebarMenu" class="col-md-3 sidebar">
            <button class="btn btn-sm btn-outline-light w-100 mb-3 fw-bold" onclick="toggleSidebar()">📂 إخفاء / إظهار القائمة</button>
            <h3 class="text-white">🌟 FARES ELNOBY</h3>
            <p class="text-muted small">منهج متكامل من A1 إلى C2</p>
            
            <!-- حساب الطالب -->
            <div class="mb-3 p-2 bg-dark rounded border border-secondary">
                <span class="small d-block text-truncate mb-1 fw-bold text-warning">👤 {{ session.get('user_email') }}</span>
                <a href="/logout" class="btn btn-sm btn-outline-danger w-100 py-0 fw-bold">تسجيل الخروج</a>
            </div>

            <!-- أزرار تحكم الأدمن -->
            <div class="mb-3">
                {% if session.get('is_admin') %}
                    <a href="/admin_logout" class="btn btn-sm btn-outline-danger w-100 fw-bold">🚪 خروج لوحة الأدمن</a>
                {% else %}
                    <a href="/admin_login_page" class="btn btn-sm btn-outline-light w-100 fw-bold">🔐 دخول الأدمن بالإيميل</a>
                {% endif %}
            </div>

            <!-- عداد التقدم الديناميكي -->
            <div class="card bg-dark text-light p-2 mb-3 border border-secondary">
                <div class="d-flex justify-content-between small mb-1 fw-bold">
                    <span>التقدم: {{ completed_count }}/{{ total_lessons }}</span>
                    <span>{{ progress_percent }}%</span>
                </div>
                <div class="progress" style="height: 8px; background-color: #495057;">
                    <div class="progress-bar bg-warning" role="progressbar" style="width: {{ progress_percent }}%;"></div>
                </div>
            </div>

            <!-- زر الشهادة المشروط ومعاينة الشهادة -->
            <div class="mb-3 d-grid gap-2">
                {% if progress_percent >= 100 %}
                    <a href="/certificate_form" class="btn btn-warning fw-bold text-dark shadow-sm">🏆 استلام الشهادة المعتمدة</a>
                {% else %}
                    <button class="btn btn-secondary fw-bold text-light" disabled>🔒 الشهادة مقفولة (أكمل 100%)</button>
                {% endif %}
                <a href="/preview_certificate" class="btn btn-outline-warning btn-sm fw-bold">✨ معاينة الشهادة الملكية</a>
            </div>
            <hr class="border-secondary">

            {% for lvl, lessons in levels.items() %}
                <div class="d-flex justify-content-between align-items-center mt-3">
                    <h5 class="text-warning m-0 fw-bold" style="font-size: 0.95rem;">{{ lvl }}</h5>
                    {% if session.get('is_admin') %}
                        <a href="/add_lesson_page?level={{ lvl }}" class="btn btn-sm btn-success px-2 py-0 fw-bold" title="إضافة درس جديد">+ إضافة</a>
                    {% endif %}
                </div>
                <div class="mt-2">
                    {% for l in lessons %}
                        <a href="/?lesson_id={{ l.id }}" class="d-flex justify-content-between align-items-center {% if current and current.id == l.id %}active{% endif %}">
                            <div>
                                <span class="badge bg-secondary me-1">{{ l.order }}</span> {{ l.title }}
                            </div>
                            {% if l.id in completed_ids %}
                                <span class="text-success fw-bold">✓</span>
                            {% endif %}
                        </a>
                    {% endfor %}
                </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- محتوى الصفحة الرئيسية -->
        <div id="mainContent" class="{% if not session.get('user_email') and not session.get('is_admin') %}col-12{% else %}col-md-9{% endif %} p-4">
            
            {% if session.get('user_email') or session.get('is_admin') %}
                {% if not show_add_page %}
                    <button class="btn btn-outline-dark mb-3 fw-bold" onclick="toggleSidebar()">📂 إخفاء / إظهار القائمة</button>
                {% endif %}
            {% endif %}

            <!-- صفحة تسجيل الدخول / إنشاء حساب للطالب -->
            {% if show_auth_page %}
            <div class="container mt-5" style="max-width: 450px;">
                <div class="card p-4 shadow bg-white border-0 rounded-4">
                    <h2 class="text-primary mb-2 text-center fw-bold">🌟 FARES ELNOBY Academy</h2>
                    <p class="text-muted text-center small mb-4">يجب تسجيل الدخول أو إنشاء حساب جديد للوصول للمنصة والدروس</p>
                    
                    {% if auth_error %}
                        <div class="alert alert-danger py-2 small text-center">{{ auth_error }}</div>
                    {% endif %}
                    
                    <form action="/handle_auth" method="POST">
                        <div class="mb-3">
                            <label class="form-label fw-bold">البريد الإلكتروني:</label>
                            <input type="email" name="email" class="form-control" required placeholder="name@example.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">كلمة المرور:</label>
                            <input type="password" name="password" class="form-control" required placeholder="أدخل كلمة المرور">
                        </div>
                        <div class="d-flex gap-2">
                            <button type="submit" name="action" value="login" class="btn btn-primary w-50 fw-bold">تسجيل الدخول</button>
                            <button type="submit" name="action" value="register" class="btn btn-success w-50 fw-bold">حساب جديد</button>
                        </div>
                    </form>
                    
                    <div class="text-center mt-3">
                        <a href="/admin_login_page" class="text-muted small text-decoration-none">🔐 دخول الأدمن</a>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- صفحة تسجيل دخول الأدمن -->
            {% if show_login_page %}
            <div class="container mt-5" style="max-width: 400px;">
                <div class="card p-4 shadow bg-white">
                    <h3 class="text-primary mb-3 text-center">🔐 دخول الأدمن</h3>
                    {% if login_error %}
                        <div class="alert alert-danger py-2 small text-center">الإيميل أو كلمة المرور غير صحيحة!</div>
                    {% endif %}
                    <form action="/admin_login" method="POST">
                        <div class="mb-3">
                            <label class="form-label fw-bold">البريد الإلكتروني:</label>
                            <input type="email" name="email" class="form-control" required value="farsalnwby16@gmail.com">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">كلمة المرور:</label>
                            <input type="password" name="password" class="form-control" required placeholder="أدخل كلمة المرور">
                        </div>
                        <button type="submit" class="btn btn-primary w-100 fw-bold">دخول الأدمن</button>
                        <a href="/" class="btn btn-secondary w-100 mt-2">العودة</a>
                    </form>
                </div>
            </div>
            {% endif %}

            <!-- عرض الدرس الحالي -->
            {% if current and (session.get('user_email') or session.get('is_admin')) and not show_add_page %}
                <div class="card shadow-sm p-4 mb-4 bg-white border-0">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h2 class="text-dark m-0">{{ current.title }}</h2>
                        <div>
                            {% if current.id in completed_ids %}
                                <span class="badge bg-success p-2">✓ تم إنجاز هذا الدرس</span>
                            {% else %}
                                <a href="/complete_lesson?lesson_id={{ current.id }}" class="btn btn-outline-success btn-sm fw-bold">☑️ تحديد كمكتمل وإضافته للتقدم</a>
                            {% endif %}
                        </div>
                    </div>
                    <p class="text-muted">{{ current.description }}</p>

                    <div class="video-container mb-3">
                        <iframe src="https://www.youtube-nocookie.com/embed/{{ current.youtube_id }}?rel=0&modestbranding=1"
                                title="YouTube video player"
                                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                allowfullscreen>
                        </iframe>
                    </div>

                    <div class="text-center mb-3">
                        <a href="https://www.youtube.com/watch?v={{ current.youtube_id }}" target="_blank" class="btn btn-outline-danger btn-sm">
                            🔴 مشاهدة الفيديو مباشرة على يوتيوب
                        </a>
                    </div>

                    <!-- مرفقات الدرس -->
                    {% if current.file %}
                    <div class="alert alert-info d-flex justify-content-between align-items-center">
                        <span>📎 ملحق مرفق مع هذا الدرس: <strong>{{ current.file }}</strong></span>
                        <a href="/download_file/{{ current.file }}" class="btn btn-sm btn-info text-white fw-bold">تحميل المرفق</a>
                    </div>
                    {% endif %}

                    <!-- لوحة تحكم الأدمن للدرس -->
                    {% if session.get('is_admin') %}
                    <div class="card bg-light p-3 border-info mb-3">
                        <h5 class="text-primary" style="font-size: 1.1rem;">⚙️ لوحة الأدمن: تعديل الدرس ورفع ملفات</h5>
                        <form action="/update_fares_video" method="POST" enctype="multipart/form-data" class="row g-3 mt-1">
                            <input type="hidden" name="lesson_id" value="{{ current.id }}">
                            <div class="col-md-8">
                                <label class="form-label fw-bold small">عنوان الدرس:</label>
                                <input type="text" name="lesson_title" class="form-control form-control-sm" value="{{ current.title }}" required>
                            </div>
                            <div class="col-md-4">
                                <label class="form-label fw-bold small">رقم الترتيب:</label>
                                <input type="number" name="lesson_order" class="form-control form-control-sm" value="{{ current.order }}" min="1" required>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-bold small">رابط يوتيوب الجديد (اختياري):</label>
                                <input type="text" name="youtube_url" class="form-control form-control-sm" placeholder="تحديث رابط يوتيوب">
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-bold small">رفع ملف شرح أو PDF:</label>
                                <input type="file" name="lesson_file" class="form-control form-control-sm">
                            </div>
                            <div class="col-md-12 text-end">
                                <button type="submit" class="btn btn-success btn-sm px-4 fw-bold">حفظ التعديلات والمرفقات</button>
                            </div>
                        </form>
                    </div>
                    {% endif %}

                    <div class="d-flex justify-content-between mt-3">
                        {% if prev_id %}
                            <a href="/?lesson_id={{ prev_id }}" class="btn btn-outline-secondary">⬅️ الدرس السابق</a>
                        {% else %}
                            <div></div>
                        {% endif %}
                        {% if next_id %}
                            <a href="/?lesson_id={{ next_id }}" class="btn btn-primary">الدرس التالي ➡️</a>
                        {% endif %}
                    </div>
                </div>

                <!-- نصوص الاستماع والشادوينج المتطورة -->
                <div class="card shadow-sm p-4 bg-white border-0">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h4 class="text-dark m-0">🎧 نصوص الاستماع والشادوينج (Speech & Audio)</h4>
                        {% if session.get('is_admin') %}
                            <button class="btn btn-sm btn-success fw-bold" data-bs-toggle="modal" data-bs-target="#addTranscriptModal">➕ إضافة عنصر استماع/شادوينج جديد</button>
                        {% endif %}
                    </div>
                    
                    <div class="list-group list-group-flush">
                        {% for item in current.transcript %}
                            <div class="list-group-item bg-transparent py-3 border-bottom">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        {% if item.title %}
                                            <span class="badge bg-primary mb-1">{{ item.title }}</span><br>
                                        {% endif %}
                                        <span class="fw-bold text-dark fs-5">{{ item.en }}</span><br>
                                        <small class="text-muted">{{ item.ar }}</small>
                                    </div>
                                    <div>
                                        {% if item.audio_type == 'local' and item.audio_val %}
                                            <audio controls src="/download_file/{{ item.audio_val }}" style="height: 38px;"></audio>
                                        {% else %}
                                            <audio controls src="/tts?text={{ item.audio_val | default(item.en) }}" style="height: 38px;"></audio>
                                        {% endif %}
                                    </div>
                                </div>
                                {% if item.yt_url %}
                                    <div class="mt-2">
                                        <a href="{{ item.yt_url }}" target="_blank" class="btn btn-outline-danger btn-sm">🔴 مشاهدة فيديو يوتيوب المرتبط بهذه الفقرة</a>
                                    </div>
                                {% endif %}
                            </div>
                        {% endfor %}
                    </div>
                </div>
            {% endif %}

            <!-- صفحة إضافة درس -->
            {% if show_add_page and session.get('is_admin') %}
            <div class="container mt-4">
                <div class="card p-4 shadow bg-white">
                    <h3 class="text-success mb-3">➕ إضافة درس جديد للمستوى: {{ target_level }}</h3>
                    <form action="/save_new_lesson" method="POST" enctype="multipart/form-data">
                        <input type="hidden" name="level" value="{{ target_level }}">
                        <div class="mb-3">
                            <label class="form-label fw-bold">عنوان الدرس:</label>
                            <input type="text" name="title" class="form-control" required placeholder="مثال: الدرس الثالث: الأزمنة">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">رابط يوتيوب:</label>
                            <input type="text" name="youtube_url" class="form-control" required placeholder="https://www.youtube.com/watch?v=...">
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">وصف الدرس:</label>
                            <textarea name="description" class="form-control" rows="3" placeholder="وصف مختصر..."></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">رفع ملف شرح أو PDF (اختياري):</label>
                            <input type="file" name="lesson_file" class="form-control">
                        </div>
                        <button type="submit" class="btn btn-success fw-bold px-4">حفظ وإضافة الدرس</button>
                        <a href="/" class="btn btn-secondary ms-2">إلغاء</a>
                    </form>
                </div>
            </div>
            {% endif %}

        </div>
    </div>
</div>

<!-- Modal إضافة عنصر استماع أو شادوينج متطور للأدمن -->
{% if session.get('is_admin') and current %}
<div class="modal fade" id="addTranscriptModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">➕ إضافة شادوينج أو استماع متطور</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form action="/add_transcript" method="POST" enctype="multipart/form-data">
                <div class="modal-body">
                    <input type="hidden" name="lesson_id" value="{{ current.id }}">
                    <div class="mb-3">
                        <label class="form-label fw-bold">عنوان العنصر / الفقرة:</label>
                        <input type="text" name="title" class="form-control" placeholder="مثال: التدريب الأول على النطق">
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">النص بالإنجليزية:</label>
                        <input type="text" name="text_en" class="form-control" required placeholder="Example: How are you doing?">
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">الترجمة بالعربية:</label>
                        <input type="text" name="text_ar" class="form-control" required placeholder="مثال: كيف حالك؟">
                    </div>
                    <hr>
                    <div class="mb-3">
                        <label class="form-label fw-bold text-success">مصدر الصوت (اختر واحداً فقط):</label>
                        <select name="audio_choice" class="form-select mb-2" onchange="toggleAudioInputs(this.value)">
                            <option value="tts">توليد صوت تلقائي (Text-to-Speech)</option>
                            <option value="local">رفع ملف صوتي محلي (MP3 / WAV)</option>
                        </select>
                        
                        <div id="localAudioDiv" style="display:none;" class="mt-2">
                            <label class="form-label small fw-bold">اختر الملف الصوتي:</label>
                            <input type="file" name="audio_file" class="form-control form-control-sm" accept="audio/*">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">رابط يوتيوب مرتبط (اختياري):</label>
                        <input type="text" name="yt_url" class="form-control" placeholder="https://www.youtube.com/watch?v=...">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">إلغاء</button>
                    <button type="submit" class="btn btn-success fw-bold">حفظ وإضافة العنصر</button>
                </div>
            </form>
        </div>
    </div>
</div>
<script>
    function toggleAudioInputs(val) {
        const localDiv = document.getElementById("localAudioDiv");
        if(val === "local") {
            localDiv.style.display = "block";
        } else {
            localDiv.style.display = "none";
        }
    }
</script>
{% endif %}

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    function toggleSidebar() {
        const sidebar = document.getElementById("sidebarMenu");
        const mainContent = document.getElementById("mainContent");
        if (sidebar && mainContent) {
            if (sidebar.classList.contains("hidden")) {
                sidebar.classList.remove("hidden");
                mainContent.classList.remove("col-md-12");
                mainContent.classList.add("col-md-9");
            } else {
                sidebar.classList.add("hidden");
                mainContent.classList.remove("col-md-9");
                mainContent.classList.add("col-md-12");
            }
        }
    }
</script>
</body>
</html>
"""

@app.route("/")
def index():
    if not session.get('user_email') and not session.get('is_admin'):
        return redirect(url_for("login_page"))

    global lessons_db
    lessons_db = load_lessons()
    
    lesson_id = request.args.get("lesson_id", type=int)
    current = None
    if lesson_id:
        current = next((l for l in lessons_db if l["id"] == lesson_id), None)
    if not current and lessons_db:
        current = lessons_db[0]

    levels = {
        "Level 1 (A1)": [], "Level 2 (A2)": [],
        "Level 3 (B1)": [], "Level 4 (B2)": [],
        "Level 5 (C1)": [], "Level 6 (C2)": []
    }
    
    for l in lessons_db:
        lvl = l.get("level", "Level 1 (A1)")
        if lvl not in levels:
            levels[lvl] = []
        levels[lvl].append(l)

    completed_lessons = []
    user_email = session.get('user_email')
    if user_email and user_email != "Admin":
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT progress FROM users WHERE email = ?", (user_email,))
        row = cursor.fetchone()
        conn.close()
        if row and row[0]:
            try:
                completed_lessons = json.loads(row[0])
            except:
                completed_lessons = []

    total_lessons = len(lessons_db)
    completed_count = len(completed_lessons)
    progress_percent = int((completed_count / total_lessons) * 100) if total_lessons > 0 else 0

    all_ids = [l["id"] for l in lessons_db]
    curr_idx = all_ids.index(current["id"]) if current and current["id"] in all_ids else 0
    prev_id = all_ids[curr_idx - 1] if curr_idx > 0 else None
    next_id = all_ids[curr_idx + 1] if curr_idx < len(all_ids) - 1 else None

    return render_template_string(
        HTML_TEMPLATE,
        levels=levels,
        current=current,
        total_lessons=total_lessons,
        completed_count=completed_count,
        progress_percent=progress_percent,
        completed_ids=completed_lessons,
        prev_id=prev_id,
        next_id=next_id,
        show_add_page=False,
        show_login_page=False,
        show_auth_page=False
    )

@app.route("/login_page")
def login_page():
    error = request.args.get("error", "")
    return render_template_string(HTML_TEMPLATE, levels={}, current=None, show_auth_page=True, auth_error=error, total_lessons=len(lessons_db), completed_count=0, progress_percent=0, completed_ids=[])

@app.route("/handle_auth", methods=["POST"])
def handle_auth():
    email = request.form.get("email")
    password = request.form.get("password")
    action = request.form.get("action")
    
    conn = sqlite3.connect(USERS_DB)
    cursor = conn.cursor()
    
    if action == "register":
        try:
            cursor.execute("INSERT INTO users (email, password, progress) VALUES (?, ?, ?)", (email, password, json.dumps([])))
            conn.commit()
            session['user_email'] = email
        except:
            conn.close()
            return redirect(url_for("login_page", error="البريد الإلكتروني مسجل مسبقاً!"))
    else:
        cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            session['user_email'] = email
        else:
            conn.close()
            return redirect(url_for("login_page", error="خطأ في البريد أو كلمة المرور!"))
            
    conn.close()
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop('user_email', None)
    session.pop('is_admin', None)
    return redirect(url_for("login_page"))

@app.route("/admin_login_page")
def admin_login_page():
    error = request.args.get("error", 0, type=int)
    return render_template_string(HTML_TEMPLATE, levels={}, current=None, show_add_page=False, show_login_page=True, login_error=error, total_lessons=len(lessons_db), completed_count=0, progress_percent=0, completed_ids=[])

@app.route("/admin_login", methods=["POST"])
def admin_login():
    email = request.form.get("email")
    pwd = request.form.get("password")
    if email == ADMIN_EMAIL and pwd == ADMIN_PASSWORD:
        session['is_admin'] = True
        session['user_email'] = "Admin"
        return redirect(url_for("index"))
    else:
        return redirect(url_for("admin_login_page", error=1))

@app.route("/admin_logout")
def admin_logout():
    session.pop('is_admin', None)
    session.pop('user_email', None)
    return redirect(url_for("login_page"))

@app.route("/complete_lesson")
def complete_lesson():
    user_email = session.get('user_email')
    if not user_email:
        return redirect(url_for("login_page", error="يجب تسجيل الدخول لحفظ تقدمك!"))
    if session.get('is_admin'):
        return redirect(url_for("index", lesson_id=request.args.get("lesson_id", type=int)))
        
    lesson_id = request.args.get("lesson_id", type=int)
    if lesson_id:
        conn = sqlite3.connect(USERS_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT progress FROM users WHERE email = ?", (user_email,))
        row = cursor.fetchone()
        if row:
            try:
                prog = json.loads(row[0])
            except:
                prog = []
            if lesson_id not in prog:
                prog.append(lesson_id)
                cursor.execute("UPDATE users SET progress = ? WHERE email = ?", (json.dumps(prog), user_email))
                conn.commit()
        conn.close()
    return redirect(url_for("index", lesson_id=lesson_id))

@app.route("/tts")
def tts():
    text = request.args.get("text", "Hello")
    tts_obj = gTTS(text=text, lang='en', slow=False)
    filepath = "temp_audio.mp3"
    tts_obj.save(filepath)
    return send_file(filepath, mimetype="audio/mp3")

@app.route("/download_file/<filename>")
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

@app.route("/add_lesson_page")
def add_lesson_page():
    if not session.get('is_admin'):
        return redirect(url_for("index"))
    global lessons_db
    lessons_db = load_lessons()
    target_level = request.args.get("level", "Level 1 (A1)")
    return render_template_string(HTML_TEMPLATE, levels={}, current=None, show_add_page=True, show_login_page=False, target_level=target_level, progress_percent=0, total_lessons=len(lessons_db), completed_count=0, completed_ids=[])

@app.route("/save_new_lesson", methods=["POST"])
def save_new_lesson():
    if not session.get('is_admin'):
        return redirect(url_for("index"))
    global lessons_db
    lessons_db = load_lessons()
    
    title = request.form.get("title")
    level = request.form.get("level")
    desc = request.form.get("description")
    yt_url = request.form.get("youtube_url", "")
    
    filename = ""
    file = request.files.get("lesson_file")
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    yt_id = "tgbNymZ7vqY"
    if "v=" in yt_url:
        yt_id = yt_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in yt_url:
        yt_id = yt_url.split("youtu.be/")[1].split("?")[0]

    new_id = max([l["id"] for l in lessons_db], default=0) + 1
    new_lesson = {
        "id": new_id,
        "level": level,
        "order": len([l for l in lessons_db if l["level"] == level]) + 1,
        "title": title,
        "description": desc,
        "youtube_id": yt_id,
        "file": filename,
        "transcript": [{"title": "الترحيب", "en": "Welcome to this new lesson.", "ar": "أهلاً بك في هذا الدرس.", "audio_type": "tts", "audio_val": "Welcome to this new lesson.", "yt_url": ""}]
    }
    lessons_db.append(new_lesson)
    save_lessons(lessons_db)
    return redirect(url_for("index", lesson_id=new_id))

@app.route("/add_transcript", methods=["POST"])
def add_transcript():
    if not session.get('is_admin'):
        return redirect(url_for("index"))
    global lessons_db
    lessons_db = load_lessons()
    
    lesson_id = int(request.form.get("lesson_id"))
    title = request.form.get("title", "")
    text_en = request.form.get("text_en")
    text_ar = request.form.get("text_ar")
    audio_choice = request.form.get("audio_choice")
    yt_url = request.form.get("yt_url", "")
    
    audio_val = text_en
    audio_type = "tts"
    
    if audio_choice == "local":
        file = request.files.get("audio_file")
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            audio_val = filename
            audio_type = "local"
            
    for l in lessons_db:
        if l["id"] == lesson_id:
            if "transcript" not in l:
                l["transcript"] = []
            l["transcript"].append({
                "title": title,
                "en": text_en,
                "ar": text_ar,
                "audio_type": audio_type,
                "audio_val": audio_val,
                "yt_url": yt_url
            })
            break
            
    save_lessons(lessons_db)
    return redirect(url_for("index", lesson_id=lesson_id))

@app.route("/update_fares_video", methods=["POST"])
def update_fares_video():
    if not session.get('is_admin'):
        return redirect(url_for("index"))
    global lessons_db
    lessons_db = load_lessons()
    
    lesson_id = int(request.form.get("lesson_id"))
    title = request.form.get("lesson_title")
    order = int(request.form.get("lesson_order"))
    yt_url = request.form.get("youtube_url", "")
    file = request.files.get("lesson_file")
    
    for l in lessons_db:
        if l["id"] == lesson_id:
            l["title"] = title
            l["order"] = order
            if yt_url.strip():
                if "v=" in yt_url:
                    l["youtube_id"] = yt_url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in yt_url:
                    l["youtube_id"] = yt_url.split("youtu.be/")[1].split("?")[0]
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                l["file"] = filename
            break
            
    save_lessons(lessons_db)
    return redirect(url_for("index", lesson_id=lesson_id))

@app.route("/certificate_form")
def certificate_form():
    default_name = session.get('user_email', 'Student Name')
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>إصدار شهادة الإنجاز - FARES ELNOBY</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body style="background: #111; height: 100vh; display: flex; align-items: center; justify-content: center; font-family: Tahoma, sans-serif;">
        <div class="card p-4 shadow bg-dark text-light border border-warning" style="width: 450px; border-radius: 12px;">
            <h3 class="text-warning text-center mb-3">🎓 إصدار الشهادة الملكية</h3>
            <p class="text-muted small text-center mb-4">أدخل الاسم بالطريقة التي تريدها أن تظهر رسمياً على الشهادة:</p>
            <form action="/certificate" method="GET">
                <div class="mb-3">
                    <label class="form-label fw-bold text-light">الاسم الثلاثي أو اللقب:</label>
                    <input type="text" name="name" class="form-control form-control-lg bg-secondary text-white border-secondary" required value="{default_name}" placeholder="مثال: فارس أحمد النوبي">
                </div>
                <button type="submit" class="btn btn-warning w-100 fw-bold py-2 text-dark">✨ إصدار وعرض الشهادة الفاخرة</button>
                <a href="/" class="btn btn-outline-light w-100 mt-2">العودة للدروس</a>
            </form>
        </div>
    </body>
    </html>
    """

@app.route("/certificate")
def certificate():
    name = request.args.get("name", "Student")
    return luxury_certificate_html(name, is_preview=False)

@app.route("/preview_certificate")
def preview_certificate():
    user_name = session.get('user_email', 'Fares Elnoby (معاينة)')
    return luxury_certificate_html(user_name, is_preview=True)

def luxury_certificate_html(name, is_preview=False):
    preview_banner = '<div style="background: #d4af37; color: #000; padding: 8px; font-weight: bold; text-align: center; font-size: 14px; margin-bottom: 20px; border-radius: 4px;">✨ معاينة الشهادة الملكية (FARES ELNOBY Academy) ✨</div>' if is_preview else ''
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>شهادة اعتماد - FARES ELNOBY</title>
        <style>
            body {{
                background-color: #111;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                font-family: 'Times New Roman', Times, serif;
            }}
            .cert-container {{
                width: 950px;
                background: #fdfbf7;
                border: 12px solid #b8860b;
                padding: 40px;
                box-shadow: 0 0 30px rgba(212, 175, 55, 0.4);
                position: relative;
                box-sizing: border-box;
                text-align: center;
            }}
            .inner-border {{
                border: 2px solid #d4af37;
                padding: 30px;
                position: relative;
            }}
            /* العلامة المائية */
            .watermark {{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-30deg);
                font-size: 85px;
                color: rgba(184, 134, 11, 0.05);
                font-weight: bold;
                z-index: 0;
                white-space: nowrap;
                pointer-events: none;
            }}
            .content {{
                position: relative;
                z-index: 1;
            }}
            h1 {{
                font-size: 42px;
                color: #b8860b;
                margin-bottom: 5px;
                text-transform: uppercase;
                letter-spacing: 2px;
            }}
            .subtitle {{
                font-size: 18px;
                color: #555;
                margin-bottom: 25px;
                letter-spacing: 1px;
            }}
            .presented {{
                font-size: 20px;
                color: #333;
                font-style: italic;
                margin-bottom: 15px;
            }}
            .student-name {{
                font-size: 45px;
                color: #1a1a1a;
                border-bottom: 3px solid #d4af37;
                display: inline-block;
                padding: 0 40px;
                margin: 10px 0 25px 0;
                font-weight: bold;
                font-family: 'Georgia', serif;
            }}
            .description {{
                font-size: 18px;
                color: #444;
                line-height: 1.6;
                max-width: 700px;
                margin: 0 auto 40px auto;
            }}
            .footer-section {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 50px;
                padding: 0 30px;
            }}
            .signature-box {{
                text-align: center;
            }}
            .signature-line {{
                width: 220px;
                border-top: 2px solid #333;
                margin: 0 auto 8px auto;
            }}
            .sig-name {{
                font-weight: bold;
                font-size: 18px;
                color: #b8860b;
            }}
            .sig-title {{
                font-size: 14px;
                color: #666;
            }}
            .badge-seal {{
                width: 100px;
                height: 100px;
                border: 4px solid #b8860b;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #fff, #f3e5ab);
                color: #b8860b;
                font-weight: bold;
                font-size: 13px;
                text-align: center;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
                line-height: 1.2;
            }}
            .back-btn {{
                margin-top: 30px;
                display: inline-block;
                padding: 12px 30px;
                background: #b8860b;
                color: #fff;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                font-family: Tahoma, sans-serif;
            }}
        </style>
    </head>
    <body>
        <div style="text-align:center;">
            {preview_banner}
            <div class="cert-container">
                <div class="watermark">FARES ELNOBY</div>
                <div class="inner-border">
                    <div class="content">
                        <div style="font-size: 20px; font-weight: bold; color: #b8860b; margin-bottom: 10px;">FARES ELNOBY ACADEMY</div>
                        <h1>Certificate of Completion</h1>
                        <div class="subtitle">شهادة إنجاز واجتياز معتمدة</div>
                        
                        <div class="presented">تمنح هذه الشهادة بكل فخر إلى المتدرب / المتدربة</div>
                        <div class="student-name">{name}</div>
                        
                        <div class="description">
                            لاجتيازه بنجاح وكفاءة تامة كافة المستويات والتدريبات المتكاملة في منصة <strong>FARES ELNOBY</strong> لتعلم اللغة الإنجليزية ونظام الشادوينج والمحادثة (من المستوى الأول A1 وحتى الاحتراف C2).
                        </div>
                        
                        <div class="footer-section">
                            <div class="signature-box">
                                <div class="signature-line"></div>
                                <div class="sig-name">Fares Elnoby</div>
                                <div class="sig-title">Founder & Instructor</div>
                            </div>
                            
                            <div class="badge-seal">
                                VERIFIED<br>&<br>APPROVED
                            </div>
                            
                            <div class="signature-box">
                                <div class="signature-line"></div>
                                <div class="sig-name">Academy Seal</div>
                                <div class="sig-title">Official Stamp</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <br>
            <a href="/" class="back-btn">العودة للمنصة الرئيسية</a>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
