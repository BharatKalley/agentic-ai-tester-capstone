import asyncio
import json
import os
import sys
from pathlib import Path

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import streamlit as st

from agents.extractor_agent import extract_requirements
from agents.orchestrator import run_workflow, run_execution_only, run_workflow_with_selective_regeneration
from utils.test_environment import TestEnvironment

st.set_page_config(page_title='Agentic AI Tester', layout='wide')
st.title('🤖 Agentic AI Tester')
st.caption('Agent A extracts requirements, Agent B generates Playwright tests, and Agent C validates hallucinations, missing scripts, edge cases and coverage with up to 5 selective retries.')

Path('data').mkdir(exist_ok=True)
Path('generated_tests').mkdir(exist_ok=True)
Path('reports').mkdir(exist_ok=True)

with st.sidebar:
    st.header('Project Controls')
    execute_tests = st.checkbox('Execute tests after generation', value=True)
    max_requirements = st.number_input('Max requirements to process (0 = all)', min_value=0, value=10, help='Use a smaller number for quick demos.')
    st.info('For full execution install Node dependencies: npm install && npx playwright install')

tab1, tab2, tab3, tab4 = st.tabs(['Generate & Validate', 'Run Tests', 'Reports', 'Environment'])

with tab1:
    uploaded_file = st.file_uploader('Upload SRS PDF', type=['pdf'])
    if uploaded_file and st.button('Run Agentic Workflow', type='primary'):
        pdf_path = Path('data') / 'uploaded_srs.pdf'
        pdf_path.write_bytes(uploaded_file.getbuffer())
        st.success(f'Uploaded to {pdf_path}')

        with st.spinner('Agent A extracting, Agent B generating, Agent C validating, executing, and fixing failed scripts...'):
            result = run_workflow(str(pdf_path), execute_tests=execute_tests, max_requirements=(max_requirements or None))
        st.session_state.last_results = result

        total = len(result)
        validation_passed = sum(1 for r in result if r.get('validation', '').upper().startswith('PASS'))
        executed = sum(1 for r in result if 'execution' in r)
        passed = sum(1 for r in result if r.get('execution', {}).get('status') == 'PASSED')
        c1, c2, c3, c4 = st.columns(4)
        c1.metric('Requirements', total)
        c2.metric('Validation Passed', validation_passed)
        c3.metric('Executed', executed)
        c4.metric('Execution Passed', passed if executed else 'N/A')

        for idx, res in enumerate(result, 1):
            req = res['requirement']
            with st.expander(f"{idx}. {req.get('id', '')} - {req.get('feature', 'Requirement')}"):
                st.write('Endpoint:', req.get('endpoint'))
                st.json(req)
                st.write('Validation:', res.get('validation'))
                st.write('Attempts:', res.get('attempts'))
                st.write('Script:', res.get('script_file'))
                if 'execution' in res:
                    st.json(res['execution'])

with tab2:
    test_dir = st.text_input('Test Directory', value='generated_tests')
    if st.button('Execute Generated Tests', type='primary'):
        with st.spinner('Running Playwright tests...'):
            results = run_execution_only(test_dir)
        st.json(results)

with tab3:
    if 'last_results' in st.session_state:
        if st.button('Selective Regeneration From Last Results'):
            with st.spinner('Regenerating only failed or missing scripts...'):
                results = run_workflow_with_selective_regeneration('data/uploaded_srs.pdf', st.session_state.last_results)
            st.session_state.last_results = results
            st.json(results)
        st.json(st.session_state.last_results)
    else:
        st.info('Run a workflow first to see reports.')

with tab4:
    env_check = TestEnvironment.full_environment_check()
    st.json(env_check)
