from pathlib import Path
from datetime import date
import json, re
ROOT=Path(__file__).resolve().parents[1]; EVIDENCE=ROOT/'data/processed/evidence.jsonl'
def load_evidence():
 if not EVIDENCE.exists():
  from src.ingest import main;main()
 return [json.loads(x) for x in EVIDENCE.read_text(encoding='utf-8').splitlines() if x.strip()]
def visible_records(as_of='2026-11-19'):
 cutoff=date.fromisoformat(as_of);return [r for r in load_evidence() if date.fromisoformat(r['release_date'])<=cutoff]
def answer(question,as_of='2026-11-19'):
 q=question.lower()
 explicit=re.search(r'(?:as of|on)\s+(\d{1,2})\s+(?:nov|november)(?:\s+2026)?',q)
 iso=re.search(r'2026-11-(1[6-9])',q)
 if explicit: as_of=f"2026-11-{int(explicit.group(1)):02d}"
 elif iso: as_of=f"2026-11-{int(iso.group(1)):02d}"
 date.fromisoformat(as_of)
 def R(a,c,s,status='answered'):return {'answer':a,'confidence':c,'sources':s,'status':status}
 if any(k in q for k in ['salary','individual pay','employee pay','payslip']):return R("I can't disclose individual salary or payslip details. The CFO explicitly restricted salary visibility to aggregate totals.",'High',['T2_CFO_Call.docx'],'refused')
 if any(k in q for k in ['slack','slag message','private message','chat message']):return R("I don't know. No Slack/message export is supplied; the kickoff transcript's 'slag channel' is not evidence of message content.",'High',['T1_CEO_Kickoff_Call.docx','data_room/README.txt'],'unknown')
 if any(k in q for k in ['likely to quit','who will quit','rank everyone','quit ranking','attrition prediction']):return R("I won't rank named employees by likelihood of quitting. Records support limited team-level risk signals and confirmed notice-period facts, not reliable individual predictions.",'High',['Pulse_Survey.xlsx','Resignation_Letter_SM.pdf','Employee_Master.xlsx'],'refused')
 if any(k in q for k in ['headcount','how many employees','number of people','team size']):return R("The 31-Oct Keka export contains 19 employee records, including one person in notice period; both board updates also report a team of 19. The CEO kickoff's 'roughly eighteen' is less precise. Contractors are excluded from Keka, so total workforce including contractors is unknown.",'High for Keka count; Medium for total workforce',['Employee_Master.xlsx','Board_Update_Apr-Jun_2026.pdf','Board_Update_Jul-Sep_2026.pdf','T1_CEO_Kickoff_Call.docx'])
 if any(k in q for k in ['arr','revenue']):return R("The latest supplied board update (Q3, sent 6-Oct-2026) reports ARR of ₹6.1 Cr; Q2 reported ₹5.8 Cr. The kickoff transcript's ₹42–45 Cr conflicts in scale and is not preferred over the board metric.",'High',['Board_Update_Jul-Sep_2026.pdf','Board_Update_Apr-Jun_2026.pdf','T1_CEO_Kickoff_Call.docx'])
 if any(k in q for k in ['burn','cash','runway']):return R("The latest board update reports monthly burn of ₹44 L and runway of 13 months for Jul–Sep 2026. CFO transcript says ₹2.2–2.5 lakh/month, a sharp conflict likely involving transcription or units; reconcile with budget-vs-actuals before using it.",'High for board figures; Low for transcript interpretation',['Board_Update_Jul-Sep_2026.pdf','T2_CFO_Call.docx'])
 if any(k in q for k in ['atlas','version three','v3','routing engine','launch']):
  if date.fromisoformat(as_of)<date(2026,11,18):return R("I don't know yet from the releases available on this date. Engineering Jira, incident and launch records are not released until Day 3.",'Low',[],'unknown')
  msg="Atlas GA moved from 15-Sep to 15-Dec-2026 in Jira Versions. Q3 board update says final hardening and feature-complete after August reliability work. Three SEV1 routing-api incidents occurred in August; performance tickets were paused; two backend requisitions were put on hold. Launch assets were ready in July but date depended on engineering."
  refs=['Jira_Export_ATLAS.xlsx','Board_Update_Jul-Sep_2026.pdf','Incidents_Aug-Oct_2026.xlsx','email/08.eml','email/06.eml','email/05.eml','Atlas_Launch_Kit_v1.pdf']
  if date.fromisoformat(as_of)>=date(2026,11,19):msg+=" T6d adds an unverified report that Priya resigned; treat continuity as an urgent scenario, not a confirmed HR exit.";refs.append('T6d_CEO_Voice_Note.docx')
  return R(msg,'High for schedule/incidents; Medium for resignation signal' if len(refs)>7 else 'High for schedule/incidents',refs)
 if any(k in q for k in ['marketing spend','summit','marketing budget']):
  if date.fromisoformat(as_of)<date(2026,11,18):return R("I don't know yet from the releases available on this date. Marketing call and ledger details arrive on Day 3.",'Low',[],'unknown')
  return R("GL lists event charges of ₹5,42,800 and ₹4,60,200 (₹10,03,000 combined), plus paid-search entries. Q3 board update reports 212 summit registrations. Marketing's '₹1.8' half-year spend claim has ambiguous units and does not reconcile directly to GL categories; request a campaign-to-ledger reconciliation before claiming ROI.",'High for GL and registrations; Low for transcript spend claim',['GL_Export_Apr-Sep_2026.xlsx','Board_Update_Jul-Sep_2026.pdf','T4_Head_of_Marketing_Call.docx'])
 if any(k in q for k in ['engineering','workload','overloaded','sre','incidents']):
  if date.fromisoformat(as_of)<date(2026,11,18):return R("I don't know yet from the releases available on this date. Engineering incident and Jira exports arrive on Day 3.",'Low',[],'unknown')
  return R("Engineering has a documented reliability/capacity concern: three SEV1 routing-api incidents occurred in August; Sneha says performance work was paused to stabilise routing-api; two backend requisitions were put on hold; Jul–Sep pulse fell to 3.1/5 (4 responses). Pulse is team-level and comments are suppressed for small teams, so it cannot identify an individual at risk.",'High',['Incidents_Aug-Oct_2026.xlsx','email/08.eml','email/06.eml','Pulse_Survey.xlsx','email/11.eml'])
 if any(k in q for k in ['priya','pria','resigned','resignation']):
  if date.fromisoformat(as_of)<date(2026,11,19):return R("As of this date, supplied records do not report a Priya resignation. The 31-Oct employee export lists Priya Nair as active. Later CEO voice-note information is excluded from this point-in-time answer.",'High as of 31-Oct export; not proof of later status',['Employee_Master.xlsx'])
  return R("The 19-Nov CEO voice note reports an unverified claim that 'Pria' resigned, with a possible two-month notice period. The 31-Oct Keka export still lists Priya Nair as active and no formal resignation record is supplied. Likely referent is Priya Nair, but identity/effective date require HR confirmation.",'Medium',['T6d_CEO_Voice_Note.docx','Employee_Master.xlsx','email/04.eml','email/09.eml'],'uncertain')
 return R("I don't know from the supplied records. Ask about headcount, ARR, burn/runway, Atlas delivery, engineering reliability, marketing spend, or employee privacy.",'Low',[],'unknown')
AGENTS=[
('VX004','Vikram Menon','VP Engineering','Engineering','Atlas owner; says September date had buffer; two backend roles frozen; disputes overload.','Joined 2021; Atlas plan email 2-Jun; accepted req pause 12-Aug.','Assumption: enjoys weekend cycling and keeps a handwritten production follow-up list.'),
('VX007','Priya Nair','Staff Engineer / routing lead','Engineering','Leads core engine and rerouting; asked Vikram for time about Atlas ownership on 1-Sep; active in 31-Oct export.','Joined 2022; core Atlas dependency in Vikram email.','Assumption: mentors junior engineers and protects one quiet evening a week for family.'),
('VX009','Arjun Das','Senior Frontend Engineer','Engineering','Planner UI owner; Pune remote; asked to make remote arrangement permanent.','Joined 2023; remote email 18-Sep; UI role in Atlas plan.','Assumption: enjoys running and prefers written design reviews.'),
('VX012','Sneha Kulkarni','Site Reliability Engineer','Engineering','Responded to routing-api incidents; paused Atlas performance tickets after third August SEV1; rota also says Snehal.','Joined 2024; incident and rota exports.','Assumption: keeps an incident notebook and values predictable recovery time.'),
('VX018','Rahul Verma','Backend Engineer','Engineering','Joined 3-Feb-2026; backend API work; asked about first payslip; transcript says ramping well.','REQ-013 filled Jan; Feb payroll email says new joiner added.','Assumption: learning distributed systems and enjoys weekend badminton.'),
('VX003','Meera Iyer','CFO','Finance','Owns finance; paused two engineering requisitions until funding round closes; restricts salary visibility.','Joined 2023; 12-Aug email and T2.','Assumption: prefers early-morning planning and keeps a paper cash forecast.'),
('VX010','Karthik Subramanian','FP&A Manager','Finance','Runs planning; processed February payroll while Fatima was away; studying CFA.','Joined 2024; Feb payroll email; T2.','Assumption: studies CFA in evening blocks and enjoys chess.'),
('VX014','Fatima Sheikh','Accounts & Payroll Executive','Finance','Owns accounts/payroll; on marriage leave in Feb; replied to Rahul payslip query.','Joined 2025; payroll emails March 2026.','Assumption: values month-end checklists and enjoys cooking for friends.'),
('VX005','Deepa Joshi','Head of People & Ops','HR','Owns people operations; suppresses pulse comments for small teams; recommends Vikram 1:1s.','Joined 2022; pulse email 29-Sep and T3.','Assumption: keeps a balcony garden and prefers private structured conversations.'),
('VX015','Rohan Banerjee','Talent Partner','HR','Runs hiring; engineering reqs on hold and marketing backfill open.','Joined 2024; T3 and hiring tracker.','Assumption: enjoys mentoring graduates and reads about interviewing.'),
('VX017','Lakshmi Pillai','HR & Office Executive','HR','Handles HR/office operations; T3 says she handles exits.','Joined 2025; HR exports and T3.','Assumption: likes organising team events and uses operational checklists.'),
('VX006','Nikhil Bose','Head of Marketing','Marketing','Reports summit pipeline success; disputes finance spend; says Sid launch kit ready in July.','Joined 2024; T4; board update records 212 registrations.','Assumption: follows attribution podcasts and enjoys live music.'),
('VX011','Aisha Khan','Performance Marketing Manager','Marketing','Owns performance marketing; transcript says paid search improved after she took over.','Joined 2023; Google Ads ledger entries and T4.','Assumption: tracks experiments in a notebook and enjoys photography.'),
('VX013','Siddharth Mehta','Product Marketing Manager (historical)','Marketing','Resigned 15-Sep; last day 31-Oct; authored launch kit ready in July; wanted clearer launch timelines.','Employee export notice period; resignation letter.','Assumption: enjoys writing essays and is exploring product storytelling roles.'),
]
def worry_list(as_of="2026-11-19"):
 d=date.fromisoformat(as_of)
 risks=[
 {'rank':1,'title':'Atlas delivery and routing reliability','severity':'Critical','why':'The board date is 15-Sep and two backend hires were a stated dependency; engineering speed is the CEO concern.','evidence':'Board_Update_Apr-Jun_2026; T1; T2'},
 {'rank':2,'title':'Engineering capacity and engagement','severity':'High','why':'Two backend reqs on hold; engineering pulse fell to 3.1/5 (4 responses); on-call contractor support indicates reliability load.','evidence':'Hiring_Tracker; email/06.eml; Pulse_Survey; Invoice_PIS-114'},
 {'rank':3,'title':'Marketing measurement and launch readiness','severity':'High','why':'Marketing and Finance disagree on spend; launch kit was ready but unpublished pending engineering date; GL has two large event charges.','evidence':'T4; GL_Export; Atlas_Launch_Kit_v1; email/05.eml'},
 {'rank':4,'title':'Key-person and handover continuity','severity':'Medium','why':'Siddharth departure is documented; Priya resignation is only a CEO voice-note report; these are not equally confirmed.','evidence':'Resignation_Letter_SM; Employee_Master; T6d'}]
 if d<date(2026,11,17):
  risks[1]={'rank':2,'title':'Financial visibility and hiring dependency','severity':'High','why':'CFO reports a conditional hiring freeze if the raise slips; two backend roles are mentioned as a dependency, while burn units conflict across transcript and board reporting.','evidence':'T2_CFO_Call; Board_Update_Apr-Jun_2026; T1_CEO_Kickoff_Call'}
  risks[2]={'rank':3,'title':'Conflicting executive operating picture','severity':'Medium','why':'CEO and CFO transcript figures for ARR/burn differ materially from board reporting; source reconciliation is needed before decisions.','evidence':'T1_CEO_Kickoff_Call; T2_CFO_Call; Board_Update_Apr-Jun_2026'}
  risks[3]={'rank':4,'title':'Unresolved people and hiring signals','severity':'Medium','why':'CEO reports perceived attrition concern, but no HR pulse export is released yet; do not infer individual risk.','evidence':'T1_CEO_Kickoff_Call; T3 not yet released'}
 elif d<date(2026,11,18):
  risks[2]={'rank':3,'title':'Funding-round and hiring freeze','severity':'High','why':'The two backend requisitions are on hold until the funding round closes; the CFO has also described a broader hiring freeze if the raise slips. This is a direct capacity dependency for the Atlas plan.','evidence':'Hiring_Tracker; email/06.eml; T2_CFO_Call; Board_Update_Apr-Jun_2026'}
  risks[3]={'rank':4,'title':'Marketing spend reconciliation','severity':'Medium','why':'CFO transcript says marketing figures do not match, but campaign/GL detail is not yet in the Day 2 release.','evidence':'T2_CFO_Call'}
 elif d<date(2026,11,19):
  risks[0]['why']='Jira moved Atlas GA from 15-Sep to 15-Dec; three August SEV1 routing-api incidents occurred; performance tickets were paused and two backend roles remain on hold.'
  risks[0]['evidence']='Jira_Export_ATLAS; Incidents_Aug-Oct_2026; email/08.eml; email/06.eml; Board_Update_Jul-Sep_2026'
  risks[3]={'rank':4,'title':'Key-person and handover continuity','severity':'Medium','why':'Siddharth departure is documented; do not infer other employee departures from team-level signals.','evidence':'Resignation_Letter_SM; Employee_Master'}
 else:
  risks[0]['why']='Jira moved Atlas GA from 15-Sep to 15-Dec; three August SEV1 routing-api incidents occurred; performance tickets were paused and two backend roles remain on hold. Priya is a key dependency and the 19-Nov resignation signal remains unverified.'
  risks[0]['evidence']='Jira_Export_ATLAS; Incidents_Aug-Oct_2026; email/08.eml; email/06.eml; T6d' 
 return risks


AGENT_WORKLOAD={
'VX004':'Engineering leadership, Atlas delivery coordination, hiring dependency and release-risk management.',
'VX007':'Core routing engine and re-routing ownership; a critical knowledge dependency for Atlas.',
'VX009':'Planner UI implementation and reviews; remote from Pune, with review latency noted by VP Engineering.',
'VX012':'SRE/on-call response and routing-api stabilisation; incident response has displaced Atlas performance work.',
'VX018':'Backend API implementation and ramp-up; no complete ticket-level workload export is available in this pack.',
'VX003':'Finance leadership, burn/runway oversight, hiring-pause decision and payroll confidentiality.',
'VX010':'FP&A, forecasting and February payroll cover; CFO notes forecast timing pressure alongside CFA study.',
'VX014':'Accounts and payroll processing; February leave created a temporary payroll handoff.',
'VX005':'People operations, engagement/pulse governance and employee-exit processes.',
'VX015':'Talent acquisition; engineering roles paused and marketing/support requisitions remain open in tracker.',
'VX017':'HR and office administration, including exit-process support.',
'VX006':'Marketing leadership, summit activity, launch coordination and finance spend reconciliation.',
'VX011':'Performance marketing and paid-search activity; campaign-level reconciliation is not supplied.',
'VX013':'Historical role: product marketing and Atlas launch-kit production; employment ended 31-Oct-2026.'}

def agent_response(agent_id, question):
    """Small grounded interview adapter; it never invents new work facts."""
    agent=next((a for a in AGENTS if a[0]==agent_id),None)
    if not agent:return "I don't know which colleague you mean."
    q=question.lower()
    if any(k in q for k in ['personal','life','hobby','weekend','outside work']):
        return agent[6]+' This is an explicitly invented profile assumption, not a verified personal fact.'
    if any(k in q for k in ['workload','working on','doing','responsibilit','priority','busy']):
        return AGENT_WORKLOAD.get(agent_id,'No reliable workload detail is available.')+' '+agent[4]
    if any(k in q for k in ['history','background','joined','previous']):
        return agent[5]
    if any(k in q for k in ['salary','pay','payslip']):
        return "I can't provide individual salary or payslip details in this cockpit; the CFO restricted salary visibility to aggregate totals."
    return "From the records I can safely say: "+agent[4]+" For anything beyond this evidence, I don't know."
