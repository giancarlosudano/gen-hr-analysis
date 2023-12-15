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
    

    st.title("Lettere di Vettura")
    
    import datetime
    import pandas as pd
    import numpy as np
    
    coldate1, coldate2 = st.columns([1,1])
    with coldate1:
        date_begin = st.date_input("Data Inizio", datetime.date(2023, 10, 1))
    with coldate2:
        date_end = st.date_input("Data Fine", datetime.date(2023, 10, 30))
    
    llm_helper = LLMHelper()
        
    st.button(label="Estrazione Dati", on_click=valutazione)
    
    with st.expander("Lettera di Vettura XXX", expanded=False):
        st.write("Estrazione Dati da Email")
        st.text_input("Oggetto Email:", value="Oggetto Email")
        st.text_input("Corpo Email", value="Corpo della Email")
        st.text_input("Allegati", value="Nomi file allegati")
        st.divider()
        st.write("Estrazione Dati da allegati Email")
        st.text_area("Mittente (1)", value="Mittente da CIM", height=100)
        st.text_input("Codice Mittente (2)", value="Valore da CIM")
        st.text_input("Codice Mittente (3)", value="Valore da CIM")
        st.text_area("Destinatario (4)", value="Valore da CIM", height=100)
        st.text_input("Codice Destinatario (5)", value="Valore da CIM")
        st.text_input("Codice Destinatario (6)", value="Valore da CIM")
        st.text_area("Raccordo di consegna (10)", value="Valore da CIM", height=100)
        st.text_input("Codice Raccordo di Destinazione (11)", value="Valore da CIM")
        st.text_input("Codice Stazione Destinatario (12)", value="Valore da CIM")
        st.text_area("Condizioni Commerciali (13)", value="Valore da CIM")
        st.text_input("Condizioni Commerciali Codice (14)", value="Valore da CIM")
        st.text_area("Luogo di Consegna / Presa in carico (16)", value="Valore da CIM")
        st.text_input("Codice Luogo di Consegna / Presa in carico (17)", value="Valore da CIM")
        st.text_area("Matricola carro / distinta (18)", value="Valore da CIM")
        st.text_input("Codice Affrancazione (49)", value="Valore da CIM")
        st.text_area("Altri trasportatori e Ruolo (57)", value="Valore da CIM")
        st.text_input("Trasportatore contrattuale (58)", value="Valore da CIM")
        
        colid1, colid2 = st.columns([1,1])
        with colid1:
            st.write("Identificazione Spedizione (62)")
            st.text_input("Codice Paese", value="Valore da CIM")
            st.text_input("Codice Stazione", value="Valore da CIM")
            st.text_input("Codice Impresa", value="Valore da CIM")
            st.text_input("Codice Spedizione", value="Valore da CIM")
        
        with colid2:
            st.write("Sistema Orpheus")
            st.text_input("Codice Paese (2)", value="Valore da CIM")
            st.text_input("Codice Stazione (2)", value="Valore da CIM")
            st.text_input("Codice Impresa (2)", value="Valore da CIM")
            st.text_input("Codice Spedizione (2)", value="Valore da CIM")
        
        st.write("Luogo e Data di stesura (29)")
        col1, col2 = st.columns([1,1])
        with col1:
            st.text_input("Luogo", value="Valore da CIM")
        with col2:
            st.text_input("Data", value="Valore da CIM")
            
        st.write("Seconda Pagina CIM")
        df1 = pd.DataFrame(np.random.randn(10, 5), columns=("col %d" % i for i in range(5)))
        st.table(df1)
        
        st.write("Terza Pagina CIM")
        df2 = pd.DataFrame(np.random.randn(10, 5), columns=("col %d" % i for i in range(5)))
        st.table(df2)
        
        st.write("Quarta Pagina CIM")
        df3 = pd.DataFrame(np.random.randn(10, 5), columns=("col %d" % i for i in range(5)))
        st.table(df3)

except Exception as e:
    st.error(traceback.format_exc())