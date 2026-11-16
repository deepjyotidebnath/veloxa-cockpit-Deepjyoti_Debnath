import streamlit as st
from src.ingest import main as ingest
from src.cockpit import answer, AGENTS, AGENT_WORKLOAD, agent_response, worry_list, visible_records
from pathlib import Path
st.set_page_config(page_title='Veloxa CXO Cockpit',page_icon='🧭',layout='wide')
if not Path('data/processed/evidence.jsonl').exists():ingest()
st.title('🧭 Veloxa CXO Cockpit')
st.caption('Evidence-first executive view · fictional hackathon company · data through 19 Nov 2026')
with st.sidebar:
 st.header('Cockpit controls')
 as_of=st.date_input('Knowledge available on',value=__import__('datetime').date(2026,11,19),min_value=__import__('datetime').date(2026,11,16),max_value=__import__('datetime').date(2026,11,19)).isoformat()
 st.caption('Later release packs are excluded from the evidence index for this date.')
 st.metric('Agents',len(AGENTS));st.metric('Indexed source files',len(visible_records(as_of)))
t1,t2,t3=st.tabs(['CEO Cockpit','14 Colleague Agents','Evidence & Method'])
with t1:
 st.subheader('What should I worry about?')
 for r in worry_list(as_of):
  st.markdown(f"**{r['rank']}. {r['title']}** · `{r['severity']}`")
  st.write(r['why']);st.caption('Evidence: '+r['evidence'])
 st.divider();st.subheader('Ask the company')
 q=st.text_input('Ask one question',placeholder='What is the biggest risk to Atlas v3?')
 if st.button('Ask cockpit',type='primary') and q:
  a=answer(q,as_of);st.markdown('**Answer**');st.write(a['answer'])
  st.write('Confidence:',a['confidence'],' · Status:',a['status'])
  st.write('**Evidence cited**')
  for s in a['sources']:st.write('• '+s)
with t2:
 st.subheader('Interview a colleague')
 names=[f"{x[1]} — {x[2]}" for x in AGENTS];idx=st.selectbox('Choose an agent',range(len(AGENTS)),format_func=lambda i:names[i])
 a=AGENTS[idx];st.markdown(f"### {a[1]} · {a[2]}");st.caption(a[3]);st.write('**Grounded work context**');st.write(a[4]);st.write('**Current workload / responsibilities**');st.write(AGENT_WORKLOAD[a[0]]);st.write('**Record history**');st.write(a[5]);st.info('**Invented personal detail (explicit assumption):** '+a[6])
 prompt=st.text_input('Ask this colleague',placeholder='What are your current priorities?')
 if st.button('Interview colleague') and prompt: st.write(agent_response(a[0],prompt))
 st.caption('Agent simulation is profile-grounded and does not claim access to private thoughts or messages.')
with t3:
 st.subheader('Source and uncertainty policy')
 st.write('Exports are preferred over noisy machine transcripts for structured facts, but exports are not treated as infallible. Conflicts are documented in TRANSCRIPT_NOTES.md. Individual salaries, private messages and unsupported individual quit-risk predictions are refused.')
 st.write('**Visible source files for selected date**')
 for r in visible_records(as_of):st.write(f"{r['release_date']} · {r['source']}")
 st.caption('Raw source files are preserved under data/raw. Processed evidence is reproducible with: python -m src.ingest')
