# UI Exception Handler Agent Specification

## Overview
A dual-agent system designed to handle UI automation exceptions through collaborative planning and execution. The system consists of two interconnected agents that work together to recover from UI automation failures.

## Agent Graph Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  Planning Agent │◄──►│  Action Agent   │
│                 │    │                 │
│ - Exception     │    │ - Plan          │
│ - Action Log    │    │ - Step Index    │
│ - Screenshot    │    │ - UI State      │
│ - Context       │    │ - Tools Access  │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Replanning    │    │   Tool Layer    │
│   Feedback      │    │                 │
│                 │    │ - UITARS GUI    │
│ - Failure       │    │ - PyAutoGUI     │
│ - Reason        │    │ - Screenshot    │
│ - Suggestions   │    │ - Validation    │
└─────────────────┘    └─────────────────┘
```

## Agent Definitions

### 1. Planning Agent
**Role**: Strategic planner and coordinator
**Responsibilities**:
- Analyze exception messages and failure context
- Generate recovery plans based on UI state and action history
- Coordinate with Action Agent for plan execution
- Handle replanning requests and adjust strategies
- Determine task feasibility

**Inputs**:
- Exception message (string): Details of the automation failure
- Action log (list): History of recent actions performed by the automation
- Screenshot (image): Current UI state where failure occurred
- Context metadata (dict): Additional system state information

**Outputs**:
- Recovery plan (structured): Step-by-step recovery actions
- Feasibility assessment (boolean): Whether task is achievable
- Next action directive (object): Immediate action for Action Agent

**Decision Logic**:
- Parse exception and correlate with UI state
- Identify root cause of failure
- Generate alternative approaches
- Prioritize recovery strategies
- Monitor execution progress

### 2. Action Agent
**Role**: Tactical executor and reporter
**Responsibilities**:
- Execute individual steps from the recovery plan
- Interact with UI through tool layer
- Monitor step execution success/failure
- Provide detailed feedback to Planning Agent
- Handle step-level error recovery

**Inputs**:
- Recovery plan (structured): From Planning Agent
- Current step index (int): Position in execution sequence
- Reasoning context (string): Why this step is needed
- UI state (image): Current screen state

**Outputs**:
- Step execution result (status): Success/Failure/In-Progress
- Feedback report (object): Detailed execution information
- Replanning request (object): When step is deemed undoable
- Success notification (boolean): When plan is completed

**Execution Flow**:
1. Receive step from plan
2. Analyze current UI state
3. Use tools to locate target UI components
4. Execute required actions
5. Validate results
6. Report status back to Planning Agent

## Tool Layer Specifications

### UITARS Integration
**Primary Tools**:

1. **UI Component Locator**
   - Function: Identify and locate UI elements on screen
   - Input: Element description, screenshot, search criteria
   - Output: Element coordinates, properties, confidence score
   - Technology: UITARS computer vision

2. **Action Executor**
   - Function: Perform UI actions (click, type, scroll, etc.)
   - Input: Action type, target coordinates, parameters
   - Output: Action result, new UI state
   - Technology: PyAutoGUI with UITARS guidance

3. **State Validator**
   - Function: Verify UI state changes after actions
   - Input: Expected state, current screenshot
   - Output: Validation result, differences detected
   - Technology: UITARS comparison algorithms

4. **Screenshot Capture**
   - Function: Capture current UI state
   - Input: Screen region (optional)
   - Output: Screenshot image, metadata
   - Technology: System screenshot APIs

## Communication Protocol

### Planning Agent → Action Agent
```json
{
  "message_type": "execute_plan",
  "plan_id": "unique_identifier",
  "steps": [
    {
      "step_id": 1,
      "action": "locate_and_click",
      "target": "OK button",
      "parameters": {...},
      "fallback_options": [...]
    }
  ],
  "context": "Exception recovery for dialog handling"
}
```

### Action Agent → Planning Agent
```json
{
  "message_type": "step_report",
  "plan_id": "unique_identifier",
  "step_id": 1,
  "status": "success|failure|undoable",
  "details": "Execution details",
  "screenshot": "base64_image_data",
  "next_action": "continue|replan|abort"
}
```

### Replanning Request Format
```json
{
  "message_type": "replan_request",
  "plan_id": "unique_identifier",
  "failed_step": 3,
  "failure_reason": "Target button not found",
  "current_state": "base64_screenshot",
  "suggested_alternatives": [...],
  "attempts_made": 2
}
```

## Error Handling & Recovery

### Failure Categories
1. **UI Element Not Found**: Component location failure
2. **Action Execution Failure**: Click/type/scroll errors
3. **State Validation Failure**: Unexpected UI changes
4. **Timeout Errors**: Operations taking too long
5. **System Level Errors**: OS or application crashes

### Recovery Strategies
1. **Retry with Variations**: Different element selectors
2. **Alternative Paths**: Different UI navigation routes
3. **Wait and Retry**: Handle timing issues
4. **Graceful Degradation**: Simplified recovery approaches
5. **User Notification**: When automated recovery fails

## Performance Metrics
- Recovery success rate
- Average recovery time
- Number of replanning iterations
- Tool accuracy metrics
- Step execution efficiency

## Configuration Parameters
- Maximum replanning attempts: 3
- Step timeout duration: 30 seconds
- Screenshot capture interval: 1 second
- UI element search confidence threshold: 0.8
- Action retry attempts: 2

## Integration Points
- Framework exception handler
- Logging system
- Screenshot service
- UITARS tool suite
- PyAutoGUI automation