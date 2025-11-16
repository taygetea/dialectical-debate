#!/usr/bin/env python3
"""
Streamlit App for Dialectical Debate System

Interactive UI for running debates, viewing graphs, and exploring narratives.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from session import DebateSession, generate_session_name, generate_continuation_strategy
from dialectic_poc import Agent, Logger, Observer
from debate_graph import NodeType, EdgeType
from agent_generation import generate_agent_ensemble
from phase2_observer_generation import generate_observer_ensemble
import tempfile
import os
import glob

# Page configuration
st.set_page_config(
    page_title="Dialectical Debate System",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for chat bubbles
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    flex-direction: column;
    color: #1a1a1a;
}
.literalist, .agent-0 {
    background-color: #e3f2fd;
    border-left: 4px solid #1976d2;
}
.symbolist, .agent-1 {
    background-color: #f3e5f5;
    border-left: 4px solid #7b1fa2;
}
.structuralist, .agent-2 {
    background-color: #e8f5e9;
    border-left: 4px solid #388e3c;
}
.agent-3 {
    background-color: #fff3e0;
    border-left: 4px solid #f57c00;
}
.agent-4 {
    background-color: #fce4ec;
    border-left: 4px solid #c2185b;
}
.agent-name {
    font-weight: bold;
    margin-bottom: 0.5rem;
}
.round-badge {
    background-color: #666;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.8rem;
    display: inline-block;
    margin-left: 0.5rem;
}
.node-card {
    border: 1px solid #ddd;
    border-radius: 0.5rem;
    padding: 1rem;
    margin-bottom: 1rem;
}
.node-header {
    font-weight: bold;
    color: #1976d2;
    margin-bottom: 0.5rem;
}
.tag {
    background-color: #e0e0e0;
    padding: 0.2rem 0.5rem;
    border-radius: 0.3rem;
    font-size: 0.8rem;
    margin-right: 0.3rem;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# Helper functions for session management
def get_saved_sessions():
    """Get list of all saved sessions from output directory"""
    output_dir = Path("output")
    if not output_dir.exists():
        return []

    sessions = []
    for session_dir in output_dir.iterdir():
        if session_dir.is_dir():
            # Look for DAG file
            dag_files = list(session_dir.glob("*_dag.json"))
            if dag_files:
                sessions.append({
                    'name': session_dir.name,
                    'path': session_dir,
                    'dag_path': dag_files[0],
                    'modified': dag_files[0].stat().st_mtime
                })

    # Sort by modification time (newest first)
    sessions.sort(key=lambda x: x['modified'], reverse=True)
    return sessions

def format_session_display_name(session_name: str) -> str:
    """Format session name for display (remove timestamp, capitalize)"""
    # Try to remove timestamp pattern (YYYYMMDD_HHMMSS)
    parts = session_name.split('_')
    if len(parts) >= 2 and parts[-2].isdigit() and len(parts[-2]) == 8:
        # Has timestamp, remove last 2 parts
        display_name = '_'.join(parts[:-2])
    else:
        display_name = session_name

    # Capitalize and replace underscores with spaces for display
    return display_name.replace('_', ' ').title()

# Initialize session state
if 'session' not in st.session_state:
    st.session_state.session = None
if 'current_node' not in st.session_state:
    st.session_state.current_node = None
if 'debate_running' not in st.session_state:
    st.session_state.debate_running = False
if 'passage_for_naming' not in st.session_state:
    st.session_state.passage_for_naming = None

# Sidebar: Configuration
st.sidebar.title("⚙️ Configuration")

# Agent customization
st.sidebar.subheader("Debate Agents")

# Toggle for auto-generation
use_auto_agents = st.sidebar.checkbox(
    "🤖 Auto-generate agents from passage",
    value=False,
    help="Generate debate agents specifically tuned to the passage using LLM"
)

if use_auto_agents:
    st.sidebar.info("Agents will be generated when you start the debate based on the passage content.")
    num_auto_agents = st.sidebar.slider("Number of agents", 2, 5, 3)
else:
    # Manual agent configuration
    st.sidebar.markdown("*Customize the debate agents below:*")

if not use_auto_agents:
    with st.sidebar.expander("🔍 The Literalist", expanded=False):
        lit_stance = st.text_area(
            "Stance",
            "You interpret text literally and factually, focusing on what is explicitly stated.",
            key="lit_stance"
        )
        lit_focus = st.text_input(
            "Focus",
            "Concrete claims and logical consistency",
            key="lit_focus"
        )

    with st.sidebar.expander("🌟 The Symbolist", expanded=False):
        sym_stance = st.text_area(
            "Stance",
            "You see deeper symbolic and archetypal meanings beneath the surface.",
            key="sym_stance"
        )
        sym_focus = st.text_input(
            "Focus",
            "Metaphorical significance and universal patterns",
            key="sym_focus"
        )

    with st.sidebar.expander("🏛️ The Structuralist", expanded=False):
        str_stance = st.text_area(
            "Stance",
            "You analyze underlying structures, patterns, and formal relationships.",
            key="str_stance"
        )
        str_focus = st.text_input(
            "Focus",
            "Systems, frameworks, and organizational principles",
            key="str_focus"
        )

# Debate settings
st.sidebar.subheader("Debate Settings")
max_rounds = st.sidebar.slider("Max Rounds (Main)", 2, 5, 3)
branch_rounds = st.sidebar.slider("Max Rounds (Branch)", 1, 4, 2)

# Auto-branching toggle
auto_branch = st.sidebar.checkbox(
    "🌿 Auto-detect and explore branch questions",
    value=True,
    help="After main debate, automatically generate an observer to identify tensions and run a branch debate"
)

if auto_branch:
    num_observers = st.sidebar.slider("Number of observers", 1, 3, 1,
                                      help="Generate multiple observers to explore different branch angles")

# Session management
st.sidebar.subheader("📂 Session Management")

# Show saved sessions
saved_sessions = get_saved_sessions()

if saved_sessions:
    st.sidebar.markdown("**Load Previous Session:**")

    session_options = {
        f"{format_session_display_name(s['name'])} ({datetime.fromtimestamp(s['modified']).strftime('%m/%d %H:%M')})": s
        for s in saved_sessions
    }

    selected_session_label = st.sidebar.selectbox(
        "Select a session:",
        ["-- Create New --"] + list(session_options.keys()),
        key="session_selector"
    )

    if selected_session_label != "-- Create New --":
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button("📂 Load Session", use_container_width=True):
                selected_session = session_options[selected_session_label]
                st.session_state.session = DebateSession(
                    selected_session['name'],
                    load_existing=True
                )

                # Load agents from first node if available
                if st.session_state.session.dag.nodes:
                    first_node = list(st.session_state.session.dag.nodes.values())[0]
                    st.session_state.current_node = first_node

                st.sidebar.success(f"✅ Loaded: {format_session_display_name(selected_session['name'])}")
                st.rerun()

        with col2:
            # Delete button
            if st.button("🗑️", help="Delete this session", use_container_width=True):
                import shutil
                selected_session = session_options[selected_session_label]
                shutil.rmtree(selected_session['path'])
                st.sidebar.warning(f"Deleted: {selected_session['name']}")
                st.rerun()

    st.sidebar.divider()

# New session creation
st.sidebar.markdown("**Create New Session:**")

# Show current session info if loaded
if st.session_state.session:
    st.sidebar.info(f"**Current:** {format_session_display_name(st.session_state.session.session_name)}")
    stats = st.session_state.session.get_stats()
    st.sidebar.markdown(f"_Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}_")
else:
    st.sidebar.info("No session loaded. Create new or load existing.")

if st.sidebar.button("➕ Create New Session"):
    # Will be created when debate starts with auto-generated name
    st.session_state.session = None
    st.session_state.current_node = None

    if not use_auto_agents:
        # Create manual agents
        agents = [
            Agent("The Literalist", lit_stance, lit_focus),
            Agent("The Symbolist", sym_stance, sym_focus),
            Agent("The Structuralist", str_stance, str_focus)
        ]
        st.session_state.agents = agents
    else:
        # Will generate agents from passage when debate starts
        st.session_state.agents = None

    st.sidebar.success("✅ Ready for new session. Session name will be auto-generated from passage.")

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_debate_turns' not in st.session_state:
    st.session_state.current_debate_turns = []
if 'agents' not in st.session_state:
    st.session_state.agents = None

# Main area: Tabs
tab1, tab2, tab3 = st.tabs(["💬 Debate Chat", "🕸️ Graph", "📖 Narrative"])

# TAB 1: Debate Chat (Unified Input + Live Debate)
with tab1:
    st.header("💬 Debate Chat")

    # Show existing debate history in chat format
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user':
            with st.chat_message("user"):
                st.markdown(msg['content'])
        elif msg['role'] == 'system':
            with st.chat_message("assistant", avatar="🎭"):
                st.markdown(msg['content'])
        elif msg['role'] == 'agent':
            with st.chat_message("assistant", avatar=msg.get('avatar', '🤔')):
                st.markdown(f"**{msg['name']}** (Round {msg.get('round', '?')})")
                st.markdown(msg['content'])

    # Input area at bottom
    st.divider()

    # Passage input
    passage = st.text_area(
        "Enter a passage to debate:",
        height=150,
        placeholder="Enter philosophical text, quotes, or any passage you want the agents to analyze...",
        key="passage_input"
    )

    if st.button("🚀 Start Main Debate", type="primary", disabled=not passage or st.session_state.debate_running, use_container_width=True):
        st.session_state.debate_running = True

        # Add user passage to chat
        st.session_state.chat_history.append({
            'role': 'user',
            'content': f"**Passage to debate:**\n\n{passage}"
        })

        # Auto-generate session name if no session exists
        if st.session_state.session is None:
            session_name = generate_session_name(passage)
            st.session_state.session = DebateSession(session_name)
            st.session_state.chat_history.append({
                'role': 'system',
                'content': f"📁 Created session: **{format_session_display_name(session_name)}**"
            })

        # Generate agents if needed
        if st.session_state.agents is None:
            agents = generate_agent_ensemble(passage, num_agents=num_auto_agents, verbose=False)
            st.session_state.agents = agents
            agent_names = ', '.join([a.name for a in agents])
            st.session_state.chat_history.append({
                'role': 'system',
                'content': f"🤖 Generated agents: **{agent_names}**"
            })
        else:
            agents = st.session_state.agents

        # Add system message for debate start
        st.session_state.chat_history.append({
            'role': 'system',
            'content': f"🎭 Starting main debate ({max_rounds} rounds)..."
        })

        # Rerun to show setup messages
        st.rerun()

    # Check if debate needs to continue (progressive execution)
    if st.session_state.debate_running and st.session_state.session:
        # Initialize debate state if needed
        if 'debate_state' not in st.session_state:
            st.session_state.debate_state = {
                'passage': passage,
                'round': 1,
                'agent_idx': 0,
                'transcript': [],
                'max_rounds': max_rounds
            }

        state = st.session_state.debate_state
        agents = st.session_state.agents

        # Check if debate is complete
        if state['round'] > state['max_rounds']:
            # Finalize debate
            from dialectic_poc import DebateTurn
            from node_factory import NodeFactory

            # Create node
            node = NodeFactory.create_node_from_transcript(
                node_type=NodeType.EXPLORATION,
                transcript=state['transcript'],
                passage=state['passage'],
                branch_question=None
            )

            # Add to DAG
            st.session_state.session.dag.add_node(node)
            st.session_state.session.save()
            st.session_state.current_node = node

            # Add completion message
            st.session_state.chat_history.append({
                'role': 'system',
                'content': f"✅ Main debate complete! **{node.topic}**"
            })

            # Cleanup
            st.session_state.debate_running = False
            del st.session_state.debate_state

            st.rerun()

        else:
            # Generate next turn
            agent = agents[state['agent_idx']]

            # Show status
            with st.status(f"Round {state['round']}: {agent.name} is thinking...", expanded=True):
                # Build prompts
                system_prompt = agent.get_system_prompt()

                if state['round'] == 1:
                    user_prompt = f"Passage:\n{state['passage']}\n\nProvide your opening analysis."
                else:
                    from dialectic_poc import DebateTurn
                    recent_turns = "\n\n".join([
                        f"{t.agent_name}: {t.content}"
                        for t in state['transcript'][-(len(agents)*2):]
                    ])
                    user_prompt = f"Previous discussion:\n{recent_turns}\n\nYour response:"

                # Make LLM call
                from dialectic_poc import llm_call, DebateTurn
                response = llm_call(system_prompt, user_prompt, temperature=0.7)

                # Create turn
                turn = DebateTurn(agent.name, response, state['round'])
                state['transcript'].append(turn)

                # Add to chat history
                avatar_map = {0: '📖', 1: '✨', 2: '🏛️', 3: '🎨', 4: '🔬'}
                st.session_state.chat_history.append({
                    'role': 'agent',
                    'name': agent.name,
                    'content': response,
                    'round': state['round'],
                    'avatar': avatar_map.get(state['agent_idx'], '🤔')
                })

            # Advance to next agent/round
            state['agent_idx'] += 1
            if state['agent_idx'] >= len(agents):
                state['agent_idx'] = 0
                state['round'] += 1
                # Add round marker for next round
                if state['round'] <= state['max_rounds']:
                    st.session_state.chat_history.append({
                        'role': 'system',
                        'content': f"**Round {state['round']}**"
                    })

            # Rerun to show turn and continue
            st.rerun()

            # Auto-branch if enabled
            if auto_branch:
                with st.spinner(f"Generating {num_observers} observer(s) to identify branch questions..."):
                    # Generate observers
                    observers_data = generate_observer_ensemble(
                        passage,
                        num_perspectives=num_observers,
                        verbose=False
                    )

                    # Convert to Observer objects
                    observers = [
                        Observer(
                            name=obs['name'],
                            bias=obs['bias'],
                            focus=obs['focus'],
                            blind_spots=obs['blind_spots'],
                            example_questions=obs.get('example_questions', []),
                            anti_examples=obs.get('anti_examples', [])
                        )
                        for obs in observers_data
                    ]

                # Run branch debates for each observer
                for i, observer in enumerate(observers, 1):
                    with st.spinner(f"Observer {i}/{num_observers} ({observer.name}) identifying branch..."):
                        # Get transcript text for observer
                        transcript_text = "\n\n".join([
                            f"**{turn['agent_name']}** (Round {turn['round_num']}):\n{turn['content']}"
                            for turn in node.turns_data
                        ])

                        # Observer identifies branch question
                        branch_question = observer.identify_branch(transcript_text, passage)

                    st.info(f"🔍 {observer.name} asks: {branch_question}")

                    with st.spinner(f"Running branch debate {i}/{num_observers}..."):
                        # Create new logger for branch
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
                            branch_log_path = f.name

                        branch_logger = Logger(branch_log_path)

                        # Run branch debate
                        branch_node = st.session_state.session.process_branch(
                            branch_question=branch_question,
                            parent_node_id=node.node_id,
                            agents=agents,
                            logger=branch_logger,
                            max_rounds=branch_rounds
                        )

                        st.success(f"✅ Branch {i} complete: {branch_node.topic[:60]}...")

            st.session_state.debate_running = False
            st.success(f"✅ All debates complete! Main node + {num_observers if auto_branch else 0} branch(es)")
            st.rerun()

# TAB 2: Graph View
with tab2:
    st.header("Debate Graph (DAG)")

    if st.session_state.session and st.session_state.session.dag.nodes:
        # Try to visualize graph
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
            from io import BytesIO

            # Create networkx graph
            G = nx.DiGraph()

            # Add nodes
            for node_id, node in st.session_state.session.dag.nodes.items():
                G.add_node(
                    node_id,
                    label=node.topic[:40] + "...",
                    type=node.node_type.value
                )

            # Add edges
            edge_colors = []
            edge_labels = {}
            for edge in st.session_state.session.dag.edges:
                G.add_edge(edge.from_node_id, edge.to_node_id)
                edge_labels[(edge.from_node_id, edge.to_node_id)] = edge.edge_type.value

                # Color by type
                if edge.edge_type == EdgeType.BRANCHES_FROM:
                    edge_colors.append('blue')
                elif edge.edge_type == EdgeType.CONTRADICTS:
                    edge_colors.append('red')
                else:
                    edge_colors.append('green')

            # Layout
            pos = nx.spring_layout(G, k=2, iterations=50)

            # Draw
            fig, ax = plt.subplots(figsize=(12, 8))

            # Node colors by type
            node_colors = []
            for node_id in G.nodes():
                node = st.session_state.session.dag.get_node(node_id)
                if node.node_type == NodeType.SYNTHESIS:
                    node_colors.append('lightgreen')
                elif node.node_type == NodeType.IMPASSE:
                    node_colors.append('lightcoral')
                elif node.node_type == NodeType.EXPLORATION:
                    node_colors.append('lightblue')
                else:
                    node_colors.append('lightgray')

            nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=4000,
                                  alpha=0.9, node_shape='s', ax=ax)  # Square nodes for text
            nx.draw_networkx_edges(G, pos, edge_color=edge_colors, arrows=True,
                                  arrowsize=20, width=2, alpha=0.6, ax=ax)

            # Labels using concise summaries
            labels = {}
            all_nodes_list = list(st.session_state.session.dag.get_all_nodes())
            for i, node_id in enumerate(G.nodes()):
                node = st.session_state.session.dag.get_node(node_id)
                # Use concise summary if available, otherwise truncate topic
                if node.concise_summary:
                    labels[node_id] = f"{i+1}.\n{node.concise_summary}"
                else:
                    labels[node_id] = f"{i+1}.\n{node.topic[:30]}..."

            nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='normal', ax=ax)

            plt.axis('off')
            plt.tight_layout()

            st.pyplot(fig)

            # Legend
            st.markdown("""
            **Node Colors:**
            - 🟢 Green: Synthesis (agreement reached)
            - 🔴 Red: Impasse (irreconcilable disagreement)
            - 🔵 Blue: Exploration (open-ended investigation)

            **Edge Colors:**
            - Blue: Branches from
            - Red: Contradicts
            - Green: Elaborates
            """)

            # Node reference table
            st.divider()
            st.subheader("Node Reference")

            all_nodes = st.session_state.session.dag.get_all_nodes()
            for i, node in enumerate(all_nodes, 1):
                # Emoji based on type
                if node.node_type == NodeType.SYNTHESIS:
                    emoji = "🟢"
                elif node.node_type == NodeType.IMPASSE:
                    emoji = "🔴"
                elif node.node_type == NodeType.EXPLORATION:
                    emoji = "🔵"
                else:
                    emoji = "⚪"

                st.markdown(f"**{i}.** {emoji} [{node.node_type.value.upper()}] {node.topic}")

                # Show summary if available
                if node.resolution:
                    with st.expander(f"View summary for node {i}"):
                        st.markdown(node.resolution)

        except ImportError:
            st.warning("Graph visualization requires networkx and matplotlib. Install with: `pip install networkx matplotlib`")

            # Fallback: text representation
            st.subheader("Nodes")
            for i, node in enumerate(st.session_state.session.dag.get_all_nodes(), 1):
                st.markdown(f"**{i}.** [{node.node_type.value}] {node.topic}")

            st.subheader("Edges")
            for edge in st.session_state.session.dag.edges:
                from_node = st.session_state.session.dag.get_node(edge.from_node_id)
                to_node = st.session_state.session.dag.get_node(edge.to_node_id)
                st.markdown(f"- {from_node.topic[:30]}... **{edge.edge_type.value}** → {to_node.topic[:30]}...")
    else:
        st.info("No graph yet. Create a session and run debates to build the graph.")

# TAB 3: Narrative View
with tab3:
    st.header("Linearized Narrative")

    if st.session_state.session and st.session_state.session.dag.nodes:
        # Generate narrative
        with st.spinner("Generating narrative..."):
            narrative = st.session_state.session.export_narrative()

        # Display with markdown
        st.markdown(narrative)

        # Download button
        st.download_button(
            label="📥 Download Narrative",
            data=narrative,
            file_name=f"{st.session_state.session.session_name}_narrative.md",
            mime="text/markdown"
        )
    else:
        st.info("No narrative yet. Create a session and run debates first.")

# Footer
st.sidebar.divider()
st.sidebar.markdown("""
### About
Dialectical Debate System v1.0

Multi-perspective debates that build knowledge graphs.

[GitHub](https://github.com/taygetea/dialectical-debate)
""")
