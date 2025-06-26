This module contains the UI Exception Handler for the framework.

The design of this module is based on the creation of 2 different interconnected agents, that collaborate through planning of steps and execution of tasks. The second agent will make use at each action of the step of 2 different tools: One for GUI grounding, and another for the execution of the action (pyautogui).

At the end of each step, or at the middle, the step agent can abort the step and call for replanning, then the planning agent will adjust the plan accordingly from the current point, or determine the task unfeasible.