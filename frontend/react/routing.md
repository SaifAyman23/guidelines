# React Router Guidelines

## Table of Contents
- [Overview](#overview)
- [Installation and Setup](#installation-and-setup)
- [Basic Routing](#basic-routing)
- [Navigation](#navigation)
- [Route Parameters](#route-parameters)
- [Nested Routes](#nested-routes)
- [Protected Routes](#protected-routes)
- [Programmatic Navigation](#programmatic-navigation)
- [Advanced Patterns](#advanced-patterns)
- [Best Practices](#best-practices)

## Overview

React Router v6 is the standard routing library for React applications. It enables navigation between different views, manages browser history, and provides a declarative way to define application routes.

## Installation and Setup

### Installation

```bash
npm install react-router-dom
```

### Basic Setup

```jsx
// index.js or main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

### Router Types

```jsx
import { 
  BrowserRouter,   // Standard HTML5 history API
  HashRouter,      // Hash-based routing (#/)
  MemoryRouter,    // In-memory routing (testing)
  NativeRouter     // React Native
} from 'react-router-dom';

// BrowserRouter (most common)
// URLs: /about, /users/123
<BrowserRouter>
  <App />
</BrowserRouter>

// HashRouter (for static hosting)
// URLs: /#/about, /#/users/123
<HashRouter>
  <App />
</HashRouter>

// MemoryRouter (for testing)
<MemoryRouter initialEntries={['/']}>
  <App />
</MemoryRouter>
```

## Basic Routing

### Simple Routes

```jsx
import { Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import Contact from './pages/Contact';
import NotFound from './pages/NotFound';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/about" element={<About />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
```

### Routes with Layout

```jsx
import { Routes, Route, Outlet } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';

function Layout() {
  return (
    <div>
      <Header />
      <main>
        <Outlet /> {/* Child routes render here */}
      </main>
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="about" element={<About />} />
        <Route path="contact" element={<Contact />} />
      </Route>
    </Routes>
  );
}
```

### Index Routes

```jsx
function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        {/* Index route - renders at parent path */}
        <Route index element={<Home />} />
        <Route path="dashboard" element={<Dashboard />}>
          {/* /dashboard shows DashboardOverview */}
          <Route index element={<DashboardOverview />} />
          <Route path="stats" element={<Stats />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Route>
    </Routes>
  );
}
```

## Navigation

### Link Component

```jsx
import { Link } from 'react-router-dom';

function Navigation() {
  return (
    <nav>
      <Link to="/">Home</Link>
      <Link to="/about">About</Link>
      <Link to="/users/123">User 123</Link>
      
      {/* Relative links */}
      <Link to="../">Back</Link>
      <Link to="./profile">Profile</Link>
      
      {/* With state */}
      <Link 
        to="/users/123"
        state={{ from: 'navigation' }}
      >
        User Profile
      </Link>
      
      {/* Replace history */}
      <Link to="/login" replace>
        Login
      </Link>
      
      {/* Custom className */}
      <Link 
        to="/about"
        className="nav-link"
        style={{ color: 'blue' }}
      >
        About
      </Link>
    </nav>
  );
}
```

### NavLink Component

```jsx
import { NavLink } from 'react-router-dom';

function Navigation() {
  return (
    <nav>
      {/* Active class automatically applied */}
      <NavLink 
        to="/"
        className={({ isActive }) => 
          isActive ? 'nav-link active' : 'nav-link'
        }
      >
        Home
      </NavLink>
      
      {/* With style function */}
      <NavLink
        to="/about"
        style={({ isActive }) => ({
          color: isActive ? 'red' : 'black',
          fontWeight: isActive ? 'bold' : 'normal'
        })}
      >
        About
      </NavLink>
      
      {/* End prop for exact matching */}
      <NavLink to="/" end>
        Home (exact match only)
      </NavLink>
    </nav>
  );
}
```

### Navigate Component

```jsx
import { Navigate } from 'react-router-dom';

function ProtectedRoute({ isAuthenticated, children }) {
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute isAuthenticated={isLoggedIn}>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
      
      {/* Redirect */}
      <Route path="/old-path" element={<Navigate to="/new-path" replace />} />
    </Routes>
  );
}
```

## Route Parameters

### URL Parameters

```jsx
import { useParams } from 'react-router-dom';

function App() {
  return (
    <Routes>
      <Route path="/users/:userId" element={<UserProfile />} />
      <Route path="/posts/:postId/comments/:commentId" element={<Comment />} />
      <Route path="/blog/:category/:slug" element={<BlogPost />} />
    </Routes>
  );
}

function UserProfile() {
  const { userId } = useParams();
  
  return <div>User ID: {userId}</div>;
}

function Comment() {
  const { postId, commentId } = useParams();
  
  return (
    <div>
      Post: {postId}, Comment: {commentId}
    </div>
  );
}

// TypeScript
function UserProfile() {
  const { userId } = useParams<{ userId: string }>();
  
  return <div>User ID: {userId}</div>;
}
```

### Optional Parameters

```jsx
function App() {
  return (
    <Routes>
      {/* Optional userId parameter */}
      <Route path="/users/:userId?" element={<Users />} />
    </Routes>
  );
}

function Users() {
  const { userId } = useParams();
  
  if (userId) {
    return <UserProfile userId={userId} />;
  }
  
  return <UserList />;
}
```

### Wildcard Parameters

```jsx
function App() {
  return (
    <Routes>
      {/* Matches: /files/doc.pdf, /files/images/photo.jpg */}
      <Route path="/files/*" element={<FileViewer />} />
    </Routes>
  );
}

function FileViewer() {
  const { '*': filepath } = useParams();
  
  return <div>File path: {filepath}</div>;
}
```

### Query Parameters

```jsx
import { useSearchParams } from 'react-router-dom';

function SearchResults() {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // Get query parameters
  const query = searchParams.get('q');
  const page = searchParams.get('page') || '1';
  const category = searchParams.get('category');
  
  // Set query parameters
  const handleSearch = (newQuery) => {
    setSearchParams({ q: newQuery, page: '1' });
  };
  
  const handlePageChange = (newPage) => {
    setSearchParams({ q: query, page: newPage });
  };
  
  // Update single parameter
  const updateCategory = (cat) => {
    const params = new URLSearchParams(searchParams);
    params.set('category', cat);
    setSearchParams(params);
  };
  
  // Delete parameter
  const clearCategory = () => {
    const params = new URLSearchParams(searchParams);
    params.delete('category');
    setSearchParams(params);
  };
  
  return (
    <div>
      <p>Search: {query}</p>
      <p>Page: {page}</p>
      <p>Category: {category}</p>
      
      <input 
        onChange={(e) => handleSearch(e.target.value)}
        value={query || ''}
      />
      
      <button onClick={() => handlePageChange(Number(page) + 1)}>
        Next Page
      </button>
    </div>
  );
}

// URL: /search?q=react&page=2&category=tutorials
```

## Nested Routes

### Basic Nesting

```jsx
import { Routes, Route, Outlet } from 'react-router-dom';

function App() {
  return (
    <Routes>
      <Route path="/dashboard" element={<DashboardLayout />}>
        <Route index element={<DashboardHome />} />
        <Route path="profile" element={<Profile />} />
        <Route path="settings" element={<Settings />} />
        <Route path="stats" element={<Stats />} />
      </Route>
    </Routes>
  );
}

function DashboardLayout() {
  return (
    <div className="dashboard">
      <aside>
        <nav>
          <Link to="/dashboard">Home</Link>
          <Link to="/dashboard/profile">Profile</Link>
          <Link to="/dashboard/settings">Settings</Link>
          <Link to="/dashboard/stats">Stats</Link>
        </nav>
      </aside>
      <main>
        <Outlet /> {/* Nested routes render here */}
      </main>
    </div>
  );
}
```

### Deep Nesting

```jsx
function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        
        <Route path="users" element={<UsersLayout />}>
          <Route index element={<UserList />} />
          <Route path=":userId" element={<UserProfile />}>
            <Route index element={<UserOverview />} />
            <Route path="posts" element={<UserPosts />} />
            <Route path="followers" element={<UserFollowers />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}

// URLs:
// /users -> UserList
// /users/123 -> UserOverview
// /users/123/posts -> UserPosts
// /users/123/followers -> UserFollowers
```

### Outlet Context

```jsx
function DashboardLayout() {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetchUser().then(setUser);
  }, []);
  
  return (
    <div>
      <h1>Dashboard</h1>
      {/* Pass context to nested routes */}
      <Outlet context={{ user, setUser }} />
    </div>
  );
}

function Profile() {
  // Access context from parent route
  const { user, setUser } = useOutletContext();
  
  return <div>{user?.name}</div>;
}

// TypeScript
type ContextType = { user: User | null; setUser: (user: User) => void };

function Profile() {
  const { user, setUser } = useOutletContext<ContextType>();
  
  return <div>{user?.name}</div>;
}
```

## Protected Routes

### Basic Protection

```jsx
import { Navigate, useLocation } from 'react-router-dom';

function ProtectedRoute({ children }) {
  const isAuthenticated = useAuth(); // Custom hook
  const location = useLocation();
  
  if (!isAuthenticated) {
    // Redirect to login, save attempted location
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route 
        path="/dashboard" 
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } 
      />
    </Routes>
  );
}

function Login() {
  const location = useLocation();
  const navigate = useNavigate();
  const from = location.state?.from?.pathname || '/';
  
  const handleLogin = async (credentials) => {
    await login(credentials);
    navigate(from, { replace: true });
  };
  
  return <LoginForm onSubmit={handleLogin} />;
}
```

### Role-Based Protection

```jsx
function RequireAuth({ allowedRoles, children }) {
  const { user } = useAuth();
  const location = useLocation();
  
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }
  
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/unauthorized" element={<Unauthorized />} />
      
      {/* Admin only */}
      <Route 
        path="/admin" 
        element={
          <RequireAuth allowedRoles={['admin']}>
            <AdminPanel />
          </RequireAuth>
        } 
      />
      
      {/* Admin or moderator */}
      <Route 
        path="/moderation" 
        element={
          <RequireAuth allowedRoles={['admin', 'moderator']}>
            <Moderation />
          </RequireAuth>
        } 
      />
      
      {/* Any authenticated user */}
      <Route 
        path="/dashboard" 
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        } 
      />
    </Routes>
  );
}
```

### Protected Route Layout

```jsx
function ProtectedLayout() {
  const { user, loading } = useAuth();
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  
  return (
    <div>
      <Header user={user} />
      <Outlet />
      <Footer />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route path="/app" element={<ProtectedLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="profile" element={<Profile />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
```

## Programmatic Navigation

### useNavigate Hook

```jsx
import { useNavigate } from 'react-router-dom';

function LoginForm() {
  const navigate = useNavigate();
  
  const handleLogin = async (credentials) => {
    const success = await login(credentials);
    
    if (success) {
      // Navigate to dashboard
      navigate('/dashboard');
      
      // Navigate with replace (no history entry)
      navigate('/dashboard', { replace: true });
      
      // Navigate with state
      navigate('/dashboard', { 
        state: { message: 'Login successful' } 
      });
      
      // Navigate back
      navigate(-1);
      
      // Navigate forward
      navigate(1);
      
      // Navigate multiple steps back
      navigate(-2);
    }
  };
  
  return <form onSubmit={handleLogin}>{/* ... */}</form>;
}
```

### Navigation with Confirmation

```jsx
function EditPost({ postId }) {
  const navigate = useNavigate();
  const [isDirty, setIsDirty] = useState(false);
  
  const handleSave = async () => {
    await savePost();
    setIsDirty(false);
    navigate('/posts');
  };
  
  const handleCancel = () => {
    if (isDirty) {
      const confirmed = window.confirm('You have unsaved changes. Discard?');
      if (!confirmed) return;
    }
    navigate('/posts');
  };
  
  return (
    <div>
      <button onClick={handleSave}>Save</button>
      <button onClick={handleCancel}>Cancel</button>
    </div>
  );
}
```

### Blocking Navigation

```jsx
import { useBlocker } from 'react-router-dom';

function EditForm() {
  const [formData, setFormData] = useState({});
  const [isDirty, setIsDirty] = useState(false);
  
  // Block navigation when form is dirty
  const blocker = useBlocker(
    ({ currentLocation, nextLocation }) =>
      isDirty && currentLocation.pathname !== nextLocation.pathname
  );
  
  return (
    <div>
      <form onChange={() => setIsDirty(true)}>
        {/* Form fields */}
      </form>
      
      {blocker.state === 'blocked' && (
        <div className="modal">
          <p>You have unsaved changes. Are you sure?</p>
          <button onClick={() => blocker.proceed()}>Leave</button>
          <button onClick={() => blocker.reset()}>Stay</button>
        </div>
      )}
    </div>
  );
}
```

## Advanced Patterns

### Lazy Loading Routes

```jsx
import { lazy, Suspense } from 'react';

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

### Route Configuration

```jsx
const routes = [
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: 'about', element: <About /> },
      {
        path: 'users',
        element: <UsersLayout />,
        children: [
          { index: true, element: <UserList /> },
          { path: ':userId', element: <UserProfile /> }
        ]
      }
    ]
  }
];

function App() {
  return <Routes>{routes.map(renderRoute)}</Routes>;
}

function renderRoute(route) {
  return (
    <Route
      key={route.path}
      path={route.path}
      element={route.element}
      index={route.index}
    >
      {route.children?.map(renderRoute)}
    </Route>
  );
}
```

### useRoutes Hook

```jsx
import { useRoutes } from 'react-router-dom';

function App() {
  const routes = useRoutes([
    {
      path: '/',
      element: <Layout />,
      children: [
        { index: true, element: <Home /> },
        { path: 'about', element: <About /> },
        {
          path: 'dashboard',
          element: <ProtectedRoute><Dashboard /></ProtectedRoute>,
          children: [
            { index: true, element: <DashboardHome /> },
            { path: 'profile', element: <Profile /> },
            { path: 'settings', element: <Settings /> }
          ]
        }
      ]
    },
    { path: '*', element: <NotFound /> }
  ]);
  
  return routes;
}
```

### Location State

```jsx
import { useLocation, useNavigate } from 'react-router-dom';

function UserList() {
  const navigate = useNavigate();
  
  const handleUserClick = (user) => {
    navigate(`/users/${user.id}`, {
      state: { 
        user,
        from: '/users',
        timestamp: Date.now()
      }
    });
  };
  
  return (
    <ul>
      {users.map(user => (
        <li key={user.id} onClick={() => handleUserClick(user)}>
          {user.name}
        </li>
      ))}
    </ul>
  );
}

function UserProfile() {
  const location = useLocation();
  const { user, from } = location.state || {};
  
  return (
    <div>
      <Link to={from}>← Back</Link>
      <h1>{user?.name}</h1>
    </div>
  );
}
```

### Custom useQuery Hook

```jsx
function useQuery() {
  const { search } = useLocation();
  return useMemo(() => new URLSearchParams(search), [search]);
}

function SearchPage() {
  const query = useQuery();
  const searchTerm = query.get('q');
  const category = query.get('category');
  const page = Number(query.get('page')) || 1;
  
  return (
    <div>
      <p>Searching for: {searchTerm}</p>
      <p>Category: {category}</p>
      <p>Page: {page}</p>
    </div>
  );
}
```

### Breadcrumbs

```jsx
import { useMatches, Link } from 'react-router-dom';

function Breadcrumbs() {
  const matches = useMatches();
  
  const crumbs = matches
    .filter(match => match.handle?.crumb)
    .map(match => match.handle.crumb(match.data));
  
  return (
    <nav>
      {crumbs.map((crumb, index) => (
        <span key={index}>
          {index > 0 && ' > '}
          {crumb}
        </span>
      ))}
    </nav>
  );
}

// Route configuration with breadcrumbs
const routes = [
  {
    path: '/',
    element: <Layout />,
    handle: { crumb: () => <Link to="/">Home</Link> },
    children: [
      {
        path: 'users',
        element: <Users />,
        handle: { crumb: () => <Link to="/users">Users</Link> },
        children: [
          {
            path: ':userId',
            element: <UserProfile />,
            handle: { 
              crumb: (data) => <span>{data.user.name}</span>
            }
          }
        ]
      }
    ]
  }
];
```

## Best Practices

### 1. Use Relative Paths

```jsx
// Bad - absolute paths
function DashboardNav() {
  return (
    <nav>
      <Link to="/dashboard">Home</Link>
      <Link to="/dashboard/profile">Profile</Link>
      <Link to="/dashboard/settings">Settings</Link>
    </nav>
  );
}

// Good - relative paths
function DashboardNav() {
  return (
    <nav>
      <Link to=".">Home</Link>
      <Link to="profile">Profile</Link>
      <Link to="settings">Settings</Link>
    </nav>
  );
}
```

### 2. Centralize Route Paths

```jsx
// routes/paths.js
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  DASHBOARD: '/dashboard',
  USER_PROFILE: '/users/:userId',
  SETTINGS: '/settings'
};

// App.jsx
import { ROUTES } from './routes/paths';

function App() {
  return (
    <Routes>
      <Route path={ROUTES.HOME} element={<Home />} />
      <Route path={ROUTES.LOGIN} element={<Login />} />
      <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
    </Routes>
  );
}

// Usage in components
function Navigation() {
  return (
    <nav>
      <Link to={ROUTES.HOME}>Home</Link>
      <Link to={ROUTES.DASHBOARD}>Dashboard</Link>
    </nav>
  );
}
```

### 3. Handle 404s Properly

```jsx
function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Home />} />
        <Route path="about" element={<About />} />
        {/* Catch-all route */}
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}

function NotFound() {
  const navigate = useNavigate();
  
  return (
    <div>
      <h1>404 - Page Not Found</h1>
      <p>The page you're looking for doesn't exist.</p>
      <button onClick={() => navigate('/')}>Go Home</button>
    </div>
  );
}
```

### 4. Preserve Scroll Position

```jsx
import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

function ScrollToTop() {
  const { pathname } = useLocation();
  
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  
  return null;
}

function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        {/* Routes */}
      </Routes>
    </BrowserRouter>
  );
}
```

### 5. Type-Safe Routes (TypeScript)

```typescript
// routes.ts
export const routes = {
  home: () => '/',
  userProfile: (userId: string) => `/users/${userId}`,
  post: (postId: number) => `/posts/${postId}`,
  search: (query: string, page?: number) => {
    const params = new URLSearchParams({ q: query });
    if (page) params.set('page', String(page));
    return `/search?${params}`;
  }
} as const;

// Usage
function UserLink({ userId }: { userId: string }) {
  return <Link to={routes.userProfile(userId)}>Profile</Link>;
}

function SearchLink() {
  return <Link to={routes.search('react', 2)}>Search</Link>;
}
```

### 6. Loading States for Lazy Routes

```jsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));

function LoadingFallback() {
  return (
    <div className="loading-container">
      <div className="spinner" />
      <p>Loading...</p>
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Suspense>
  );
}
```

### 7. Error Boundaries for Routes

```jsx
import { Component } from 'react';

class RouteErrorBoundary extends Component {
  state = { hasError: false, error: null };
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Route error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h1>Something went wrong</h1>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}

function App() {
  return (
    <RouteErrorBoundary>
      <Routes>
        {/* Routes */}
      </Routes>
    </RouteErrorBoundary>
  );
}
```

### 8. Route Transitions

```jsx
import { useLocation } from 'react-router-dom';
import { CSSTransition, TransitionGroup } from 'react-transition-group';

function AnimatedRoutes() {
  const location = useLocation();
  
  return (
    <TransitionGroup>
      <CSSTransition
        key={location.key}
        timeout={300}
        classNames="fade"
      >
        <Routes location={location}>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </CSSTransition>
    </TransitionGroup>
  );
}

// CSS
// .fade-enter { opacity: 0; }
// .fade-enter-active { opacity: 1; transition: opacity 300ms; }
// .fade-exit { opacity: 1; }
// .fade-exit-active { opacity: 0; transition: opacity 300ms; }
```
