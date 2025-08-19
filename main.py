import os
import mysql.connector
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ✅ Create model instance
model = genai.GenerativeModel("gemini-1.5-flash")


def get_schema():
    """Fetch database schema (tables + columns) from MySQL"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Sibin"),
            database=os.getenv("DB_NAME", "smart_retrieval"),
        )
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
    """Run SQL query on MySQL DB and print results"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Sibin"),
            database=os.getenv("DB_NAME", "smart_retrieval"),
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        # Print column headers
        col_names = [desc[0] for desc in cursor.description]
        print("\t".join(col_names))
        print("-" * 50)

        # Print each row
        for row in results:
            print("\t".join(str(x) for x in row))

        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")


def prompt_to_sql(user_prompt):
    """Convert natural language to SQL using Gemini"""
    schema = get_schema()  # dynamically fetch schema
    response = model.generate_content(f"""
    Convert this request into a valid MySQL query.
    Request: {user_prompt}
    Database schema:
    {schema}
    Only return the SQL query without explanations or markdown.
    """)
    
    sql = response.text.strip()

    # 🧹 Clean SQL
    if sql.startswith("```"):
        sql = sql.split("```")[1]
    sql = sql.replace("sql", "").replace("```", "").strip()

    return sql


if __name__ == "__main__":
    print("🤖 Smart Retrieval System (Prompt-based)")
    while True:
        user_prompt = input("\nAsk your query (or type 'exit' to quit): ")
        if user_prompt.lower() == "exit":
            print("👋 Goodbye!")
            break
        sql_query = prompt_to_sql(user_prompt)
        print(f"\n📝 Generated SQL:\n{sql_query}\n")
        run_query(sql_query)
