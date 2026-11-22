
from flask import Flask, render_template, request, redirect, url_for, session
from ai_engine import generate_content
from database import (
    create_table,
    register_user,
    get_user_by_email,
    verify_password,
    save_history,
    get_history,
    delete_history
)

import webbrowser
from threading import Timer

app = Flask(__name__)

# Session security key
app.secret_key = "promptly-ai-development-secret-key-change-later"

# Create database tables
create_table()


# Available AI tools
TOOLS = {
    "general": {
        "title": "AI Content Generator",
        "description": "Generate creative content using AI.",
        "placeholder": "Enter your topic or idea..."
    },
    "blog": {
        "title": "AI Blog Writer",
        "description": "Create engaging and informative blog articles.",
        "placeholder": "Enter your blog topic..."
    },
    "social": {
        "title": "Social Media Content Generator",
        "description": "Create attractive social media captions and posts.",
        "placeholder": "Enter your social media topic..."
    },
    "email": {
        "title": "AI Email Writer",
        "description": "Write professional emails in seconds.",
        "placeholder": "Enter your email requirements..."
    },
    "summary": {
        "title": "AI Text Summarizer",
        "description": "Convert long text into short and meaningful summaries.",
        "placeholder": "Paste your long text here..."
    },
    "sentiment": {
        "title": "AI Sentiment Analyzer",
        "description": "Analyze text and identify its emotional tone.",
        "placeholder": "Enter a review, comment or sentence to analyze..."
    }
}


# Registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("home"))

    error = ""

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            error = "Please fill in all the fields."

        elif len(password) < 8:
            error = "Password must contain at least 8 characters."

        else:
            success = register_user(name, email, password)

            if success:
                return redirect(url_for("login"))

            error = "This email is already registered."

    return render_template("register.html", error=error)


# Login page
@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("home"))

    error = ""

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email)

        if user and verify_password(user, password):

            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("home"))

        error = "Invalid email or password."

    return render_template("login.html", error=error)


# Logout
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# Main dashboard and AI tools
@app.route("/", methods=["GET", "POST"])
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    selected_tool = request.values.get("tool", "general")

    if selected_tool not in TOOLS:
        selected_tool = "general"

    tool = TOOLS[selected_tool]

    generated_content = ""
    user_prompt = ""

    if request.method == "POST":

        user_prompt = request.form.get("prompt", "").strip()

        if user_prompt:

            instructions = {
                "general": (
                    "Generate useful, creative and well-organized content."
                ),
                "blog": (
                    "Write a detailed and engaging blog article with "
                    "a title, introduction, headings and conclusion."
                ),
                "social": (
                    "Create an engaging social media post with an "
                    "attractive caption, suitable hashtags and emojis."
                ),
                "email": (
                    "Write a professional email with a suitable subject, "
                    "greeting, body and closing."
                ),
                "summary": (
                    "Summarize the following text into a clear, short "
                    "and meaningful summary. Include all important points "
                    "and avoid unnecessary details."
                ),
                "sentiment": (
                    "Analyze the sentiment of the given text. Classify it "
                    "as POSITIVE, NEGATIVE or NEUTRAL. Explain the reason "
                    "briefly and provide a confidence estimate. Do not "
                    "claim a mathematically measured confidence score."
                )
            }

            full_prompt = (
                instructions[selected_tool]
                + "\n\nUser's text:\n"
                + user_prompt
            )

            generated_content = generate_content(full_prompt)

            if (
                generated_content
                and not generated_content.startswith("Error:")
                and not generated_content.startswith("Error generating")
            ):
                save_history(
                    session["user_id"],
                    tool["title"],
                    user_prompt,
                    generated_content
                )

        else:
            generated_content = "Please enter a prompt first."

    return render_template(
        "index.html",
        generated_content=generated_content,
        user_prompt=user_prompt,
        selected_tool=selected_tool,
        tool=tool,
        user_name=session.get("user_name")
    )


# Private generation history
@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    records = get_history(session["user_id"])

    return render_template(
        "history.html",
        records=records,
        user_name=session.get("user_name")
    )


# Delete history
@app.route("/delete-history/<int:history_id>", methods=["POST"])
def delete_history_record(history_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    delete_history(history_id, session["user_id"])

    return redirect(url_for("history"))


# Open Chrome automatically
def open_browser():
    webbrowser.open("http://127.0.0.1:5000/login")


if __name__ == "__main__":

    Timer(1.5, open_browser).start()

    app.run(debug=True, use_reloader=False)
