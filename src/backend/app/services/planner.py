from ortools.sat.python import cp_model
from typing import List, Dict
import math

def generate_optimized_plan(needs: List[Dict], resources: List[Dict]):
    model = cp_model.CpModel()
    assignments = {}
    
    valid_needs = []
    for n in needs:
        try:
            val = float(n.get("amount") or 1)
            amount = math.ceil(val)
        except:
            amount = 1
        
        if amount <= 0:
            continue
            
        cat = str(n.get("category")).split('.')[-1].lower()
        valid_needs.append({"id": n.get("id"), "category": cat, "urgency": n.get("urgency", 1), "amount": amount})
        
    valid_resources = []
    for r in resources:
        caps = r.get("capabilities")
        if not isinstance(caps, dict):
            caps = {}
        # Lowercase all capability keys and float-parse values
        parsed_caps = {}
        for k, v in caps.items():
            try: parsed_caps[k.lower()] = math.ceil(float(v))
            except: pass
            
        valid_resources.append({"id": r.get("id"), "caps": parsed_caps, "version": r.get("version", 1)})
        
    for n_idx, need in enumerate(valid_needs):
        category = need["category"]
        for r_idx, resource in enumerate(valid_resources):
            capacity = resource["caps"].get(category, 0)
            if capacity <= 0:
                continue
            assignments[(n_idx, r_idx)] = model.NewIntVar(0, capacity, f"assign_n{n_idx}_r{r_idx}")

    # A resource can only be assigned up to its capability in that category
    for r_idx, resource in enumerate(valid_resources):
        r_vars = [assignments[(n, r_idx)] for n in range(len(valid_needs)) if (n, r_idx) in assignments]
        if r_vars:
            max_cap = max(list(resource["caps"].values()) + [0])
            model.Add(sum(r_vars) <= max_cap)
            
    # A need can be served up to its requested amount
    for n_idx, need in enumerate(valid_needs):
        n_vars = [assignments[(n_idx, r)] for r in range(len(valid_resources)) if (n_idx, r) in assignments]
        if n_vars:
            model.Add(sum(n_vars) <= need["amount"])

    # Objective: maximize urgency * amount_assigned
    objective_terms = []
    for n_idx, need in enumerate(valid_needs):
        try:
            urgency = int(need["urgency"])
        except:
            urgency = 1
        for r_idx in range(len(valid_resources)):
            if (n_idx, r_idx) in assignments:
                objective_terms.append(urgency * assignments[(n_idx, r_idx)])
                
    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)

    result = {
        "status": solver.StatusName(status),
        "assignments": []
    }
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for n_idx, need in enumerate(valid_needs):
            for r_idx, resource in enumerate(valid_resources):
                if (n_idx, r_idx) in assignments:
                    val = solver.Value(assignments[(n_idx, r_idx)])
                    if val > 0:
                        result["assignments"].append({
                            "need_id": str(need["id"]),
                            "resource_id": str(resource["id"]),
                            "amount_assigned": int(val),
                            "resource_version": resource["version"]
                        })
                        
    return result
