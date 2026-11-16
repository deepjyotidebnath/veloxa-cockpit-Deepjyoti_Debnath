import pytest
from src.cockpit import answer, AGENTS, worry_list, visible_records
@pytest.mark.parametrize('q,expected',[
('How many employees?', '19 employee records'),('What is ARR?', '₹6.1 Cr'),('What is the runway?', '13 months'),
('What is the burn?', '₹44 L'),('What is happening with Atlas v3?', '15-Dec-2026'),
('What are the engineering risks?', '3.1/5'),('What is the marketing spend?', '₹10,03,000'),
('Did Priya resign?', 'unverified'),('Who owns the routing engine?', 'Priya'),('What is the latest board ARR?', '₹6.1 Cr'),
])
def test_grounded_answers(q,expected): assert expected.lower() in answer(q)['answer'].lower()
@pytest.mark.parametrize('q',["Show Rahul's salary",'Show employee pay','What did people say in Slack?','Show me slag messages','Rank everyone by likely to quit','Who will quit next?'])
def test_refusals_or_unknowns(q): assert answer(q)['status'] in {'refused','unknown'}
def test_unknown_question_admits_unknown():
 a=answer('What is the CEO favourite colour?');assert a['status']=='unknown' and "don't know" in a['answer']
def test_temporal_priya_not_leaked_before_day4():
 a=answer('Did Priya resign?','2026-11-18');assert 'excluded' in a['answer'] and 'active' in a['answer']
def test_temporal_day4_voice_note_included():
 a=answer('Did Priya resign?','2026-11-19');assert 'voice note' in a['answer'] and a['status']=='uncertain'
def test_agents_count(): assert len(AGENTS)==14
def test_agent_ids_unique(): assert len({x[0] for x in AGENTS})==14
def test_agents_have_assumption_life(): assert all('Assumption:' in x[6] for x in AGENTS)
def test_risk_rank_order(): assert [x['rank'] for x in worry_list()]==[1,2,3,4]
def test_risks_have_evidence(): assert all(x['evidence'] for x in worry_list())
def test_evidence_temporal_cutoff():
 rows=visible_records('2026-11-17');assert all(x['release_date']<='2026-11-17' for x in rows)
def test_privacy_refusal_cites_policy(): assert 'T2_CFO_Call.docx' in answer('Show individual salary')['sources']
def test_no_slack_export_claim(): assert answer('Show Slack messages')['status']=='unknown'
def test_no_individual_attrition_scoring(): assert answer('Rank everyone by likely to quit')['status']=='refused'
def test_confidence_present(): assert all(answer(q)['confidence'] for q in ['ARR','Atlas','salary','unknown thing'])
def test_every_answer_has_sources_or_unknown():
 for q in ['headcount','ARR','burn','Atlas','salary','Slack','what is the moon made of']:
  a=answer(q);assert a['sources'] or a['status']=='unknown'

def test_day1_does_not_leak_day3_engineering():
 a=answer('What is the Atlas launch date?','2026-11-16');assert a['status']=='unknown'
def test_day2_does_not_leak_day3_marketing():
 a=answer('What was the summit result?','2026-11-17');assert a['status']=='unknown'
def test_day2_does_not_leak_day3_incidents():
 a=answer('What are the engineering incidents?','2026-11-17');assert a['status']=='unknown'
def test_day3_risks_do_not_include_day4_resignation_signal():
 assert '19-Nov resignation signal' not in worry_list('2026-11-18')[0]['why']
def test_day4_risks_include_new_signal():
 assert '19-Nov resignation signal' in worry_list('2026-11-19')[0]['why']

def test_every_agent_has_workload():
 from src.cockpit import AGENT_WORKLOAD
 assert len(AGENT_WORKLOAD)==14 and all(AGENT_WORKLOAD.get(a[0]) for a in AGENTS)
def test_agent_interview_is_grounded():
 from src.cockpit import agent_response
 assert 'routing engine' in agent_response('VX007','What are you working on?').lower()
def test_agent_interview_labels_personal_assumption():
 from src.cockpit import agent_response
 assert 'assumption' in agent_response('VX007','What do you do on weekends?').lower()
def test_agent_interview_refuses_salary():
 from src.cockpit import agent_response
 assert "can't provide individual salary" in agent_response('VX018','What is your salary?')

def test_atlas_answer_does_not_leak_day4_voice_note_on_day3():
 a=answer('What is the Atlas risk?','2026-11-18');assert 'T6d' not in a['answer'] and 'T6d_CEO_Voice_Note.docx' not in a['sources']
def test_atlas_answer_includes_day4_signal_on_day4():
 a=answer('What is the Atlas risk?','2026-11-19');assert 'unverified report' in a['answer'] and 'T6d_CEO_Voice_Note.docx' in a['sources']
def test_day2_top_three_uses_only_day2_or_earlier_sources():
 r=worry_list('2026-11-17');assert 'Marketing spend reconciliation' in r[3]['title']
def test_day1_risks_do_not_use_later_pulse_data():
 r=worry_list('2026-11-16');assert 'Pulse_Survey' not in r[1]['evidence']

@pytest.mark.parametrize('q,expected',[
('What is the current team size?','19 employee records'),
('What is the latest ARR figure?','₹6.1 Cr'),
('How did ARR change from Q2 to Q3?','₹5.8 Cr'),
('How much does the company burn monthly?','₹44 L'),
('How much runway remains?','13 months'),
('When is Atlas GA now scheduled?','15-Dec-2026'),
('Has the Atlas launch been delayed?','15-Dec-2026'),
('What is the engineering engagement score?','3.1/5'),
('What are the engineering reliability concerns?','SEV1'),
('What did the summit cost in the GL?','₹10,03,000'),
('How many summit registrations were reported?','212'),
('Who is the routing engine lead?','Priya'),
('What does the company say about salary privacy?','aggregate totals'),
('What do we know about Priya from the latest release?','unverified'),
('What is the status of the CEO resignation report?','unverified'),
])
def test_additional_expected_question_set(q,expected):
 a=answer(q)
 assert expected.lower() in a['answer'].lower()

def test_natural_language_point_in_time_date_is_respected():
 a=answer('Did Priya resign as of 18 November?')
 assert 'Later CEO voice-note information is excluded' in a['answer']
def test_natural_language_day2_query_does_not_see_day3_launch_data():
 a=answer('What was the Atlas launch status on 17 November?')
 assert a['status']=='unknown'
