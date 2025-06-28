# **Proposal: User and Admin Management System for KAgent Web UI**

## **Current State Analysis**

The kagent system already has:
- ✅ OAuth2-proxy integration with multiple providers (GitHub, Google, Azure, OIDC)
- ✅ JWT-based authentication with role-based access control (RBAC)
- ✅ User model with roles (`["user"]` default) and infrastructure for admin roles
- ✅ Auth middleware active and auth dependencies exist (but not used in current routes)
- ❌ **No auth endpoints registered** - Auth routes exist but not included in FastAPI app
- ⚠️ **Inconsistent database user_id tracking** - Most models have user_id but Tool/ToolServer bypass BaseDBModel

## **Phase 1: Backend API Development**

### **1.1 Enhanced User Management API**
Create comprehensive user management endpoints:

```python
# New endpoints to add to autogenstudio/web/routes/users.py
@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(
    page: int = 1,
    limit: int = 20,
    search: str = None,
    role_filter: str = None
) -> Dict[str, Any]

@router.post("/users", dependencies=[Depends(require_admin)])
async def create_user(user_data: CreateUserRequest) -> Dict[str, Any]

@router.put("/users/{user_id}", dependencies=[Depends(require_admin)])
async def update_user(user_id: str, user_data: UpdateUserRequest) -> Dict[str, Any]

@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: str) -> Dict[str, Any]

@router.put("/users/{user_id}/roles", dependencies=[Depends(require_admin)])
async def update_user_roles(user_id: str, roles: List[str]) -> Dict[str, Any]

@router.put("/users/{user_id}/status", dependencies=[Depends(require_admin)])
async def toggle_user_status(user_id: str, enabled: bool) -> Dict[str, Any]
```

### **1.2 Enhanced Database Models**
Extend the existing User model and create persistent user storage:

```python
# Add to autogenstudio/datamodel/db.py
class UserDB(BaseDBModel, table=True):
    """Database model for storing user information."""
    
    external_id: str = Field(unique=True, index=True)  # OAuth provider ID
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: str  # github, google, azure, etc.
    roles: List[str] = Field(default=["user"], sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
```

### **1.3 Role and Permission System**
Implement granular permissions:

```python
# New file: autogenstudio/web/auth/permissions.py
class Permission(str, Enum):
    # Agent permissions
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    
    # Model permissions
    MODEL_CREATE = "model:create"
    MODEL_READ = "model:read"
    MODEL_UPDATE = "model:update"
    MODEL_DELETE = "model:delete"
    
    # User management permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Admin permissions
    ADMIN_PANEL = "admin:panel"
    SYSTEM_CONFIG = "system:config"

ROLE_PERMISSIONS = {
    "user": [
        Permission.AGENT_READ, Permission.AGENT_CREATE, Permission.AGENT_UPDATE,
        Permission.MODEL_READ, Permission.MODEL_CREATE, Permission.MODEL_UPDATE,
    ],
    "admin": [
        # All user permissions plus admin permissions
        *ROLE_PERMISSIONS["user"],
        Permission.AGENT_DELETE, Permission.MODEL_DELETE,
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.ADMIN_PANEL, Permission.SYSTEM_CONFIG,
    ]
}
```

## **Phase 2: Frontend UI Components**

### **2.1 Admin Panel Layout**
Create a dedicated admin section:

```tsx
// ui/src/app/admin/layout.tsx
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <AdminSidebar />
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}

// ui/src/components/admin/AdminSidebar.tsx
export function AdminSidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white">
      <nav className="p-4 space-y-2">
        <AdminNavLink href="/admin/users" icon={Users}>
          User Management
        </AdminNavLink>
        <AdminNavLink href="/admin/roles" icon={Shield}>
          Roles & Permissions
        </AdminNavLink>
        <AdminNavLink href="/admin/system" icon={Settings}>
          System Settings
        </AdminNavLink>
        <AdminNavLink href="/admin/audit" icon={FileText}>
          Audit Logs
        </AdminNavLink>
      </nav>
    </aside>
  )
}
```

### **2.2 User Management Interface**

```tsx
// ui/src/app/admin/users/page.tsx
export default function UsersPage() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">User Management</h1>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add User
        </Button>
      </div>
      
      <UserFilters />
      <UserTable />
      <CreateUserDialog />
      <EditUserDialog />
    </div>
  )
}

// ui/src/components/admin/UserTable.tsx
export function UserTable() {
  const columns = [
    { key: 'name', label: 'Name' },
    { key: 'email', label: 'Email' },
    { key: 'provider', label: 'Provider' },
    { key: 'roles', label: 'Roles' },
    { key: 'status', label: 'Status' },
    { key: 'lastLogin', label: 'Last Login' },
    { key: 'actions', label: 'Actions' }
  ]
  
  return (
    <DataTable
      columns={columns}
      data={users}
      loading={loading}
      onEdit={handleEdit}
      onDelete={handleDelete}
      onToggleStatus={handleToggleStatus}
    />
  )
}
```

### **2.3 Role Management Interface**

```tsx
// ui/src/app/admin/roles/page.tsx
export default function RolesPage() {
  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Roles & Permissions</h1>
        <Button onClick={() => setShowCreateRoleDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Create Role
        </Button>
      </div>
      
      <RolesList />
      <PermissionMatrix />
    </div>
  )
}

// ui/src/components/admin/PermissionMatrix.tsx
export function PermissionMatrix() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Permission Matrix</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Permission</TableHead>
              {roles.map(role => (
                <TableHead key={role.name}>{role.name}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {permissions.map(permission => (
              <TableRow key={permission.key}>
                <TableCell>{permission.label}</TableCell>
                {roles.map(role => (
                  <TableCell key={`${role.name}-${permission.key}`}>
                    <Checkbox
                      checked={role.permissions.includes(permission.key)}
                      onCheckedChange={(checked) => 
                        handlePermissionToggle(role.name, permission.key, checked)
                      }
                    />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
```

## **Phase 3: Enhanced Authentication Flow**

### **3.1 User Registration & Onboarding**

```tsx
// ui/src/components/auth/UserOnboarding.tsx
export function UserOnboarding() {
  return (
    <Card className="max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Welcome to KAgent</CardTitle>
        <CardDescription>
          Complete your profile to get started
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form>
          <FormField name="displayName" label="Display Name" />
          <FormField name="organization" label="Organization (Optional)" />
          <FormField name="role" label="Primary Use Case">
            <Select>
              <SelectItem value="developer">Developer</SelectItem>
              <SelectItem value="analyst">Data Analyst</SelectItem>
              <SelectItem value="manager">Project Manager</SelectItem>
              <SelectItem value="other">Other</SelectItem>
            </Select>
          </FormField>
        </Form>
      </CardContent>
    </Card>
  )
}
```

### **3.2 Enhanced Header with User Menu**

```tsx
// ui/src/components/Header.tsx - Enhanced user menu
export function UserMenu() {
  const { user } = useAuth()
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarImage src={user?.avatar_url} alt={user?.name} />
            <AvatarFallback>{user?.name?.charAt(0)}</AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end">
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium">{user?.name}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
            <div className="flex gap-1">
              {user?.roles?.map(role => (
                <Badge key={role} variant="secondary" className="text-xs">
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/profile">
            <User className="mr-2 h-4 w-4" />
            Profile
          </Link>
        </DropdownMenuItem>
        {user?.roles?.includes('admin') && (
          <DropdownMenuItem asChild>
            <Link href="/admin">
              <Shield className="mr-2 h-4 w-4" />
              Admin Panel
            </Link>
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout}>
          <LogOut className="mr-2 h-4 w-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```

## **Phase 4: Advanced Features**

### **4.1 Audit Logging**

```python
# autogenstudio/web/audit/models.py
class AuditLog(BaseDBModel, table=True):
    """Audit log for tracking user actions."""
    
    user_id: str
    action: str  # CREATE, UPDATE, DELETE, LOGIN, etc.
    resource_type: str  # agent, model, user, etc.
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
```

### **4.2 Team/Organization Management**

```tsx
// ui/src/app/admin/organizations/page.tsx
export default function OrganizationsPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Organizations</h1>
      <OrganizationsList />
      <TeamManagement />
    </div>
  )
}
```

### **4.3 Resource Ownership & Sharing**

```python
# Enhanced database models with ownership
class Agent(BaseDBModel, table=True):
    # ... existing fields ...
    owner_id: str  # User who created the agent
    shared_with: List[str] = Field(default=[], sa_column=Column(JSON))  # User IDs
    organization_id: Optional[str] = None
    visibility: str = Field(default="private")  # private, organization, public
```

## **Phase 5: Implementation Plan**

### **Sprint 1 (2 weeks): Backend Foundation**
- [ ] Create user management API endpoints
- [ ] Implement enhanced User database model
- [ ] Add role-based permission system
- [ ] Create audit logging infrastructure

### **Sprint 2 (2 weeks): Admin UI Core**
- [ ] Build admin panel layout and navigation
- [ ] Implement user management interface
- [ ] Create role management UI
- [ ] Add user creation/editing forms

### **Sprint 3 (2 weeks): Authentication Enhancement**
- [ ] Enhance user registration flow
- [ ] Implement user onboarding
- [ ] Update header with user menu
- [ ] Add profile management page

### **Sprint 4 (1 week): Advanced Features**
- [ ] Implement audit logging UI
- [ ] Add organization/team management
- [ ] Create resource sharing functionality
- [ ] Add system settings panel

### **Sprint 5 (1 week): Testing & Polish**
- [ ] Write comprehensive tests
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation and deployment

## **Security Considerations**

1. **Input Validation**: All user inputs validated and sanitized
2. **Rate Limiting**: API endpoints protected against abuse
3. **Audit Trails**: All administrative actions logged
4. **Role Validation**: Server-side role checking on all operations
5. **Session Management**: Secure JWT handling with proper expiration
6. **CSRF Protection**: Cross-site request forgery prevention

## **Technical Dependencies**

### **Backend:**
- FastAPI dependencies already in place
- SQLAlchemy/SQLModel for database operations
- Existing JWT authentication system
- OAuth2-proxy integration

### **Frontend:**
- React/Next.js framework already established
- Shadcn/ui component library
- Zustand for state management
- Existing routing and layout system

## **Web UI Focus**

This proposal is specifically for the **kagent web UI** component:

### **Web UI Components:**
- **Frontend React/Next.js application** (`ui/src/`)
- **Backend Python FastAPI** (`python/src/autogenstudio/web/`)
- **OAuth2-proxy integration** (already configured in Helm charts)

### **What This Proposal Addresses:**

1. **Web UI Admin Panel** - New admin interface accessible through the web browser
2. **User Management Interface** - Web forms and tables for managing users
3. **Role-Based UI Controls** - Show/hide features based on user roles
4. **Enhanced Authentication Flow** - Better login/logout experience in the web UI
5. **Profile Management** - User profile pages and settings

This proposal leverages the existing robust authentication infrastructure while adding comprehensive user and admin management capabilities that integrate seamlessly with the current kagent web UI architecture.

## **Reasoning**

### **How I Discovered the Existing JWT + RBAC System**

I systematically analyzed the codebase to understand the current authentication state before proposing enhancements:

### **JWT Authentication Evidence:**

**From `auth/manager.py` - JWT Creation:**
```python
def create_token(self, user: User) -> str:
    """Create a JWT token for authenticated user."""
    payload = {
        "sub": user.id,
        "name": user.name,
        "email": user.email,
        "provider": user.provider,
        "roles": user.roles,  # ← ROLES EMBEDDED IN JWT!
        "exp": expiry,
    }
    return jwt.encode(payload, self.config.jwt_secret, algorithm="HS256")
```

**From `auth/manager.py` - JWT Validation:**
```python
# Decode and validate JWT
payload = jwt.decode(token, self.config.jwt_secret, algorithms=["HS256"])

# Create User object from token payload
return User(
    id=payload.get("sub"),
    name=payload.get("name", "Unknown User"),
    email=payload.get("email"),
    provider=payload.get("provider", "jwt"),
    roles=payload.get("roles", ["user"]),  # ← EXTRACTING ROLES!
)
```

### **Role-Based Access Control Evidence:**

**From `auth/dependencies.py` - RBAC Implementation:**
```python
def require_roles(required_roles: List[str]):
    """
    Dependency factory to require specific roles.
    Example:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_roles(["admin"]))):
            # Only users with admin role will get here
            return {"message": "Welcome, admin!"}
    """

    def _require_roles(user: User = Depends(require_authenticated)) -> User:
        """Require that the user has at least one of the specified roles."""
        user_roles = set(user.roles or [])
        if not any(role in user_roles for role in required_roles):
            raise ForbiddenException(f"This endpoint requires one of these roles: {', '.join(required_roles)}")
        return user

    return _require_roles


def require_admin(user: User = Depends(require_roles(["admin"]))) -> User:
    """Convenience dependency to require admin role."""
    return user
```

### **User Model with Roles:**

**From `auth/models.py` - User Structure:**
```python
class User(BaseModel):
    """User model for authenticated users."""

    id: str
    name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    provider: Optional[str] = None
    roles: List[str] = ["user"]  # ← DEFAULT ROLE SYSTEM!
    metadata: Optional[Dict[str, Any]] = None
```

### **OAuth2-Proxy Integration Evidence:**

**From `helm/kagent/values.yaml` - OAuth Configuration:**
```yaml
oauth2Proxy:
  enabled: false
  provider: "github"  # github, google, azure, oidc, etc.
  clientId: ""
  clientSecret: ""
  cookieSecret: ""
```

**From `helm/kagent/tests/oauth2-proxy_test.yaml` - Integration Tests:**
```yaml
suite: test oauth2-proxy
templates:
  - deployment.yaml
  - nginx-configmap.yaml
  - oauth2-proxy-secret.yaml
  - service.yaml
```

### **Authentication Middleware Evidence:**

**From `auth/middleware.py` - Request Processing:**
```python
# Handle authentication for all other requests
try:
    user = await self.auth_manager.authenticate_request(request)
    # Add user to request state for use in route handlers
    request.state.user = user
    return await call_next(request)
```

### **Why This Analysis Was Critical:**

1. **Foundation Assessment**: Understanding existing auth infrastructure prevented rebuilding working systems
2. **Integration Strategy**: Knowing the current patterns allowed proposing compatible enhancements
3. **Security Model**: Understanding JWT + RBAC implementation ensured security consistency
4. **OAuth Flow**: Recognizing oauth2-proxy integration guided the enhancement approach
5. **User Management Gap**: Identified that while auth exists, user management UI was missing

### **Key Discoveries:**

- ✅ **JWT tokens already include roles** - No need to redesign token structure
- ✅ **RBAC dependencies properly defined** - Can use `require_admin()` and `require_roles()` (but currently unused in any routes)
- ✅ **OAuth2-proxy configured** - Can build on existing provider integrations
- ✅ **User model supports roles** - Can extend without breaking changes
- ✅ **Auth middleware functional** - Can hook into existing request processing
- ❌ **No admin UI** - This is the main gap the proposal addresses
- ❌ **No user management endpoints** - Backend APIs need to be created
- ❌ **No persistent user storage** - Database models need enhancement
- ❌ **No actual admin users** - Infrastructure exists but no mechanism to create/assign admin roles

### **Critical Discovery About Auth Dependencies:**

**Current Route Implementation Gap:**

While the auth infrastructure exists, **current routes don't use the auth dependencies**:

```python
# Current routes use manual user_id parameters (no auth enforcement)
@router.get("/")
async def list_sessions(user_id: str, db=Depends(get_db)) -> Dict:

@router.get("/")  
async def list_tools(user_id: str, db=Depends(get_db)) -> Dict:

# Only auth routes use auth dependencies
@router.get("/me")
async def get_user_info(current_user: User = Depends(get_current_user)):
```

**This means:** Routes are not protected by role-based access control despite the infrastructure existing.

### **Critical Discovery About Auth Endpoints:**

**Auth Routes Not Registered in FastAPI App:**

While auth routes are defined in `authroutes.py`, they are **never included in the FastAPI app**:

```python
# Auth router exists with /me endpoint defined
@router.get("/me")
async def get_user_info(current_user: User = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "provider": current_user.provider,
        "roles": current_user.roles,
    }

# BUT in app.py, authroutes.router is imported but NEVER included:
api.include_router(sessions.router, prefix="/sessions")
api.include_router(runs.router, prefix="/runs")
api.include_router(teams.router, prefix="/teams")
# ... other routers included ...
# MISSING: api.include_router(authroutes.router, prefix="/auth")
```

**This means:** `/api/auth/me` returns 404 - the endpoint doesn't exist from the API perspective despite being defined.

### **Critical Discovery About RBAC Dependencies:**

**RBAC Dependencies Are Properly Defined But Never Used:**

While RBAC dependencies are well-designed and functional, **NO routes actually use them**:

```python
# RBAC dependencies are properly defined in auth/dependencies.py:
def require_authenticated(user: User = Depends(get_current_user)) -> User:
    """Require that the user is authenticated (not anonymous)."""
    if user.id == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_roles(required_roles: List[str]):
    """Dependency factory to require specific roles."""
    def _require_roles(user: User = Depends(require_authenticated)) -> User:
        user_roles = set(user.roles or [])
        if not any(role in user_roles for role in required_roles):
            raise ForbiddenException(f"This endpoint requires one of these roles: {', '.join(required_roles)}")
        return user
    return _require_roles

def require_admin(user: User = Depends(require_roles(["admin"]))) -> User:
    """Convenience dependency to require admin role."""
    return user

# BUT all actual routes bypass authentication with manual user_id parameters:
@router.get("/")
async def list_teams(user_id: str, db=Depends(get_db)) -> Dict:

@router.get("/")
async def list_tools(user_id: str, db=Depends(get_db)) -> Dict:

@router.get("/")
async def list_sessions(user_id: str, db=Depends(get_db)) -> Dict:

# Only examples exist in code comments (not real routes):
async def admin_endpoint(user: User = Depends(require_roles(["admin"]))):
    # This is just a comment example!
    return {"message": "Welcome, admin!"}
```

**This means:** Despite having excellent RBAC infrastructure, **ZERO routes are actually protected** by role-based access control.

### **Critical Discovery About Database Infrastructure:**

**Inconsistent user_id Tracking Across Database Models:**

While most models properly inherit user_id tracking, **some models bypass the standard BaseDBModel**:

```python
# ✅ CORRECT: Most models inherit from BaseDBModel
class BaseDBModel(SQLModel, table=False):
    user_id: Optional[str] = None  # ← Standard user_id field
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    version: Optional[str] = "0.0.1"

class Team(BaseDBModel, table=True):     # ✅ Inherits user_id correctly
class Message(BaseDBModel, table=True):  # ✅ Inherits user_id correctly  
class Session(BaseDBModel, table=True):  # ✅ Inherits user_id correctly

# ❌ INCONSISTENT: Some models bypass BaseDBModel
class Tool(SQLModel, table=True):        # ← DIRECTLY inherits SQLModel!
    user_id: Optional[str] = None        # ← Manual user_id field
    # Missing: created_at, updated_at, version

class ToolServer(SQLModel, table=True):  # ← DIRECTLY inherits SQLModel!
    user_id: Optional[str] = None        # ← Manual user_id field
    # Missing: created_at, updated_at, version

# ❌ REDUNDANT: Some models redefine inherited fields
class Run(BaseDBModel, table=True):
    user_id: Optional[str] = None        # ← REDUNDANT redefinition of inherited field
```

**This means:** Database infrastructure is mostly consistent but has architectural inconsistencies that need fixing.

### **Critical Discovery About Admin Roles:**

**What I Found vs. What I Initially Claimed:**

**Initial Incorrect Claim:** "User model with roles (`["user"]` default, `["admin"]` for admins)"

**Actual Evidence Found:**

**Admin Infrastructure Exists:**
```python
# From auth/dependencies.py - Admin role checking exists
def require_admin(user: User = Depends(require_roles(["admin"]))) -> User:
    """Convenience dependency to require admin role."""
    return user

# Example usage in code comments:
async def admin_endpoint(user: User = Depends(require_roles(["admin"]))):
    # Only users with admin role will get here
    return {"message": "Welcome, admin!"}
```

**But No Admin Creation Mechanism:**
```python
# From auth/models.py - Only default user role
class User(BaseModel):
    roles: List[str] = ["user"]  # ← Only shows default ["user"], no admin creation
```

**The Reality:** The system has complete infrastructure for admin roles (checking, validation, dependencies) but **no mechanism to actually create admin users**. This makes the proposal even more critical - it needs to include:

1. **Bootstrap admin creation** - Initial admin user setup
2. **Admin role assignment** - Mechanism to promote users to admin
3. **Admin user management** - Interface to manage admin privileges
- ❌ **No actual admin users** - Infrastructure exists but no mechanism to create/assign admin roles

This systematic analysis revealed that kagent has excellent authentication foundations but lacks the management interface layer - exactly what this proposal provides. 
