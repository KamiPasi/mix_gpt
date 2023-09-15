import json
import time
import requests
import streamlit as st
from streamlit_javascript import st_javascript

st.set_page_config(page_title="MixGPT", page_icon='🤖', layout="wide")


def get_from_local_storage(k, out=[]):
    if k not in st.session_state:
        with st.spinner(f"Load {k}"):
            v = st_javascript(f"JSON.parse(localStorage.getItem('{k}'));")
            time.sleep(3)
        return v or out
    else:
        return st.session_state[k]


def set_to_local_storage(k, v):
    jdata = json.dumps(v)
    st_javascript(
        f"localStorage.setItem('{k}', JSON.stringify({jdata}));")


def get_con_title():
    # return "test"
    prompt_title = [{"role": "user", "content": "总结上述对话, 10字以内"}]
    chat_title = ""
    for title_ in ask(st.session_state.messages+prompt_title, engine="gpt-3.5-turbo"):
        chat_title += title_
    return chat_title


def save_to_local_storage(model_name):
    with st.spinner("正在保存当前会话"):
        title = get_con_title()
        _con_dict = {"title": title, "conversation": st.session_state.messages}
        st.session_state[f"{model_name}_con"].insert(0, _con_dict)
        set_to_local_storage(f"{model_name}_con", st.session_state[f"{model_name}_con"])
        st.success(f"{title} 保存成功!")


def set_chat(model_name):
    save_to_local_storage(model_name)


def save_key(k):
    st.session_state['url_key'].update({k: st.session_state[k]})
    set_to_local_storage('url_key', st.session_state['url_key'])



def ask(messages, engine, plugins=[], plugin_sets=[]):
    json_data = {
        'prompt': messages,
        'lang': 'zh-CN',
        'model': engine,
        'plugins': plugins,
        'pluginSets': plugin_sets,
        'getRecommendQuestions': True,
        'isSummarize': False,
        'webVersion': '1.3.2',
        'userAgent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76',
        'isExtension': False,
    }
    response = requests.post('https://chatai.mixerbox.com/api/chat/stream', headers=st.session_state.headers,
                             json=json_data, stream=True)
    for i in response:
        for res in i.decode().split("\n"):
            if "event: signal" in res:
                break
            if res.startswith("data"):
                yield res.replace("data:", "")


if 'url_key' not in st.session_state:
    script = """await (async function () {
        let localStorageData = {};

  for (let i = 0; i < localStorage.length; i++) {
    let key = localStorage.key(i);
    let value = localStorage.getItem(key);
    localStorageData[key] = value;
  }

  return localStorageData;
    })()
    """
    print("--------------------------------")
    v = st_javascript(script)
    time.sleep(3)
    print(v)
    st.session_state['url_key'] = json.loads(v.get('url_key', "{}"))
    st.session_state.local_storage = v

# st.session_state
with st.sidebar:

    key = st.text_input("Cookie:", st.session_state['url_key'].get("key") or "", on_change=save_key, key="key", args=('key',), type="password")
    if not key:
        st.warning("请输cookie")
        st.stop()
    else:
        st.session_state.headers = {
            'authority': 'chatai.mixerbox.com',
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5,zh-TW;q=0.4',
            # Already added when you pass json=
            # 'content-type': 'application/json',
            # Requests sorts cookies= alphabetically
            'cookie': key,
            'origin': 'https://chatai.mixerbox.com',
            'referer': 'https://chatai.mixerbox.com/chat',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Microsoft Edge";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.76',
        }

    if 'models' not in st.session_state:
        st.session_state['models'] = ['gpt-3.5-turbo', "gpt-4"]
        for model_ in st.session_state.models:
            st.session_state[f"{model_}_con"] = json.loads(st.session_state.local_storage.get(f"{model_}_con", "[]"))

    model = st.selectbox("选择模型:", st.session_state.models)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # st.write("--------------------------------------------")
    col1, col2 = st.columns(2)

    if col1.button("New Chat", use_container_width=True):
        st.session_state.messages = []
    if col2.button("Retry", use_container_width=True):
        if st.session_state.messages[-1]['role'] == 'user':
            st.session_state.messages.pop()
        else:
            st.session_state.messages.pop()
            st.session_state.messages.pop()
        retry_prompt = st.session_state.last_prompt
    else:
        retry_prompt = None
    st.write("--------------------------------------------")

    con_dict = st.selectbox("选择会话:", st.session_state[f"{model}_con"], format_func=lambda x: x.get("title"))
    col11, col22 = st.columns(2)
    if col11.button("Load", use_container_width=True):
        st.session_state.messages = con_dict["conversation"]
    col22_b = col22.button("Save", on_click=set_chat, args=(model,), use_container_width=True)


st.title('Mix GPT')


for message in [{"role": "user", "content": "How can I help you?"}]+st.session_state.messages:
    with st.chat_message(message["role"].replace("system", "user")):
        st.markdown(message["content"])

# Accept user input
prompt = st.chat_input("输入你的困惑") or retry_prompt
if prompt:
    # Display user message in chat message container
    with st.chat_message("user"):
        st.session_state.last_prompt = prompt
        st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking"):
            message_placeholder = st.empty()
            prompt = prompt.strip()
            full_response = ""
            if prompt.startswith("/"):
                order = prompt.split(" ", 1)[0]
                if order == "/retry":
                    pass
                else:
                    message_placeholder.markdown("未知指令!")
            else:
                for chunk in ask(st.session_state.messages, model):
                    # print(chunk, end="")
                    if chunk:
                        full_response += chunk + ""
                        message_placeholder.markdown(full_response + "▌")
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                message_placeholder.markdown(full_response)
