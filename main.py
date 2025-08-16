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

def run_query(query):
    """Run SQL query on MySQL DB and print results"""
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "Sibin"),
            database=os.getenv("DB_NAME", "smart_retrieval")
        )
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        for row in results:
            print(row)
        conn.close()
    except mysql.connector.Error as err:
        print(f"❌ Database Error: {err}")

def prompt_to_sql(user_prompt):
    response = model.generate_content(f"""
    Convert this request into a valid MySQL query.
    Request: {user_prompt}
    Table: products
    Columns: id, name, category, price
    Only return the SQL query without explanations or markdown.
    """)
    sql = response.text.strip()

    # 🧹 Clean SQL from markdown (```sql ... ```)
    if sql.startswith("```"):
        sql = sql.split("```")[1]  # take inside content
    sql = sql.replace("sql", "").replace("```", "").strip()

    return sql

if __name__ == "__main__":
    print("📦 Smart Product Finder (Prompt-based)")
    while True:
        user_prompt = input("\nAsk your query (or type 'exit' to quit): ")
        if user_prompt.lower() == "exit":
            print("👋 Goodbye!")
            break
        sql_query = prompt_to_sql(user_prompt)
        print(f"\n📝 Generated SQL: {sql_query}\n")
        run_query(sql_query)
