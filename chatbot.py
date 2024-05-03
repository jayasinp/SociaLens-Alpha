import openai
def talktogpt(input):
    #OpenAI API Key
    #openai.api_key = 
    gpt = openai.chat.completions.create(
                messages=[
                    {
                        "role": "system", "content": "You are a helpful assistant.",
                        "content": input,
                    }
                ],
                model="gpt-3.5-turbo",
            )
    response=gpt.choices[0].message.content
    return response 
