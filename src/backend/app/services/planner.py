from ortools.sat.python import cp_model
from typing import List, Dict

def generate_optimized_plan(needs: List[Dict], resources: List[Dict]):
    """
    Uses OR-Tools CP-SAT solver to generate an optimized allocation of resources to needs.
    This is a simplified knapsack-style assignment model for the hackathon baseline.
    """
    model = cp_model.CpModel()
    
    # 1. Decision Variables
    # x[(n_idx, r_idx)] = 1 if resource r is assigned to need n
    assignments = {}
    for n_idx, need in enumerate(needs):
        category = need.get('category')
        for r_idx, resource in enumerate(resources):
            caps = resource.get('capabilities', {})
            if category not in caps:
                continue
            assignments[(n_idx, r_idx)] = model.NewBoolVar(f'assign_n{n_idx}_r{r_idx}')

    # 2. Constraints
    # A resource can only be assigned to at most one need at a time in this time horizon
    for r_idx, resource in enumerate(resources):
        model.Add(sum(assignments[(n_idx, r_idx)] for n_idx in range(len(needs)) if (n_idx, r_idx) in assignments) <= 1)
        
    # A need can be served by multiple resources if amount > capacity, 
    # but for simplicity, limit to max 1 resource per need for this iteration.
    for n_idx, need in enumerate(needs):
        model.Add(sum(assignments[(n_idx, r_idx)] for r_idx in range(len(resources)) if (n_idx, r_idx) in assignments) <= 1)

    # 3. Objective Function
    # Maximize the value of served needs, weighted by urgency.
    # High urgency gets a higher weight.
    objective_terms = []
    for n_idx, need in enumerate(needs):
        urgency = need.get("urgency", 1)
        # In a real model, we'd multiply by capacity satisfied. 
        # Here we just weight the boolean assignment by urgency.
        for r_idx, resource in enumerate(resources):
            if (n_idx, r_idx) in assignments: objective_terms.append(urgency * 10 * assignments[(n_idx, r_idx)])
            
    model.Maximize(sum(objective_terms))

    # 4. Solve
    solver = cp_model.CpSolver()
    # TRD requires 5 second limit
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    # 5. Extract Results
    result = {
        "status": solver.StatusName(status),
        "assignments": []
    }
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for n_idx, need in enumerate(needs):
            for r_idx, resource in enumerate(resources):
                if (n_idx, r_idx) in assignments and solver.Value(assignments[(n_idx, r_idx)]):
                    result["assignments"].append({
                        "need_id": need.get("id", n_idx),
                        "resource_id": resource.get("id", r_idx)
                    })
                    
    return result
