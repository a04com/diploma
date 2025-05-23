from pymongo import MongoClient

# Подключение к MongoDB
client = MongoClient("mongodb+srv://alasylkhh:admin@cluster0.6fmla.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
questions = client['questions']            
collection = questions['ent']  # При необходимости замени на нужную коллекцию

# Словарь соответствий topic -> topic_name
topic_mapping = {
    'Test 3': 'Тест 3'  # Уже на русском — можно оставить как есть, но добавим для единообразия
}

# Обновление всех документов с соответствием topic -> topic_name
for topic, topic_name in topic_mapping.items():
    result = collection.update_many(
        {'topic': topic},
        {'$set': {'topic_name': topic_name}}
    )
    print(f'Обновлено {result.modified_count} документов для topic \"{topic}\"')
