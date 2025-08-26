import os
import mysql.connector
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, render_template

# Load environment variables from .env (for local dev)
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Flask app
app = Flask(__name__)


# ---------- DB Functions ----------
def get_connection():
    """Create and return a MySQL connection"""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )


def get_schema():
    """Fetch database schema (tables + columns) from MySQL"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        schema = []
        cursor.execute("SHOW TABLES")
        tables = [t[0] for t in cursor.fetchall()]

        for table in tables:
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            cols = [col[0] for col in cursor.fetchall()]
            schema.append(f"Table: {table} (Columns: {', '.join(cols)})")

        conn.close()
        return "\n".join(schema)

    except mysql.connector.Error as err:
        return f"Error fetching schema: {err}"


def run_query(query):
    """Run SQL query on MySQL DB and return results"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]
        conn.close()
        return {"columns": col_names, "rows": results}

    except mysql.connector.Error as err:
        return {"error": str(err)}


def prompt_to_sql(user_prompt):
    """Convert natural language to SQL using Gemini"""
    schema = get_schema()
    response = model.generate_content(f"""
    Convert this request into a valid MySQL query.
    Request: {user_prompt}
    Database schema:
    {schema}
    Only return the SQL query without explanations or markdown.
    """)
    
    sql = response.text.strip()

    # 🧹 Clean SQL if Gemini wraps it in markdown
    if sql.startswith("```"):
        sql = sql.split("```")[1]
    sql = sql.replace("sql", "").replace("```", "").strip()

    return sql


# ---------- Flask Routes ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_prompt = request.form["query"]
        sql_query = prompt_to_sql(user_prompt)
        results = run_query(sql_query)
        return render_template("index.html", query=user_prompt, sql=sql_query, results=results)
    return render_template("index.html")


# ---------- Run App ----------
if __name__ == "__main__":
    app.run(debug=True)
