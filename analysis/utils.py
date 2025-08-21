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

def generate_chat_title(df, filename: str) -> str:
    sample = df.head().to_string(index=False)
    prompt = f"""
You are to craft a very short, descriptive chat title (max 6 words) for a data analysis session.
Use the provided file name and dataset preview to infer the theme.
- Output ONLY the title text, no quotes, no punctuation at the end, no markdown.

File name: {filename}
Dataset preview (first 5 rows):
{sample}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You generate concise, meaningful titles."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=30,
            temperature=0.4,
        )
        title = response.choices[0].message.content.strip()
        title = title.strip('\"\' ').rstrip('.!?:;')
        return title if title else (filename or "Untitled Chat")
    except Exception:
        return filename or "Untitled Chat"

def infer_chart_spec(question: str, df) -> dict | None:
    sample = df.head().to_string(index=False)
    prompt = f"""
Given the user's question and a sample of the dataset, decide if a chart should be created. If so, output a SMALL JSON object ONLY (no extra text) with:
- type: one of [bar, line, scatter, hist, box, pie]
- x: column name for x-axis (optional for hist/pie)
- y: column name for y-axis/values (optional for hist/pie)
- agg: optional aggregation for bar (sum|mean|count)
- bins: optional integer for hist
- title: short title
- hue: optional grouping column (optional)
Return null if a chart is not appropriate.

Question: {question}
Dataset sample (first 5 rows):
{sample}

Output JSON only, no markdown, no explanations.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You output minimal JSON specs for charts."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=120,
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        # Basic safety: if response doesn't look like JSON, skip
        if not content or (not content.startswith('{') and not content.lower().startswith('null')):
            return None
        import json as _json
        spec = _json.loads(content)
        if spec is None:
            return None
        if isinstance(spec, dict) and 'type' in spec:
            return spec
        return None
    except Exception:
        return None