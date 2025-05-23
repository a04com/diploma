from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import os
from groq import Groq
from bson import ObjectId

app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB connection
client = MongoClient("mongodb+srv://alasylkhh:admin@cluster0.6fmla.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['auth_db']
users = db['users']

questions = client['questions']
questions_algebra = questions['algebra']
questions_geometry = questions['geometry']
questions_trigonometry = questions['trigonometry']
questions_ent = questions['ent']

groq_client = Groq(api_key='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')

def ask_groq_ai(exercise, user_message):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful AI assistant for teaching math. When answering math questions, you will: 1. Write formulas using plain Markdown formatting (e.g., a^2 + b^2 = c^2) 2. Explain each step of the solution clearly and logically 3. Keep explanations concise but complete—neither too short nor too long 4. Give examples when useful, but stay focused on the main problem 5. Use simple, clear language appropriate for a student audience 6. Always explain why each step is taken, not just what to do 7. Be honest if you're unsure, and guide the user on how to find the answer."
        },
        {"role": "user", "content": f"Exercise: {exercise}\nUser question: {user_message}"}
    ]
    chat_completion = groq_client.chat.completions.create(
        messages=messages,
        model="llama-3.3-70b-versatile",
        temperature=0.7,
        max_tokens=1000,
    )
    return chat_completion.choices[0].message.content

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('about_us'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check if user already exists
        if users.find_one({'username': username}):
            flash('Пользователь с таким именем уже существует!')
            return redirect(url_for('signup'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        users.insert_one({
            'username': username,
            'password': hashed_password,
            'language': 'ru'  # Set default language to Russian
        })
        
        flash('Аккаунт успешно создан! Пожалуйста, войдите.')
        return redirect(url_for('signin'))
    
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль!')
            return redirect(url_for('signin'))
    
    return render_template('signin.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('signin'))
    username = session['username']
    user = users.find_one({'username': username})
    title = user.get('title', None)
    language = user.get('language', 'ru')  # Default to Russian
    algebra_solved = user.get('algebra_solved', 0)
    total_algebra = questions_algebra.count_documents({})
    geometry_solved = user.get('geometry_solved', 0)
    total_geometry = questions_geometry.count_documents({})
    trigonometry_solved = user.get('trigonometry_solved', 0)
    total_trigonometry = questions_trigonometry.count_documents({})
    ent_solved = user.get('ent_solved', 0)
    total_ent = questions_ent.count_documents({})

    # Get all topics and their names for each course
    algebra_topics = []
    for topic in questions_algebra.distinct('topic'):
        topic_doc = questions_algebra.find_one({'topic': topic})
        if topic_doc and 'topic_name' in topic_doc:
            algebra_topics.append((topic, topic_doc['topic_name']))
        else:
            algebra_topics.append((topic, topic))

    geometry_topics = []
    for topic in questions_geometry.distinct('topic'):
        topic_doc = questions_geometry.find_one({'topic': topic})
        if topic_doc and 'topic_name' in topic_doc:
            geometry_topics.append((topic, topic_doc['topic_name']))
        else:
            geometry_topics.append((topic, topic))

    trigonometry_topics = []
    for topic in questions_trigonometry.distinct('topic'):
        topic_doc = questions_trigonometry.find_one({'topic': topic})
        if topic_doc and 'topic_name' in topic_doc:
            trigonometry_topics.append((topic, topic_doc['topic_name']))
        else:
            trigonometry_topics.append((topic, topic))

    ent_topics = []
    for topic in questions_ent.distinct('topic'):
        topic_doc = questions_ent.find_one({'topic': topic})
        if topic_doc and 'topic_name' in topic_doc:
            ent_topics.append((topic, topic_doc['topic_name']))
        else:
            ent_topics.append((topic, topic))

    # --- Search logic ---
    search_query = request.args.get('search', '').strip().lower()
    show_courses = {'algebra': True, 'geometry': True, 'trigonometry': True, 'ent': True}
    filtered = {
        'algebra': [],
        'geometry': [],
        'trigonometry': [],
        'ent': []
    }
    if search_query:
        # Check for course name match
        course_map = {
            'алгебра': 'algebra',
            'геометрия': 'geometry',
            'тригонометрия': 'trigonometry',
            'ент': 'ent',
        }
        if search_query in course_map:
            for k in show_courses:
                show_courses[k] = (k == course_map[search_query])
            if show_courses['algebra']:
                filtered['algebra'] = algebra_topics
            if show_courses['geometry']:
                filtered['geometry'] = geometry_topics
            if show_courses['trigonometry']:
                filtered['trigonometry'] = trigonometry_topics
            if show_courses['ent']:
                filtered['ent'] = ent_topics
        else:
            # Search in all topics
            for topic, topic_name in algebra_topics:
                if search_query in topic_name.lower():
                    show_courses['algebra'] = True
                    filtered['algebra'].append((topic, topic_name))
            for topic, topic_name in geometry_topics:
                if search_query in topic_name.lower():
                    show_courses['geometry'] = True
                    filtered['geometry'].append((topic, topic_name))
            for topic, topic_name in trigonometry_topics:
                if search_query in topic_name.lower():
                    show_courses['trigonometry'] = True
                    filtered['trigonometry'].append((topic, topic_name))
            for topic, topic_name in ent_topics:
                if search_query in topic_name.lower():
                    show_courses['ent'] = True
                    filtered['ent'].append((topic, topic_name))
            # Hide courses with no results
            for k in show_courses:
                if not filtered[k]:
                    show_courses[k] = False
    else:
        filtered['algebra'] = algebra_topics
        filtered['geometry'] = geometry_topics
        filtered['trigonometry'] = trigonometry_topics
        filtered['ent'] = ent_topics

    return render_template(
        'dashboard.html',
        username=username,
        title=title,
        language=language,
        algebra_solved=algebra_solved,
        total_algebra=total_algebra,
        geometry_solved=geometry_solved,
        total_geometry=total_geometry,
        trigonometry_solved=trigonometry_solved,
        total_trigonometry=total_trigonometry,
        ent_solved=ent_solved,
        total_ent=total_ent,
        algebra_topics=filtered['algebra'],
        geometry_topics=filtered['geometry'],
        trigonometry_topics=filtered['trigonometry'],
        ent_topics=filtered['ent'],
        show_courses=show_courses
    )

@app.route('/signout')
def signout():
    session.pop('username', None)
    return redirect(url_for('signin'))

@app.route('/algebra/<topic>', methods=['GET', 'POST'])
def algebra_topic(topic):
    exercises = list(questions_algebra.find({'topic': topic}))
    feedback = {}
    username = session.get('username')
    user = users.find_one({'username': username}) if username else None
    solved_ids = set(user.get('algebra_solved_ids', [])) if user else set()
    new_correct = 0
    if request.method == 'POST':
        for ex in exercises:
            qid_str = str(ex['_id'])
            user_answer_idx = request.form.get(f'answer_{ex["_id"]}')
            if user_answer_idx is not None:
                try:
                    user_answer_idx = int(user_answer_idx)
                    is_correct = ex['options'][user_answer_idx] == ex['answer']
                    if is_correct:
                        feedback[qid_str] = 'correct'
                        if qid_str not in solved_ids:
                            solved_ids.add(qid_str)
                            new_correct += 1
                    else:
                        feedback[qid_str] = 'incorrect'
                except Exception:
                    feedback[qid_str] = 'incorrect'
            else:
                feedback[qid_str] = 'unanswered'
        # Update user progress in DB
        if user and new_correct > 0:
            users.update_one(
                {'_id': user['_id']},
                {'$set': {'algebra_solved_ids': list(solved_ids), 'algebra_solved': len(solved_ids)}}
            )
    return render_template('algebra_topic.html', topic=topic, exercises=exercises, feedback=feedback)

@app.route('/geometry/<topic>', methods=['GET', 'POST'])
def geometry_topic(topic):
    exercises = list(questions_geometry.find({'topic': topic}))
    feedback = {}
    username = session.get('username')
    user = users.find_one({'username': username}) if username else None
    solved_ids = set(user.get('geometry_solved_ids', [])) if user else set()
    new_correct = 0
    if request.method == 'POST':
        for ex in exercises:
            qid_str = str(ex['_id'])
            user_answer_idx = request.form.get(f'answer_{ex["_id"]}')
            if user_answer_idx is not None:
                try:
                    user_answer_idx = int(user_answer_idx)
                    is_correct = ex['options'][user_answer_idx] == ex['answer']
                    if is_correct:
                        feedback[qid_str] = 'correct'
                        if qid_str not in solved_ids:
                            solved_ids.add(qid_str)
                            new_correct += 1
                    else:
                        feedback[qid_str] = 'incorrect'
                except Exception:
                    feedback[qid_str] = 'incorrect'
            else:
                feedback[qid_str] = 'unanswered'
        # Update user progress in DB
        if user and new_correct > 0:
            users.update_one(
                {'_id': user['_id']},
                {'$set': {'geometry_solved_ids': list(solved_ids), 'geometry_solved': len(solved_ids)}}
            )
    return render_template('geometry_topic.html', topic=topic, exercises=exercises, feedback=feedback)

@app.route('/trigonometry/<topic>', methods=['GET', 'POST'])
def trigonometry_topic(topic):
    exercises = list(questions_trigonometry.find({'topic': topic}))
    feedback = {}
    username = session.get('username')
    user = users.find_one({'username': username}) if username else None
    solved_ids = set(user.get('trigonometry_solved_ids', [])) if user else set()
    new_correct = 0
    if request.method == 'POST':
        for ex in exercises:
            qid_str = str(ex['_id'])
            user_answer_idx = request.form.get(f'answer_{ex["_id"]}')
            if user_answer_idx is not None:
                try:
                    user_answer_idx = int(user_answer_idx)
                    is_correct = ex['options'][user_answer_idx] == ex['answer']
                    if is_correct:
                        feedback[qid_str] = 'correct'
                        if qid_str not in solved_ids:
                            solved_ids.add(qid_str)
                            new_correct += 1
                    else:
                        feedback[qid_str] = 'incorrect'
                except Exception:
                    feedback[qid_str] = 'incorrect'
            else:
                feedback[qid_str] = 'unanswered'
        # Update user progress in DB
        if user and new_correct > 0:
            users.update_one(
                {'_id': user['_id']},
                {'$set': {'trigonometry_solved_ids': list(solved_ids), 'trigonometry_solved': len(solved_ids)}}
            )
    return render_template('trigonometry_topic.html', topic=topic, exercises=exercises, feedback=feedback)

@app.route('/ent/<topic>', methods=['GET', 'POST'])
def ent_topic(topic):
    exercises = list(questions_ent.find({'topic': topic}))
    feedback = {}
    username = session.get('username')
    user = users.find_one({'username': username}) if username else None
    solved_ids = set(user.get('ent_solved_ids', [])) if user else set()
    new_correct = 0
    if request.method == 'POST':
        for ex in exercises:
            qid_str = str(ex['_id'])
            user_answer_idx = request.form.get(f'answer_{ex["_id"]}')
            if user_answer_idx is not None:
                try:
                    user_answer_idx = int(user_answer_idx)
                    is_correct = ex['options'][user_answer_idx] == ex['answer']
                    if is_correct:
                        feedback[qid_str] = 'correct'
                        if qid_str not in solved_ids:
                            solved_ids.add(qid_str)
                            new_correct += 1
                    else:
                        feedback[qid_str] = 'incorrect'
                except Exception:
                    feedback[qid_str] = 'incorrect'
            else:
                feedback[qid_str] = 'unanswered'
        # Update user progress in DB
        if user and new_correct > 0:
            users.update_one(
                {'_id': user['_id']},
                {'$set': {'ent_solved_ids': list(solved_ids), 'ent_solved': len(solved_ids)}}
            )
    return render_template('ent_topic.html', topic=topic, exercises=exercises, feedback=feedback)

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    data = request.get_json()
    exercise = data.get('exercise', '')
    user_message = data.get('message', '')
    try:
        ai_response = ask_groq_ai(exercise, user_message)
        return jsonify({'response': ai_response})
    except Exception as e:
        return jsonify({'response': 'Sorry, there was an error with the AI service.'}), 500

@app.route('/add_delete', methods=['GET'])
def add_delete():
    if 'username' not in session:
        return redirect(url_for('signin'))
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        flash('Доступ запрещен.')
        return redirect(url_for('dashboard'))
    # List of courses and their collections
    courses = [
        {'name': 'Алгебра', 'collection': questions_algebra},
        {'name': 'Геометрия', 'collection': questions_geometry},
        {'name': 'Тригонометрия', 'collection': questions_trigonometry},
        {'name': 'ЕНТ', 'collection': questions_ent},
    ]
    # For now, just show the course names and topics
    course_topics = {}
    for course in courses:
        topics = course['collection'].distinct('topic')
        course_topics[course['name']] = topics
    return render_template('add_delete.html', courses=courses, course_topics=course_topics)

@app.route('/admin_get_exercises')
def admin_get_exercises():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    course = request.args.get('course')
    topic = request.args.get('topic')
    if not course or not topic:
        return jsonify({'error': 'Missing course or topic'}), 400
    collection_map = {
        'Алгебра': questions_algebra,
        'Геометрия': questions_geometry,
        'Тригонометрия': questions_trigonometry,
        'ЕНТ': questions_ent,
    }
    collection = collection_map.get(course)
    if collection is None:
        return jsonify({'error': 'Invalid course'}), 400
    exercises = list(collection.find({'topic': topic}))
    for ex in exercises:
        ex['_id'] = str(ex['_id'])
    return jsonify({'exercises': exercises})

@app.route('/admin_update_exercise', methods=['POST'])
def admin_update_exercise():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.json
    course = data.get('course')
    ex_id = data.get('id')
    question = data.get('question')
    options = data.get('options')
    answer = data.get('answer')
    if not (course and ex_id and question and options and answer):
        return jsonify({'error': 'Missing fields'}), 400
    collection_map = {
        'Алгебра': questions_algebra,
        'Геометрия': questions_geometry,
        'Тригонометрия': questions_trigonometry,
        'ЕНТ': questions_ent,
    }
    collection = collection_map.get(course)
    if collection is None:
        return jsonify({'error': 'Invalid course'}), 400
    result = collection.update_one({'_id': ObjectId(ex_id)}, {'$set': {'question': question, 'options': options, 'answer': answer}})
    if result.modified_count:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Update failed'}), 400

@app.route('/admin_delete_exercise', methods=['POST'])
def admin_delete_exercise():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.json
    course = data.get('course')
    ex_id = data.get('id')
    if not (course and ex_id):
        return jsonify({'error': 'Missing fields'}), 400
    collection_map = {
        'Алгебра': questions_algebra,
        'Геометрия': questions_geometry,
        'Тригонометрия': questions_trigonometry,
        'ЕНТ': questions_ent,
    }
    collection = collection_map.get(course)
    if collection is None:
        return jsonify({'error': 'Invalid course'}), 400
    result = collection.delete_one({'_id': ObjectId(ex_id)})
    if result.deleted_count:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Delete failed'}), 400

@app.route('/admin_add_exercise', methods=['POST'])
def admin_add_exercise():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.json
    course = data.get('course')
    topic = data.get('topic')
    question = data.get('question')
    options = data.get('options')
    answer = data.get('answer')
    if not (course and topic and question and options and answer):
        return jsonify({'error': 'Missing fields'}), 400
    collection_map = {
        'Алгебра': questions_algebra,
        'Геометрия': questions_geometry,
        'Тригонометрия': questions_trigonometry,
        'ЕНТ': questions_ent,
    }
    collection = collection_map.get(course)
    if collection is None:
        return jsonify({'error': 'Invalid course'}), 400
    new_ex = {
        'topic': topic,
        'question': question,
        'options': options,
        'answer': answer
    }
    result = collection.insert_one(new_ex)
    if result.inserted_id:
        return jsonify({'success': True, 'id': str(result.inserted_id)})
    else:
        return jsonify({'error': 'Insert failed'}), 400

@app.route('/admin_delete_topic', methods=['POST'])
def admin_delete_topic():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.json
    course = data.get('course')
    topic = data.get('topic')
    if not (course and topic):
        return jsonify({'error': 'Missing course or topic'}), 400
    collection_map = {
        'Алгебра': questions_algebra,
        'Геометрия': questions_geometry,
        'Тригонометрия': questions_trigonometry,
        'ЕНТ': questions_ent,
    }
    collection = collection_map.get(course)
    if collection is None:
        return jsonify({'error': 'Invalid course'}), 400
    result = collection.delete_many({'topic': topic})
    if result.deleted_count > 0:
        return jsonify({'success': True, 'deleted_count': result.deleted_count})
    else:
        return jsonify({'error': 'No exercises found for this topic'}), 404

@app.route('/admin_add_topic', methods=['POST'])
def admin_add_topic():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    username = session['username']
    user = users.find_one({'username': username})
    if not user or user.get('title') != 'admin':
        return jsonify({'error': 'Access denied'}), 403
    data = request.json
    course = data.get('course')
    topic = data.get('topic')
    topic_name = data.get('topic_name')
    level = data.get('level')
    question = data.get('question')
    options = data.get('options')
    answer = data.get('answer')
    if not (course and topic and topic_name and level and question and options and answer):
        return jsonify({'error': 'Missing fields'}), 400
    collection_map = {
        'Алгебра': questions_algebra,
        'Геометрия': questions_geometry,
        'Тригонометрия': questions_trigonometry,
        'ЕНТ': questions_ent,
    }
    collection = collection_map.get(course)
    if collection is None:
        return jsonify({'error': 'Invalid course'}), 400
    new_ex = {
        'topic': topic,
        'topic_name': topic_name,
        'level': level,
        'question': question,
        'options': options,
        'answer': answer
    }
    result = collection.insert_one(new_ex)
    if result.inserted_id:
        return jsonify({'success': True, 'topic': topic, 'topic_name': topic_name})
    else:
        return jsonify({'error': 'Insert failed'}), 400

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

if __name__ == '__main__':
    app.run(debug=True)
