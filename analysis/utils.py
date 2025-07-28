import openai
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def generate_response(df):
    prompt = f"""You're a data analyst. Analyze the following dataset and provide insights and and identify any patterns, trends, or anomalies. Suggest visualizations that would help understand the data.

Data (first 5 rows):
{df.head().to_string(index=False)}
Return your analysis in a structured format, including bulleted insights, suggested visualizations, and any anomalies detected.
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