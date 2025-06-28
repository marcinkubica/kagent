# **Proposal: User and Admin Management System for KAgent Web UI**

## **Current State Analysis**

The kagent system already has:
- ✅ OAuth2-proxy integration with multiple providers (GitHub, Google, Azure, OIDC)
- ✅ JWT-based authentication with role-based access control (RBAC)
- ✅ User model with roles (`["user"]` default, `["admin"]` for admins)
- ✅ Auth middleware and dependencies (`require_admin`, `require_roles`)
- ✅ Basic user info endpoint (`/api/auth/me`)
- ✅ Database infrastructure with user_id tracking across all entities

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
