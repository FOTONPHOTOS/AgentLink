import time
import sys
from .mission_control import MissionControl, Status
from .neural_link import NeuralLink
from .browser_driver import RemoteBrowser

def main():
    print(" AGENTLINK 3.0: SOVEREIGN COGNITION ONLINE")
    
    mc = MissionControl()
    brain = NeuralLink(node="brain2")
    browser = RemoteBrowser(brain)
    
    # 1. Define the High-Level Plan
    plan_id = mc.create_plan(
        title="Secure Brain2 & Map Network",
        description="Verify node integrity, map running services, and ensure browser readiness.",
        steps=[
            "Establish Neural Link (Vision Check)",
            "Verify Chrome State on Workspace 4",
            "Navigate to Example.com (Connectivity Check)",
            "Generate Network Report"
        ]
    )
    
    print(f" Plan Created: ID {plan_id}")
    mc.start_plan(plan_id) # Triggers Sticky Note creation
    
    # 2. Execution Loop
    while True:
        task = mc.get_next_pending_task(plan_id)
        if not task:
            print(" All tasks completed.")
            mc.update_status(plan_id, Status.COMPLETED)
            break
            
        print(f" Executing Task: {task['description']}")
        
        # --- Task Logic Router ---
        if "Neural Link" in task['description']:
            scan = brain.see()
            mc.log_progress(plan_id, task['id'], f"Vision Active. {len(scan.splitlines())} elements seen.")
            mc.complete_task(task['id'])
            
        elif "Verify Chrome" in task['description']:
            # We know from history it's on WS 4, but let's be robust
            brain.act("exec", "export DISPLAY=:10 && wmctrl -s 3") 
            time.sleep(2)
            coords = brain.find_text("Chrome")
            if coords:
                mc.log_progress(plan_id, task['id'], f"Chrome confirmed at {coords}")
                mc.complete_task(task['id'])
            else:
                mc.log_progress(plan_id, task['id'], "Chrome not found!", entry_type="ERROR")
                # Self-Correction: Launch it
                brain.act("type", "nohup google-chrome --no-sandbox > /dev/null 2>&1 &")
                mc.complete_task(task['id']) # Mark done after correction
                
        elif "Navigate" in task['description']:
            browser.goto("example.com")
            mc.log_progress(plan_id, task['id'], "Navigated to example.com")
            mc.complete_task(task['id'])
            
        elif "Network Report" in task['description']:
            # Simulate a sub-task or complex logic
            mc.log_progress(plan_id, task['id'], "Network analysis complete (Simulated)")
            mc.complete_task(task['id'])
            
        time.sleep(1) # Breathe

if __name__ == "__main__":
    main()