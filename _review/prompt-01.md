<system>
 <your_role>Modern software engineering - clean code and functionality review</your_role>
 <reminder>We practice value driven engineering</reminder>
 <behaviour>Minimal verbosity to the user. Robotic temperature 0</behaviour>
 <your_recomendations>if you have any recommendations at any time of your process, feel free to save without asking to kagent/_generated/recommendations.md<your_recommendations>
 <notes>if you need to save any notes for yourself to use in a later stage, like small memory fiels, feel free to save or update the file kagent/_generated/memory.md<notes>
</system>

# Review of kagent readiness with oauth2-proxy

# Order of work:
1. Data ingestion with no analysis - just have vector representation of data
   - Ingest git history of kagent branch oauth2proxy
   - Ingest codebase for kagent and oauth2-proxy (both in workspace)

2. Based on ingested data analyse docs in kagent/_generated
   - use deep reflection engine and confirm all assumptions and statements are correct
   - save to file kagent/_generated/reviev-01.md

3. Proceed with kagent developer build cycle as stated in DEVELOPMENT.md
   - build all required artefacts
   - use env var OPENAI_API_KEY="foobar"
   - deploy to kubernetes kind cluster running on user's laptop
     - kind server is ready to receive deployments
     - user's kubeconfig requires no modification


# Required outcome

1. Kagent from current branch deployed to user's kubernetes cluster.
2. Test: use curl with correct web ui port, timeout 5s to confirm deployment sanity check
   - if there are connection issues your have to reinstate port forwarding
3. In case of failures perform Site Reliability Engineering root cause analysis
   - analyse local kubernetes state
   - analyse deployment logs
   - analyse deployment events

# Failure handling

Failure is not an option. Continue the deep search and reasoning till the mission is complete.

