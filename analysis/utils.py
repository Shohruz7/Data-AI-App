import openai
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def generate_response(df):
    prompt = f"""You're a data analyst. Analyze the following dataset and provide insights and and identify any patterns, trends, or anomalies. Suggest visualizations that would help understand the data.

Data (first 5 rows):
{df.head().to_string(index=False)}
Return your analysis in a structured format, Include a few bulleted insights, suggested some visualizations, and any anomalies detected. 
Do not include any code or raw data in your response. DO NOT include any markdown formatting. Do not include too much text, be concise and to the point.
User will ask questions based on this analysis later or ask for more visualizations. 
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert data analyst."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.7,
    )
    return response.choices[0].message.content
def answer_question(question, df):
    prompt = f"""
You are a data analyst. Use the dataset below to answer the user's question.

Dataset sample:
{df.head().to_string(index=False)}

Question: {question}

Provide a concise and clear answer using the data above. Suggest visualizations if relevant, but do not include raw code or markdown formatting.
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert data analyst."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1000,
        temperature=0.7,
    )
    return response.choices[0].message.content