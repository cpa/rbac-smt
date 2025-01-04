from flask import Flask, request, jsonify, render_template_string, send_file
import subprocess
import json
import tempfile
import os

app = Flask(__name__)

HTML = open("index.html").read()

@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/check', methods=['POST'])
def check():
    data = request.json
    
    smt = """(set-option :produce-models true)
; Declare sorts
(declare-sort User)
(declare-sort Role)
(declare-sort Permission)
(declare-sort Resource)
(declare-sort Tenant)

; Inheritance directions
(declare-datatypes ((Direction 0)) ((Upwards Downwards)))

; Declare functions and predicates
(declare-fun UserAssignedRole (User Role Tenant) Bool)
(declare-fun RoleAssignedPermission (Role Permission Tenant) Bool)
(declare-fun PermissionAppliesToResource (Permission Resource) Bool)
(declare-fun Subtenant (Tenant Tenant) Bool)
(declare-fun InheritanceDirection (Resource) Direction)
(declare-fun HasPermission (User Permission Tenant Resource) Bool)
(declare-fun PathUp (Tenant Tenant) Bool)
(declare-fun PathDown (Tenant Tenant) Bool)

; Axiom 1: Paths
(assert
  (forall ((t Tenant))
    (and (PathUp t t) (PathDown t t))
  )
)

(assert
  (forall ((t1 Tenant) (t2 Tenant))
    (=> (Subtenant t1 t2)
        (and (PathUp t1 t2) (PathDown t2 t1))
    )
  )
)

(assert
  (forall ((t1 Tenant) (t2 Tenant) (t3 Tenant))
    (and
      (=> (and (PathUp t1 t2) (PathUp t2 t3)) (PathUp t1 t3))
      (=> (and (PathDown t1 t2) (PathDown t2 t3)) (PathDown t1 t3))
    )
  )
)

; Axiom 2: Direct Permission
(assert
  (forall ((u User) (r Role) (p Permission) (t Tenant) (res Resource))
    (=> (and (UserAssignedRole u r t)
             (RoleAssignedPermission r p t)
             (PermissionAppliesToResource p res))
        (HasPermission u p t res))
  )
)

; Axiom 3: Inherited Permission via Resource
(assert
  (forall ((u User) (r Role) (p Permission) (t0 Tenant) (t Tenant) (res Resource) (dir Direction))
    (=> (and
          (UserAssignedRole u r t0)
          (RoleAssignedPermission r p t0)
          (PermissionAppliesToResource p res)
          (= (InheritanceDirection res) dir)
          (or (and (= dir Upwards) (PathUp t0 t))
              (and (= dir Downwards) (PathDown t0 t))))
        (HasPermission u p t res))
  )
)

"""
    # Declare constants for all entities
    for tenant in data['tenants']:
        smt += f"(declare-const {tenant} Tenant)\n"
    
    for resource in data['resources']:
        smt += f"(declare-const {resource['name']} Resource)\n"
        smt += f"(declare-const {resource['name']}_read Permission)\n"
        smt += f"(declare-const {resource['name']}_write Permission)\n"
    
    for role in data['roles']:
        smt += f"(declare-const {role['name']} Role)\n"
        # Declare a user for each role for testing
        smt += f"(declare-const user_{role['name']} User)\n"

    # Make tenants distinct
    if len(data['tenants']) > 1:
        tenants_list = " ".join(data['tenants'])
        smt += f"(assert (distinct {tenants_list}))\n"

    # Add tenant relationships
    for rel in data['relations']:
        smt += f"(assert (Subtenant {rel['child']} {rel['parent']}))\n"

    # Add resources and their properties
    for resource in data['resources']:
        # Set inheritance direction based on sharing
        if resource['sharedDown']:
            smt += f"(assert (= (InheritanceDirection {resource['name']}) Downwards))\n"
        elif resource['sharedUp']:
            smt += f"(assert (= (InheritanceDirection {resource['name']}) Upwards))\n"
        
        # Set permission applicability
        smt += f"(assert (PermissionAppliesToResource {resource['name']}_read {resource['name']}))\n"
        smt += f"(assert (PermissionAppliesToResource {resource['name']}_write {resource['name']}))\n"

    # Add role assignments
    for role in data['roles']:
        smt += f"(assert (UserAssignedRole user_{role['name']} {role['name']} {role['tenant']}))\n"

    # Add permissions
    for perm in data['permissions']:
        perm_const = f"{perm['resource']}_{perm['action']}"
        smt += f"(assert (RoleAssignedPermission {perm['role']} {perm_const} {perm['tenant']}))\n"

    # Add the user's query
    smt += f"\n{data['query']}\n"
    smt += "(check-sat)\n(get-model)\n"

    print(smt)

    # Call Z3
    try:
        process = subprocess.Popen(['z3', '-smt2', '-in'], 
                                 stdin=subprocess.PIPE, 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        stdout, stderr = process.communicate(input=smt)
        return stdout if stdout else stderr
    except Exception as e:
        return str(e)

@app.route('/save', methods=['POST'])
def save():
    data = request.json
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data, f, indent=2)
        temp_path = f.name

    response = send_file(
        temp_path,
        mimetype='application/json',
        as_attachment=True,
        download_name='rbac_state.json'
    )

    @response.call_on_close
    def cleanup():
        os.remove(temp_path)
    
    return response

@app.route('/load', methods=['POST'])
def load():
    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
    
    if not file.filename.endswith('.json'):
        return 'Invalid file type', 400

    try:
        data = json.load(file)
        return jsonify(data)
    except json.JSONDecodeError:
        return 'Invalid JSON file', 400

if __name__ == '__main__':
    app.run(debug=True, port=9000)
