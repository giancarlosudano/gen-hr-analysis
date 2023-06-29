import logging as logger
import streamlit as st
import os
import traceback
from utilities.LLMHelper import LLMHelper
from utilities.AzureFormRecognizerClient import AzureFormRecognizerClient
from collections import OrderedDict 
import time
import json
import pandas as pd

def valutazione():
    try:
        
        llm_helper = LLMHelper(temperature=0, max_tokens=1500)

        start_time_gpt = time.perf_counter()

        print("Prompt Estrazione:")
        print(st.session_state["prompt_estrazione"])
        print("JD:")
        print(st.session_state["jd"])
        
        llm_skills_text = llm_helper.get_hr_completion(st.session_state["prompt_estrazione"].format(jd = st.session_state["jd"]))
        end_time_gpt = time.perf_counter()
        gpt_duration = end_time_gpt - start_time_gpt

        st.markdown(f"Risposta GPT in *{gpt_duration:.2f}*:")
        st.markdown(llm_skills_text)
        
        inizio_json = llm_skills_text.index('{')
        fine_json = llm_skills_text.rindex('}') + 1

        json_string = llm_skills_text[inizio_json:fine_json]
        json_data = json.loads(json_string)
        
        st.json(json_data)
        
        container = st.session_state["container"] 
        cv_urls = llm_helper.blob_client.get_all_urls(container_name=container)
        
        form_client = AzureFormRecognizerClient()

        for cv_url in cv_urls:
            try:
                start_time_cv = time.perf_counter()
                results = form_client.analyze_read(cv_url['fullpath'])
                end_time_cv = time.perf_counter()
                duration = end_time_cv - start_time_cv
                cv = results[0]
                
                exp = st.expander(f"CV {cv_url['file']} caricato in {duration:.2f} secondi", expanded = True)
                with exp:
                    st.markdown(cv)

                matching_count = 0
                delay = int(st.session_state['delay'])
                
                for competenza in json_data["competenze"]:
                    time.sleep(delay)
                    skill = competenza["skill"]
                    description = competenza["description"]
                    
                    llm_match_text = llm_helper.get_hr_completion(st.session_state["prompt_confronto"].format(cv = cv, skill = skill, description = description))
                    
                    # cerco la stringa "true]" invece di "[true]" perchè mi sono accorto che a volte usa la rispota [Risposta: True] invece di Risposta: [True]
                    if 'true]' in llm_match_text.lower() or 'possibilmente vera' in llm_match_text.lower():
                        matching_count = matching_count + 1
                        cv_url['found'] += skill + ' ----- '

                    st.markdown(f"Requisito: :blue[{skill}: {description}]")
                    st.markdown("Risposta GPT: ")
                    st.markdown(f"{llm_match_text}")
                    st.markdown(f"**Matching Count: {matching_count}**")
                    
                cv_url['matching'] = matching_count

            except Exception as e:
                error_string = traceback.format_exc()
                st.error(error_string)

        df = pd.DataFrame(cv_urls)
        df = df.sort_values(by=['matching'], ascending=False)
        
        st.write('')
        st.markdown('## Risultati Matching CV')
        st.markdown(df.to_html(render_links=True),unsafe_allow_html=True)

    except Exception as e:
        error_string = traceback.format_exc() 
        st.error(error_string)
        print(error_string)

try:
    
    prompt_estrazione_default = """Fai una analisi accurata della Job Description delimitata da ###
Cerca tutte le competenze richieste nella job description, mostra il ragionamento che ti ha portato a scegliere ogni singola competenza
non aggregare le competenze che trovi aggregate in singole righe
Cerca le competenze in modo completo in tutta la Job description, non solo nella parte iniziale. 
Alla fine mostra tutte le competenze trovate sotto forma di unico file json con dentro una lista di elementi chiamata "competenze" e i singoli elementi avranno chiave "skill" e valore "description"

La job description è la seguente:
###
{jd}
###

Risposta:\n"""

    prompt_confronto_default = """
Verifica se nel seguente CV delimitato da ### è presente la seguente competenza delimitata da --- 
Considera anche una possibile deduzione ad (esempio: se un candidato conosce linguaggi di programmazione è probabile che conosca anche i sistemi operativi).
Mostra il ragionamento step by step che ti ha portato alla risposta.                     
Mostra la risposta finale esclusivamente con il valore di True o False tra parentesi quadre. Se pensi che la risposta sia "possibilmente Vera" scrivi [True] e se pensi che sia "possibilmente falsa" scrivi [False]  

il CV è il seguente:
###
{cv}
###

la competenza da cercare è:
---
{skill}: {description}
---

Esempio di risposta:

Ragionamento: 'inserisci qui il tuo ragionamento'
Risposta: [True] o [False]
"""

    container_default = "documents-cv"
    
    jd_default = "Inserisci qui una job description"
    st.title("Matching CV")

    if st.session_state['delay'] is None or st.session_state['delay'] == '':
        st.session_state['delay'] = 1
    
    llm_helper = LLMHelper()
        
    st.session_state["container"] = container_default
    st.session_state["prompt_estrazione"] = prompt_estrazione_default
    st.session_state["prompt_confronto"] = prompt_confronto_default
    
    st.session_state["jd"] = st.text_area(label="Matching dei CV in archivio rispetto a questa Job Description:", value=jd_default, height=300)

    st.session_state['delay'] = st.slider("Delay in secondi tra le chiamate Open AI", 0, 5, st.session_state['delay'])
    st.button(label="Calcola match", on_click=valutazione)

    result_placeholder = st.empty()

except Exception as e:
    st.error(traceback.format_exc())