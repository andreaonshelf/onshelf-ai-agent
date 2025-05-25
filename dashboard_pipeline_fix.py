        if show_pipeline_debugger:
            if pipeline_data:
                # Master Orchestrator Panel
                st.subheader("🎭 Master AI Orchestrator")
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Current Stage", f"{pipeline_data['processing_status']['current_stage']}/4")
                with col2:
                    st.metric("Iteration", f"{pipeline_data['processing_status']['iteration']}/{pipeline_data['processing_status']['max_iterations']}")
                with col3:
                    st.metric("Accuracy", f"{pipeline_data['processing_status']['accuracy']:.1%}")
                with col4:
                    st.metric("API Cost", f"${pipeline_data['processing_status']['cost']:.2f}")
                with col5:
                    status_color = {"processing": "🟡", "completed": "🟢", "failed": "🔴"}
                    st.metric("Status", f"{status_color.get(pipeline_data['processing_status']['status'], '⚪')} {pipeline_data['processing_status']['status'].title()}")
                
                # Current processing details
                with st.container():
                    st.markdown("### 🔄 Current Processing")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.info(f"**Task:** {pipeline_data['processing_status']['current_task']}")
                        st.warning(f"**AI Reasoning:** {pipeline_data['processing_status']['ai_reasoning']}")
                        st.success(f"**Next Action:** {pipeline_data['processing_status']['next_action']}")
                    with col2:
                        # Progress visualization
                        progress = pipeline_data['processing_status']['current_stage'] / 4
                        st.progress(progress)
                        st.caption(f"Overall Progress: {progress:.0%}")
                
                st.divider()
                
                # Pipeline Stages Visualization
                st.subheader("🔄 Pipeline Stages")
                
                stage_cols = st.columns(4)
                for i, stage in enumerate(pipeline_data['pipeline_stages']):
                    with stage_cols[i]:
                        status_class = stage['status']
                        accuracy_text = f"{stage['accuracy']:.1%}" if stage['accuracy'] else "N/A"
                        stage_html = f"""
                        <div class='pipeline-stage {status_class}'>
                            <h4>{stage['stage']}</h4>
                            <p>Status: {stage['status'].title()}</p>
                            <p>Accuracy: {accuracy_text}</p>
                        </div>
                        """
                        st.markdown(stage_html, unsafe_allow_html=True)
                
                st.divider()
                
                # Multi-Model Comparison
                st.subheader("🤖 Multi-Model Comparison")
                
                model_cols = st.columns(3)
                for i, (model_name, model_data) in enumerate(pipeline_data['model_results'].items()):
                    with model_cols[i]:
                        badge_class = {"claude-4-sonnet": "model-claude", "gpt-4o": "model-gpt4o", "gemini-2.5-flash": "model-gemini"}.get(model_name, "model-badge")
                        st.markdown(f"<h4><span class='model-badge {badge_class}'>{model_name}</span></h4>", unsafe_allow_html=True)
                        st.metric("Accuracy", f"{model_data['accuracy']:.1%}")
                        st.metric("Confidence", f"{model_data['confidence']:.1%}")
                        st.metric("Time", f"{model_data['processing_time']:.1f}s")
                        st.metric("Products", model_data['products_detected'])
                
                # AI Orchestrator Decision Tree
                if show_orchestrator:
                    st.divider()
                    st.subheader("🌳 AI Orchestrator Decision Tree")
                    
                    with st.expander("View Current Decision Context"):
                        decision_data = {
                            "current_accuracy": pipeline_data['processing_status']['accuracy'],
                            "options": [
                                {"action": "Continue with current model", "confidence": 0.85, "cost": 0.05},
                                {"action": "Switch to Claude for spatial", "confidence": 0.95, "cost": 0.15},
                                {"action": "Run consensus voting", "confidence": 0.98, "cost": 0.25}
                            ],
                            "selected": "Switch to Claude for spatial",
                            "reasoning": "Position conflicts detected. Claude has superior spatial reasoning."
                        }
                        
                        # Decision visualization
                        fig = go.Figure()
                        for i, option in enumerate(decision_data['options']):
                            selected = option['action'] == decision_data['selected']
                            fig.add_trace(go.Bar(
                                x=[option['confidence']],
                                y=[option['action']],
                                orientation='h',
                                marker_color='green' if selected else 'gray',
                                name=option['action']
                            ))
                        
                        fig.update_layout(
                            title="Decision Options Confidence",
                            xaxis_title="Confidence Score",
                            showlegend=False,
                            height=300
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.write(f"**Selected:** {decision_data['selected']}")
                        st.write(f"**Reasoning:** {decision_data['reasoning']}")
            else:
                # No active processing
                st.info("🔍 No active processing at the moment")
                st.markdown("""
                ### 📥 Start Processing
                
                To see the pipeline debugger in action:
                1. Add an image to the processing queue
                2. Wait for processing to begin
                3. The debugger will show real-time progress
                
                **Current Queue Status:**
                """)
                
                # Show queue summary
                if not queue_df.empty:
                    status_counts = queue_df['status'].value_counts()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Pending", status_counts.get('pending', 0))
                    with col2:
                        st.metric("Processing", status_counts.get('processing', 0))
                    with col3:
                        st.metric("Completed", status_counts.get('completed', 0))
                else:
                    st.info("Queue is empty. Add items to process.")
        else:
            st.info("Pipeline debugger is disabled")