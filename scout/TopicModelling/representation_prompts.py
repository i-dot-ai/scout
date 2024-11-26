summarization_prompt = """
I have a topic that is described by the following keywords: [KEYWORDS]
In this topic, the following documents are a small but representative subset of all documents in the topic:
[DOCUMENTS]

Based on the information above, please give a summary of no more than 250 words of this topic. The summary should focus on the common themes in the topics and not the content of the documents. You should return the summary in the following format:
topic: <summary>
"""

# Few-shot prompting
system_prompt = """
You are a helpful assistant working on topic modelling of documents relating the assurance review process of the UK's infrastructure and projects authority. You are tasked with coming up with a simple label of one, two, or three words to describe the primary theme of a topic, that would be useful for senior decision makers at the infrastructure and projects authority.
"""

examples = """
EXAMPLE 1
Output: Inflation
Input chunk: <placeholder>


EXAMPLE 2
Output: Sustainability
Input chunk: <placeholder>

EXAMPLE 3
Output: Scheduling
    Input chunk: <placeholder>

"""

instruction = """
    Based on the examples given, you should assign a theme to a topic with the following keywords: [KEYWORDS]
    and a small but representative subset of all documents in this topic:
    [DOCUMENTS]

    You should return the theme label in the following format:
    topic: <theme label>
    """

primary_theme_prompt = system_prompt + examples + instruction