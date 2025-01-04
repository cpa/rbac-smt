# RBAC Tenant Manager

A proof of concept for managing role-based access control (RBAC) in multi-tenant environments. The application allows you to define tenants, roles, resources, and permissions, and verify access control policies using the Z3 SMT solver (or any solver that speaks SMTLIB for that matter)

## Prerequisites

You need to have Python 3.7+ and pip installed on your system.

### Installing Z3

The application requires the Z3 SMT solver to be installed and available in your system path.

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install z3
```

#### macOS
```bash
brew install z3
```

#### Windows
1. Download the latest Z3 release from [https://github.com/Z3Prover/z3/releases](https://github.com/Z3Prover/z3/releases)
2. Extract the archive
3. Add the bin directory to your system PATH

To verify Z3 is properly installed, run:
```bash
z3 --version
```

### Installing Python Dependencies

1. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix or MacOS:
source venv/bin/activate
```

2. Install the required Python packages:
```bash
pip install flask
```

## Running the Application

1. Clone this repository:
```bash
git clone <repository-url>
cd rbac-tenant-manager
```

2. Make sure your virtual environment is activated

3. Run the Flask application:
```bash
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

The web interface allows you to:
- Create and manage tenants
- Define tenant hierarchies
- Create roles and resources
- Set up permissions
- Test access control queries using SMT solver

## Testing Queries

In the SMT Query section, you can write queries to test your RBAC configuration. For example:

```scheme
(HasPermission user_admin1 res1_read client1 res1)
```

This checks if user_admin1 has read permission on res1 in client1's context.

## Data Import/Export

You can save and load your RBAC configuration using the provided buttons in the interface. The data is saved in JSON format.
