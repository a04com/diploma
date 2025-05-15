from groq import Groq

# Initialize the Groq client
client = Groq(
    api_key='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',
)

def main():
    # System message to set up the assistant's behavior
    messages = [
        {
            "role": "system",
            "content": """Ты — полезный ИИ-ассистент для изучения математики.
Отвечая на математические вопросы, ты всегда:

Записываешь формулы с помощью обычного Markdown (например, a^2 + b^2 = c^2)

Объясняешь каждый шаг решения ясно и логично

Делаешь объяснения короткими, но полными

Приводишь примеры, если это помогает, но не отвлекаешься от основной задачи

Используешь простой и понятный язык, подходящий для ученика

Всегда объясняешь, почему делается каждый шаг, а не просто что делать

Если ты в чём-то не уверен, честно об этом говоришь и подсказываешь, где можно найти ответ

Отвечаешь на языке, на котором был задан вопрос

Всегда отвечаешь кратко и по делу
            """
        },
    ]

    print("Welcome to the Groq Chatbot! Type 'exit' to end the conversation.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        # Add user message to conversation history
        messages.append({"role": "user", "content": user_input})

        # Get chatbot response
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1000,
        )

        assistant_response = chat_completion.choices[0].message.content
        
        # Add assistant response to conversation history
        messages.append({"role": "assistant", "content": assistant_response})

        print(f"\nAssistant: {assistant_response}\n")

if __name__ == "__main__":
    main()