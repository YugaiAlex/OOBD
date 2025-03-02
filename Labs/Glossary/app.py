from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import string

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flash messages

RUSSIAN_ALPHABET = "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
DATABASE = "glossary.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            definition TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def load_terms():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT term, definition FROM glossary")
    rows = cursor.fetchall()
    conn.close()
    return [{'terms': row[0], 'definitions': row[1]} for row in rows]

def save_term(term, definition):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO glossary (term, definition) VALUES (?, ?)", (term, definition))
    conn.commit()
    conn.close()

def delete_term(term):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM glossary WHERE term = ?", (term,))
    conn.commit()
    conn.close()

init_db()
glossary_terms = load_terms()

@app.route('/')
def index():
    letter = request.args.get('letter', 'ALL').upper()
    search_query = request.args.get('q', '').strip().lower()
    sort_order = request.args.get('sort', 'asc')  # По умолчанию A-Z

    filtered_terms = glossary_terms

    if letter != 'ALL':
        filtered_terms = [t for t in glossary_terms if t['terms'][0].upper() == letter]

    if search_query:
        filtered_terms = [
            t for t in filtered_terms
            if search_query in t['terms'].lower() or search_query in t['definitions'].lower()
        ]

    def sort_key(term):
        first_char = term['terms'][0].upper()
        return (first_char not in string.ascii_uppercase, first_char, term['terms'].lower())

    filtered_terms.sort(key=sort_key, reverse=(sort_order == 'desc'))

    return render_template(
        'index.html',
        terms=filtered_terms,
        letters=list(string.ascii_uppercase) + list(RUSSIAN_ALPHABET),
        selected_letter=letter,
        sort_order=sort_order
    )

@app.route('/add', methods=['POST'])
def add_term():
    term = request.form.get('term').strip()
    definition = request.form.get('definition').strip()

    if not term or not definition:
        flash("Термин и определение не могут быть пустыми.", "error")
        return redirect(url_for('index'))

    save_term(term, definition)
    flash("Термин успешно добавлен.", "success")
    return redirect(url_for('index'))

@app.route('/delete/<term>', methods=['POST'])
def delete_term_route(term):
    delete_term(term)
    flash("Термин успешно удален.", "success")
    return redirect(url_for('index'))

@app.route('/query/<level>')
def execute_query(level):
    query_results = None

    if level == 'simple':
        query = "SELECT * FROM glossary LIMIT 5;"  # Вывод первых пяти строк
    elif level == 'medium':
        query = "SELECT term, LENGTH(definition) AS def_length FROM glossary ORDER BY def_length DESC LIMIT 5;"  # Вывод 5 терминов с самыми длинными определениями
    elif level == 'complex':
        query = """
            WITH RankedTerms AS (
                SELECT
                    term,
                    definition,
                    ROW_NUMBER() OVER (
                        PARTITION BY SUBSTR(term, 1, 1)
                        ORDER BY id DESC
                    ) AS rn
                FROM
                    glossary
                WHERE
                    SUBSTR(UPPER(term), 1, 1) IN ('V', 'W', 'X', 'Y', 'Z')
            )
            SELECT
                term,
                definition
            FROM
                RankedTerms
            WHERE
                rn = 1;
        """  # выводит только последние термины из тех что начинаются на последние 5 букв алфавита(по одному на каждую букву)
    else:
        flash("Неверный уровень запроса!", "error")
        return redirect(url_for('index'))

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(query)
        query_results = cursor.fetchall()
        conn.close()
    except Exception as e:
        flash(f"Ошибка выполнения SQL-запроса: {e}", "error")

    return render_template("query_results.html", results=query_results, level=level)

if __name__ == '__main__':
    app.run(debug=True)
