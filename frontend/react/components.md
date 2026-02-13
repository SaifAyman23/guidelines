# React Components Guidelines

## Table of Contents
- [Overview](#overview)
- [Component Architecture](#component-architecture)
- [Functional vs Class Components](#functional-vs-class-components)
- [Props and PropTypes](#props-and-proptypes)
- [Component Composition](#component-composition)
- [Component Patterns](#component-patterns)
- [Component Organization](#component-organization)
- [Best Practices](#best-practices)

## Overview

Components are the building blocks of React applications. They are reusable, self-contained pieces of UI that encapsulate structure, behavior, and styling. Modern React emphasizes functional components with hooks over class components.

## Component Architecture

### Basic Functional Component

```jsx
import React from 'react';

/**
 * UserCard component displays user information
 * @param {Object} props - Component props
 * @param {string} props.name - User's name
 * @param {string} props.email - User's email
 * @param {string} props.avatar - URL to user's avatar
 */
function UserCard({ name, email, avatar }) {
  return (
    <div className="user-card">
      <img src={avatar} alt={name} />
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  );
}

export default UserCard;
```

### Component with Hooks

```jsx
import React, { useState, useEffect } from 'react';

function Counter({ initialCount = 0, onCountChange }) {
  const [count, setCount] = useState(initialCount);
  
  useEffect(() => {
    onCountChange?.(count);
  }, [count, onCountChange]);
  
  const increment = () => setCount(prev => prev + 1);
  const decrement = () => setCount(prev => prev - 1);
  const reset = () => setCount(initialCount);
  
  return (
    <div className="counter">
      <p>Count: {count}</p>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
      <button onClick={reset}>Reset</button>
    </div>
  );
}

export default Counter;
```

### Component with TypeScript

```tsx
import React, { FC, useState } from 'react';

interface TodoItemProps {
  id: string;
  text: string;
  completed: boolean;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

const TodoItem: FC<TodoItemProps> = ({ 
  id, 
  text, 
  completed, 
  onToggle, 
  onDelete 
}) => {
  return (
    <div className={`todo-item ${completed ? 'completed' : ''}`}>
      <input
        type="checkbox"
        checked={completed}
        onChange={() => onToggle(id)}
      />
      <span>{text}</span>
      <button onClick={() => onDelete(id)}>Delete</button>
    </div>
  );
};

export default TodoItem;
```

## Functional vs Class Components

### Functional Components (Recommended)

Functional components are the modern standard in React. They're simpler, more concise, and support hooks.

```jsx
import React, { useState, useEffect } from 'react';

function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    let isMounted = true;
    
    async function fetchUser() {
      try {
        setLoading(true);
        const response = await fetch(`/api/users/${userId}`);
        const data = await response.json();
        
        if (isMounted) {
          setUser(data);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err.message);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    
    fetchUser();
    
    return () => {
      isMounted = false;
    };
  }, [userId]);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user found</div>;
  
  return (
    <div className="user-profile">
      <h2>{user.name}</h2>
      <p>{user.email}</p>
      <p>{user.bio}</p>
    </div>
  );
}

export default UserProfile;
```

### Class Components (Legacy)

Class components are still supported but not recommended for new code.

```jsx
import React, { Component } from 'react';

class UserProfile extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: null,
      loading: true,
      error: null
    };
  }
  
  componentDidMount() {
    this.fetchUser();
  }
  
  componentDidUpdate(prevProps) {
    if (prevProps.userId !== this.props.userId) {
      this.fetchUser();
    }
  }
  
  componentWillUnmount() {
    this.isMounted = false;
  }
  
  async fetchUser() {
    const { userId } = this.props;
    this.isMounted = true;
    
    try {
      this.setState({ loading: true });
      const response = await fetch(`/api/users/${userId}`);
      const data = await response.json();
      
      if (this.isMounted) {
        this.setState({ user: data, error: null });
      }
    } catch (error) {
      if (this.isMounted) {
        this.setState({ error: error.message });
      }
    } finally {
      if (this.isMounted) {
        this.setState({ loading: false });
      }
    }
  }
  
  render() {
    const { user, loading, error } = this.state;
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!user) return <div>No user found</div>;
    
    return (
      <div className="user-profile">
        <h2>{user.name}</h2>
        <p>{user.email}</p>
        <p>{user.bio}</p>
      </div>
    );
  }
}

export default UserProfile;
```

## Props and PropTypes

### Props Basics

```jsx
import React from 'react';

// Destructuring props in parameters
function Greeting({ name, age, isAdmin }) {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>Age: {age}</p>
      {isAdmin && <span>Admin Badge</span>}
    </div>
  );
}

// Default props
Greeting.defaultProps = {
  age: 18,
  isAdmin: false
};

export default Greeting;
```

### PropTypes Validation

```jsx
import React from 'react';
import PropTypes from 'prop-types';

function Article({ title, author, publishedDate, tags, onRead }) {
  return (
    <article>
      <h2>{title}</h2>
      <p>By {author.name}</p>
      <time>{publishedDate.toLocaleDateString()}</time>
      <div className="tags">
        {tags.map(tag => <span key={tag}>{tag}</span>)}
      </div>
      <button onClick={onRead}>Read More</button>
    </article>
  );
}

Article.propTypes = {
  title: PropTypes.string.isRequired,
  author: PropTypes.shape({
    name: PropTypes.string.isRequired,
    email: PropTypes.string
  }).isRequired,
  publishedDate: PropTypes.instanceOf(Date).isRequired,
  tags: PropTypes.arrayOf(PropTypes.string),
  onRead: PropTypes.func
};

Article.defaultProps = {
  tags: [],
  onRead: () => {}
};

export default Article;
```

### TypeScript Props (Preferred)

```tsx
import React, { FC, ReactNode } from 'react';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  children: ReactNode;
  onClick?: () => void;
  className?: string;
}

const Button: FC<ButtonProps> = ({ 
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  children,
  onClick,
  className = ''
}) => {
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    className
  ].filter(Boolean).join(' ');
  
  return (
    <button
      className={classes}
      disabled={disabled || loading}
      onClick={onClick}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};

export default Button;
```

### Children Props

```jsx
import React from 'react';

// Simple children
function Card({ children }) {
  return (
    <div className="card">
      {children}
    </div>
  );
}

// Render props pattern
function DataProvider({ render, data }) {
  return render(data);
}

// Usage
<DataProvider 
  data={{ name: 'John' }}
  render={(data) => <div>{data.name}</div>}
/>

// Children as function
function Toggle({ children }) {
  const [on, setOn] = React.useState(false);
  
  return children({
    on,
    toggle: () => setOn(!on)
  });
}

// Usage
<Toggle>
  {({ on, toggle }) => (
    <button onClick={toggle}>
      {on ? 'ON' : 'OFF'}
    </button>
  )}
</Toggle>
```

## Component Composition

### Basic Composition

```jsx
import React from 'react';

// Base components
function Header({ children }) {
  return <header className="header">{children}</header>;
}

function Main({ children }) {
  return <main className="main">{children}</main>;
}

function Footer({ children }) {
  return <footer className="footer">{children}</footer>;
}

// Composed layout
function Layout({ children }) {
  return (
    <div className="layout">
      <Header>
        <h1>My App</h1>
        <nav>Navigation</nav>
      </Header>
      <Main>{children}</Main>
      <Footer>© 2024 My App</Footer>
    </div>
  );
}

export default Layout;
```

### Composition vs Inheritance

React recommends composition over inheritance. Use containment and specialization.

```jsx
import React from 'react';

// Containment - components contain other components
function Dialog({ title, children }) {
  return (
    <div className="dialog">
      <h2>{title}</h2>
      <div className="dialog-content">
        {children}
      </div>
    </div>
  );
}

// Specialization - specific version of generic component
function WelcomeDialog() {
  return (
    <Dialog title="Welcome">
      <p>Thank you for visiting our application!</p>
    </Dialog>
  );
}

// Multiple slots
function SplitPane({ left, right }) {
  return (
    <div className="split-pane">
      <div className="split-pane-left">{left}</div>
      <div className="split-pane-right">{right}</div>
    </div>
  );
}

// Usage
function App() {
  return (
    <SplitPane
      left={<Contacts />}
      right={<Chat />}
    />
  );
}
```

### Compound Components

```jsx
import React, { createContext, useContext, useState } from 'react';

// Tabs context
const TabsContext = createContext();

function Tabs({ children, defaultTab }) {
  const [activeTab, setActiveTab] = useState(defaultTab);
  
  return (
    <TabsContext.Provider value={{ activeTab, setActiveTab }}>
      <div className="tabs">{children}</div>
    </TabsContext.Provider>
  );
}

function TabList({ children }) {
  return <div className="tab-list">{children}</div>;
}

function Tab({ id, children }) {
  const { activeTab, setActiveTab } = useContext(TabsContext);
  const isActive = activeTab === id;
  
  return (
    <button
      className={`tab ${isActive ? 'active' : ''}`}
      onClick={() => setActiveTab(id)}
    >
      {children}
    </button>
  );
}

function TabPanels({ children }) {
  return <div className="tab-panels">{children}</div>;
}

function TabPanel({ id, children }) {
  const { activeTab } = useContext(TabsContext);
  
  if (activeTab !== id) return null;
  
  return <div className="tab-panel">{children}</div>;
}

// Compose compound component
Tabs.List = TabList;
Tabs.Tab = Tab;
Tabs.Panels = TabPanels;
Tabs.Panel = TabPanel;

// Usage
function App() {
  return (
    <Tabs defaultTab="home">
      <Tabs.List>
        <Tabs.Tab id="home">Home</Tabs.Tab>
        <Tabs.Tab id="profile">Profile</Tabs.Tab>
        <Tabs.Tab id="settings">Settings</Tabs.Tab>
      </Tabs.List>
      <Tabs.Panels>
        <Tabs.Panel id="home">Home Content</Tabs.Panel>
        <Tabs.Panel id="profile">Profile Content</Tabs.Panel>
        <Tabs.Panel id="settings">Settings Content</Tabs.Panel>
      </Tabs.Panels>
    </Tabs>
  );
}

export default Tabs;
```

## Component Patterns

### Higher-Order Components (HOC)

HOCs are functions that take a component and return a new component with additional props or behavior.

```jsx
import React from 'react';

// Basic HOC
function withLoading(Component) {
  return function WithLoadingComponent({ isLoading, ...props }) {
    if (isLoading) {
      return <div>Loading...</div>;
    }
    return <Component {...props} />;
  };
}

// HOC with configuration
function withAuth(Component, { requiredRole } = {}) {
  return function WithAuthComponent(props) {
    const { user } = useAuth(); // Custom hook
    
    if (!user) {
      return <Redirect to="/login" />;
    }
    
    if (requiredRole && user.role !== requiredRole) {
      return <div>Unauthorized</div>;
    }
    
    return <Component {...props} user={user} />;
  };
}

// HOC with data fetching
function withData(Component, dataSource) {
  return function WithDataComponent(props) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
      let isMounted = true;
      
      dataSource().then(result => {
        if (isMounted) {
          setData(result);
          setLoading(false);
        }
      });
      
      return () => { isMounted = false; };
    }, []);
    
    return (
      <Component 
        {...props} 
        data={data} 
        loading={loading} 
      />
    );
  };
}

// Usage
const UserList = withAuth(
  withLoading(
    withData(UserListComponent, fetchUsers)
  ),
  { requiredRole: 'admin' }
);
```

### Render Props Pattern

```jsx
import React, { useState } from 'react';

// Mouse tracker with render prop
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  
  const handleMouseMove = (event) => {
    setPosition({
      x: event.clientX,
      y: event.clientY
    });
  };
  
  return (
    <div 
      onMouseMove={handleMouseMove}
      style={{ height: '100vh' }}
    >
      {render(position)}
    </div>
  );
}

// Usage
function App() {
  return (
    <MouseTracker
      render={({ x, y }) => (
        <div>
          <h1>Move the mouse around!</h1>
          <p>Current position: ({x}, {y})</p>
        </div>
      )}
    />
  );
}

// Or with children as function
function DataFetcher({ url, children }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [url]);
  
  return children({ data, loading, error });
}

// Usage
<DataFetcher url="/api/users">
  {({ data, loading, error }) => {
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error!</div>;
    return <UserList users={data} />;
  }}
</DataFetcher>
```

### Custom Hooks Pattern (Preferred over HOC/Render Props)

```jsx
import { useState, useEffect } from 'react';

// Custom hook for data fetching
function useDataFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    let isMounted = true;
    
    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(url);
        const result = await response.json();
        
        if (isMounted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    
    fetchData();
    
    return () => { isMounted = false; };
  }, [url]);
  
  return { data, loading, error };
}

// Usage in component
function UserList() {
  const { data: users, loading, error } = useDataFetch('/api/users');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

### Container/Presentational Pattern

```jsx
// Presentational Component (UI only)
function UserListView({ users, onUserClick, loading }) {
  if (loading) {
    return <div>Loading users...</div>;
  }
  
  return (
    <ul className="user-list">
      {users.map(user => (
        <li key={user.id} onClick={() => onUserClick(user)}>
          <img src={user.avatar} alt={user.name} />
          <span>{user.name}</span>
        </li>
      ))}
    </ul>
  );
}

// Container Component (logic)
function UserListContainer() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  
  useEffect(() => {
    fetch('/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data);
        setLoading(false);
      });
  }, []);
  
  const handleUserClick = (user) => {
    navigate(`/users/${user.id}`);
  };
  
  return (
    <UserListView
      users={users}
      loading={loading}
      onUserClick={handleUserClick}
    />
  );
}

export default UserListContainer;
```

### Provider Pattern

```jsx
import React, { createContext, useContext, useState } from 'react';

// Create context
const ThemeContext = createContext();

// Provider component
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };
  
  const value = {
    theme,
    toggleTheme
  };
  
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

// Custom hook for consuming context
export function useTheme() {
  const context = useContext(ThemeContext);
  
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  
  return context;
}

// Usage in component
function ThemedButton() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <button 
      className={`btn btn-${theme}`}
      onClick={toggleTheme}
    >
      Toggle Theme
    </button>
  );
}

// App setup
function App() {
  return (
    <ThemeProvider>
      <ThemedButton />
    </ThemeProvider>
  );
}
```

## Component Organization

### File Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.test.tsx
│   │   │   ├── Button.module.css
│   │   │   └── index.ts
│   │   ├── Input/
│   │   └── Card/
│   ├── features/
│   │   ├── UserProfile/
│   │   │   ├── UserProfile.tsx
│   │   │   ├── UserProfile.test.tsx
│   │   │   ├── UserAvatar.tsx
│   │   │   ├── UserBio.tsx
│   │   │   └── index.ts
│   │   └── TodoList/
│   └── layouts/
│       ├── MainLayout/
│       └── AuthLayout/
```

### Component File Template

```tsx
// Button/Button.tsx
import React, { FC, ButtonHTMLAttributes } from 'react';
import styles from './Button.module.css';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

/**
 * Button component with multiple variants and sizes
 * 
 * @example
 * ```tsx
 * <Button variant="primary" size="md" onClick={handleClick}>
 *   Click me
 * </Button>
 * ```
 */
export const Button: FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  className = '',
  children,
  ...props
}) => {
  const classes = [
    styles.button,
    styles[variant],
    styles[size],
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
};

export default Button;
```

```typescript
// Button/index.ts
export { Button, type ButtonProps } from './Button';
export { default } from './Button';
```

## Best Practices

### 1. Keep Components Small and Focused

```jsx
// Bad - component doing too much
function UserDashboard() {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [comments, setComments] = useState([]);
  const [followers, setFollowers] = useState([]);
  // ... lots of logic
  
  return (
    <div>
      {/* Hundreds of lines of JSX */}
    </div>
  );
}

// Good - split into smaller components
function UserDashboard() {
  const { user } = useUser();
  
  return (
    <div className="dashboard">
      <UserHeader user={user} />
      <UserStats user={user} />
      <UserPosts userId={user.id} />
      <UserFollowers userId={user.id} />
    </div>
  );
}
```

### 2. Use Descriptive Names

```jsx
// Bad
function UC({ u, p }) {
  return <div>{u.n}</div>;
}

// Good
function UserCard({ user, showProfile }) {
  return <div>{user.name}</div>;
}
```

### 3. Avoid Prop Drilling

```jsx
// Bad - prop drilling
function App() {
  const [user, setUser] = useState(null);
  return <Dashboard user={user} />;
}

function Dashboard({ user }) {
  return <Sidebar user={user} />;
}

function Sidebar({ user }) {
  return <UserMenu user={user} />;
}

// Good - use context
const UserContext = createContext();

function App() {
  const [user, setUser] = useState(null);
  
  return (
    <UserContext.Provider value={user}>
      <Dashboard />
    </UserContext.Provider>
  );
}

function UserMenu() {
  const user = useContext(UserContext);
  return <div>{user.name}</div>;
}
```

### 4. Memoize Expensive Computations

```jsx
import React, { useMemo } from 'react';

function ProductList({ products, filters }) {
  // Memoize filtered products
  const filteredProducts = useMemo(() => {
    return products.filter(product => {
      return Object.entries(filters).every(([key, value]) => {
        return product[key] === value;
      });
    });
  }, [products, filters]);
  
  return (
    <ul>
      {filteredProducts.map(product => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
```

### 5. Handle Errors Gracefully

```jsx
import React, { Component } from 'react';

// Error Boundary
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('Error caught:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
        </div>
      );
    }
    
    return this.props.children;
  }
}

// Usage
function App() {
  return (
    <ErrorBoundary>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

### 6. Use Fragments to Avoid Extra DOM Nodes

```jsx
// Bad - adds unnecessary div
function List() {
  return (
    <div>
      <li>Item 1</li>
      <li>Item 2</li>
    </div>
  );
}

// Good - use fragment
function List() {
  return (
    <>
      <li>Item 1</li>
      <li>Item 2</li>
    </>
  );
}
```

### 7. Conditional Rendering Patterns

```jsx
function Component({ condition, data }) {
  // Ternary for simple conditions
  return condition ? <ComponentA /> : <ComponentB />;
  
  // Logical && for single condition
  return data && <Display data={data} />;
  
  // Early return for complex conditions
  if (!data) return null;
  if (data.error) return <Error error={data.error} />;
  
  return <Display data={data} />;
}
```

### 8. List Keys

```jsx
// Bad - using index as key (avoid unless list never changes)
{items.map((item, index) => (
  <div key={index}>{item.name}</div>
))}

// Good - using unique ID
{items.map(item => (
  <div key={item.id}>{item.name}</div>
))}

// Good - generating stable key
{items.map(item => (
  <div key={`${item.type}-${item.name}`}>
    {item.name}
  </div>
))}
```

### 9. Controlled vs Uncontrolled Components

```jsx
// Controlled component (recommended)
function ControlledInput() {
  const [value, setValue] = useState('');
  
  return (
    <input 
      value={value}
      onChange={(e) => setValue(e.target.value)}
    />
  );
}

// Uncontrolled component (use for simple forms)
function UncontrolledInput() {
  const inputRef = useRef();
  
  const handleSubmit = () => {
    console.log(inputRef.current.value);
  };
  
  return (
    <input ref={inputRef} defaultValue="Hello" />
  );
}
```

### 10. Component Documentation

```tsx
/**
 * Modal component for displaying content in an overlay
 * 
 * @component
 * @example
 * ```tsx
 * <Modal
 *   isOpen={true}
 *   onClose={handleClose}
 *   title="Confirm Action"
 * >
 *   <p>Are you sure?</p>
 * </Modal>
 * ```
 */
interface ModalProps {
  /** Controls modal visibility */
  isOpen: boolean;
  /** Callback when modal should close */
  onClose: () => void;
  /** Modal title */
  title?: string;
  /** Modal content */
  children: ReactNode;
  /** Optional CSS class name */
  className?: string;
}

const Modal: FC<ModalProps> = ({ 
  isOpen, 
  onClose, 
  title, 
  children,
  className 
}) => {
  // Component implementation
};
```
