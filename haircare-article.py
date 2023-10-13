import os
import autogen
import requests
from bs4 import BeautifulSoup
import json
from autogen import config_list_from_json
from langchain.agents import initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain import PromptTemplate
import openai
from dotenv import load_dotenv

# Load API key
load_dotenv()
config_list = config_list_from_json(env_or_file="OAI_CONFIG_LIST")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define hair care research function
def hair_care_research(query):
    # ... [contents of the research function, same as before]

# Define content creation function for hair care articles
def write_hair_care_content(research_material, topic):
    hair_care_editor = autogen.AssistantAgent(
        name="hair_care_editor",
        system_message="You're an editor specialized in hair care. Define the structure of a hair care article using the material provided, then forward it to the writer.",
        llm_config={"config_list": config_list},
    )

    hair_care_writer = autogen.AssistantAgent(
        name="hair_care_writer",
        system_message="You're a writer focusing on hair care topics. Craft an article using the structure given by the editor and feedback from the reviewer. Complete the article in 2 iterations, and then append TERMINATE.",
        llm_config={"config_list": config_list},
    )

    hair_care_reviewer = autogen.AssistantAgent(
        name="hair_care_reviewer",
        system_message="You're an expert in hair care content. Review the written article, provide critiques, and offer feedback for improvements. Conclude after 2 iterations with TERMINATE.",
        llm_config={"config_list": config_list},
    )

    user_proxy = autogen.UserProxyAgent(
        name="admin",
        system_message="A human admin overseeing the hair care article creation. The editor will discuss the structure with this admin. The final writing needs admin approval.",
        code_execution_config=False,
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="TERMINATE",
    )

    groupchat = autogen.GroupChat(
        agents=[user_proxy, hair_care_editor, hair_care_writer, hair_care_reviewer],
        messages=[],
        max_round=20
    )
    
    manager = autogen.GroupChatManager(groupchat=groupchat)

    user_proxy.initiate_chat(manager, message=f"Write a hair care article about {topic}, based on this research material: {research_material}")

    user_proxy.stop_reply_at_receive(manager)
    user_proxy.send("Provide the finalized hair care article. Ensure it includes only the article content. Conclude with TERMINATE.", manager)

    return user_proxy.last_message()["content"]

# Define hair care assistant agent
llm_config_hair_care_assistant = {
    "functions": [
        {
            "name": "hair_care_research",
            "description": "Research about a given hair care topic and return research materials, including reference links.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic for hair care research."
                    }
                },
                "required": ["query"]
            },
        },
        {
            "name": "write_hair_care_content",
            "description": "Create content based on the research material for a hair care topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "research_material": {
                        "type": "string",
                        "description": "Research materials on a hair care topic, including any available reference links."
                    },
                    "topic": {
                        "type": "string",
                        "description": "The hair care topic for the article."
                    }
                },
                "required": ["research_material", "topic"]
            }
        }
    ],
    "config_list": config_list
}

hair_care_assistant = autogen.AssistantAgent(
    name="hair_care_assistant",
    system_message="You are a hair care writing assistant. Utilize the 'hair_care_research' function to gather the latest information on hair care topics. Then, use the 'write_hair_care_content' function to craft a quality article. Conclude your task with TERMINATE.",
    llm_config=llm_config_hair_care_assistant
)

user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    human_input_mode="TERMINATE",
    function_map={
        "write
