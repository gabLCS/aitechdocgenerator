from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
from logging_config import get_custom_logger

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "flask_secret_key")
API_URL = "http://127.0.0.1:8000"

logger = get_custom_logger("initialization", "initialization.log")

def run_startup_checks():
    logger.info("==========================================")
    logger.info("Initializing Flask Frontend Application...")
    
    # 1. Dependency checks
    logger.info("Checking critical packages dependencies...")
    dependencies = [
        ("flask", "Flask"),
        ("requests", "Requests"),
        ("jinja2", "Jinja2")
    ]
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            logger.info(f"Dependency '{package_name}' is verified.")
        except ImportError as e:
            logger.error(f"Dependency '{package_name}' import failed: {e}")
            
    # 2. Check Backend Server Connectivity
    logger.info(f"Checking connection to Backend Service at '{API_URL}'...")
    try:
        resp = requests.get(API_URL, timeout=3.0)
        if resp.status_code == 200:
            logger.info(f"Backend Service is active and responsive. Response: {resp.json()}")
        else:
            logger.warning(f"Backend Service responded with unexpected status code: {resp.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend Service Connection failed. Ensure backend is running at '{API_URL}': {e}")
        
    # 3. Security configurations check
    logger.info("Checking configurations...")
    if app.secret_key == "flask_secret_key":
        logger.warning("Application is using default 'flask_secret_key' for session signing. Ensure this is changed in production.")
    else:
        logger.info("Session secret key check completed.")
        
    logger.info("Frontend Application initialization process completed.")
    logger.info("==========================================")

# Execute startup verifications on load
run_startup_checks()

@app.route("/")
def index():
    if "access_token" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        try:
            response = requests.post(f"{API_URL}/auth/token", data={"username": email, "password": password})
            
            if response.status_code == 200:
                token_data = response.json()
                session["access_token"] = token_data["access_token"]
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials")
        except requests.exceptions.ConnectionError:
            flash("Could not connect to backend server. Is it running?")
            
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        payload = {"name": name, "email": email, "password": password}
        try:
            response = requests.post(f"{API_URL}/auth/register", json=payload)
            
            if response.status_code == 200:
                flash("Registration successful! Please login.")
                return redirect(url_for("login"))
            else:
                flash(f"Error: {response.text}")
        except requests.exceptions.ConnectionError:
             flash("Could not connect to backend server.")
            
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "access_token" not in session:
        return redirect(url_for("login"))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    try:
        # Get User Info
        user_resp = requests.get(f"{API_URL}/auth/me", headers=headers)
        if user_resp.status_code == 401:
             session.clear()
             return redirect(url_for("login"))
             
        user = user_resp.json()
        
        # Get Repos
        repos_resp = requests.get(f"{API_URL}/repos/", headers=headers)
        repos = repos_resp.json() if repos_resp.status_code == 200 else []
        
        # Enrich repos with analysis status (Optional, skipping for MVP complexity)
        # But we need basic flow.
        
        return render_template("dashboard.html", user=user, repos=repos)
    except requests.exceptions.ConnectionError:
        flash("Backend unreachable")
        return render_template("dashboard.html", user={"name": "Offline User"}, repos=[])


@app.route("/repos/add", methods=["POST"])
def add_repo():
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    url = request.form.get("url")
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    resp = requests.post(f"{API_URL}/repos/", json={"url": url}, headers=headers)
    if resp.status_code != 200:
        flash(f"Failed to add repository: {resp.text[:200]}")
    else:
        flash("Repository added successfully!", "success")
    return redirect(url_for("dashboard"))

@app.route("/repos/delete/<int:repo_id>")
def delete_repo(repo_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    resp = requests.delete(f"{API_URL}/repos/{repo_id}", headers=headers)
    if resp.status_code != 200:
        flash(f"Failed to delete repository: {resp.text[:200]}")
    else:
        flash("Repository deleted.", "success")
    return redirect(url_for("dashboard"))

@app.route("/analyses/start/<int:repo_id>", methods=["POST"])
def start_analysis_route(repo_id):
    if "access_token" not in session:
         return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    # For query params in POST (FastAPI expects ?repository_id=X)
    resp = requests.post(f"{API_URL}/analyses/?repository_id={repo_id}", headers=headers, json={})
    
    if resp.status_code == 200:
        job = resp.json()
        return redirect(url_for("view_analysis", job_id=job["id"]))
    else:
        flash(f"Failed to start analysis: {resp.text}")
        return redirect(url_for("dashboard"))

@app.route("/analyses/<int:job_id>")
def view_analysis(job_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    resp = requests.get(f"{API_URL}/analyses/{job_id}", headers=headers)
    
    if resp.status_code != 200:
        flash("Analysis Job not found")
        return redirect(url_for("dashboard"))
        
    job = resp.json()
    document = ""
    
    if job["status"] == "DONE":
        doc_resp = requests.get(f"{API_URL}/analyses/{job_id}/document", headers=headers)
        if doc_resp.status_code == 200:
             document = doc_resp.json().get("markdown", "")
    
    return render_template("analysis_result.html", job=job, document=document)

@app.route("/analyzed-repos")
def analyzed_repos():
    if "access_token" not in session:
        return redirect(url_for("login"))
        
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    try:
        # Fetch all repos
        repos_resp = requests.get(f"{API_URL}/repos/", headers=headers)
        if repos_resp.status_code != 200:
            flash("Error fetching repositories")
            return redirect(url_for("dashboard"))
            
        all_repos = repos_resp.json()
        
        # Filter for repos with at least one DONE job
        analyzed_list = []
        for repo in all_repos:
            # Sort jobs by id desc to get latest?
            # Schema includes 'jobs' list now
            valid_jobs = [j for j in repo.get("jobs", []) if j["status"] == "DONE"]
            if valid_jobs:
                # Get the latest one
                # Assuming jobs are returned, we pick the last one or sort
                # Safety sort
                valid_jobs.sort(key=lambda x: x["id"], reverse=True)
                last_job = valid_jobs[0]
                
                analyzed_list.append({
                    "repo": repo,
                    "last_job": last_job
                })
        
        return render_template("analyzed_repos.html", analyzed_repos=analyzed_list)
        
    except Exception as e:
        print(e)
        flash(f"Error: {e}")
        return redirect(url_for("dashboard"))

@app.route("/analyses/<int:job_id>/pdf")
def download_pdf_route(job_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
    
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    
    backend_url = f"{API_URL}/analyses/{job_id}/download_pdf"
    
    try:
        req = requests.get(backend_url, headers=headers, stream=True)
        
        if req.status_code == 200:
             from flask import Response, stream_with_context
             return Response(stream_with_context(req.iter_content(chunk_size=1024)), 
                             content_type=req.headers['Content-Type'],
                             headers={"Content-Disposition": f"attachment; filename=report_{job_id}.pdf"})
        else:
             flash("Could not generate/download PDF")
             return redirect(url_for("view_analysis", job_id=job_id))
    except Exception as e:
        flash(f"Error downloading PDF: {e}")
        return redirect(url_for("view_analysis", job_id=job_id))


@app.route("/chat/<int:repo_id>")
def chat(repo_id):
    if "access_token" not in session:
        return redirect(url_for("login"))

    headers = {"Authorization": f"Bearer {session['access_token']}"}

    # Fetch repo info
    repo_resp = requests.get(f"{API_URL}/repos/{repo_id}", headers=headers)
    if repo_resp.status_code != 200:
        flash("Repository not found")
        return redirect(url_for("dashboard"))
    repo = repo_resp.json()

    # Fetch sessions for this repo
    sessions_resp = requests.get(
        f"{API_URL}/chat/sessions?repository_id={repo_id}",
        headers=headers,
    )
    sessions = sessions_resp.json().get("sessions", []) if sessions_resp.status_code == 200 else []

    # Get session_id from query param
    session_id = request.args.get("session_id")
    messages = []
    if session_id:
        hist_resp = requests.get(
            f"{API_URL}/chat/sessions/{session_id}/history",
            headers=headers,
        )
        if hist_resp.status_code == 200:
            messages = hist_resp.json().get("messages", [])

    return render_template(
        "chat.html",
        repo=repo,
        sessions=sessions,
        session_id=session_id,
        messages=messages,
    )

@app.route("/api/analyses/<int:job_id>/steps")
def api_analysis_steps(job_id):
    """JSON proxy: returns current status + steps list for AJAX polling."""
    if "access_token" not in session:
        from flask import jsonify
        return jsonify({"error": "unauthorized"}), 401
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.get(f"{API_URL}/analyses/{job_id}/steps", headers=headers, timeout=5)
        from flask import jsonify
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        from flask import jsonify
        return jsonify({"error": str(e)}), 500

@app.route("/api/analyses/<int:job_id>/document")
def api_analysis_document(job_id):
    """JSON proxy: returns the generated markdown document."""
    if "access_token" not in session:
        from flask import jsonify
        return jsonify({"error": "unauthorized"}), 401
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        resp = requests.get(f"{API_URL}/analyses/{job_id}/document", headers=headers, timeout=10)
        from flask import jsonify
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        from flask import jsonify
        return jsonify({"error": str(e)}), 500

@app.route("/analyses/<int:job_id>/delete", methods=["POST"])
def delete_analysis_route(job_id):
    if "access_token" not in session:
        return redirect(url_for("login"))
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    resp = requests.delete(f"{API_URL}/analyses/{job_id}", headers=headers)
    if resp.status_code == 200:
        flash("Analysis deleted.", "success")
    else:
        flash(f"Failed to delete analysis: {resp.text[:200]}")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(port=5001, debug=True)
