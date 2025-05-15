import os
from groq import Groq

# Initialize the Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

def main():
    # System message to set up the assistant's behavior
    messages = [
        {
            "role": "system",
            "content": """You are a helpful AI assistant for teaching math.  
            When answering math questions, you will:  
            1. Write formulas using plain Markdown formatting (e.g., a^2 + b^2 = c^2)  
            2. Explain each step of the solution clearly and logically  
            3. Keep explanations concise but complete—neither too short nor too long  
            4. Give examples when useful, but stay focused on the main problem  
            5. Use simple, clear language appropriate for a student audience  
            6. Always explain why each step is taken, not just what to do  
            7. Be honest if you're unsure, and guide the user on how to find the answer  
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