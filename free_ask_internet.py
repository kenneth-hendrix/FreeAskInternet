# -*- coding: utf-8 -*-

import json
import os 
from pprint import pprint
import requests
import trafilatura
from trafilatura import bare_extraction
from concurrent.futures import ThreadPoolExecutor
import concurrent
import requests
import openai
import time 
from datetime import datetime
from urllib.parse import urlparse
import tldextract
import platform
import urllib.parse

 
def extract_url_content(url):
    downloaded = trafilatura.fetch_url(url)
    content =  trafilatura.extract(downloaded)
    
    return {"url":url, "content":content}


 

def search_web_ref(query:str, debug=False):
 
    content_list = []

    try:

        safe_string = urllib.parse.quote_plus(":all !general " + query)

        response = requests.get('http://searxng:8080?q=' + safe_string + '&format=json')
        response.raise_for_status()
        search_results = response.json()
 
        if debug:
            print("JSON Response:")
            pprint(search_results)
        pedding_urls = []

        conv_links = []

        if search_results.get('results'):
            for item in search_results.get('results')[0:9]:
                name = item.get('title')
                snippet = item.get('content')
                url = item.get('url')
                pedding_urls.append(url)

                if url:
                    url_parsed = urlparse(url)
                    domain = url_parsed.netloc
                    icon_url =  url_parsed.scheme + '://' + url_parsed.netloc + '/favicon.ico'
                    site_name = tldextract.extract(url).domain
 
                conv_links.append({
                    'site_name':site_name,
                    'icon_url':icon_url,
                    'title':name,
                    'url':url,
                    'snippet':snippet
                })

            results = []
            futures = []

            executor = ThreadPoolExecutor(max_workers=10) 
            for url in pedding_urls:
                futures.append(executor.submit(extract_url_content,url))
            try:
                for future in futures:
                    res = future.result(timeout=5)
                    results.append(res)
            except concurrent.futures.TimeoutError:
                print("任务执行超时")
                executor.shutdown(wait=False,cancel_futures=True)

            for content in results:
                if content and content.get('content'):
                    
                    item_dict = {
                        "url":content.get('url'),
                        "content": content.get('content'),
                        "length":len(content.get('content'))
                    }
                    content_list.append(item_dict)
                if debug:
                    print("URL: {}".format(url))
                    print("=================")
 
        return  content_list
    except Exception as ex:
        raise ex


def gen_prompt(question,content_list, context_length_limit=11000,debug=False):
    
    limit_len = (context_length_limit - 2000)
    if len(question) > limit_len:
        question = question[0:limit_len]
    
    ref_content = [ item.get("content") for item in content_list]

    if len(ref_content) > 0:
        

        prompts = '''
        You are an AI question-and-answer assistant developed based on the content returned by search engines. You will be provided with a user question, and you need to compose a clear, concise, and accurate answer. The answer must be correct, precise, and written in an expert's neutral and professional tone. Please limit your answer to 2000 characters. Do not provide irrelevant information or be repetitive. If the context information provided is insufficient, write "Information missing:" followed by the relevant topic. Except for code, specific names, or reference numbers, the answer's language should be the same as the question's. Here are the contents of the context:
        '''  + "\n\n" + "```" 
        ref_index = 1

        for ref_text in ref_content:
            
            prompts = prompts + "\n\n" + ref_text
            ref_index += 1

        if len(prompts) >= limit_len:
            prompts = prompts[0:limit_len]        
        prompts = prompts + '''
```
Remember, do not repeat the context verbatim. If the answer is long, try to structure it and summarize in paragraphs. Below is the user question:
''' + question  
 
     
    else:
        prompts = question

    if debug:
        print(prompts)
        print("总长度："+ str(len(prompts)))
    return prompts



def chat(prompt, stream=True, debug=False):
    openai.base_url = "http://freegpt35:3040/v1/"
    openai.api_key = "EMPTY"
    total_content = ""
    for chunk in openai.chat.completions.create(
        model="gpt-3.5-turbo",
        # model='Qwen1.5-1.8B-Chat',
        messages=[{
            "role": "user",
            "content": prompt
        }],
        stream=True,
        max_tokens=1024,temperature=0.2
    ):
        stream_resp = chunk.dict()
        token = stream_resp["choices"][0]["delta"].get("content", "")
        if token:
            
            total_content += token
            yield token
    if debug:
        print(total_content)
 

 
    
def ask_internet(query:str,  debug=False):
  
    content_list = search_web_ref(query,debug=debug)
    if debug:
        print(content_list)
    prompt = gen_prompt(query,content_list,context_length_limit=6000,debug=debug)
    total_token =  ""
 
    for token in chat(prompt=prompt):
    # for token in daxianggpt.chat(prompt=prompt):
        if token:
            total_token += token
            yield token
    yield "\n\n"
    # 是否返回参考资料
    if True:
        yield "---"
        yield "\n"
        yield "Sources:\n"
        count = 1
        for url_content in content_list:
            url = url_content.get('url')
            yield "*[{}. {}]({})*".format(str(count),url,url )  
            yield "\n"
            count += 1
 